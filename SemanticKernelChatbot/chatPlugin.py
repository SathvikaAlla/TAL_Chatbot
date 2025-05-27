
import os
from semantic_kernel.core_plugins import ConversationSummaryPlugin
from lampPlugin import LampCompatibilityPlugin

from semantic_kernel import Kernel

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_arguments import KernelArguments

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

class LampChatService:
    def __init__(self):
        self.kernel = Kernel()
        self._init_services()
        self._init_plugins()
    
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
    
    async def get_response(self, query: str, history: list) -> str:
        prompt = """
            [System Message]
            You are a lamp compatibility expert for TAL BV.
            Help user by giving concise and detailed answers about lamp compatibility with power converters. 
            You MUST use these functions when appropriate:
                - get_compatible_lamps for converter ARTNR questions
                - get_converters_by_lamp_type for lamp type queries
                - get_lamp_limits for min/max lamp counts
            When answering about compatible lamps list lamps in bullet points

            [User Query]
            {{$query}}
            """


        
        
        
        settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True)
        )
        args = KernelArguments(query=query, history=history, settings=settings)
        
        return await self.kernel.invoke_prompt(
            prompt=prompt,
            arguments=args,
            settings=settings
        )
