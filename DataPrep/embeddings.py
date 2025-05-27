# # from azure.cosmos import CosmosClient
# # import openai
# # import json
# # from dotenv import load_dotenv
# # import os

# # from dotenv import load_dotenv
# # load_dotenv(dotenv_path="/Users/alessiacolumban/TAL_Chatbot/.env")

# # # Check environment variables
# # for var in ["YOUR_COSMOS_DB_ENDPOINT", "YOUR_COSMOS_DB_KEY", "DATABASE_NAME", "CONTAINER_NAME", "OPENAI_API_BASE", "AZURE_OPENAI_API_KEY"]:
# #     if not os.getenv(var):
# #         raise ValueError(f"Missing environment variable: {var}")

# # ENDPOINT = os.getenv("YOUR_COSMOS_DB_ENDPOINT")
# # KEY = os.getenv("YOUR_COSMOS_DB_KEY")
# # DATABASE_NAME = os.getenv("DATABASE_NAME")
# # CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# # # Azure OpenAI settings
# # openai.api_type = "azure"
# # openai.api_base = os.getenv("OPENAI_API_BASE")
# # openai.api_version = "2023-05-15"
# # openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
# # EMBEDDING_MODEL = "text-embedding-ada-002"

# # # Connect to Cosmos DB
# # client = CosmosClient(ENDPOINT, KEY)
# # database = client.get_database_client(DATABASE_NAME)
# # container = database.get_container_client(CONTAINER_NAME)

# # # Fetch all documents
# # items = container.query_items(
# #     query="SELECT * FROM c",
# #     enable_cross_partition_query=True
# # )

# # # Generate and save embeddings
# # for item in items:
# #     try:
# #         text = item.get("Name", "") + ". " + item.get("CONVERTER DESCRIPTION:", "")
# #         response = openai.Embedding.create(input=text, engine=EMBEDDING_MODEL)
# #         embedding = response["data"][0]["embedding"]
# #         item["embedding"] = embedding
# #         container.upsert_item(item)
# #         print(f"Processed item: {item['id']}")
# #     except Exception as e:
# #         print(f"Error processing item {item.get('id', 'unknown')}: {str(e)}")

# # print("Embeddings generated and saved.")
# from azure.cosmos import CosmosClient
# import openai
# from dotenv import load_dotenv
# import os

# load_dotenv(dotenv_path="/Users/alessiacolumban/TAL_Chatbot/.env")

# # Check environment variables
# for var in ["YOUR_COSMOS_DB_ENDPOINT", "YOUR_COSMOS_DB_KEY", "DATABASE_NAME", "CONTAINER_NAME", "OPENAI_API_BASE", "AZURE_OPENAI_API_KEY"]:
#     if not os.getenv(var):
#         raise ValueError(f"Missing environment variable: {var}")

# ENDPOINT = os.getenv("YOUR_COSMOS_DB_ENDPOINT")
# KEY = os.getenv("YOUR_COSMOS_DB_KEY")
# DATABASE_NAME = os.getenv("DATABASE_NAME")
# CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# # Azure OpenAI settings
# openai.api_type = "azure"
# openai.api_base = os.getenv("OPENAI_API_BASE")
# openai.api_version = "2023-05-15"
# openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
# EMBEDDING_MODEL = "text-embedding-ada-002"

# # Connect to Cosmos DB
# client = CosmosClient(ENDPOINT, KEY)
# database = client.get_database_client(DATABASE_NAME)
# container = database.get_container_client(CONTAINER_NAME)

# # Fetch all documents
# items = container.query_items(
#     query="SELECT * FROM c",
#     enable_cross_partition_query=True
# )

# # Generate and save embeddings
# for item in items:
#     try:
#         # Skip if already embedded (optional)
#         if "embedding" in item:
#             print(f"Skipping item (already embedded): {item['id']}")
#             continue

#         # Get text to embed
#         name = item.get("Name", "")
#         # Check if field is "CONVERTER DESCRIPTION:" or "CONVERTER_DESCRIPTION"
#         desc = item.get("CONVERTER DESCRIPTION:", item.get("CONVERTER_DESCRIPTION", ""))
#         text = f"{name}. {desc}".strip()

#         if len(text) < 5:
#             print(f"Warning: item {item['id']} has very short text: {text}")

#         # Generate embedding
#         response = openai.Embedding.create(input=text, engine=EMBEDDING_MODEL)
#         embedding = response["data"][0]["embedding"]
#         item["embedding"] = embedding
#         container.upsert_item(item)
#         print(f"Processed item: {item['id']}")
#     except Exception as e:
#         print(f"Error processing item {item.get('id', 'unknown')}: {str(e)}")

# print("Embeddings generated and saved.")
from azure.cosmos import CosmosClient
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="/Users/alessiacolumban/TAL_Chatbot/.env")

# Env checks...
for var in ["YOUR_COSMOS_DB_ENDPOINT", "YOUR_COSMOS_DB_KEY", "DATABASE_NAME", "CONTAINER_NAME", "OPENAI_API_BASE", "AZURE_OPENAI_API_KEY"]:
    if not os.getenv(var):
        raise ValueError(f"Missing environment variable: {var}")

ENDPOINT = os.getenv("YOUR_COSMOS_DB_ENDPOINT")
KEY = os.getenv("YOUR_COSMOS_DB_KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# New Azure OpenAI client (replaces old `openai.Embedding.create`)
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2023-05-15",
    azure_endpoint=os.getenv("OPENAI_API_BASE"),
)

EMBEDDING_MODEL = "text-embedding-ada-002"

# Connect to Cosmos DB
cosmos = CosmosClient(ENDPOINT, KEY)
database = cosmos.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

# Fetch and embed documents
items = container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True)
for item in items:
    try:
        if "embedding" in item:
            print(f"Skipping item (already embedded): {item['id']}")
            continue

        name = item.get("Name", "")
        desc = item.get("CONVERTER DESCRIPTION:", item.get("CONVERTER_DESCRIPTION", ""))
        text = f"{name}. {desc}".strip()

        if len(text) < 5:
            print(f"Warning: item {item['id']} has very short text: {text}")

        # Updated embedding call
        response = client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        embedding = response.data[0].embedding
        item["embedding"] = embedding
        container.upsert_item(item)
        print(f"Processed item: {item['id']}")

    except Exception as e:
        print(f"Error processing item {item.get('id', 'unknown')}: {str(e)}")

print("Embeddings generated and saved.")
