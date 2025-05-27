# import os
# from openai import AzureOpenAI
# from dotenv import load_dotenv

# load_dotenv()

# client = AzureOpenAI(
#     api_version="2024-12-01-preview",
#     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
#     api_key=os.getenv("AZURE_OPENAI_API_KEY"),
# )

# conversation = []

# while True:
#     user_input = input("You: ")
#     if user_input.lower() == "quit":
#         break
#     conversation.append({"role": "user", "content": user_input})
#     response = client.chat.completions.create(
#         model="o3-mini",
#         messages=conversation
#     )
#     assistant_reply = response.choices[0].message.content
#     print("Assistant:", assistant_reply)
#     conversation.append({"role": "assistant", "content": assistant_reply})
import os
import re
from openai import AzureOpenAI
from numpy import dot, array
from numpy.linalg import norm
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

required_vars = [
    "YOUR_COSMOS_DB_ENDPOINT", "YOUR_COSMOS_DB_KEY",
    "DATABASE_NAME", "CONTAINER_NAME",
    "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"
]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing environment variable: {var}")

# --- Cosmos DB setup ---
cosmos_client = CosmosClient(
    os.getenv("YOUR_COSMOS_DB_ENDPOINT"),
    os.getenv("YOUR_COSMOS_DB_KEY")
)
database = cosmos_client.get_database_client(os.getenv("DATABASE_NAME"))
container = database.get_container_client(os.getenv("CONTAINER_NAME"))

# --- Azure OpenAI setup ---
openai_client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)
EMBEDDING_MODEL = "text-embedding-ada-002"
CHAT_MODEL = "o3-mini"

def get_embedding(text):
    """Get embedding from Azure OpenAI."""
    try:
        response = openai_client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        embedding = response.data[0].embedding
        if not isinstance(embedding, list):
            raise ValueError("Generated embedding is not a valid list")
        return array(embedding)
    except Exception as e:
        raise ValueError(f"Embedding error: {str(e)}")

def query_cosmos_vector(embedding, top_k=3):
    """Query Cosmos DB for similar items using cosine similarity."""
    items = list(container.query_items(
        query="SELECT c.id, c.Name, c.CONVERTER_DESCRIPTION_, c.embedding FROM c",
        enable_cross_partition_query=True
    ))
    best = []
    for item in items:
        if "embedding" not in item:
            continue
        try:
            item_vec = array(item["embedding"])
            sim = dot(embedding, item_vec) / (norm(embedding) * norm(item_vec))
            best.append((sim, item))
        except Exception as e:
            print(f"Error processing embedding for item {item.get('id')}: {str(e)}")
            continue
    best.sort(reverse=True, key=lambda x: x[0])
    return [item for (sim, item) in best[:top_k]]

def get_converter_by_number(number):
    """Get converter by ARTNR or id."""
    # Try by ARTNR
    query = "SELECT * FROM c WHERE c.ARTNR = @artnr"
    params = [{"name": "@artnr", "value": int(number)}]
    items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    if items:
        return items[0]
    # Try by id
    query = "SELECT * FROM c WHERE c.id LIKE @id"
    params = [{"name": "@id", "value": f"%{number}%"}]
    items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    if items:
        return items[0]
    return None

def search_cosmos_by_keywords(keywords):
    """Search Cosmos DB by multiple keywords in various fields."""
    keywords = keywords.lower().split()
    
    # Build the query dynamically to include all keywords
    query = """
    SELECT * FROM c
    WHERE (
        LOWER(c.Name) LIKE @keyword OR
        LOWER(c.CONVERTER_DESCRIPTION_) LIKE @keyword OR
        LOWER(c.TYPE) LIKE @keyword OR
        LOWER(c.LOCATION) LIKE @keyword OR
        LOWER(c.DIMMABILITY) LIKE @keyword OR
        LOWER(c.ARTNR) LIKE @keyword OR
        LOWER(c.LifeCycle) LIKE @keyword OR
        LOWER(c.Barcode) LIKE @keyword OR
        LOWER(c.SIZE__L_B_H__mm_) LIKE @keyword OR
        LOWER(c.EFFICIENCY__full_load) LIKE @keyword OR
        LOWER(c.NOM__INPUT_VOLTAGE__V_) LIKE @keyword OR
        LOWER(c.OUTPUT_VOLTAGE__V_) LIKE @keyword OR
        LOWER(c.Unit) LIKE @keyword OR
        LOWER(c.Listprice) LIKE @keyword
    )
    """
    
    # Use the first keyword for simplicity (can be extended for multiple keywords)
    params = [{"name": "@keyword", "value": f"%{keywords[0]}%"}]
    
    return list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))

