# cosmosConnector.py
from jsonschema import ValidationError
from langchain_openai import AzureOpenAIEmbeddings
from models.converterModels import PowerConverter
import os
from azure.cosmos import CosmosClient, exceptions
from typing import List, Optional, Dict
import logging
import os
from dotenv import load_dotenv
from semantic_kernel.functions import kernel_function
from rapidfuzz import process, fuzz
from CosmosDBHandlers.cosmosChatHistoryHandler import ChatMemoryHandler
load_dotenv()
# Initialize logging
logger = logging.getLogger(__name__)

class CosmosLampHandler:
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.client = CosmosClient(
            os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
            os.getenv("AZURE_COSMOS_DB_KEY")
        )
        self.chat_memory_handler = ChatMemoryHandler()
        self.database = self.client.get_database_client("TAL_DB")
        self.container = self.database.get_container_client("Converters_with_embeddings")
        self.logger = logging.Logger("test")
        # self.logger = logger
        self.embedding_model = AzureOpenAIEmbeddings(
            azure_endpoint=os.environ["OPENAI_API_ENDPOINT"],
            azure_deployment=os.environ["OPENAI_EMBEDDINGS_MODEL_DEPLOYMENT"],
            api_key=os.environ["AZURE_OPENAI_KEY"]
        )
    
    def _fuzzy_match_lamp(self, query: str, targets: list[str], threshold=60) -> list:
        """Advanced partial matching"""
        from rapidfuzz import process, fuzz
        
        normalized_query = self._normalize_lamp_name(query)
        normalized_targets = [self._normalize_lamp_name(t) for t in targets]
        
        return process.extract( 
            normalized_query,
            normalized_targets,
            scorer=fuzz.token_set_ratio,
            score_cutoff=threshold
        )
    
    def _normalize_lamp_name(self,name: str) -> str:
        """Standardize lamp names for matching"""
        return (
            name.lower()
            .replace(",", ".")
            .replace("-", " ")
            .replace("/", " ")
            .translate(str.maketrans("", "", "()"))
            .strip()
        )

    async def _generate_embedding(self, query: str) -> List[float]:
        """Generate embedding for the given query using Azure OpenAI"""
        try:
            return self.embedding_model.embed_query(query)
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {str(e)}")
            raise
    
    async def get_converter_info(self, artnr:int) -> PowerConverter:
        """Get information about a converter from its artnr"""
        try:
            parameters = [{"name": "@artnr", "value": artnr}]
            query = "SELECT * FROM c WHERE c.artnr = @artnr"
            
            # Collect results properly
            result = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            )
            
            if not result:
                return None
            
            else:
                for r in result:
                 converter = PowerConverter(**r)
            
            return converter
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve converter {artnr} - {e}")
            

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
            self.logger.error(f"Failed to get compatible lamps: {str(e)}")
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
                lamp_type = self._normalize_lamp_name(lamp_type)
                matches = self._fuzzy_match_lamp(lamp_type, lamp_keys)

                if matches:
                    converters.append(PowerConverter(**item))
            
            if not converters:
                return []
            
            return converters
            
        except Exception as e:
            self.logger.error(f"Lamp type search failed: {str(e)}")
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
            lamp_keys = list(lamps.keys())

            # Fuzzy match with normalization
            matches = self._fuzzy_match_lamp(self._normalize_lamp_name(lamp_type), lamp_keys, threshold=60)
            if not matches:
                raise ValueError(f"No matching lamp type found for '{lamp_type}'")

            # Get best match from original keys using match index
            best_match = lamp_keys[matches[0][2]]

            return {
                "min": int(lamps[best_match]["min"]),
                "max": int(lamps[best_match]["max"])
            }

        except Exception as e:
            self.logger.error(f"Failed to get lamp limits: {str(e)}")
            raise
    
    async def get_converters_by_dimming(
        self,
        dimming_type: str,
        voltage_current: Optional[str] = None,
        lamp_type: Optional[str] = None,
        threshold: int = 75
    ) -> List[PowerConverter]:
        """Search converters by dimming type and voltage/current/lamp_type specifications with fuzzy matching"""
        try:
            # Base query construction
            query = "SELECT * FROM c WHERE IS_DEFINED(c.dimmability)"
            results = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            converters = []
            for item in results:
                # Fuzzy match converter type if specified
                if voltage_current:
                    item_type = item.get("type", "")
                    item_types = item_type.split(" ")
                    for conv_type in item_types: # handle types like 24V DC
                        if fuzz.ratio(conv_type.lower(), voltage_current.lower()) < threshold:
                            continue
                if lamp_type:
                    item_lamps = item.get("lamps", "")
                    lamp_type = self._normalize_lamp_name(lamp_type)
                    lamp_matches = self._fuzzy_match_lamp(lamp_type, item_lamps.keys())
                    if not lamp_matches:
                        continue

                # Fuzzy match dimming types
                if dimming_type!= None:
                    dimmability = item.get("dimmability", "")
                    match_types = dimmability.split('/')
                    match_types += dimmability.split(" ")
                    for option in match_types:
                        if fuzz.ratio(option.lower().strip(), dimming_type.lower()) >= threshold:
                            converters.append(PowerConverter(**item))
                            break
                else:
                    converters.append(PowerConverter(**item))
                    break
            
            self.logger.info(f"Found {len(converters)} converters matching criteria")
            return converters
            
        except Exception as e:
            self.logger.error(f"Dimming query failed: {str(e)}")
            return []
    
    

    async def query_converters(self, query: str, user_input:str) -> List[PowerConverter]:
        try:
            print(f"Executing query: {query}")
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            print(f"Query returned {len(items)} items")
            items = items[:10] 

            items = [PowerConverter(**item) for item in items] if items else []

            self.logger.info(f"Query returned {len(items)} items after conversion")

            if len(items)==0:
                await self.chat_memory_handler.log_sql_query(user_input, query, "null")

            else:
                await self.chat_memory_handler.log_sql_query(user_input, query, "success")

            return str(items)
        
        except exceptions.CosmosHttpResponseError as ex:
            await self.chat_memory_handler.log_sql_query(user_input, query, "error")
            print(f"Cosmos DB error: {ex}")
            self.logger.error(f"Bad request SQL failed: {str(e)}")
            return [] 
        
        except Exception as e:
            self.logger.info(f"Query failed: {str(e)}") 
            return f"Query failed: {str(e)}"
        
    
    async def get_converters_by_voltage_current(
        self,
        artnr: Optional[int] = None,
        current: Optional[str]=None,
        input_voltage: Optional[str] = None,
        output_voltage: Optional[str] = None,
        lamp_type: Optional[str] = None
    ) -> List[PowerConverter]:
        """Query converters by voltage ranges"""
        try:
            # Handle ARTNR lookup
            if artnr:
                converter = await self.get_converter_info(artnr)
                self.logger.info(f"Used converter info returned {converter}")
                return [converter] if converter else []
            
            # Parse voltage ranges
            input_min, input_max = self._parse_voltage(input_voltage) if input_voltage else (None, None)
            output_min, output_max = self._parse_voltage(output_voltage) if output_voltage else (None, None)
            normalized_lamp_type = self._normalize_lamp_name(lamp_type) if lamp_type else None

            # Build query
            query_parts = []
            if input_min and input_max:
                query_parts.append(f"c.nom_input_voltage_v.min <= {input_max} AND c.nom_input_voltage_v.max >= {input_min}")
                self.logger.info(f"c.nom_input_voltage_v.min <= {input_max} AND c.nom_input_voltage_v.max >= {input_min}")
            if output_min and output_max:
                query_parts.append(f"c.output_voltage_v.min <= {output_max} AND c.output_voltage_v.max >= {output_min}")
                self.logger.info(f"c.nom_input_voltage_v.min <= {output_max} AND c.nom_input_voltage_v.max >= {output_min}")
            if current:
                 query_parts.append(f"c.type LIKE '%{current}%'")

                
            query = "SELECT * FROM c" + (" WHERE " + " AND ".join(query_parts) if query_parts else "")
            
            results = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            converters = []
            for item in results:
                if normalized_lamp_type:
                    item_lamps = item.get("lamps", {})
                    if not item_lamps:  # Skip if no lamps data
                        continue
                        
                    lamp_matches = self._fuzzy_match_lamp(normalized_lamp_type, item_lamps.keys())
                    if not lamp_matches:  
                        continue
                
                converters.append(PowerConverter(**item))
            
            self.logger.info(f"Found {len(converters)} matching converters")
            return converters
        
        except Exception as e:
            self.logger.error(f"Voltage query failed: {str(e)}")
            return []

    def _parse_voltage(self, voltage_str: str) -> tuple[float, float]:
        import re
        voltage_str = voltage_str.strip().replace(',', '.')
        voltage_str = re.sub(r'[^0-9.\-]', '', voltage_str)
        match = re.match(r"^(\d+(?:\.\d+)?)(?:-+(\d+(?:\.\d+)?))?$", voltage_str)
        if match:
            min_v = float(match.group(1))
            max_v = float(match.group(2)) if match.group(2) else min_v
            return min_v, max_v
        else:
            return None, None 

if __name__ == "__main__":
    handler = CosmosLampHandler()
    # Example usage
    import asyncio

    async def main():
        # lamps = await handler.get_compatible_lamps(930573)
        # print("Compatible lamps:", lamps)

        # converters = await handler.get_converters_by_dimming(voltage_current="350ma",lamp_type="haloled")
        # for result in converters:
        #     print(f"\t{result.name} (ARTNR: {result.artnr})")
        #     print(f"\tLamp types: {', '.join(result.lamps.keys())}\n")

        

        conv = await handler.get_converters_by_lamp_type("boa")
        print([c.artnr for c in conv])
        limits = await handler.get_lamp_limits(930544, "boa")  
        print("Lamp limits:", limits)
        # hybrid_results = await handler.hybrid_search("give me converters for boa wc which cost less than 50 ")
        # print("Hybrid search results:")
        # for result in hybrid_results:
        #     print(f"\t{result.converter_description} (ARTNR: {result.artnr})")
        #     print(f"\ttypes: {result.type}")
        #     print(f"\tprice: {result.price}")
        #     print(f'\tpdf_link: {result.pdf_link}\n')

    asyncio.run(main())