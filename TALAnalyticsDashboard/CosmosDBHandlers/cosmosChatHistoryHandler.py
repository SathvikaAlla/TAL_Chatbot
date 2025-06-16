
# cosmosConnector.py
from azure.cosmos import exceptions
from datetime import datetime, timedelta, timezone
import uuid
from langchain_openai import AzureOpenAIEmbeddings
import os
from azure.cosmos import CosmosClient, PartitionKey
from typing import List, Optional, Dict
import logging
import os
from dotenv import load_dotenv
load_dotenv()
# Initialize Cosmos DB containers

class ChatMemoryHandlerForAnalytics():
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.cosmos_client = CosmosClient(
            os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
            os.getenv("AZURE_COSMOS_DB_KEY")
        )
        self.logger = logger
        self.indexing_policy = {
            "indexingMode": "consistent",
            "includedPaths": [{"path": "/*"}],  # Indexes all properties, including nested
            "excludedPaths": [
                {
                    "path": '/"_etag"/?'
                },
                {
                    "path": "/embedding/*"
                }
                ],
        }


        self.vector_embedding_policy = {
            "vectorEmbeddings": [
                {
                    "path": "/embedding",
                    "dataType": "float32",
                    "distanceFunction": "cosine",
                    "dimensions": 1536,
                }
            ]
        }

        self.embedding_model = AzureOpenAIEmbeddings(
            azure_endpoint=os.environ["OPENAI_API_ENDPOINT"],
            azure_deployment=os.environ["OPENAI_EMBEDDINGS_MODEL_DEPLOYMENT"],
            api_key=os.environ["AZURE_OPENAI_KEY"]
        )

        self.database = self.cosmos_client.create_database_if_not_exists("TAL_ChatData")

        # Container for chat history
        self.chat_container = self.database.create_container_if_not_exists(
            id="ChatHistory",
            partition_key=PartitionKey(path="/functionUsed"),
            indexing_policy=self.indexing_policy,
            vector_embedding_policy=self.vector_embedding_policy
        )

        # Container for SQL queries
        self.sql_container = self.database.create_container_if_not_exists(
            id="GeneratedQueries", 
            partition_key=PartitionKey(path="/state")
        )
        
    async def _generate_embedding(self, query: str) -> List[float]:
        """Generate embedding for the given query using Azure OpenAI"""
        try:
            return self.embedding_model.embed_query(query)
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {str(e)}")
            raise

    async def get_semantic_faqs(self, limit: int = 5, threshold: float = 0.1) -> List[Dict]:
        """Retrieve FAQs using vector embeddings for semantic similarity"""
        try:            
            query = """
            SELECT c.question FROM c
            """
            raw_results = list(self.chat_container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=-1
            ))

            # Group by question in Python
            from collections import Counter
            question_counts = Counter(item['question'] for item in raw_results)
            top_questions = question_counts.most_common(limit)

            # Generate embeddings for top questions
            faq_embeddings = {}
            for question_text, count in top_questions:
                embedding = await self._generate_embedding(question_text)
                faq_embeddings[question_text] = {
                    'embedding': embedding,
                    'count': count
                }

            # Cluster similar questions
            clustered_faqs = []
            processed = set()
            
            for text, data in faq_embeddings.items():
                if text in processed:
                    continue

                query = """
                SELECT TOP 50 c.question, VectorDistance(c.embedding, @embedding) as distance
                FROM c
                ORDER BY VectorDistance(c.embedding, @embedding)
                """
                parameters = [{"name": "@embedding", "value": data['embedding']}]
                    
                similar_results = list(self.chat_container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                similarity_threshold = threshold  
                filtered_results = []
                for item in similar_results:
                    similarity = 1 - item['distance']  # Convert distance to similarity
                    if similarity <= similarity_threshold:
                        filtered_results.append(item['question'])

                # Count occurrences of similar questions
                similar_question_counts = Counter(filtered_results)
                cluster_count = sum(similar_question_counts.values())
                
                clustered_faqs.append({
                    "representative_question": text,
                    "similar_questions": list(similar_question_counts.keys()),
                    "total_occurrences": cluster_count,
                    "similarity_scores": {q: 1 - item['distance'] for item in similar_results for q in [item['question']] if 1 - item['distance'] >= similarity_threshold}
                })
                
                # Mark all similar questions as processed
                processed.update(filtered_results)
                clustered_faqs.append({
                    "representative_question": text,
                    "similar_questions": [text],
                    "total_occurrences": data['count'],
                    "similarity_scores": {text: 1.0}
                })
                processed.add(text)

            return sorted(clustered_faqs[:limit], key=lambda x: x['total_occurrences'], reverse=True)
            
        except exceptions.CosmosHttpResponseError as ex:
            print(f"Cosmos DB error: {ex}")
            self.logger.error(f"Semantic FAQ retrieval failed: {str(e)}")
            return []
        except Exception as e:
            if self.logger:
                self.logger.error(f"Semantic FAQ retrieval failed: {str(e)}")
            return []

    async def get_sql_query_statistics(self):
        """Get comprehensive SQL query statistics - CORRECTED"""
        try:
            # Get total queries
            total_query = "SELECT VALUE COUNT(1) FROM c"
            total_queries = list(self.sql_container.query_items(
                query=total_query,
                enable_cross_partition_query=True
            ))[0]
            
            # Get queries by state
            state_query = "SELECT c.state FROM c"
            state_results = list(self.sql_container.query_items(
                query=state_query,
                enable_cross_partition_query=True
            ))
            
            from collections import Counter
            state_counts = Counter(item['state'] for item in state_results)
            
            # Get top original questions
            question_query = "SELECT c.originalQuestion FROM c"
            question_results = list(self.sql_container.query_items(
                query=question_query,
                enable_cross_partition_query=True
            ))
            
            question_counts = Counter(item['originalQuestion'] for item in question_results)
            top_questions = [
                {'question': q, 'count': c} 
                for q, c in question_counts.most_common(10)
            ]
            
            return {
                'total_queries': total_queries,
                'success_count': state_counts.get('success', 0),
                'error_count': state_counts.get('error', 0),
                'null_count': state_counts.get('null', 0),  # Changed from 'failed_count'
                'top_questions': top_questions,
                'success_rate': (state_counts.get('success', 0) / total_queries * 100) if total_queries > 0 else 0
            }
        except Exception as e:
            print(f"Error getting SQL statistics: {e}")
            return {'total_queries': 0, 'success_count': 0, 'error_count': 0, 'null_count': 0, 'top_questions': [], 'success_rate': 0}


    async def get_sql_query_timeline(self, days=7):
        """Get SQL query generation timeline"""
        try:
            start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            query = f"""
            SELECT c.timestamp, c.state, c.originalQuestion
            FROM c 
            WHERE c.timestamp >= '{start_date}'
            ORDER BY c.timestamp
            """
            
            results = list(self.sql_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            timeline_data = []
            for item in results:
                date = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                timeline_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'hour': date.hour,
                    'minute': date.minute,
                    'datetime': date,
                    'state': item['state'],
                    'question': item['originalQuestion']
                })
            
            return timeline_data
        except Exception as e:
            self.logger.error(f"Error getting SQL timeline: {e}")
            return []

    async def get_recent_sql_queries(self, limit=20):
        """Get recent SQL query generations with details"""
        try:
            query = f"""
            SELECT TOP {limit} c.originalQuestion, c.generatedSql, c.state, c.timestamp
            FROM c
            ORDER BY c.timestamp DESC
            """
            
            results = list(self.sql_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return results
        except Exception as e:
            self.logger.error(f"Error getting recent SQL queries: {e}")
            return []

    async def get_sql_error_analysis(self):
        """Analyze failed SQL query patterns - CORRECTED"""
        try:
            query = """
            SELECT c.originalQuestion, c.generatedSql, c.state, c.timestamp
            FROM c
            WHERE c.state != 'success'
            ORDER BY c.timestamp DESC
            """
            
            results = list(self.sql_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return results
        except Exception as e:
            print(f"Error getting SQL error analysis: {e}")
            return []

import asyncio



handler = ChatMemoryHandlerForAnalytics()

async def main():
    faqs = await handler.get_semantic_faqs()
    for faq in faqs:
        
        print("\n",faq["representative_question"],faq["similar_questions"],"\n")

if __name__ == "__main__":
    asyncio.run(main())
