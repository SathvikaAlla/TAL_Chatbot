import json
import uuid
from azure.cosmos import CosmosClient, PartitionKey
import os
from dotenv import load_dotenv, find_dotenv


#use find_dotenv() to verify .env file location
print(find_dotenv())
# load defined environment variables from .env file
load_dotenv() 


file_path = "SemanticKernelImprovedRegex/converters_improved.json"

indexing_policy = {
    "indexingMode": "consistent",
    "includedPaths": [{"path": "/*"}],  
    "excludedPaths": [
        {
            "path": '/"_etag"/?'
        }
        ],
}


HOST = os.environ["AZURE_COSMOS_DB_ENDPOINT"]
KEY = os.environ["AZURE_COSMOS_DB_KEY"]

cosmos_client = CosmosClient(HOST, KEY)
database_name = "TAL_DB"
container_name = "Converters"
partition_key = PartitionKey(path="/artnr") # set ARTNR as partition key which improves performance when querying
cosmos_container_properties = {"partition_key": partition_key}

database = cosmos_client.get_database_client("TAL")

database = cosmos_client.create_database_if_not_exists(database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=partition_key,
    indexing_policy=indexing_policy,
    default_ttl=-1)

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    item["id"] = str(uuid.uuid4())
    container.create_item(item)
    # print(f"Converter with ARTNR {item["artnr"]} uploaded") log if needed


query = "SELECT VALUE COUNT(1) FROM c"
results = container.query_items(query=query, enable_cross_partition_query=True)
count_result = list(results)
count = count_result[0] if count_result else 0
print(f"Total items in container: {count}")

if count == len(data):
    print(f"\nAll {count} items uploaded successfully!")
else:
    print(f"Upload incomplete: {count} items in container, {len(data)} items expected")
