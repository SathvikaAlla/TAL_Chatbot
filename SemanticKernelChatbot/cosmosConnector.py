# cosmosConnector.py
from azure.cosmos.aio import CosmosClient  # Changed to async client
from models.converterModels import PowerConverter
import os

class CosmosLampHandler:
    def __init__(self):
        self.client = CosmosClient(
            os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
            os.getenv("AZURE_COSMOS_DB_KEY")
        )
        self.database = self.client.get_database_client("tal_db")
        self.container = self.database.get_container_client("converters")

    async def get_compatible_lamps(self, artnr: int):
        parameters = [{"name": "@artnr", "value": artnr}]
        query = "SELECT c.lamps FROM c WHERE c.ARTNR = @artnr"
        results = self.container.query_items(
            query=query,
            parameters=parameters        )
        return [list(item["lamps"].keys()) async for item in results][0]

    async def get_converters_by_lamp_type(self, lamp_type: str):
        # Use bracket notation for property names
        query = f"""
        SELECT c.ARTNR, c.CONVERTER DESCRIPTION, c.EFFICIENCY, c.IP_RATING, c.pdf_link
        FROM c 
        WHERE IS_DEFINED(c.lamps['{lamp_type}'])
        """
        results = self.container.query_items(
            query=query        )
        
        converters = []
        async for item in results:
            converters.append(PowerConverter(**item))
        return converters

    
    async def get_lamp_limits(self, artnr: int, lamp_type: str):
        parameters = [{"name": "@artnr", "value": artnr}]
        lamp_type = lamp_type.capitalize() 
        query = f"""
        SELECT VALUE {{
            "min": c.lamps['{lamp_type}'].min,
            "max": c.lamps['{lamp_type}'].max
        }} FROM c WHERE c.ARTNR = @artnr
        """
        results = self.container.query_items(
            query=query,
            parameters=parameters        )
        return [item async for item in results][0]

