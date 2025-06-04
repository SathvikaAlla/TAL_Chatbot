# cosmosConnector.py
from models.converterModels import PowerConverter
import os
from azure.cosmos import CosmosClient
from typing import List, Optional, Dict
from rapidfuzz import fuzz
import logging
import os
from dotenv import load_dotenv

load_dotenv()
# Initialize logging
logger = logging.getLogger(__name__)

class CosmosLampHandler:
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.client = CosmosClient(
            os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
            os.getenv("AZURE_COSMOS_DB_KEY")
        )
        self.database = self.client.get_database_client("TAL_DB")
        self.container = self.database.get_container_client("Converters")
        self.logger = logger

    async def get_compatible_lamps(self, artnr: int) -> List[str]:
        """Get compatible lamps for a converter with fuzzy matching"""
        try:
            parameters = [{"name": "@artnr", "value": artnr}]
            query = "SELECT * FROM c WHERE c.artnr = @artnr"
            
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
            WHERE c.artnr = @artnr
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
    


    async def query_converters(self, query: str) -> str:
        try:
            print(f"Executing query: {query}")
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            print(f"Query returned {len(items)} items")
            items = items[:10] 
            # self.logger.debug(f"Raw items: {items}")

            items = [PowerConverter(**item) for item in items] if items else []

            self.logger.info(f"Query returned {len(items)} items after conversion")            

            return str(items)
        except Exception as e:
            self.logger.info(f"Query failed: {str(e)}")
            return f"Query failed: {str(e)}"
