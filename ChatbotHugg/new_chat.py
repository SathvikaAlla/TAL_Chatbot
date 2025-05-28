# import os
# import json
# import re
# import gradio as gr
# from transformers import pipeline, AutoTokenizer
# from langchain_core.documents import Document
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.vectorstores import FAISS
# from langchain_core.prompts import ChatPromptTemplate
# from typing import List, TypedDict
# from langgraph.graph import StateGraph, START
# from dotenv import load_dotenv

# # --- Configuration ---

# load_dotenv()
# os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
# file_path = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"
# try:
#     with open(file_path, 'r', encoding='utf-8') as f:
#         product_data = json.load(f)
# except Exception as e:
#     print(f"Error loading product data: {e}")
#     product_data = {}

# tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
# max_length = tokenizer.model_max_length

# docs = [Document(page_content=str(value), metadata={"source": key}) for key, value in product_data.items()]
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
# vector_store = FAISS.from_documents(docs, embeddings)
# chatbot = pipeline("text-generation", model="facebook/blenderbot-400M-distill")

# # --- Helper Functions ---

# def parse_float(s):
#     """Convert a string with either dot or comma as decimal separator to float."""
#     try:
#         return float(s.replace(',', '.').strip())
#     except Exception:
#         return float('inf')  # fallback for missing or invalid values

# def normalize_artnr(artnr):
#     """Convert ARTNR to string for robust matching."""
#     try:
#         return str(int(float(artnr)))
#     except Exception:
#         return str(artnr)

# def get_product_by_artnr(artnr, tech_info):
#     artnr_str = normalize_artnr(artnr)
#     for value in tech_info.values():
#         if normalize_artnr(value.get("ARTNR", "")) == artnr_str:
#             return value
#     return None

# def extract_converter_and_lamp(user_message: str):
#     match = re.search(r"how many (\w+) lamps?.*converter (\d+)", user_message.lower())
#     if match:
#         lamp_name = match.group(1)
#         converter_number = match.group(2)
#         return lamp_name, converter_number
#     return None, None

# def get_technical_fit_info(product_data: dict) -> dict:
#     results = {}
#     for key, value in product_data.items():
#         results[key] = {
#             "TYPE": value.get("TYPE", "N/A"),
#             "ARTNR": value.get("ARTNR", "N/A"),
#             "CONVERTER DESCRIPTION": value.get("CONVERTER DESCRIPTION:", "N/A"),
#             "STRAIN RELIEF": value.get("STRAIN RELIEF", "N/A"),
#             "LOCATION": value.get("LOCATION", "N/A"),
#             "DIMMABILITY": value.get("DIMMABILITY", "N/A"),
#             "EFFICIENCY": value.get("EFFICIENCY @full load", "N/A"),
#             "OUTPUT VOLTAGE": value.get("OUTPUT VOLTAGE (V)", "N/A"),
#             "INPUT VOLTAGE": value.get("NOM. INPUT VOLTAGE (V)", "N/A"),
#             "SIZE": value.get("SIZE: L*B*H (mm)", "N/A"),
#             "WEIGHT": value.get("Gross Weight", "N/A"),
#             "Listprice": value.get("Listprice", "N/A"),
#             "LAMPS": value.get("lamps", {}),
#             "PDF_LINK": value.get("pdf_link", "N/A")
#         }
#     return results

# tech_info = get_technical_fit_info(product_data)

# def get_lamp_quantity(converter_number: str, lamp_name: str, tech_info: dict) -> str:
#     v = get_product_by_artnr(converter_number, tech_info)
#     if not v:
#         return f"Sorry, I could not find converter {converter_number}."
#     for lamp_key, lamp_vals in v["LAMPS"].items():
#         if lamp_name.lower() in lamp_key.lower():
#             min_val = lamp_vals.get("min", "N/A")
#             max_val = lamp_vals.get("max", "N/A")
#             if min_val == max_val:
#                 return f"You can use {min_val} {lamp_key} lamp(s) with converter {converter_number}."
#             else:
#                 return f"You can use between {min_val} and {max_val} {lamp_key} lamp(s) with converter {converter_number}."
#     return f"Sorry, no data found for lamp '{lamp_name}' with converter {converter_number}."

