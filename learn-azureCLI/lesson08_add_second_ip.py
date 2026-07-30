from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import ARecord

subscription_id = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"

resource_group = "bnlwe-cc01-d-00000-mic-rg"
zone_name = "web1.com"
record_name = "sdktest"

credential = DefaultAzureCredential()

client = DnsManagementClient(
    credential,
    subscription_id
)

# Step 1: Read the existing record set
record_set = client.record_sets.get(
    resource_group_name=resource_group,
    zone_name=zone_name,
    relative_record_set_name=record_name,
    record_type="A"
)

print("Existing IPs:")
for record in record_set.a_records:
    print(f" - {record.ipv4_address}")

# Step 2: Add another IP
new_ip = "30.30.30.30"

record_set.a_records.append(
    ARecord(ipv4_address=new_ip)
)

# Step 3: Write the updated record set back
client.record_sets.create_or_update(
    resource_group_name=resource_group,
    zone_name=zone_name,
    relative_record_set_name=record_name,
    record_type="A",
    parameters=record_set
)

print(f"\nAdded {new_ip} successfully.")
