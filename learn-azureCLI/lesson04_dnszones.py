from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient

# Subscription containing the DNS zones
subscription_id = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"

credential = DefaultAzureCredential()

client = DnsManagementClient(
    credential,
    subscription_id
)

print("=" * 70)
print("Azure DNS Zones")
print("=" * 70)

for zone in client.zones.list():

    print(f"Zone Name      : {zone.name}")
    print(f"Resource Group : {zone.id.split('/')[4]}")
    print(f"Location       : {zone.location}")
    print(f"Zone Type      : {zone.zone_type}")

    print("-" * 70)
