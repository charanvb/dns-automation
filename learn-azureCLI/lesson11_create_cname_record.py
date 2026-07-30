from azure.identity import DefaultAzureCredential
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import (
    RecordSet,
    CnameRecord,
    RecordType
)

subscription_id = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"

resource_group = "bnlwe-cc01-d-00000-mic-rg"
zone_name = "web1.com"

record_name = "sdktestcname"
	
credential = DefaultAzureCredential()

client = DnsManagementClient(
    credential,
    subscription_id
)

record = RecordSet(
    ttl=300,
    cname_record=CnameRecord(
        cname="testcname.com"
		)
)

print(f"Creating CNAME record '{record_name}'...")

client.record_sets.create_or_update(
    resource_group_name=resource_group,
    zone_name=zone_name,
    relative_record_set_name=record_name,
    record_type=RecordType.CNAME,
    parameters=record
)

print("Done.")

