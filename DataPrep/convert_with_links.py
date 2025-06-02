from azure.cosmos import CosmosClient
import openai
import json
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()

# Required env vars
for var in ["YOUR_COSMOS_DB_ENDPOINT", "YOUR_COSMOS_DB_KEY", "DATABASE_NAME", "CONTAINER_NAME", "OPENAI_API_BASE", "AZURE_OPENAI_API_KEY"]:
    if not os.getenv(var):
        raise ValueError(f"Missing environment variable: {var}")

# Cosmos DB config
ENDPOINT = os.getenv("YOUR_COSMOS_DB_ENDPOINT")
KEY = os.getenv("YOUR_COSMOS_DB_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# Azure OpenAI settings
openai.api_type = "azure"
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = "2023-05-15"
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-ada-002"

# Connect to Cosmos DB
client = CosmosClient(ENDPOINT, KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

# Fetch all documents
items = container.query_items(
    query="SELECT * FROM c",
    enable_cross_partition_query=True
)

# Generate and save embeddings
for item in tqdm(items, desc="Generating embeddings"):
    try:
        name = item.get("Name", "")
        description = item.get("CONVERTER DESCRIPTION:", "")  # Adjust if key name differs
        text = f"{name}. {description}"
        response = openai.Embedding.create(input=text, engine=EMBEDDING_MODEL)
        embedding = response["data"][0]["embedding"]
        item["embedding"] = embedding
        container.upsert_item(item)
        print(f"Processed item: {item.get('id', 'unknown')}")
    except Exception as e:
        print(f"Error processing item {item.get('id', 'unknown')}: {str(e)}")

print("✅ Embeddings generated and saved.")