# def answer_technical_question(question: str, tech_info: dict) -> str:
#     q = question.lower()
#     # Outdoor installation
#     if "outdoor" in q:
#         return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})"
#                          for v in tech_info.values()
#                          if "outdoor" in v["LOCATION"].lower() or "in&outdoor" in v["LOCATION"].lower()])
#     # Most efficient 24V converter
#     if "most efficient" in q and "24v" in q:
#         candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower()]
#         if not candidates:
#             return "No 24V converters found."
#         best = max(
#             candidates,
#             key=lambda x: float(str(x["EFFICIENCY"]).replace(',', '.')) if str(x["EFFICIENCY"]).replace('.', '').replace(',','').isdigit() else 0
#         )
#         return f"The most efficient 24V converter is {best['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(best['ARTNR'])}) with efficiency {best['EFFICIENCY']}."
#     # 24V converter with dimming
#     if "24v" in q and ("dimmable" in q or "dimming" in q or "supports dimming" in q):
#         candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower() and "dimmable" in v["DIMMABILITY"].lower()]
#         if not candidates:
#             return "No 24V converters with dimming found."
#         return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
#     # Recommend for 19.2W LEDLINE
#     if "19.2w ledline" in q:
#         candidates = []
#         for v in tech_info.values():
#             for lamp, vals in v["LAMPS"].items():
#                 if "ledline" in lamp.lower() and "19.2w" in lamp.lower():
#                     candidates.append(f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}) supports {lamp}")
#         return "\n".join(candidates) if candidates else "No converter found for 19.2W LEDLINE."
#     # Strain relief
#     if "strain relief" in q:
#         candidates = [v for v in tech_info.values() if v["STRAIN RELIEF"].lower() == "yes"]
#         return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
#     # Comparison
#     if "compare" in q:
#         numbers = re.findall(r'\d+', question)
#         if len(numbers) >= 2:
#             a = get_product_by_artnr(numbers[0], tech_info)
#             b = get_product_by_artnr(numbers[1], tech_info)
#             if a and b:
#                 return (f"Comparison:\n"
#                         f"- {a['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(a['ARTNR'])}): {a['DIMMABILITY']}, {a['LOCATION']}, Efficiency {a['EFFICIENCY']}\n"
#                         f"- {b['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(b['ARTNR'])}): {b['DIMMABILITY']}, {b['LOCATION']}, Efficiency {b['EFFICIENCY']}")
#     # IP20 vs IP67
#     if "ip20 and ip67" in q:
#         ip20 = [v for v in tech_info.values() if "ip20" in str(v["CONVERTER DESCRIPTION"]).lower()]
#         ip67 = [v for v in tech_info.values() if "ip67" in str(v["CONVERTER DESCRIPTION"]).lower()]
#         return (f"IP20 converters:\n" + "\n".join([f"- {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in ip20]) + "\n\n" +
#                 f"IP67 converters:\n" + "\n".join([f"- {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in ip67]))
#     # More than 1 LEDLINE 9.6W
#     if "support more than 1 ledline 9.6w" in q:
#         candidates = []
#         for v in tech_info.values():
#             for lamp, vals in v["LAMPS"].items():
#                 if "ledline" in lamp.lower() and "9.6w" in lamp.lower() and float(str(vals.get("max", 0)).replace(',', '.')) > 1:
#                     candidates.append(f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}) supports up to {vals['max']} {lamp}")
#         return "\n".join(candidates) if candidates else "No converter supports more than 1 LEDLINE 9.6W lamp."
#     # Smallest 24V converters
#     if "smallest 24v" in q:
#         candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower()]
#         if not candidates:
#             return "No 24V converters found."
#         # Use parse_float to handle both dot and comma decimal separators
#         smallest = min(
#             candidates,
#             key=lambda x: parse_float(str(x["SIZE"].split('*')[0]))
#         )
#         return f"Smallest 24V converter: {smallest['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(smallest['ARTNR'])}), size: {smallest['SIZE']}"
#     # Under 100mm length
#     if "under 100mm" in q or ("length" in q and "100" in q):
#         candidates = [v for v in tech_info.values() if parse_float(str(v["SIZE"].split('*')[0])) < 100]
#         return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}), size: {v['SIZE']}" for v in candidates])
#     # Use-case: 2x 14.4W LEDLINE
#     if "2x 14.4w ledline" in q:
#         for v in tech_info.values():
#             for lamp, vals in v["LAMPS"].items():
#                 if "ledline" in lamp.lower() and "14.4w" in lamp.lower() and float(str(vals.get("max", 0)).replace(',', '.')) >= 2:
#                     return f"You can use {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}) for 2x 14.4W LEDLINE."
#     # Can I use converter X with Y lamp
#     if "can i use converter" in q and "ledline" in q:
#         numbers = re.findall(r'\d+', question)
#         if numbers:
#             v = get_product_by_artnr(numbers[0], tech_info)
#             if v:
#                 for lamp, vals in v["LAMPS"].items():
#                     if "ledline" in lamp.lower():
#                         return f"Converter {numbers[0]} supports up to {vals.get('max', 0)} {lamp}."
#     # IP67 and 1-10V dimming
#     if "ip67" in q and "1-10v" in q:
#         candidates = [v for v in tech_info.values() if "ip67" in str(v["CONVERTER DESCRIPTION"]).lower() and "1-10v" in str(v["DIMMABILITY"]).lower()]
#         if candidates:
#             return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
#     # Built-in strain relief
#     if "built-in strain relief" in q:
#         return answer_technical_question("Which converters have strain relief included?", tech_info)
#     # Indoor and outdoor
#     if "indoor and outdoor" in q:
#         candidates = [v for v in tech_info.values() if "in&outdoor" in v["LOCATION"].lower()]
#         return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
#     # Datasheet/documentation
#     if "datasheet" in q or "documentation" in q:
#         numbers = re.findall(r'\d+', question)
#         if numbers:
#             v = get_product_by_artnr(numbers[0], tech_info)
#             if v and v["PDF_LINK"] != "N/A":
#                 return f"Datasheet for {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}): {v['PDF_LINK']}"
#     # Pricing
#     if "price" in q or "affordable" in q:
#         if "most affordable 24v" in q:
#             candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower() and str(v["Listprice"]) != "N/A"]
#             if candidates:
#                 cheapest = min(candidates, key=lambda x: float(str(x["Listprice"]).replace(',', '.')))
#                 return f"Most affordable 24V converter: {cheapest['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(cheapest['ARTNR'])}), price: {cheapest['Listprice']}"
#         elif "price below" in q:
#             price_match = re.search(r'€(\d+)', question)
#             price = float(price_match.group(1)) if price_match else 65
#             candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower() and str(v["Listprice"]) != "N/A" and float(str(v["Listprice"]).replace(',', '.')) < price]
#             return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}), price: {v['Listprice']}" for v in candidates])
#     # Weight
#     if "weight" in q:
#         numbers = re.findall(r'\d+', question)
#         if numbers:
#             v = get_product_by_artnr(numbers[0], tech_info)
#             if v and v["WEIGHT"] != "N/A":
#                 return f"Weight of {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}): {v['WEIGHT']} kg"
#     # Input voltage
#     if "input voltage" in q:
#         numbers = re.findall(r'\d+', question)
#         if numbers:
#             v = get_product_by_artnr(numbers[0], tech_info)
#             if v and v["INPUT VOLTAGE"] != "N/A":
#                 return f"Input voltage range of {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}): {v['INPUT VOLTAGE']}"
#     # All 24V converters
#     if "show me all 24v converters" in q:
#         candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower()]
#         return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
#     return None