def ask_chatbot(question, conversation):
    """Ask the chatbot a question using all search methods."""
    try:
        # 1. Try direct converter number lookup
        match = re.search(r'converter\s*(\d{5})', question, re.IGNORECASE)
        if match:
            number = match.group(1)
            converter = get_converter_by_number(number)
            if converter:
                # Extract specific information based on the question
                if "input voltage" in question.lower():
                    return f"Input Voltage: {converter.get('NOM__INPUT_VOLTAGE__V_', 'N/A')}"
                elif "efficiency" in question.lower():
                    return f"Efficiency: {converter.get('EFFICIENCY__full_load', 'N/A')}"
                elif "ip rating" in question.lower():
                    return f"IP Rating: {converter.get('IP', 'N/A')}"
                elif "dimmability" in question.lower():
                    return f"Dimmability: {converter.get('DIMMABILITY', 'N/A')}"
                elif "location" in question.lower():
                    return f"Location: {converter.get('LOCATION', 'N/A')}"
                elif "supported lamps" in question.lower():
                    lamps = "\n".join([
                        f"- {k}: min {v['min']}, max {v['max']}" 
                        for k, v in converter.get("lamps", {}).items() if isinstance(v, dict) and k != "id"
                    ])
                    return f"Supported Lamps:\n{lamps}"
                elif "pdf" in question.lower():
                    return f"PDF Link: {converter.get('pdf_link', 'N/A')}"
                else:
                    # General fallback response
                    return f"**{converter['Name']}**\nDescription: {converter.get('CONVERTER_DESCRIPTION_', 'N/A')}"

        # 2. Try keyword search
        items = search_cosmos_by_keywords(question)
        if items:
            # Return the first matching item with relevant fields
            item = items[0]
            if "input voltage" in question.lower():
                return f"Input Voltage: {item.get('NOM__INPUT_VOLTAGE__V_', 'N/A')}"
            elif "efficiency" in question.lower():
                return f"Efficiency: {item.get('EFFICIENCY__full_load', 'N/A')}"
            elif "ip rating" in question.lower():
                return f"IP Rating: {item.get('IP', 'N/A')}"
            elif "dimmability" in question.lower():
                return f"Dimmability: {item.get('DIMMABILITY', 'N/A')}"
            elif "location" in question.lower():
                return f"Location: {item.get('LOCATION', 'N/A')}"
            elif "supported lamps" in question.lower():
                lamps = "\n".join([
                    f"- {k}: min {v['min']}, max {v['max']}" 
                    for k, v in item.get("lamps", {}).items() if isinstance(v, dict) and k != "id"
                ])
                return f"Supported Lamps:\n{lamps}"
            elif "pdf" in question.lower():
                return f"PDF Link: {item.get('pdf_link', 'N/A')}"
            else:
                # General fallback response
                return f"**{item['Name']}**\nDescription: {item.get('CONVERTER_DESCRIPTION_', 'N/A')}"

        # 3. Fall back to semantic vector search and LLM
        embedding = get_embedding(question)
        similar = query_cosmos_vector(embedding)
        if similar:
            context = "\n\n".join([
                f"Converter: {item['Name']}\nDescription: {item['CONVERTER_DESCRIPTION_']}\nID: {item['id']}"
                for item in similar
            ])
            messages = conversation + [
                {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
            ]
            response = openai_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content

        return "Sorry, I couldn't find any relevant information."

    except Exception as e:
        return f"Sorry, an error occurred: {str(e)}"

# --- Main chat loop ---
conversation = []
print("Welcome to the LED Converter Chatbot!")
print("Type 'quit' to exit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    conversation.append({"role": "user", "content": user_input})
    answer = ask_chatbot(user_input, conversation)
    print("Assistant:", answer)
    conversation.append({"role": "assistant", "content": answer})
