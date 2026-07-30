from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

# Your default subscription
subscription_id = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"

credential = DefaultAzureCredential()

client = ResourceManagementClient(
    credential,
    subscription_id
)

print("=" * 60)
print("Resource Groups")
print("=" * 60)

for rg in client.resource_groups.list():
    print(f"Name     : {rg.name}")
    print(f"Location : {rg.location}")
    print("-" * 60)
