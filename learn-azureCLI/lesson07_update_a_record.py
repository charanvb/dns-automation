from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import RecordSet, ARecord

subscription_id = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"

resource_group = "bnlwe-cc01-d-00000-mic-rg"
zone_name = "web1.com"

credential = DefaultAzureCredential()

client = DnsManagementClient(
    credential,
    subscription_id
)

record = RecordSet(
    ttl=300,
    a_records=[
        ARecord(ipv4_address="20.20.20.20")
    ]
)

client.record_sets.create_or_update(
    resource_group_name=resource_group,
    zone_name=zone_name,
    relative_record_set_name="sdktest",
    record_type="A",
    parameters=record
)

print("Record Updated")
