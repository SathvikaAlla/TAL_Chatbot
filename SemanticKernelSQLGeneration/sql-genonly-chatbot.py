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

# Database Plugin
class CosmosDBPlugin:
    def __init__(self):
        self.client = CosmosClient(
            os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
            os.getenv("AZURE_COSMOS_DB_KEY")
        )
        self.database = self.client.get_database_client("TAL_DB")
        self.container = self.database.get_container_client("Converters")
        self.logger = logger

    @kernel_function(
        name="query_converters",
        description="Execute SQL query against Cosmos DB converters collection"
    )
    async def query_converters(self, query: str) -> str:
        try:
            print(f"Executing query: {query}")
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            print(f"Query returned {len(items)} items")
            items = items[:10] 
            self.logger.debug(f"Raw items: {items}")

            items = [PowerConverter(**item) for item in items] if items else []

            self.logger.info(f"Query returned {len(items)} items after conversion")
            self.logger.debug(f"Items: {items}")

            

            return str(items)
        except Exception as e:
            self.logger.info(f"Query failed: {str(e)}")
            return f"Query failed: {str(e)}"

# SQL Generation Plugin
class NL2SQLPlugin:
    @kernel_function(name="generate_sql", description="Generate Cosmos DB SQL query")
    async def generate_sql(self, question: str) -> str:
        sql = await self._generate_sql_helper(question)
        if "SELECT *" not in sql and "FROM c" in sql:
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
                - input_voltage_v: dictionary with min/max values for input voltage
                - input_voltage_v.min (e.g., 198)
                - input_voltage_v.max (e.g., 264)
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
kernel.add_plugin(CosmosDBPlugin(), "CosmosDBPlugin")
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
    - generate_sql: Creates SQL queries from natural language
    - query_converters: Executes SQL queries against the database
    
    Follow these steps:
    1. Generate SQL using generate_sql
    2. Execute query with query_converters
    3. Format results into natural language response

    Query Guidelines:
    1. When performing SELECT ALL queries always use SELECT *. Never use SELECT c.* or SELECT c
    2. For questions about lamp compatibility, ALWAYS use SELECT * FROM c WHERE IS_DEFINED(c.lamps["lamp_name"])
    3. For questions about lamps that can be used with a converter, ALWAYS use SELECT c.lamps FROM c WHERE c.artnr = @artnr
    5. For questions about lamp limits, query for the lamps dictionary and return min/max values

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