# # --- Prompt and Graph ---

# custom_prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a helpful technical assistant for TAL BV and assist users in finding information. Use the provided documentation to answer questions accurately and with necessary sources."),
#     ("human", """Context: {context}
# Question: {question}
# Answer:""")
# ])

# class State(TypedDict):
#     question: str
#     context: List[Document]
#     answer: str

# def retrieve(state: State):
#     retriever = vector_store.as_retriever(search_kwargs={"k": 3})
#     retrieved_docs = retriever.invoke(state["question"])
#     return {"context": retrieved_docs}

# def generate(state: State):
#     docs_content = "\n\n".join(doc.page_content for doc in state["context"])
#     prompt = f"""
#     You are a helpful technical assistant for TAL BV and assist users in finding information. Use the provided documentation to answer questions accurately and with necessary sources.

#     Context: {docs_content}
#     Question: {state["question"]}
#     Answer:
#     """
#     input_ids = tokenizer.encode(prompt, truncation=True, max_length=max_length, return_tensors="pt")
#     truncated_prompt = tokenizer.decode(input_ids[0])
#     response = chatbot(truncated_prompt, max_new_tokens=32, do_sample=True, temperature=0.2)
#     answer = response[0]['generated_text'].split("Answer:", 1)[-1].strip()
#     return {"answer": answer}

# graph_builder = StateGraph(State)
# graph_builder.add_node("retrieve", retrieve)
# graph_builder.add_node("generate", generate)
# graph_builder.add_edge(START, "retrieve")
# graph_builder.add_edge("retrieve", "generate")
# graph = graph_builder.compile()

