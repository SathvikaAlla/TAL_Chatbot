# cosmosConnector.py
from jsonschema import ValidationError
from models.converterModels import PowerConverter
import os
from azure.cosmos import CosmosClient
from typing import List, Optional, Dict
from models.converterVectorStoreModels import PowerConverterVector
from langchain_openai import AzureOpenAIEmbeddings
from rapidfuzz import fuzz
import logging
import os
from dotenv import load_dotenv

load_dotenv()
# Initialize logging
logger = logging.getLogger(__name__)

class CosmosLampHandler:
    def __init__(self):
        self.client = CosmosClient(
            os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
            os.getenv("AZURE_COSMOS_DB_KEY")
        )
        self.database = self.client.get_database_client("tal_db")
        self.container = self.database.get_container_client("converters")

        self.embedding_model = AzureOpenAIEmbeddings(
            azure_endpoint=os.environ["OPENAI_API_ENDPOINT"],
            azure_deployment=os.environ["OPENAI_EMBEDDINGS_MODEL_DEPLOYMENT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"]
        )

    async def _generate_embedding(self, query: str) -> List[float]:
        """Generate embedding for the given query using Azure OpenAI"""
        try:
            return self.embedding_model.embed_query(query)
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    async def get_compatible_lamps(self, artnr: int) -> List[str]:
        """Get compatible lamps for a converter with fuzzy matching"""
        try:
            parameters = [{"name": "@artnr", "value": artnr}]
            query = "SELECT * FROM c WHERE c.ARTNR = @artnr"
            
            # Collect results properly
            results = [item for item in list(self.container.query_items(
                query=query,
                parameters=parameters
            ))]
            
            if not results:
                return []
                
            return list(results[0]["lamps"].keys())
        
        except Exception as e:
            logger.error(f"Failed to get compatible lamps: {str(e)}")
            return []
        
    async def get_converters_by_lamp_type(self, lamp_type: str, threshold: int = 75) -> List[PowerConverter]:
        """Get converters with fuzzy-matched lamp types"""
        try:
            # Case-insensitive search with fuzzy matching
            query = """
            SELECT
                *
            FROM c WHERE IS_DEFINED(c.lamps)"""
            converters = []
            results = list(self.container.query_items(
                                                    query=query,
                                                    enable_cross_partition_query=True))
            for item in results:
                lamp_keys = item.get("lamps", {}).keys()
                matches = [key for key in lamp_keys 
                          if fuzz.ratio(key.lower(), lamp_type.lower()) >= threshold]
                
                if matches:
                    converters.append(PowerConverter(**item))
            
            return converters
            
        except Exception as e:
            logger.error(f"Lamp type search failed: {str(e)}")
            return []

    
    async def get_lamp_limits(self, artnr: int, lamp_type: str) -> Dict[str, int]:
        """Get lamp limits with typo tolerance"""
        try:
            parameters = [{"name": "@artnr", "value": artnr}]
            query = """
            SELECT c.lamps FROM c 
            WHERE c.ARTNR = @artnr
            """
            results_iter = list(self.container.query_items(
                query=query,
                parameters=parameters
            ))

            results = [item for item in results_iter]  # Collect results asynchronously

            if not results:
                return {}

            lamps = results[0]["lamps"]

            # Fuzzy match lamp type
            best_match = max(
                lamps.keys(),
                key=lambda x: fuzz.ratio(x.lower(), lamp_type.lower())
            )

            if fuzz.ratio(best_match.lower(), lamp_type.lower()) < 65:
                raise ValueError("No matching lamp type found")

            return {
                "min": int(lamps[best_match]["min"]),
                "max": int(lamps[best_match]["max"])
            }

        except Exception as e:
            logger.error(f"Failed to get lamp limits: {str(e)}")
            raise

    async def hybrid_search(self, query: str, artnr: Optional[int] = None, threshold: int = 75) -> List[PowerConverterVector]:
        """Hybrid search using raw Cosmos DB vector search"""
        try:
            # Generate embedding
            query_vector = await self._generate_embedding(query)
            
            sql_query = """
                SELECT TOP 10
                    c.id,
                    c["CONVERTER DESCRIPTION:"],
                    c["IP"],
                    c["EFFICIENCY @full load"],
                    c["Name"],
                    c["ARTNR"],
                    c["TYPE"],
                    c["lamps"],
                    c["pdf_link"],
                    c["NOM. INPUT VOLTAGE (V)"],
                    c["OUTPUT VOLTAGE (V)"],
                    c["Unit"],
                    c["Listprice"],
                    c["LifeCycle"],
                    c["SIZE: L*B*H (mm)"],
                    c["CCR (AMPLITUDE)"],
                    c["DIMMABILITY"],
                    c["DIMLIST TYPE"],
                    VectorDistance(c.embedding, @vector) AS SimilarityScore
                FROM c 
                ORDER BY VectorDistance(c.embedding, @vector)
                """
            
            parameters = [{"name": "@vector", "value": query_vector}]

            # Execute query
            results = list(self.container.query_items(
                query=sql_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            items = []
            for item in results:
                items.append(item)
         
            converters = []
            for item in items:
                # Convert float values to integers before validation
                if "lamps" in item:
                    for lamp_key in item["lamps"]:
                        lamp_data = item["lamps"][lamp_key]
                        lamp_data["min"] = int(lamp_data["min"])
                        lamp_data["max"] = int(lamp_data["max"])
                if "OUTPUT VOLTAGE (V)" in item:
                    item["OUTPUT VOLTAGE (V)"] = str(item["OUTPUT VOLTAGE (V)"])
                converters.append(PowerConverterVector(**item))
                   
            return converters
        except ValidationError as exc:
            print(exc)
                
        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            print(f"Hybrid search failed: {str(e)}")
            
            
# -------------------------------------- TESTING --------------------------------------
if __name__ == "__main__":
    handler = CosmosLampHandler()
    # Example usage
    import asyncio

    async def main():
        lamps = await handler.get_compatible_lamps(930573)
        print("Compatible lamps:", lamps)

        converters = await handler.get_converters_by_lamp_type("boa wc")
        for result in converters:
            print(f"\t{result.name} (ARTNR: {result.artnr})")
            print(f"\tLamp types: {', '.join(result.lamps.keys())}\n")

        limits = await handler.get_lamp_limits(930573, "boa wc")
        print("Lamp limits:", limits)

        hybrid_results = await handler.hybrid_search("give me converters for boa wc which cost less than 50 ")
        print("Hybrid search results:")
        for result in hybrid_results:
            print(f"\t{result.converter_description} (ARTNR: {result.artnr})")
            print(f"\ttypes: {result.type}")
            print(f"\tprice: {result.price}")
            print(f'\tpdf_link: {result.pdf_link}\n')

    asyncio.run(main())