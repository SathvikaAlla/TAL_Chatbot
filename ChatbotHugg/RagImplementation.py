import os
import json
import re
import gradio as gr
from transformers import pipeline, AutoTokenizer
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from typing import List, TypedDict
from langgraph.graph import StateGraph, START

# --- Configuration ---

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the Hugging Face API token
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
file_path = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        product_data = json.load(f)
except Exception as e:
    print(f"Error loading product data: {e}")
    product_data = {}

tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
max_length = tokenizer.model_max_length

docs = [Document(page_content=str(value), metadata={"source": key}) for key, value in product_data.items()]
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = FAISS.from_documents(docs, embeddings)
chatbot = pipeline("text-generation", model="facebook/blenderbot-400M-distill")

# --- Helper Functions ---

def normalize_artnr(artnr):
    """Convert ARTNR to string for robust matching."""
    try:
        return str(int(float(artnr)))
    except Exception:
        return str(artnr)

def get_product_by_artnr(artnr, tech_info):
    artnr_str = normalize_artnr(artnr)
    for value in tech_info.values():
        if normalize_artnr(value.get("ARTNR", "")) == artnr_str:
            return value
    return None

def extract_converter_and_lamp(user_message: str):
    match = re.search(r"how many (\w+) lamps?.*converter (\d+)", user_message.lower())
    if match:
        lamp_name = match.group(1)
        converter_number = match.group(2)
        return lamp_name, converter_number
    return None, None

def get_technical_fit_info(product_data: dict) -> dict:
    results = {}
    for key, value in product_data.items():
        results[key] = {
            "TYPE": value.get("TYPE", "N/A"),
            "ARTNR": value.get("ARTNR", "N/A"),
            "CONVERTER DESCRIPTION": value.get("CONVERTER DESCRIPTION:", "N/A"),
            "STRAIN RELIEF": value.get("STRAIN RELIEF", "N/A"),
            "LOCATION": value.get("LOCATION", "N/A"),
            "DIMMABILITY": value.get("DIMMABILITY", "N/A"),
            "EFFICIENCY": value.get("EFFICIENCY @full load", "N/A"),
            "OUTPUT VOLTAGE": value.get("OUTPUT VOLTAGE (V)", "N/A"),
            "INPUT VOLTAGE": value.get("NOM. INPUT VOLTAGE (V)", "N/A"),
            "SIZE": value.get("SIZE: L*B*H (mm)", "N/A"),
            "WEIGHT": value.get("Gross Weight", "N/A"),
            "Listprice": value.get("Listprice", "N/A"),
            "LAMPS": value.get("lamps", {}),
            "PDF_LINK": value.get("pdf_link", "N/A")
        }
    return results

tech_info = get_technical_fit_info(product_data)

def get_lamp_quantity(converter_number: str, lamp_name: str, tech_info: dict) -> str:
    v = get_product_by_artnr(converter_number, tech_info)
    if not v:
        return f"Sorry, I could not find converter {converter_number}."
    for lamp_key, lamp_vals in v["LAMPS"].items():
        if lamp_name.lower() in lamp_key.lower():
            min_val = lamp_vals.get("min", "N/A")
            max_val = lamp_vals.get("max", "N/A")
            if min_val == max_val:
                return f"You can use {min_val} {lamp_key} lamp(s) with converter {converter_number}."
            else:
                return f"You can use between {min_val} and {max_val} {lamp_key} lamp(s) with converter {converter_number}."
    return f"Sorry, no data found for lamp '{lamp_name}' with converter {converter_number}."