# # --- Chatbot Function ---

# def tal_langchain_chatbot(user_message, history):
#     lamp_name, converter_number = extract_converter_and_lamp(user_message)
#     if lamp_name and converter_number:
#         answer = get_lamp_quantity(converter_number, lamp_name, tech_info)
#     else:
#         answer = answer_technical_question(user_message, tech_info)
#         if not answer:
#             response = graph.invoke({"question": user_message})
#             answer = response["answer"]
#     history = history or []
#     history.append({"role": "user", "content": user_message})
#     history.append({"role": "assistant", "content": answer})
#     return history, history, ""

# # --- Gradio UI ---

# custom_css = """
# #chatbot-toggle-btn {
#     position: fixed;
#     bottom: 30px;
#     right: 30px;
#     z-index: 10001;
#     background-color: #ED1C24;
#     color: white;
#     border: none;
#     border-radius: 50%;
#     width: 56px;
#     height: 56px;
#     font-size: 28px;
#     font-weight: bold;
#     cursor: pointer;
#     box-shadow: 0 4px 12px rgba(0,0,0,0.3);
#     display: flex;
#     align-items: center;
#     justify-content: center;
#     transition: all 0.3s ease;
# }
# #chatbot-panel {
#     position: fixed;
#     bottom: 100px;
#     right: 30px;
#     z-index: 10000;
#     width: 380px;
#     height: 560px;
#     background-color: #ffffff;
#     border-radius: 20px;
#     box-shadow: 0 4px 24px rgba(0,0,0,0.25);
#     overflow: hidden;
#     display: flex;
#     flex-direction: column;
#     font-family: 'Arial', sans-serif;
# }
# #chatbot-panel.hide {
#     display: none !important;
# }
# #chat-header {
#     background-color: #ED1C24;
#     color: white;
#     padding: 16px;
#     font-weight: bold;
#     font-size: 16px;
#     display: flex;
#     align-items: center;
#     gap: 12px;
# }
# #chat-header img {
#     border-radius: 50%;
#     width: 32px;
#     height: 32px;
# }
# .gr-chatbot {
#     flex: 1;
#     overflow-y: auto;
#     padding: 12px;
#     background-color: #f8f8f8;
#     border: none;
# }
# .gr-textbox {
#     padding: 10px;
#     border-top: 1px solid #eee;
# }
# .gr-textbox textarea {
#     background-color: white;
#     border: 1px solid #ccc;
#     border-radius: 8px;
# }
# footer {
#     display: none !important;
# }
# """

# def toggle_visibility(current_state):
#     new_state = not current_state
#     return new_state, gr.update(visible=new_state)

# with gr.Blocks(css=custom_css) as demo:
#     visibility_state = gr.State(False)
#     history = gr.State([])

#     chatbot_toggle = gr.Button("💬", elem_id="chatbot-toggle-btn")
#     with gr.Column(visible=False, elem_id="chatbot-panel") as chatbot_panel:
#         gr.HTML("""
#         <div id='chat-header'>
#             <img src="https://www.svgrepo.com/download/490283/pixar-lamp.svg" />
#             Lofty the TAL Bot
#         </div>
#         """)
#         chat = gr.Chatbot(label="Chat", elem_id="chat-window", type="messages")
#         msg = gr.Textbox(placeholder="Type your message here...", show_label=False)
#         send = gr.Button("Send")
#         send.click(
#             fn=tal_langchain_chatbot, 
#             inputs=[msg, history], 
#             outputs=[chat, history, msg]
#         )
#         msg.submit(
#             fn=tal_langchain_chatbot, 
#             inputs=[msg, history], 
#             outputs=[chat, history, msg]
#         )

#     chatbot_toggle.click(
#         fn=toggle_visibility,
#         inputs=visibility_state,
#         outputs=[visibility_state, chatbot_panel]
#     )

# if __name__ == "__main__":
#     demo.launch()
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
from dotenv import load_dotenv

# --- Configuration ---

load_dotenv()
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Suppress HuggingFace parallelism warnings

file_path = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        product_data = json.load(f)
except Exception as e:
    print(f"Error loading product data: {e}")
    product_data = {}

tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
tokenizer.truncation_side = "left"  # Keep the most recent context
max_length = tokenizer.model_max_length

docs = [Document(page_content=str(value), metadata={"source": key}) for key, value in product_data.items()]
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
vector_store = FAISS.from_documents(docs, embeddings)
chatbot = pipeline("text-generation", model="facebook/blenderbot-400M-distill")

