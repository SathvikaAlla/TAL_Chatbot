import os
import gradio as gr
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env
load_dotenv(find_dotenv())

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_azure_ai.vectorstores import AzureCosmosDBNoSqlVectorSearch
from azure.cosmos import CosmosClient, PartitionKey
from langchain_core.documents import Document
from typing import List, TypedDict
from langgraph.graph import StateGraph, START
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    temperature=0.2,
    max_tokens=512,
    top_p=0.95
)

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=os.getenv("OPENAI_API_ENDPOINT"),
    azure_deployment=os.getenv("OPENAI_EMBEDDINGS_MODEL_DEPLOYMENT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION")  # Optional, but can be included
)


# --- Cosmos DB Vector Search ---
vector_embedding_policy = {
    "vectorEmbeddings": [
        {
            "path": "/embedding",
            "dataType": "float32",
            "distanceFunction": "cosine",
            "dimensions": 1536,
        }
    ]
}
indexing_policy = {
    "indexingMode": "consistent",
    "includedPaths": [{"path": "/*"}],
    "excludedPaths": [{"path": '/"_etag"/?'}],
    "vectorIndexes": [{"path": "/embedding", "type": "diskANN"}],
    "fullTextIndexes": [{"path": "/text"}]
}
full_text_policy = {
    "defaultLanguage": "en-US",
    "fullTextPaths": [{"path": "/text", "language": "en-US"}],
}
partition_key = PartitionKey(path="/ARTNR")
cosmos_container_properties = {"partition_key": partition_key}

# Initialize Cosmos Client
cosmos_client = CosmosClient(
    os.getenv("AZURE_COSMOS_DB_ENDPOINT"),
    credential=os.getenv("AZURE_COSMOS_DB_KEY")
)

vector_store = AzureCosmosDBNoSqlVectorSearch(
    vector_embedding_policy=vector_embedding_policy,
    embedding=embeddings,
    indexing_policy=indexing_policy,
    cosmos_client=cosmos_client,
    database_name=os.getenv("AZURE_COSMOS_DB_DATABASE"),
    container_name="langchain_python_container",
    cosmos_container_properties=cosmos_container_properties,
    cosmos_database_properties={},
    full_text_policy=full_text_policy,
    full_text_search_enabled=True,
    vector_search_fields={"text_field": "text", "embedding_field": "embedding"}  # <-- Use this
)


# --- Prompt and Graph ---
custom_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful technical assistant for TAL BV and assist users in finding information. Use the provided documentation to answer questions accurately and with necessary sources."),
    ("human", """Context: {context}
Question: {question}
Answer:""")
])

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str

def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}

def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = custom_prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}

graph_builder = StateGraph(State)
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate", generate)
graph_builder.add_edge(START, "retrieve")
graph_builder.add_edge("retrieve", "generate")
graph = graph_builder.compile()

# --- Gradio Chatbot Function ---
def tal_langchain_chatbot(user_message, history):
    response = graph.invoke({"question": user_message})
    answer = response["answer"]
    history = history or []
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": answer})
    return history, history, ""  # third return value clears the textbox


# --- UI and CSS ---
custom_css = """
#chatbot-toggle-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 10001;
    background-color: #ED1C24;
    color: white;
    border: none;
    border-radius: 50%;
    width: 56px;
    height: 56px;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}
#chatbot-panel {
    position: fixed;
    bottom: 100px;
    right: 30px;
    z-index: 10000;
    width: 380px;
    height: 560px;
    background-color: #ffffff;
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    font-family: 'Arial', sans-serif;
}
#chatbot-panel.hide {
    display: none !important;
}
#chat-header {
    background-color: #ED1C24;
    color: white;
    padding: 16px;
    font-weight: bold;
    font-size: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}
#chat-header img {
    border-radius: 50%;
    width: 32px;
    height: 32px;
}
.gr-chatbot {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    background-color: #f8f8f8;
    border: none;
}
.gr-textbox {
    padding: 10px;
    border-top: 1px solid #eee;
}
.gr-textbox textarea {
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 8px;
}
footer {
    display: none !important;
}
"""

def toggle_visibility(current_state):
    new_state = not current_state
    return new_state, gr.update(visible=new_state)

with gr.Blocks(css=custom_css) as demo:
    visibility_state = gr.State(False)
    history = gr.State([])

    chatbot_toggle = gr.Button("💬", elem_id="chatbot-toggle-btn")
    with gr.Column(visible=False, elem_id="chatbot-panel") as chatbot_panel:
        gr.HTML("""
        <div id='chat-header'>
            <img src="https://www.svgrepo.com/download/490283/pixar-lamp.svg" />
            Lofty the TAL Bot
        </div>
        """)
        chat = gr.Chatbot(label="Chat", elem_id="chat-window", type="messages")
        msg = gr.Textbox(placeholder="Type your message here...", show_label=False)
        send = gr.Button("Send")
        send.click(
            fn=tal_langchain_chatbot, 
            inputs=[msg, history], 
            outputs=[chat, history, msg]
        )
        msg.submit(
            fn=tal_langchain_chatbot, 
            inputs=[msg, history], 
            outputs=[chat, history, msg]
        )


    chatbot_toggle.click(
        fn=toggle_visibility,
        inputs=visibility_state,
        outputs=[visibility_state, chatbot_panel]
    )

if __name__ == "__main__":
    demo.launch()
