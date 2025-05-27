# cosmos_connector.py
import json
from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql import (
    AzureCosmosDBNoSQLMemoryStore)
from azure.cosmos.aio import CosmosClient  # Changed to async client

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel import Kernel
import os
from typing import List, Tuple, Optional

from SemanticKernelChatbot.models.converterModels import PowerConverter
from azure.cosmos import PartitionKey

class CosmosDBManager:
    def __init__(self):
        self.client = CosmosClient(
            os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
            os.getenv("AZURE_COSMOS_DB_KEY")
        )
        
        self.memory_store = AzureCosmosDBNoSQLMemoryStore(
            cosmos_client=self.client,
            database_name="tal_db"  
        )

    async def initialize(self):
        partition_key = PartitionKey(path="/ARTNR")
        await self.memory_store.create_collection(collection_name="converters", 
                                                  data_model=PowerConverter,
                                                  partition_key=partition_key)


    async def hybrid_search(self, query: str, artnr: Optional[int] = None) -> List[dict]:
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        
        # Vector similarity search
        results = await self.memory_store.get_nearest_matches(
            query_embedding=query_embedding,
            min_relevance_score=0.7,
            limit=5
        )
        
        # Convert to Cosmos DB query
        ids = [record.id for record, _ in results]
        sql_query = f"SELECT * FROM c WHERE c.id IN ({','.join(f'\"{id}\"' for id in ids)})"
        
        if artnr:
            sql_query += f" AND c.ARTNR = {artnr}"
            
        return await self.execute_sql_query(sql_query)
