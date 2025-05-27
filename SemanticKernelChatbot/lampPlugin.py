# skPlugin.py
from typing import Annotated
from semantic_kernel.functions import kernel_function
from cosmosConnector import CosmosLampHandler

class LampCompatibilityPlugin:
    def __init__(self):
        self.db = CosmosLampHandler()
    
    @kernel_function(
        description="Get compatible lamps for a converter by ARTNR",
        name="get_compatible_lamps"
    )
    async def get_compatible_lamps(
        self,
        artnr: Annotated[int, "Converter ARTNR (partition key)"]
    ) -> str:
        lamps = await self.db.get_compatible_lamps(artnr)
        return f"Compatible lamps: {', '.join(lamps)}" if lamps else "No lamps found"

    @kernel_function(
        description="Find converters compatible with specific lamp type",
        name="get_converters_by_lamp_type"
    )
    async def get_converters_by_lamp_type(
        self,
        lamp_type: Annotated[str, "Lamp model (e.g., Haloled, B4)"]
    ) -> str:

        converters = await self.db.get_converters_by_lamp_type(lamp_type)
        if not converters:
            return "No compatible converters found"
        return "\n".join([f"{c.name} (ARTNR: {c.artnr})" for c in converters])

    @kernel_function(
        description="Get min/max lamps for a converter",
        name="get_lamp_limits"
    )
    async def get_lamp_limits(
        self,
        artnr: Annotated[int, "Converter ARTNR"],
        lamp_type: Annotated[str, "Lamp model (e.g., Haloled)"]
    ) -> str:
        limits = await self.db.get_lamp_limits(artnr, lamp_type)
        return f"{lamp_type}: Min {limits['min']} - Max {limits['max']} lamps"
