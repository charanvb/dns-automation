from azure.identity import DefaultAzureCredential
from azure.mgmt.resource.subscriptions import SubscriptionClient

print("=" * 60)
print("Azure Subscription Demo")
print("=" * 60)

credential = DefaultAzureCredential()

client = SubscriptionClient(credential)

for sub in client.subscriptions.list():
    print(f"Name : {sub.display_name}")
    print(f"ID   : {sub.subscription_id}")
    print(f"State: {sub.state}")
    print("-" * 60)

