from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient

subscription_id = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"

resource_group = "bnlwe-cc01-d-00000-mic-rg"
zone_name = "web1.com"

credential = DefaultAzureCredential()

client = DnsManagementClient(
    credential,
    subscription_id
)

print("=" * 90)
print(f"DNS Records for {zone_name}")
print("=" * 90)

records = client.record_sets.list_by_dns_zone(
    resource_group_name=resource_group,
    zone_name=zone_name
)

for record in records:

    print(f"Name       : {record.name}")
    print(f"Type       : {record.type.split('/')[-1]}")
    print(f"TTL        : {record.ttl}")

    if record.a_records:
        for a in record.a_records:
            print(f"Address    : {a.ipv4_address}")

    if record.aaaa_records:
        for aaaa in record.aaaa_records:
            print(f"Address    : {aaaa.ipv6_address}")

    if record.cname_record:
        print(f"CNAME      : {record.cname_record.cname}")

    if record.mx_records:
        for mx in record.mx_records:
            print(f"MX         : {mx.preference} {mx.exchange}")

    if record.txt_records:
        for txt in record.txt_records:
            print(f"TXT        : {' '.join(txt.value)}")

    print("-" * 90)

