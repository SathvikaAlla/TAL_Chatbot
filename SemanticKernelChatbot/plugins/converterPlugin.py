#converterPlugin.py
from typing import Annotated, Optional
from CosmosDBHandlers.cosmosConnector import CosmosLampHandler
from semantic_kernel.functions import kernel_function

class ConverterPlugin:
    def __init__(self, logger):
        self.logger = logger
        self.db = CosmosLampHandler(logger=logger)

    
    @kernel_function(
        name="query_converters",
        description="Execute SQL query against Cosmos DB converters collection"
    )
    async def query_converters(
        self, 
        user_input:Annotated[str,"Natural Language question the user asked"],
        query: Annotated[str,"SQL generated from NL2SQL plugin"]) -> str:
        try:
            items = await self.db.query_converters(query, user_input)
            self.logger.info(f"Executed query: {query}")
            if not items:
                return "No items found for the given query."
            return str(items)
        except Exception as e:
            return f"Query failed: {str(e)}"
    
    @kernel_function(
            name = "get_converter_info",
            description="Get information about a converter using its artnr (partition key)"
    )
    async def get_converter_info(self, artnr:int) -> str:
        try:
            converter = await self.db.get_converter_info(artnr)
            self.logger.info(f"Used get_converter_info with artrn: {artnr}")
            return  f"{converter.model_dump()})"
        except Exception as e:
            f"Failed to retrieve converter {artnr} - {e}"
    
    
    
    @kernel_function
    async def get_compatible_lamps(
        self,
        artnr: Annotated[int, "Converter artnr (partition key)"]
    ) -> str:
        """Get compatible lamps for a converter by artnr"""
        try:
            lamps = await self.db.get_compatible_lamps(artnr)
            self.logger.info(f"Used get_compatible_lamps with artnr: {artnr}")
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
            return "\n".join([f"{c.model_dump()})" for c in converters]) if converters else "No converters found"
        except Exception as e:
            return f"Error retrieving converters: {str(e)}"
    
    @kernel_function(
            name="get_converters_by_dimming",
            description="Find converters of a specified dimming type"
    )
    async def get_converters_by_dimming(
        self,
        dimming_type: Annotated[str, "Dimming type mentioned like dali, mains, 1-10v"],
        voltage_current: Annotated[str | None,"Voltage or current specification like 350mA, 24V DC"] = None,
        lamp_type: Annotated[str | None, "Lamp model (e.g., Haloled, B4)"] = None,
        threshold: int = 75) -> str:
        """Search converters by dimming type with technical specifications"""
        try:
            converters = await self.db.get_converters_by_dimming(
                                                    dimming_type=dimming_type,
                                                    voltage_current=voltage_current,
                                                    lamp_type=lamp_type,
                                                    threshold=threshold)
            self.logger.info(f"""Used get_converters_by_dimming with dimming type: {dimming_type}
                                                                     voltage_current: {voltage_current}
                                                                     lamp_type: {lamp_type}""")
            if not converters:
                return "No relavent converters found"
            return "\n".join([f"{c.model_dump()})" for c in converters]) if converters else "No converters found"
            
        
        except Exception as e:
            return f"Error returning converters: {str(e)}"
        
    
    @kernel_function(
        name="get_lamp_limits",
        description="Get min/max lamps for a converter by artnr and lamp type"
    )
    async def get_lamp_limits(
        self,
        artnr: Annotated[int, "Converter artnr"],
        lamp_type: Annotated[str, "Lamp model (e.g., Haloled)"]
    ) -> str:
        """Get min/max lamps for a converter"""
        try:
            limits = await self.db.get_lamp_limits(artnr, lamp_type)
            self.logger.info(f"Used get_lamp_limits with ARTNR: {artnr} and lamp_type: {lamp_type}")
            return f"{lamp_type}: Min {limits['min']} - Max {limits['max']} lamps"
        except Exception as e:
            return f"Error retrieving lamp limits: {str(e)}"

    @kernel_function(
        name="get_converters_by_voltage_current",
        description="Get converters that have the mentioned input/output voltage range or current"
    )
    async def get_converters_by_voltage_current(
        self,
        artnr: Annotated[int | None, ""] = None,
        current: Annotated[str | None, "Current like 350mA, 700mA"]=None,
        input_voltage: Annotated[str | None, "Input voltage range like '198-464' NEVER ip, null if no voltage"] = None,
        output_voltage: Annotated[str | None, "Output voltage range like '24', '2-25' null if no voltage"] = None,
        lamp_type:  Annotated[str | None, "Lamp model (e.g., Haloled, B4)"] = None,
    ) -> str:
        try:
            converters = await self.db.get_converters_by_voltage_current(artnr=artnr,
                                                                current=current,
                                                                input_voltage=input_voltage,
                                                                output_voltage=output_voltage,
                                                                lamp_type=lamp_type)
            self.logger.info(f"""Used get_converters_by_voltage_current with input_voltage: {input_voltage}
                                                                     output_voltage: {output_voltage}
                                                                     current: {current}
                                                                     lamp_type: {lamp_type}
                                                                     artnr: {artnr}""")
            if not converters:
                return "No relavent converters found"
            return "\n".join([f"{c.model_dump()})" for c in converters]) if converters else "No converters found" 

        except Exception as e:
            return f"Error retrieving converters"  