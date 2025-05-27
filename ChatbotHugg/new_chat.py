import os
import json
import re
import gradio as gr
from transformers import pipeline
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from typing import List, TypedDict
from langgraph.graph import StateGraph, START
from transformers import AutoTokenizer

# --- Configuration ---

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "***REMOVED***"

file_path = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        product_data = json.load(f)
except Exception as e:
    print(f"Error loading product data: {e}")
    product_data = {}

tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
max_length = tokenizer.model_max_length

docs = [Document(page_content=str(value), metadata={"source": key}) 
        for key, value in product_data.items()]

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = FAISS.from_documents(docs, embeddings)

chatbot = pipeline(
    "text-generation",
    model="facebook/blenderbot-400M-distill"
)

# --- Helper Functions ---

def extract_converter_and_lamp(user_message: str):
    # Example: "how many haloled lamps can I use for converter 40067"
    match = re.search(r"how many (\w+) lamps.*converter (\d+)", user_message.lower())
    if match:
        lamp_name = match.group(1)
        converter_number = match.group(2)
        return lamp_name, converter_number
    return None, None

def get_lamp_quantity(converter_number: str, lamp_name: str, product_data: dict) -> str:
    # Find the product by ARTNR or key
    matched_key = None
    for key, value in product_data.items():
        artnr = value.get("ARTNR", None)
        if artnr is not None and str(int(artnr)) == converter_number:
            matched_key = key
            break
        if converter_number in key:
            matched_key = key
            break
    if not matched_key:
        return f"Sorry, I could not find converter {converter_number}."

    lamps = product_data[matched_key].get("lamps", {})
    # Find lamp matching lamp_name (case insensitive, partial match)
    for lamp_key, lamp_vals in lamps.items():
        if lamp_name.lower() in lamp_key.lower():
            min_val = lamp_vals.get("min", "N/A")
            max_val = lamp_vals.get("max", "N/A")
            if min_val == max_val:
                return f"You can use {min_val} {lamp_key} lamp(s) with converter {converter_number}."
            else:
                return f"You can use between {min_val} and {max_val} {lamp_key} lamp(s) with converter {converter_number}."
    return f"Sorry, no data found for lamp '{lamp_name}' with converter {converter_number}."

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
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    retrieved_docs = retriever.invoke(state["question"])
    return {"context": retrieved_docs}

def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    prompt = f"""
    You are a helpful technical assistant for TAL BV and assist users in finding information. Use the provided documentation to answer questions accurately and with necessary sources.

    Context: {docs_content}
    Question: {state["question"]}
    Answer:
    """
    input_ids = tokenizer.encode(prompt, truncation=True, max_length=max_length, return_tensors="pt")
    truncated_prompt = tokenizer.decode(input_ids[0])
    response = chatbot(truncated_prompt, max_new_tokens=32, do_sample=True, temperature=0.2)
    answer = response[0]['generated_text'].split("Answer:", 1)[-1].strip()
    return {"answer": answer}

graph_builder = StateGraph(State)
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate", generate)
graph_builder.add_edge(START, "retrieve")
graph_builder.add_edge("retrieve", "generate")
graph = graph_builder.compile()

# --- Chatbot Function ---

def tal_langchain_chatbot(user_message, history):
    lamp_name, converter_number = extract_converter_and_lamp(user_message)
    if lamp_name and converter_number:
        answer = get_lamp_quantity(converter_number, lamp_name, product_data)
    else:
        response = graph.invoke({"question": user_message})
        answer = response["answer"]
    history = history or []
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": answer})
    return history, history, ""

# --- Gradio UI ---

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
