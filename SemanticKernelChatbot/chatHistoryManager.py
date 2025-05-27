from azure.cosmos import CosmosClient
from datetime import datetime
import os

class ChatHistoryManager:
    def __init__(self):
        self.client = CosmosClient(
            os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
            os.getenv("AZURE_COSMOS_DB_KEY")
        )
        self.database = self.client.get_database_client("ChatHistory")
        self.container = self.database.get_container_client("Sessions")
    
    async def store_interaction(self, session_id: str, user_query: str, response: str):
        interaction = {
            "id": str(datetime.utcnow().timestamp()),
            "sessionId": session_id,
            "userQuery": user_query,
            "botResponse": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.container.upsert_item(interaction)