# --- Helper Functions ---

def parse_float(s):
    try:
        if isinstance(s, (list, tuple)):
            s = s[0]
        return float(str(s).replace(',', '.').strip())
    except Exception:
        return float('inf')

def normalize_artnr(artnr):
    try:
        return str(int(float(artnr)))
    except Exception:
        return str(artnr)
    
def normalize_ip(ip):
    if isinstance(ip, (int, float)):
        # Convert to int and prefix with "IP"
        return f"IP{int(ip)}"
    elif isinstance(ip, str):
        # Remove "IP" prefix (if present), split at decimal, take first part, re-add "IP"
        ip_part = ip.replace("IP", "").split(".")[0]
        return f"IP{ip_part}"
    else:
        return "N/A"


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
            "PDF_LINK": value.get("pdf_link", "N/A"),
            "IP": value.get("IP", "N/A"),
            "CLASS": value.get("CLASS", "N/A"),
            "LifeCycle": value.get("LifeCycle", "N/A"),
            "Name": value.get("Name", "N/A"),
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

def get_recommended_converter_any(user_message, tech_info):
    match = re.search(r'(\d+)\s*x\s*([\w\d\s\-,.*]+)', user_message, re.IGNORECASE)
    if not match:
        return None
    num_lamps = int(match.group(1))
    lamp_query = match.group(2).strip().lower()
    candidates = []
    for v in tech_info.values():
        for lamp, vals in v["LAMPS"].items():
            lamp_norm = lamp.lower().replace(',', '.')
            if all(word in lamp_norm for word in lamp_query.split()):
                max_lamps = float(str(vals.get("max", 0)).replace(',', '.'))
                if max_lamps >= num_lamps:
                    candidates.append((v, lamp, max_lamps))
    if not candidates:
        return f"Sorry, I couldn't find a converter that supports {num_lamps}x {lamp_query.title()}."
    else:
        return "\n".join([
            f"You can use {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}) for {num_lamps}x {lamp_query.title()} (max supported: {max_lamps} for '{lamp}')."
            for v, lamp, max_lamps in candidates
        ])
    

def recommend_converters_for_lamp(lamp_query, tech_info):
    """
    Returns all converters that support the requested lamp type (fuzzy, case-insensitive).
    """
    lamp_query_norm = lamp_query.lower().replace(",", ".").strip()
    results = []
    for v in tech_info.values():
        lamps = v.get("LAMPS", {})
        for lamp_name, lamp_data in lamps.items():
            lamp_name_norm = lamp_name.lower().replace(",", ".").strip()
            # Fuzzy match: all words in the lamp_query must be in the lamp_name
            if all(word in lamp_name_norm for word in lamp_query_norm.split()):
                min_val = lamp_data.get("min", "N/A")
                max_val = lamp_data.get("max", "N/A")
                desc = v.get("CONVERTER DESCRIPTION", v.get("CONVERTER DESCRIPTION:", "N/A")).strip()
                artnr = v.get("ARTNR", "N/A")
                results.append(f"{desc} (ARTNR: {int(float(artnr)) if artnr != 'N/A' else 'N/A'}), supports {min_val} to {max_val} x \"{lamp_name}\"")
    if not results:
        return f"Sorry, I couldn't find a converter for '{lamp_query}'."
    return "Recommended converters:\n" + "\n".join(results)

def answer_technical_question(question: str, tech_info: dict) -> str:
    q = question.lower()
    # ... (other logic here)

    # --- Lamp-only queries like "Which converter should I use for 'LEDLINE medium power 9.6W' strips?" ---
    lamp_only_match = re.search(
        r'(?:which converter (?:should i use|is suitable|supports|do i need)[\w\s]*for)\s*[“"\'“]?([a-zA-Z0-9 ,.\-]+)[”"\']?(?: strips?)?',
        q
    )
    if lamp_only_match:
        lamp_query = lamp_only_match.group(1).strip()
        return recommend_converters_for_lamp(lamp_query, tech_info)

    # ... (rest of your logic)
    return "I do not know the answer to this question."



