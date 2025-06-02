#converterPlugin.py
from typing import Annotated, Optional
from cosmosConnector import CosmosLampHandler
from semantic_kernel.functions import kernel_function

class ConverterPlugin:
    def __init__(self, logger):
        self.logger = logger
        self.db = CosmosLampHandler(logger=logger)

    
    @kernel_function(
        name="query_converters",
        description="Execute SQL query against Cosmos DB converters collection"
    )
    async def query_converters(self, query: str) -> str:
        try:
            items = await self.db.query_converters(query)
            self.logger.info(f"Executed query: {query}")
            if not items:
                return "No items found for the given query."
            return str(items)
        except Exception as e:
            return f"Query failed: {str(e)}"
    
    
    @kernel_function
    async def get_compatible_lamps(
        self,
        artnr: Annotated[int, "Converter ARTNR (partition key)"]
    ) -> str:
        """Get compatible lamps for a converter by ARTNR"""
        try:
            lamps = await self.db.get_compatible_lamps(artnr)
            self.logger.info(f"Used get_compatible_lamps with ARTNR: {artnr}")
            return f"Compatible lamps: {', '.join(lamps)}" if lamps else "No lamps found"
        except Exception as e:
            return f"Error retrieving compatible lamps: {str(e)}"
        
        
    @kernel_function(
        name="get_converters_by_lamp_type",
        description="Find converters compatible with a specific lamp type"
    )
    async def get_converters_by_lamp_type(
        self,
        lamp_type: Annotated[str, "Lamp model (e.g., Haloled, B4)"]
    ) -> str:
        """Find converters compatible with specific lamp type"""
        try:
            converters = await self.db.get_converters_by_lamp_type(lamp_type)
            self.logger.info(f"Used get_converters_by_lamp_type with lamp_type: {lamp_type}")
            if not converters:
                return "No compatible converters found"
            return "\n".join([f"{c.name} (ARTNR: {c.artnr})\nTYPE: {c.type}\nMANUAL: {c.pdf_link}" for c in converters])
        except Exception as e:
            return f"Error retrieving converters: {str(e)}"
        
    
    @kernel_function(
        name="get_lamp_limits",
        description="Get min/max lamps for a converter by ARTNR and lamp type"
    )
    async def get_lamp_limits(
        self,
        artnr: Annotated[int, "Converter ARTNR"],
        lamp_type: Annotated[str, "Lamp model (e.g., Haloled)"]
    ) -> str:
        """Get min/max lamps for a converter"""
        try:
            limits = await self.db.get_lamp_limits(artnr, lamp_type)
            self.logger.info(f"Used get_lamp_limits with ARTNR: {artnr} and lamp_type: {lamp_type}")
            return f"{lamp_type}: Min {limits['min']} - Max {limits['max']} lamps"
        except Exception as e:
            return f"Error retrieving lamp limits: {str(e)}"