def answer_technical_question(question: str, tech_info: dict) -> str:
    q = question.lower()
    # Outdoor installation
    if "outdoor" in q:
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})"
                         for v in tech_info.values()
                         if "outdoor" in v["LOCATION"].lower() or "in&outdoor" in v["LOCATION"].lower()])
    # Most efficient 24V converter
    if "most efficient" in q and "24v" in q:
        candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower()]
        if not candidates:
            return "No 24V converters found."
        best = max(candidates, key=lambda x: float(str(x["EFFICIENCY"]).replace(',', '.')) if str(x["EFFICIENCY"]).replace('.', '').replace(',','').isdigit() else 0)
        return f"The most efficient 24V converter is {best['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(best['ARTNR'])}) with efficiency {best['EFFICIENCY']}."
    # 24V converter with dimming
    if "24v" in q and ("dimmable" in q or "dimming" in q or "supports dimming" in q):
        candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower() and "dimmable" in v["DIMMABILITY"].lower()]
        if not candidates:
            return "No 24V converters with dimming found."
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
    # Recommend for 19.2W LEDLINE
    if "19.2w ledline" in q:
        candidates = []
        for v in tech_info.values():
            for lamp, vals in v["LAMPS"].items():
                if "ledline" in lamp.lower() and "19.2w" in lamp.lower():
                    candidates.append(f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}) supports {lamp}")
        return "\n".join(candidates) if candidates else "No converter found for 19.2W LEDLINE."
    # Strain relief
    if "strain relief" in q:
        candidates = [v for v in tech_info.values() if v["STRAIN RELIEF"].lower() == "yes"]
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
    # Comparison
    if "compare" in q:
        numbers = re.findall(r'\d+', question)
        if len(numbers) >= 2:
            a = get_product_by_artnr(numbers[0], tech_info)
            b = get_product_by_artnr(numbers[1], tech_info)
            if a and b:
                return (f"Comparison:\n"
                        f"- {a['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(a['ARTNR'])}): {a['DIMMABILITY']}, {a['LOCATION']}, Efficiency {a['EFFICIENCY']}\n"
                        f"- {b['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(b['ARTNR'])}): {b['DIMMABILITY']}, {b['LOCATION']}, Efficiency {b['EFFICIENCY']}")
    # IP20 vs IP67
    if "ip20 and ip67" in q:
        ip20 = [v for v in tech_info.values() if "ip20" in str(v["CONVERTER DESCRIPTION"]).lower()]
        ip67 = [v for v in tech_info.values() if "ip67" in str(v["CONVERTER DESCRIPTION"]).lower()]
        return (f"IP20 converters:\n" + "\n".join([f"- {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in ip20]) + "\n\n" +
                f"IP67 converters:\n" + "\n".join([f"- {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in ip67]))
    # More than 1 LEDLINE 9.6W
    if "support more than 1 ledline 9.6w" in q:
        candidates = []
        for v in tech_info.values():
            for lamp, vals in v["LAMPS"].items():
                if "ledline" in lamp.lower() and "9.6w" in lamp.lower() and float(str(vals.get("max", 0))) > 1:
                    candidates.append(f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}) supports up to {vals['max']} {lamp}")
        return "\n".join(candidates) if candidates else "No converter supports more than 1 LEDLINE 9.6W lamp."
    # Smallest 24V converters
    if "smallest 24v" in q:
        candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower()]
        if not candidates:
            return "No 24V converters found."
        smallest = min(candidates, key=lambda x: float(str(x["SIZE"].split('*')[0])))
        return f"Smallest 24V converter: {smallest['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(smallest['ARTNR'])}), size: {smallest['SIZE']}"
    # Under 100mm length
    if "under 100mm" in q or ("length" in q and "100" in q):
        candidates = [v for v in tech_info.values() if float(str(v["SIZE"].split('*')[0])) < 100]
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}), size: {v['SIZE']}" for v in candidates])
    # Use-case: 2x 14.4W LEDLINE
    if "2x 14.4w ledline" in q:
        for v in tech_info.values():
            for lamp, vals in v["LAMPS"].items():
                if "ledline" in lamp.lower() and "14.4w" in lamp.lower() and float(str(vals.get("max", 0))) >= 2:
                    return f"You can use {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}) for 2x 14.4W LEDLINE."
    # Can I use converter X with Y lamp
    if "can i use converter" in q and "ledline" in q:
        numbers = re.findall(r'\d+', question)
        if numbers:
            v = get_product_by_artnr(numbers[0], tech_info)
            if v:
                for lamp, vals in v["LAMPS"].items():
                    if "ledline" in lamp.lower():
                        return f"Converter {numbers[0]} supports up to {vals.get('max', 0)} {lamp}."
    # IP67 and 1-10V dimming
    if "ip67" in q and "1-10v" in q:
        candidates = [v for v in tech_info.values() if "ip67" in str(v["CONVERTER DESCRIPTION"]).lower() and "1-10v" in str(v["DIMMABILITY"]).lower()]
        if candidates:
            return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
    # Built-in strain relief
    if "built-in strain relief" in q:
        return answer_technical_question("Which converters have strain relief included?", tech_info)
    # Indoor and outdoor
    if "indoor and outdoor" in q:
        candidates = [v for v in tech_info.values() if "in&outdoor" in v["LOCATION"].lower()]
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
    # Datasheet/documentation
    if "datasheet" in q or "documentation" in q:
        numbers = re.findall(r'\d+', question)
        if numbers:
            v = get_product_by_artnr(numbers[0], tech_info)
            if v and v["PDF_LINK"] != "N/A":
                return f"Datasheet for {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}): {v['PDF_LINK']}"
    # Pricing
    if "price" in q or "affordable" in q:
        if "most affordable 24v" in q:
            candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower() and str(v["Listprice"]) != "N/A"]
            if candidates:
                cheapest = min(candidates, key=lambda x: float(str(x["Listprice"]).replace(',', '.')))
                return f"Most affordable 24V converter: {cheapest['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(cheapest['ARTNR'])}), price: {cheapest['Listprice']}"
        elif "price below" in q:
            price_match = re.search(r'€(\d+)', question)
            price = float(price_match.group(1)) if price_match else 65
            candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower() and str(v["Listprice"]) != "N/A" and float(str(v["Listprice"]).replace(',', '.')) < price]
            return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}), price: {v['Listprice']}" for v in candidates])
    # Weight
    if "weight" in q:
        numbers = re.findall(r'\d+', question)
        if numbers:
            v = get_product_by_artnr(numbers[0], tech_info)
            if v and v["WEIGHT"] != "N/A":
                return f"Weight of {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}): {v['WEIGHT']} kg"
    # Input voltage
    if "input voltage" in q:
        numbers = re.findall(r'\d+', question)
        if numbers:
            v = get_product_by_artnr(numbers[0], tech_info)
            if v and v["INPUT VOLTAGE"] != "N/A":
                return f"Input voltage range of {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}): {v['INPUT VOLTAGE']}"
    # All 24V converters
    if "show me all 24v converters" in q:
        candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower()]
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
    return None

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
    # Lamp quantity questions
    lamp_name, converter_number = extract_converter_and_lamp(user_message)
    if lamp_name and converter_number:
        answer = get_lamp_quantity(converter_number, lamp_name, tech_info)
    else:
        # Technical, comparison, size, use-case, installation, pricing, product info questions
        answer = answer_technical_question(user_message, tech_info)
        if not answer:
            # Fall back to LLM
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
