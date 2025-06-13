
# cosmosConnector.py
from jsonschema import ValidationError
from langchain_openai import AzureOpenAIEmbeddings
from models.converterModels import PowerConverter
from models.converterVectorStoreModels import PowerConverterVector
import os
from azure.cosmos import CosmosClient, PartitionKey
from typing import List, Optional, Dict
import logging
import os
from dotenv import load_dotenv
# Initialize Cosmos DB containers


cosmos_client = CosmosClient(os.getenv("COSMOS_DB_ENDPOINT"), os.getenv("COSMOS_DB_KEY"))

database = cosmos_client.create_database_if_not_exists("ChatDatabase")

# Container for chat history
chat_container = database.create_container_if_not_exists(
    id="ChatHistory",
    partition_key=PartitionKey(path="/sessionId"),
    default_ttl= 86400  # Auto-delete after 24h
)

# Container for SQL queries
sql_container = database.create_container_if_not_exists(
    id="GeneratedQueries", 
    partition_key=PartitionKey(path="/queryType")
)


