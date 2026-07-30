from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient

subscription_id = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"

resource_group = "bnlwe-cc01-d-00000-mic-rg"
zone_name = "web1.com"
record_name = "sdktest"

ip_to_remove = "30.30.30.30"

credential = DefaultAzureCredential()

client = DnsManagementClient(
    credential,
    subscription_id
)

# Read existing record set
record_set = client.record_sets.get(
    resource_group_name=resource_group,
    zone_name=zone_name,
    relative_record_set_name=record_name,
    record_type="A"
)

print("Before:")

for record in record_set.a_records:
    print(record.ipv4_address)

# Remove matching IP
record_set.a_records = [
    record
    for record in record_set.a_records
    if record.ipv4_address != ip_to_remove
]

# Save back to Azure
client.record_sets.create_or_update(
    resource_group_name=resource_group,
    zone_name=zone_name,
    relative_record_set_name=record_name,
    record_type="A",
    parameters=record_set
)

print("\nAfter:")

for record in record_set.a_records:
    print(record.ipv4_address)
