"""
DNS record validation logic.
Each validator returns a list of error strings (empty = valid).
Module 2 will wire these into the DNS request submission flow.
"""
from __future__ import annotations

import ipaddress
import re

_LABEL_RE = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$")
_WILDCARD_LABEL_RE = re.compile(r"^\*$")
MAX_FQDN_LEN = 253
MAX_LABEL_LEN = 63


def validate_hostname(label: str, *, allow_wildcard: bool = False) -> list[str]:
    errors: list[str] = []
    if allow_wildcard and label == "*":
        return errors
    if len(label) > MAX_FQDN_LEN:
        errors.append(f"Hostname exceeds {MAX_FQDN_LEN} characters.")
    parts = label.rstrip(".").split(".")
    for part in parts:
        if len(part) > MAX_LABEL_LEN:
            errors.append(f"Label '{part}' exceeds {MAX_LABEL_LEN} characters.")
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?$", part) and part:
            errors.append(f"Label '{part}' contains invalid characters.")
    return errors


def validate_a_record(value: str) -> list[str]:
    try:
        addr = ipaddress.IPv4Address(value)
        if addr.is_loopback:
            return ["A record value must not be a loopback address."]
        return []
    except ValueError:
        return [f"'{value}' is not a valid IPv4 address."]


def validate_aaaa_record(value: str) -> list[str]:
    try:
        addr = ipaddress.IPv6Address(value)
        if addr.is_loopback:
            return ["AAAA record value must not be a loopback address."]
        return []
    except ValueError:
        return [f"'{value}' is not a valid IPv6 address."]


def validate_cname_record(value: str) -> list[str]:
    return validate_hostname(value)


def validate_txt_record(value: str) -> list[str]:
    errors: list[str] = []
    if len(value) > 4096:
        errors.append("TXT record value exceeds 4096 characters.")
    # Reject obvious injection attempts
    if any(c in value for c in ["\x00", "\n", "\r"]):
        errors.append("TXT record value contains invalid control characters.")
    return errors


def validate_mx_record(value: str) -> list[str]:
    """Value should be 'priority hostname', e.g. '10 mail.example.com'."""
    errors: list[str] = []
    parts = value.split()
    if len(parts) != 2:
        return ["MX record value must be 'priority hostname', e.g. '10 mail.example.com'."]
    priority_str, hostname = parts
    try:
        prio = int(priority_str)
        if not (0 <= prio <= 65535):
            errors.append("MX priority must be 0–65535.")
    except ValueError:
        errors.append(f"'{priority_str}' is not a valid MX priority.")
    errors.extend(validate_hostname(hostname))
    return errors


def validate_srv_record(value: str) -> list[str]:
    """Value: 'priority weight port target', e.g. '0 5 80 sip.example.com'."""
    errors: list[str] = []
    parts = value.split()
    if len(parts) != 4:
        return [
            "SRV record value must be 'priority weight port target', "
            "e.g. '0 5 5060 sip.example.com'."
        ]
    for idx, (field, name) in enumerate(
        zip(parts[:3], ["priority", "weight", "port"])
    ):
        try:
            n = int(field)
            if not (0 <= n <= 65535):
                errors.append(f"SRV {name} must be 0–65535.")
        except ValueError:
            errors.append(f"'{field}' is not a valid SRV {name}.")
    errors.extend(validate_hostname(parts[3]))
    return errors


def validate_ptr_record(value: str) -> list[str]:
    return validate_hostname(value)


def validate_ns_record(value: str) -> list[str]:
    return validate_hostname(value)


VALIDATORS: dict[str, object] = {
    "A": validate_a_record,
    "AAAA": validate_aaaa_record,
    "CNAME": validate_cname_record,
    "TXT": validate_txt_record,
    "MX": validate_mx_record,
    "SRV": validate_srv_record,
    "PTR": validate_ptr_record,
    "NS": validate_ns_record,
}


def validate_record(record_type: str, value: str) -> list[str]:
    """Dispatch to the correct validator. Returns list of error strings."""
    fn = VALIDATORS.get(record_type.upper())
    if fn is None:
        return []  # OTHER type — no client-side validation
    return fn(value)  # type: ignore[call-arg]
