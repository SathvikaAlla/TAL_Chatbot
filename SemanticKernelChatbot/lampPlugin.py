#lampPlugin.py
from typing import Annotated, Optional
from bettercosmosConnector import CosmosLampHandler
from semantic_kernel.functions import kernel_function

class LampCompatibilityPlugin:
    def __init__(self):
        self.db = CosmosLampHandler()

    @kernel_function
    async def get_compatible_lamps(
        self,
        artnr: Annotated[int, "Converter ARTNR (partition key)"]
    ) -> str:
        """Get compatible lamps for a converter by ARTNR"""
        try:
            lamps = await self.db.get_compatible_lamps(artnr)
            # return f"Compatible lamps: {', '.join(lamps)}" if lamps else "No lamps found"
            return "\n".join([
                f"{c.model_dump()})"
                for c in lamps
            ]) if lamps else "No lamps found"
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
            if not converters:
                return "No compatible converters found"
            # return "\n".join([f"{c.name} (ARTNR: {c.artnr})\nTYPE: {c.type}\nMANUAL: {c.pdf_link}" for c in converters])
            return "\n".join([
            f"{c.model_dump()})"
            for c in converters
        ])              
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
            return f"{lamp_type}: Min {limits['min']} - Max {limits['max']} lamps"
        except Exception as e:
            return f"Error retrieving lamp limits: {str(e)}"


    @kernel_function(
        name="hybrid_search",
        description="Hybrid search for lamps or converters using semantic and keyword search"
    )
    async def hybrid_search(
        self,
        query: Annotated[str, "Free-text query for lamps or converters"],
        artnr: Annotated[Optional[int], "Optional converter ARTNR"] = None
    ) -> str:
        """
        Hybrid search: combines semantic and keyword search for robust retrieval.
        """
        results = await self.db.hybrid_search(query, artnr)
        if not results:
            return "No relevant converters found."
        # Adjust formatting as needed for your PowerConverterVector model
        return "\n".join([
            f"{c.model_dump()})"
            for c in results
        ])              