def answer_technical_question(question: str, tech_info: dict) -> str:
    q = question.lower()
    # Efficiency at full load for all converters
    if "efficiency at full load for each converter" in q or "efficiency for each converter" in q:
        result = []
        for v in tech_info.values():
            description = v.get("CONVERTER DESCRIPTION", "N/A").strip()
            efficiency = v.get("EFFICIENCY", "N/A")
            result.append(f"{description}: {efficiency}")
        return "\n".join(result)
    # Generalized lamp fit for any type in the database
    if re.search(r"\d+\s*x\s*[\w\d\s\-,.*]+", q):
        result = get_recommended_converter_any(question, tech_info)
        if result:
            return result
    # Outdoor installation
    if "outdoor" in q:
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})"
                         for v in tech_info.values()
                         if "outdoor" in v["LOCATION"].lower() or "in&outdoor" in v["LOCATION"].lower()])
    # Most efficient converter for any type
    if "most efficient" in q:
        type_match = re.search(r'(\d+\s*v|\d+\s*ma)', q)
        if type_match:
            search_type = type_match.group(1).replace(' ', '').lower()
            candidates = [v for v in tech_info.values() if search_type in v["TYPE"].replace(' ', '').lower()]
            if not candidates:
                return f"No {search_type.upper()} converters found."
            best = max(
                candidates,
                key=lambda x: float(str(x["EFFICIENCY"]).replace(',', '.')) if str(x["EFFICIENCY"]).replace('.', '').replace(',','').isdigit() else 0
            )
            return f"The most efficient {search_type.upper()} converter is {best['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(best['ARTNR'])}) with efficiency {best['EFFICIENCY']}."
        else:
            candidates = [v for v in tech_info.values() if str(v["EFFICIENCY"]).replace(',', '.').replace('.', '').isdigit()]
            if not candidates:
                return "No converters with efficiency data found."
            best = max(
                candidates,
                key=lambda x: float(str(x["EFFICIENCY"].replace(',', '.')) if isinstance(x["EFFICIENCY"], str) else x["EFFICIENCY"])
            )
            return f"The most efficient converter overall is {best['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(best['ARTNR'])}) with efficiency {best['EFFICIENCY']}."
    # Dimming support
    if "dimmable" in q or "dimming" in q or "1-10v" in q or "dali" in q or "casambi" in q or "touchdim" in q:
        candidates = [v for v in tech_info.values() if any(dim in v["DIMMABILITY"].lower() for dim in ["dimmable", "1-10v", "dali", "casambi", "touchdim"])]
        if not candidates:
            return "No dimmable converters found."
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}), Dimming: {v['DIMMABILITY']}" for v in candidates])
    # Strain relief
    if "strain relief" in q:
        candidates = [v for v in tech_info.values() if v["STRAIN RELIEF"].lower() == "yes"]
        yesno = "Yes" if candidates else "No"
        details = "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in candidates])
        return f"{yesno}. " + (details if details else "")
        # Input voltage range for each converter
    if "input voltage range for each converter" in q or "input voltage range" in q and "each" in q:
        result = []
        for v in tech_info.values():
            description = v.get("CONVERTER DESCRIPTION", "N/A").strip()
            input_voltage = v.get("INPUT VOLTAGE", "N/A")
            result.append(f"{description}: {input_voltage}")
        return "\n".join(result)

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
    if "ip20" in q and "ip67" in q:
        ip20 = [v for v in tech_info.values() if "ip20" in str(v["CONVERTER DESCRIPTION"]).lower()]
        ip67 = [v for v in tech_info.values() if "ip67" in str(v["CONVERTER DESCRIPTION"]).lower()]
        return (f"IP20 converters:\n" + "\n".join([f"- {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in ip20]) + "\n\n" +
                f"IP67 converters:\n" + "\n".join([f"- {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])})" for v in ip67]))
    # Size/space
    if "smallest" in q or "compact" in q:
        candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower()]
        if not candidates:
            return "No 24V converters found."
        smallest = min(
            candidates,
            key=lambda x: parse_float(str(x["SIZE"].split('*')[0]))
        )
        return f"Smallest 24V converter: {smallest['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(smallest['ARTNR'])}), size: {smallest['SIZE']}"
    if "under 100mm" in q or ("length" in q and "100" in q):
        candidates = [v for v in tech_info.values() if parse_float(str(v["SIZE"].split('*')[0])) < 100]
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}), size: {v['SIZE']}" for v in candidates])
    # Documentation
    if "datasheet" in q or "manual" in q or "pdf" in q:
        numbers = re.findall(r'\d+', question)
        if numbers:
            v = get_product_by_artnr(numbers[0], tech_info)
            if v and v["PDF_LINK"] != "N/A":
                return f"Datasheet/manual for {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}): {v['PDF_LINK']}"
    # Pricing
    if "price" in q or "affordable" in q:
        if "most affordable" in q:
            candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower() and str(v["Listprice"]) != "N/A"]
            if candidates:
                cheapest = min(candidates, key=lambda x: float(str(x["Listprice"]).replace(',', '.')))
                return f"Most affordable 24V converter: {cheapest['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(cheapest['ARTNR'])}), price: {cheapest['Listprice']}"
        elif "price below" in q:
            price_match = re.search(r'€(\d+)', question)
            price = float(price_match.group(1)) if price_match else 65
            candidates = [v for v in tech_info.values() if "24v" in v["TYPE"].lower() and str(v["Listprice"]) != "N/A" and float(str(v["Listprice"].replace(',', '.'))) < price]
            return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}), price: {v['Listprice']}" for v in candidates])
    # Product info
    if "weight" in q:
        numbers = re.findall(r'\d+', question)
        if numbers:
            v = get_product_by_artnr(numbers[0], tech_info)
            if v and v["WEIGHT"] != "N/A":
                return f"Weight of {v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}): {v['WEIGHT']} kg"
    
    
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
    # Lifecycle
    if "active" in q or "lifecycle" in q:
        candidates = [v for v in tech_info.values() if v.get("LifeCycle", "").upper() == "A"]
        return "\n".join([f"{v['CONVERTER DESCRIPTION']} (ARTNR: {normalize_artnr(v['ARTNR'])}) is active." for v in candidates])
    
    if "output voltage for each converter" in q or "output voltage for each model" in q:
        result = []
        for v in tech_info.values():
            description = v.get("CONVERTER DESCRIPTION", "N/A").strip()
            output_voltage = v.get("OUTPUT VOLTAGE", "N/A")
            result.append(f"{description}: {output_voltage}")
        return "\n".join(result)
    
    if "ip rating for each converter" in q and "what does it mean" in q:
        ip_meaning = {
            "IP20": "Protected against solid foreign objects ≥12mm (e.g., fingers), no protection against water. Suitable for indoor use in protected environments like cabinets.",
            "IP54": "Protected against limited dust ingress and water splashes from any direction. Suitable for outdoor use in sheltered locations.",
            "IP65": "Dust-tight and protected against low-pressure water jets. Suitable for outdoor use.",
            "IP66": "Dust-tight and protected against powerful water jets. Suitable for outdoor use in harsh environments.",
            "IP67": "Dust-tight and protected against temporary immersion in water. Suitable for outdoor use, even in harsh environments."
        }
        result = ["IP rating for each converter and installation meaning:"]
        for v in tech_info.values():
            description = v.get("CONVERTER DESCRIPTION", "N/A").strip()
            ip = v.get("IP", "N/A")
            normalized_ip = normalize_ip(ip)
            meaning = ip_meaning.get(normalized_ip, "No specific installation guidance available.")
            result.append(f"{description}: {normalized_ip} – {meaning}")
        return "\n".join(result)
    
    if "class of each converter" in q or "class (electrical safety class) of each converter" in q:
        result = ["Class (electrical safety class) for each converter:"]
        for v in tech_info.values():
            description = v.get("CONVERTER DESCRIPTION", "N/A").strip()
            class_ = v.get("CLASS", "N/A")
            result.append(f"{description}: Class {class_}")
        return "\n".join(result)
    
    if "dimensions" in q and "lbh" in q or ("dimensions" in q and "l*b*h" in q) or ("dimensions of each converter" in q):
        result = ["Dimensions (LBH) for each converter:"]
        for v in tech_info.values():
            description = v.get("CONVERTER DESCRIPTION", "N/A").strip()
            size = v.get("SIZE", "N/A")
            result.append(f"{description}: {size}")
        return "\n".join(result)
    
    if "weight of converter" in q or "weight of each converter" in q or ("gross weight" in q and "each" in q):
        result = ["Gross weight of each converter:"]
        for v in tech_info.values():
            description = v.get("CONVERTER DESCRIPTION", "N/A").strip()
            weight = v.get("WEIGHT", v.get("Gross Weight", "N/A"))
            result.append(f"{description}: {weight} kg")
        return "\n".join(result)
    
    # Example: "What is the difference between the 24V DC and 48V LED converters?"
    if "difference between" in q and any(
        (f"{x}v" in q and f"{y}v" in q) or
        (f"{x}ma" in q and f"{y}ma" in q)
        for x, y in [(24, 48), (180, 250), (250, 260), (260, 350), (350, 500), (500, 700)]
    ):
        # Extract the two types from the question (simplified for demo)
        parts = q.split("between")[1].split("and")
        type1 = parts[0].strip().lower()
        type2 = parts[1].strip().lower()

        # Build a technical explanation based on the types
        if "24v" in type1 and "48v" in type2:
            explanation = (
                "Difference between 24V DC and 48V LED converters:\n"
                "- **Power Delivery:** 48V converters can deliver the same power at half the current compared to 24V, reducing cable size and cost.\n"
                "- **Efficiency:** 48V systems are generally more efficient, especially over longer cable runs, due to lower current and less voltage drop.\n"
                "- **Safety:** Both 24V and 48V are considered Safety Extra Low Voltage (SELV), but 48V is still below the 60V SELV limit, so it remains safe for most installations.\n"
                "- **Compatibility:** 48V converters are better for large LED systems or longer runs, while 24V is common for smaller or standard installations.\n"
                "- **System Design:** 48V allows for higher power LED arrays and longer cable runs without significant voltage drop or power loss[2][3][4].\n"
            )
        elif any(f"{x}ma" in type1 and f"{y}ma" in type2 for x, y in [(180, 250), (250, 260), (260, 350), (350, 500), (500, 700)]):
            # Example for current-based converters
            current1 = type1.split("ma")[0].strip()
            current2 = type2.split("ma")[0].strip()
            explanation = (
                f"Difference between {current1}mA and {current2}mA LED converters:\n"
                f"- **Current Output:** {current2}mA converters can drive more power-hungry or larger LED installations compared to {current1}mA.\n"
                f"- **Application:** {current1}mA is typically used for smaller LED strips or modules, while {current2}mA is used for larger or more demanding LED setups.\n"
                f"- **Efficiency:** Higher current converters (like {current2}mA) may require thicker cables to minimize voltage drop and power loss over distance.\n"
            )
        else:
            explanation = "Sorry, I couldn't find a technical comparison for those converter types. Please specify the types you want to compare (e.g., 24V vs 48V, or 180mA vs 350mA)."

        return explanation
    
    # Example: "What is the difference between remote and in-track LED converters?"
    if "difference between remote and in-track" in q.lower() or "remote vs in-track" in q.lower():
        explanation = (
            "Difference between 'remote' and 'in-track' LED converters:\n\n"
            "- **Remote Converters:**\n"
            "  - The converter (driver) is located outside the LED track or rail, often in a central location or remote enclosure.\n"
            "  - Multiple LED tracks or fixtures can be powered from a single remote converter.\n"
            "  - Remote converters are easier to access for maintenance or replacement.\n"
            "  - They are typically used for larger installations or when you want to centralize power management.\n"
            "  - Remote converters can be more efficient and reliable, as they are not limited by the space or heat constraints of the track.\n\n"
            "- **In-Track Converters:**\n"
            "  - The converter is mounted directly inside or alongside the LED track or rail.\n"
            "  - Each track usually has its own dedicated converter.\n"
            "  - In-track converters are more compact and can be used for smaller installations or where a centralized converter is not practical.\n"
            "  - They are less visible and can be easier to install in tight spaces.\n"
            "  - Maintenance or replacement may require access to the track itself.\n\n"
            "**Summary:**\n"
            "Remote converters are best for larger, more complex systems with centralized power, while in-track converters are ideal for smaller, standalone tracks or where space and aesthetics are a concern."
        )
        return explanation
    
    if "minimum and maximum number of lamps" in q or "min and max number of lamps" in q or "min max lamps" in q:
        result = ["Minimum and maximum number of lamps that can be connected to each converter:"]
        for v in tech_info.values():
            description = v.get("CONVERTER DESCRIPTION", "N/A").strip()
            lamps = v.get("LAMPS", {})
            if not lamps:
                result.append(f"{description}: No lamp compatibility data available.")
            else:
                for lamp_name, lamp_data in lamps.items():
                    min_val = lamp_data.get("min", "N/A")
                    max_val = lamp_data.get("max", "N/A")
                    result.append(f"{description}: {lamp_name} – min: {min_val}, max: {max_val}")
        return "\n".join(result)



    # Default fallback
    return "I do not know the answer to this question."



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

def tal_langchain_chatbot(user_message, history):
    lamp_name, converter_number = extract_converter_and_lamp(user_message)
    if lamp_name and converter_number:
        answer = get_lamp_quantity(converter_number, lamp_name, tech_info)
    else:
        answer = answer_technical_question(user_message, tech_info)
        if not answer:
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
    border_top: 1px solid #eee;
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
