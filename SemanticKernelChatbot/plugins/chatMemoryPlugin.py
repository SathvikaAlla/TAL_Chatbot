#converterPlugin.py
from datetime import datetime
from typing import Annotated, Dict, List, Optional
import uuid
from CosmosDBHandlers.cosmosConnector import CosmosLampHandler
from semantic_kernel.functions import kernel_function
from CosmosDBHandlers.cosmosChatHistoryHandler import ChatMemoryHandler

class ChatMemoryPlugin:
    def __init__(self, logger):
        self.logger = logger
        self.chat_memory_handler = ChatMemoryHandler(logger)

    @kernel_function(name="log_interaction", description="Logs chat interactions")
    async def log_interaction(self, session_id: str, question: str, function_used: str, answer: str):

        try:
            await self.chat_memory_handler.log_interaction(session_id=session_id,
                                                           question=question,
                                                           function_used=function_used,
                                                           answer=answer)
        except Exception as e:
            self.logger.error(f"Failed to log chat interaction: {str(e)}")

    @kernel_function(name="log_sql_query", description="Logs generated SQL queries")
    async def log_sql_query(self, original_question: str, generated_sql: str, state:str="success"):
        
        try:
            await self.chat_memory_handler.log_sql_query(original_question=original_question,
                                                         generated_sql=generated_sql,
                                                         state=state)
        except Exception as e:
            self.logger.error(f"Failed to log SQL query: {str(e)}")
    
    @kernel_function(name="get_semantic_faqs")
    async def get_semantic_faqs(self, limit:int=6, threshold: float = 0.1) -> List[str]:
        """Retrieve FAQs using vector embeddings for semantic similarity"""
        try:
            faqs_dict = await self.chat_memory_handler.get_semantic_faqs(limit=limit+5, threshold=threshold)
            faqs = [faq["representative_question"] for faq in faqs_dict]
            
            # Remove duplicates while preserving order
            unique_faqs = list(dict.fromkeys(faqs))
            
            self.logger.info(unique_faqs)
            return unique_faqs[:limit]
        except Exception as e:
            self.logger.error(f"Semantic FAQ retrieval failed: {str(e)}")
            return []