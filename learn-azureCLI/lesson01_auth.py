from azure.identity import DefaultAzureCredential

print("=" * 60)
print("Azure Authentication Demo")
print("=" * 60)

credential = DefaultAzureCredential()

print("Credential object created.")

token = credential.get_token(
    "https://management.azure.com/.default"
)

print()
print("Authentication successful!")
print()
print(f"Token expires : {token.expires_on}")
print(f"Access token  : {token.token[:60]}...")
