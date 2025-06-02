#converterPlugin.py
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments

class NL2SQLPlugin:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.chat_history = ChatHistory()
 
    @kernel_function(name="generate_sql", description="Generate Cosmos DB SQL query")
    async def generate_sql(self, question: str) -> str:
        return await self._generate_sql_helper(question)

    async def _generate_sql_helper(self, question: str) -> str:
        prompt = f"""Convert to Cosmos DB SQL: {question}
            Collection: converters (alias 'c')
            Fields:
                - TYPE (e.g., '350mA')
                - ARTNR (numeric (int) article number e.g., 930546)
                - "OUTPUT VOLTAGE (V)" (e.g., 27-40V)
                - lamps: dictionary with min/max values for lamp types for this converter
                - "NOM. INPUT VOLTAGE" (e.g, '198-264V')
                - CLASS (safety class)
                - DIMMABILITY (e.g., 'MAINS DIM LC')
                - Listprice (e.g., 58)
                - LifeCycle (e.g., 'Active')
                - "SIZE: L*B*H (mm)" (e.g., '150x30x30')
                - "CCR (AMPLITUDE)" (e.g., 'YES', 'NO')
                - "DIMLIST TYPE" (e.g., 'DALI')
                - pdf_link (link to product PDF)
                - embedding (vector for hybrid search)
                - "CONVERTER DESCRIPTION:" (e.g., 'POWERLED CONVERTER REMOTE 180mA 8W IP20 1-10V')
                - IP (Ingress Protection, integer values e.g., 20,67)
                - "EFFICIENCY @full load" (e.g., 0.9)
                - Name (e.g., 'Power Converter 350mA')
                - Unit (e.g., 'PC')
            Return ONLY SQL without explanations"""
        self.chat_history.add_user_message(prompt)
        
        settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True)
        )
        
        # response = await chat_service.get_chat_message_content(
        #     chat_history=chat_history,
        #     settings=settings
        # )
        args = KernelArguments(query=question, history=self.chat_history, settings=settings)
        return await self.kernel.invoke_prompt(
        prompt=prompt,
        arguments=args
    )
        
    
