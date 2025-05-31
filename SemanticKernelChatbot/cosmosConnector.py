# # cosmosConnector.py
# from models.converterModels import PowerConverter
# import os
# from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql import (
#     AzureCosmosDBNoSQLMemoryStore)
# from azure.cosmos.aio import CosmosClient  
# import os
# from typing import List, Optional

# from models.converterVectorStoreModels import PowerConverterVector
# from azure.cosmos import PartitionKey
# from langchain_openai import AzureOpenAIEmbeddings


# class CosmosLampHandler:
#     def __init__(self):
#         self.client = CosmosClient(
#             os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
#             os.getenv("AZURE_COSMOS_DB_KEY")
#         )
#         self.database = self.client.get_database_client("tal_db")
#         self.container = self.database.get_container_client("converters")


#         self.memory_store = AzureCosmosDBNoSQLMemoryStore(
#             cosmos_client=self.client,
#             database_name="tal_db"  
#         )

#         self.embedding_model = AzureOpenAIEmbeddings(
#             azure_endpoint=os.environ["OPENAI_API_ENDPOINT"],
#             azure_deployment=os.environ["OPENAI_EMBEDDINGS_MODEL_DEPLOYMENT"],
#             api_key=os.environ["AZURE_OPENAI_API_KEY"]
#         )

#     async def initialize(self):
#         partition_key = PartitionKey(path="/ARTNR")
#         await self.memory_store.create_collection(collection_name="converters", 
#                                                   data_model=PowerConverterVector,
#                                                   partition_key=partition_key)
    
#     async def _generate_embedding(self, query: str) -> List[float]:
#         """Generate embedding for the given query using the Azure OpenAI model."""
#         embedding = await self.embedding_model.embed_query(query)
#         return embedding
    

#     # Hardcoded querying

#     async def get_compatible_lamps(self, artnr: int):
#         parameters = [{"name": "@artnr", "value": artnr}]
#         query = "SELECT c.lamps FROM c WHERE c.ARTNR = @artnr"
#         results = self.container.query_items(
#             query=query,
#             parameters=parameters        )
#         return [list(item["lamps"].keys()) async for item in results][0]

#     async def get_converters_by_lamp_type(self, lamp_type: str):
#         # Use bracket notation for property names
#         query = f"""
#         SELECT *
#         FROM c 
#         WHERE IS_DEFINED(c.lamps['{lamp_type}'])
#         """
#         results = self.container.query_items(
#             query=query        )
        
#         converters = []
#         async for item in results:
#             converters.append(PowerConverter(**item))
#         return converters

    
#     async def get_lamp_limits(self, artnr: int, lamp_type: str):
#         parameters = [{"name": "@artnr", "value": artnr}]
#         query = f"""
#         SELECT VALUE {{
#             "min": c.lamps['{lamp_type}'].min,
#             "max": c.lamps['{lamp_type}'].max
#         }} FROM c WHERE c.ARTNR = @artnr
#         """
#         results = self.container.query_items(
#             query=query,
#             parameters=parameters        )
#         return [item async for item in results][0]
    
#     async def hybrid_search(self, query: str, artnr: Optional[int] = None) -> List[dict]:
#         # Generate query embedding
#         query_embedding = await self._generate_embedding(query)
        
#         # Vector similarity search
#         results = await self.memory_store.get_nearest_matches(
#             collection_name="converters",
#             embedding=query_embedding,
#             min_relevance_score=0.7,
#             limit=5
#         )
        
#         # Convert to Cosmos DB query
#         ids = [record.id for record, _ in results]
#         sql_query = f"SELECT * FROM c WHERE c.id IN ({','.join(f'\"{id}\"' for id in ids)})"
        
#         if artnr:
#             parameters = [{"name": "@artnr", "value": artnr}]
#             sql_query += " AND c.ARTNR = @artnr"
            
#         return await self.execute_sql_query(sql_query)

#     async def execute_sql_query(self, query: str) -> List[dict]:
#         """Execute raw SQL query"""
#         items = []
#         async for item in self.container.query_items(query=query, enable_cross_partition_query=True):
#             items.append(item)
#         return items