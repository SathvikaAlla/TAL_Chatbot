import logging
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from azure.cosmos import CosmosClient
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from models.converterModels import PowerConverter  
from plugins.converterPlugin import ConverterPlugin
import os
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("kernel")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s"
))
logger.addHandler(handler)


# Initialize Semantic Kernel
kernel = Kernel()

# Add Azure OpenAI Chat Service
kernel.add_service(AzureChatCompletion(
    service_id="chat",
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY")
))

# SQL Generation Plugin
class NL2SQLPlugin:
    @kernel_function(name="generate_sql", description="Generate Cosmos DB SQL query")
    async def generate_sql(self, question: str) -> str:
        sql = await self._generate_sql_helper(question)
        # if ["DELETE", "UPDATE", "INSERT"] in sql:
        #     return ""
        if "FROM converters c" in sql:
            sql = sql.replace("FROM converters c", "FROM c")
        if "SELECT *" not in sql and "FROM c" in sql:
            sql = sql.replace("SELECT c.*,", "SELECT *")
            sql = sql.replace("SELECT c.*", "SELECT *")
            sql = sql.replace("SELECT c", "SELECT *")

        return sql

    async def _generate_sql_helper(self, question: str) -> str:
        from semantic_kernel.contents import ChatHistory
        
        chat_service = kernel.get_service("chat")
        chat_history = ChatHistory()
        chat_history.add_user_message(f"""Convert to Cosmos DB SQL: {question}
            Collection: converters (alias 'c')
            Fields:
                - type (e.g., '350mA')
                - artnr (numeric (int) article number e.g., 930546)
                - output_voltage_v: dictionary with min/max values for output voltage
                - output_voltage_v.min (e.g., 15)
                - output_voltage_v.max (e.g., 40)
                - nom_input_voltage_v: dictionary with min/max values for input voltage
                - nom_input_voltage_v.min (e.g., 198)
                - nom_input_voltage_v.max (e.g., 264)
                - lamps: dictionary with min/max values for lamp types for this converter
                - lamps["lamp_name"].min (e.g., 1)
                - lamps["lamp_name"].max (e.g., 10)
                - nom_input_voltage (e.g, '198-264V')
                - class (safety class)
                - dimmability (e.g., 'MAINS DIM LC')
                - listprice (e.g., 58)
                - lifecycle (e.g., 'Active')
                - size (e.g., '150x30x30')
                - dimlist_type (e.g., 'DALI')
                - pdf_link (link to product PDF)
                - converter_description (e.g., 'POWERLED CONVERTER REMOTE 180mA 8W IP20 1-10V')
                - ip (Ingress Protection, integer values e.g., 20,67)
                - efficiency_full_load (e.g., 0.9)
                - name (e.g., 'Power Converter 350mA')
                - unit (e.g., 'PC')
            Return ONLY SQL without explanations""")
        
        response = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=AzureChatPromptExecutionSettings()
        )
        
        return str(response)
    

# Register plugins
kernel.add_plugin(ConverterPlugin(logger=logger), "CosmosDBPlugin")
kernel.add_plugin(NL2SQLPlugin(), "NL2SQLPlugin")

# Updated query handler using function calling
async def handle_query(user_input: str):
    
    settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True)        
        )
    
    prompt = f"""
    You are a converter database expert. Process this user query:
    {user_input}
    
    Available functions:
    - generate_sql: Creates SQL queries (use only for complex queries or schema keywords)
    - query_converters: Executes SQL queries
    - get_compatible_lamps: Simple ARTNR-based lamp queries
    - get_converters_by_lamp_type: Simple lamp type searches
    - get_lamp_limits: Simple ARTNR+lamp combinations
    
    Decision Flow:
    1. Use simple functions if query matches these patterns:
       - "lamps for [ARTNR]" → get_compatible_lamps
       - "converters for [lamp type]" → get_converters_by_lamp_type
       - "min/max [lamp] for [ARTNR]" → get_lamp_limits
    
    2. Use SQL generation ONLY when:
       - Query contains schema keywords: voltage, price, type, ip, efficiency, size, class, dimmability
       - Combining multiple conditions (AND/OR/NOT)
       - Needs complex filtering/sorting
       - Requesting technical specifications
    
    SQL Guidelines (if needed):
    1. Always use SELECT * instead of field lists
    2. For exact matches use: WHERE c.[field] = value
    3. For ranges use: WHERE c.[field].min >= X AND c.[field].max <= Y
    4. Limit results with SELECT TOP 10
    
    Examples:
    User: "Show IP67 converters under €100" → generate_sql
    User: "What lamps work with 930560?" → get_compatible_lamps
    User: "Voltage range for 930562" → generate_sql
    """
    
    result = await kernel.invoke_prompt(
        prompt=prompt,
        settings=settings
    )
    
    return str(result)

# Example usage
async def main():

   while True:
        try:
            query = input("User: ")
            if query.lower() in ["exit", "quit"]:
                break

            response = await handle_query(query)
            print(response)
            
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())