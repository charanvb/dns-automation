from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import (
    RecordSet,
    TxtRecord,
    RecordType
)

subscription_id = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"

resource_group = "bnlwe-cc01-d-00000-mic-rg"
zone_name = "web1.com"
record_name = "sdktesttxt"

credential = DefaultAzureCredential()

client = DnsManagementClient(
    credential,
    subscription_id
)

record_set = RecordSet(
    ttl=300,
    txt_records=[
        TxtRecord(
            value=[
                "Hello from Azure SDK"
            ]
        )
    ]
)

print(f"Creating TXT record '{record_name}'...")

client.record_sets.create_or_update(
    resource_group_name=resource_group,
    zone_name=zone_name,
    relative_record_set_name=record_name,
    record_type=RecordType.TXT,
    parameters=record_set
)

print("Done.")
