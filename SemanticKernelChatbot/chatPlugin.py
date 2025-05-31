
import os
from semantic_kernel.core_plugins import ConversationSummaryPlugin
from lampPlugin import LampCompatibilityPlugin

from semantic_kernel import Kernel

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents.chat_history import ChatHistory

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

class LampChatService:
    def __init__(self):
        self.kernel = Kernel()
        self._init_services()
        self._init_plugins()
        self.history = ChatHistory()
    
    def _init_services(self):
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat",
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_KEY")
            )
        )
    
    def _init_plugins(self):
        self.kernel.add_plugin(LampCompatibilityPlugin(), "LampExpert")
    
    async def get_response(self, query: str) -> str:
        # prompt = """
        #     [System Message]
        #     You are a lamp compatibility expert for TAL BV.
        #     Help user by giving concise and detailed answers about lamp compatibility with power converters. 
        #     You MUST use these functions when appropriate:
        #         - get_compatible_lamps for converter ARTNR questions
        #         - get_converters_by_lamp_type for lamp type queries
        #         - get_lamp_limits for min/max lamp counts
        #         - hybrid_search when you recognize a query with different keywords
        #     When answering about compatible lamps list lamps in bullet points
        #     When answering about converters, list the artnr, name, type, and pdf_link  

        #     [User Query]
        #     {{$query}}
        #     """
        prompt = """
            [System Message]
            **Role**: You are a TAL BV lamp/converter compatibility expert with hybrid search capabilities.
            **Primary Functions**:
                1. ARTNR lookup → `get_compatible_lamps` 
                2. Lamp type → `get_converters_by_lamp_type`
                3. Technical specs → `hybrid_search`
                4. Limits → `get_lamp_limits`

            **Keyword Detection Protocol**:
            - Step 1: Scan query for:
                * ARTNR patterns: "93xxxx", "artnr", "model number"
                * Lamp types: "haloled", "B4", "LEDLINE"
                * Numeric specs: "IP67", "350mA", "€50-€100"
                * Limit terms: "minimum", "maximum", "how many"
            
            - Step 2: Match patterns to functions:
                {% if "artnr" in query|lower or any(4-6 digit number) %}
                    → get_compatible_lamps
                {% elif "type" in query|lower or lamp brands %}
                    → get_converters_by_lamp_type  
                {% elif "price"|"cost"|"spec"|"IP"|"voltage" %}
                    → hybrid_search
                {% else %}
                    → hybrid_search (fallback)
                %}

            [User Query]
            {{$query}}
            """



        settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True)
        )
        args = KernelArguments(query=query, history=self.history, settings=settings)
        
        return await self.kernel.invoke_prompt(
            prompt=prompt,
            arguments=args,
            settings=settings
        )
