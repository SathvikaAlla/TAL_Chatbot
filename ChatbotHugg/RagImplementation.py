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

from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load the model and tokenizer
llm_model = GPT2LMHeadModel.from_pretrained("/Users/alessiacolumban/TAL_Chatbot/results")
llm_tokenizer = GPT2Tokenizer.from_pretrained("/Users/alessiacolumban/TAL_Chatbot/results")
llm_tokenizer.pad_token = llm_tokenizer.eos_token


# --- Configuration ---

load_dotenv()
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

file_path = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        product_data = json.load(f)
except Exception as e:
    print(f"Error loading product data: {e}")
    product_data = {}

tokenizer = AutoTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
tokenizer.truncation_side = "left"
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
    
def parse_price(val):
    if isinstance(val, float) or isinstance(val, int):
        return float(val)
    try:
        return float(str(val).replace(',', '.'))
    except Exception:
        return float('inf')

def normalize_artnr(artnr):
    try:
        return str(int(float(artnr)))
    except Exception:
        return str(artnr)

def normalize_ip(ip):
    if isinstance(ip, (int, float)):
        return f"IP{int(ip)}"
    elif isinstance(ip, str):
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

def recommend_converters_for_lamp(lamp_query, tech_info):
    def normalize(s):
        # Lowercase, remove commas and dots, strip spaces
        return s.lower().replace(",", "").replace(".", "").strip()
    norm_query = normalize(lamp_query)
    query_words = set(norm_query.split())
    results = []
    for v in tech_info.values():
        lamps = v.get("LAMPS", {})
        for lamp_name, lamp_data in lamps.items():
            norm_lamp = normalize(lamp_name)
            lamp_words = set(norm_lamp.split())
            # Match if all query words are in lamp name OR query is a substring of lamp name OR lamp name is a substring of query
            if (
                query_words.issubset(lamp_words)
                or norm_query in norm_lamp
                or norm_lamp in norm_query
            ):
                min_val = lamp_data.get("min", "N/A")
                max_val = lamp_data.get("max", "N/A")
                desc = v.get("CONVERTER DESCRIPTION", v.get("CONVERTER DESCRIPTION:", "N/A")).strip()
                artnr = v.get("ARTNR", "N/A")
                results.append(f"{desc} (ARTNR: {int(float(artnr)) if artnr != 'N/A' else 'N/A'}), supports {min_val} to {max_val} x \"{lamp_name}\"")
    if not results:
        return f"Sorry, I couldn't find a converter for '{lamp_query}'."
    return "Recommended converters:\n" + "\n".join(results)


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

def answer_technical_question(question: str, tech_info: dict) -> str:
    q = question.lower()

    # --- Lamp-only queries like "Which converter should I use for 'LEDLINE medium power 9.6W' strips?" ---
    lamp_match = re.search(
        r'(?:for|recommend|use|need)[\s:]*["“”\']?([a-zA-Z0-9 ,.\-]+w)[\s"”\']*(?:strips?|ledline|lamps?)?', q
    )
    if lamp_match:
        lamp_query = lamp_match.group(1).strip()
        result = recommend_converters_for_lamp(lamp_query, tech_info)
        if result and "couldn't find" not in result:
            return result

    # Fallback: match any lamp in the database if all its words are in the question
    def normalize_lamp_string(s):
        return set(s.lower().replace(",", "").replace(".", "").split())
    q_words = set(q.replace(",", "").replace(".", "").split())
    for v in tech_info.values():
        for lamp_name in v.get("LAMPS", {}):
            lamp_words = normalize_lamp_string(lamp_name)
            if lamp_words and lamp_words.issubset(q_words):
                result = recommend_converters_for_lamp(lamp_name, tech_info)
                if result and "couldn't find" not in result:
                    return result



def answer_technical_question(question: str, tech_info: dict) -> str:
    q = question.lower()
    # Try to extract lamp name after 'for', 'recommend', 'use', etc.
    lamp_match = re.search(
        r'(?:for|recommend|use|need)[\s:]*["“”\']?([a-zA-Z0-9 ,.\-]+w)[\s"”\']*(?:strips?|ledline|lamps?)?', q
    )
    if lamp_match:
        lamp_query = lamp_match.group(1).strip()
        result = recommend_converters_for_lamp(lamp_query, tech_info)
        if result and "couldn't find" not in result:
            return result

    # Fallback: match any lamp in the database if all its words are in the question
    def normalize_lamp_string(s):
        return set(s.lower().replace(",", "").replace(".", "").split())
    q_words = set(q.replace(",", "").replace(".", "").split())
    for v in tech_info.values():
        for lamp_name in v.get("LAMPS", {}):
            lamp_words = normalize_lamp_string(lamp_name)
            if lamp_words and lamp_words.issubset(q_words):
                result = recommend_converters_for_lamp(lamp_name, tech_info)
                if result and "couldn't find" not in result:
                    return result
    
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
            candidates = [
                v for v in tech_info.values()
                if search_type in str(v["TYPE"]).replace(' ', '').lower()
                and str(v.get("EFFICIENCY", v.get("EFFICIENCY @full load", ""))).replace(',', '.').replace('.', '').isdigit()
            ]
            if not candidates:
                return f"No {search_type.upper()} converters found."
            best = max(
                candidates,
                key=lambda x: float(str(x.get("EFFICIENCY", x.get("EFFICIENCY @full load", "0"))).replace(',', '.'))
            )
            desc = best.get("CONVERTER DESCRIPTION", best.get("CONVERTER DESCRIPTION:", "N/A")).strip()
            artnr = int(float(best.get("ARTNR", "N/A"))) if best.get("ARTNR") else "N/A"
            eff = best.get("EFFICIENCY", best.get("EFFICIENCY @full load", "N/A"))
            return f"The most efficient {search_type.upper()} converter is {desc} (ARTNR: {artnr}) with efficiency {eff}."
        else:
            # fallback: show most efficient overall
            candidates = [
                v for v in tech_info.values()
                if str(v.get("EFFICIENCY", v.get("EFFICIENCY @full load", ""))).replace(',', '.').replace('.', '').isdigit()
            ]
            if not candidates:
                return "No converters with efficiency data found."
            best = max(
                candidates,
                key=lambda x: float(str(x.get("EFFICIENCY", x.get("EFFICIENCY @full load", "0"))).replace(',', '.'))
            )
            desc = best.get("CONVERTER DESCRIPTION", best.get("CONVERTER DESCRIPTION:", "N/A")).strip()
            artnr = int(float(best.get("ARTNR", "N/A"))) if best.get("ARTNR") else "N/A"
            eff = best.get("EFFICIENCY", best.get("EFFICIENCY @full load", "N/A"))
            return f"The most efficient converter overall is {desc} (ARTNR: {artnr}) with efficiency {eff}."

    # Dimming support
    if "dimmable" in q or "dimming" in q or "1-10v" in q or "dali" in q or "casambi" in q or "touchdim" in q:
        type_match = re.search(r'(\d+\s*v|\d+\s*ma)', q)
        type_query = type_match.group(1).replace(" ", "").lower() if type_match else None
        results = []
        for v in tech_info.values():
            type_str = str(v.get("TYPE", "")).lower().replace(" ", "")
            dim = v.get("DIMMABILITY", "").upper()
            if ("DIM" in dim or "1-10V" in dim or "DALI" in dim or "CASAMBI" in dim or "TOUCHDIM" in dim) and (not type_query or type_query in type_str):
                desc = v.get("CONVERTER DESCRIPTION", v.get("CONVERTER DESCRIPTION:", "N/A")).strip()
                artnr = int(float(v.get("ARTNR", "N/A"))) if v.get("ARTNR") else "N/A"
                results.append(f"{desc} (ARTNR: {artnr}), Dimming: {dim}")
        if not results:
            return f"No{' ' + type_query.upper() if type_query else ''} converters with dimming support found."
        return "\n".join(results)

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
            candidates = [
            v for v in tech_info.values()
            if "24v" in v["TYPE"].lower()
            and str(v["Listprice"]) != "N/A"
            and parse_price(v["Listprice"]) < price
        ]            
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


# --- LLM fallback function ---
def llm_fallback(question):
    prompt = f"User: {question}\nAssistant:"
    inputs = llm_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
    outputs = llm_model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_new_tokens=64,
        do_sample=True,
        temperature=0.7,
        pad_token_id=llm_tokenizer.eos_token_id
    )
    completion = llm_tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the assistant's answer
    if "Assistant:" in completion:
        return completion.split("Assistant:")[-1].strip()
    else:
        return completion.strip()

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

# --- Main chatbot function ---
def tal_langchain_chatbot(user_message, history=None):
    # 1. Try to answer from database/rules
    answer = answer_technical_question(user_message, tech_info)
    # 2. If no answer, use the LLM
    if not answer or answer.lower() == "i do not know the answer to this question.":
        answer = llm_fallback(user_message)
    # 3. Update history and return
    if history is None:
        history = []
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
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
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
    width: 600px;       /* Increased width */
    height: 700px;      /* Increased height */
    background-color: #ffffff;
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    font-family: 'Arial', sans-serif;
}

#chatbot-panel.hide {
    display: none !important;
}

#chat-header {
    background-color: #ED1C24;
    color: white;
    padding: 20px;
    font-weight: bold;
    font-size: 22px;
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    box-sizing: border-box;
}

#chat-header img {
    border-radius: 50%;
    width: 40px;
    height: 40px;
}

.gr-chatbot {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    background-color: #f9f9f9;
    border-top: 1px solid #eee;
    border-bottom: 1px solid #eee;
    display: flex;
    flex-direction: column;
    gap: 12px;
    box-sizing: border-box;
}

.gr-textbox {
    padding: 16px 20px;
    background-color: #fff;
    display: flex;
    align-items: center;
    gap: 12px;
    border-top: 1px solid #eee;
    box-sizing: border-box;
}

.gr-textbox textarea {
    flex: 1;
    resize: none;
    padding: 12px;
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-family: inherit;
    font-size: 16px;
    box-sizing: border-box;
    height: 48px;
    line-height: 1.5;
}

.gr-textbox button {
    background-color: #ED1C24;
    border: none;
    color: white;
    border-radius: 8px;
    padding: 12px 20px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.3s ease;
    font-size: 16px;
}

.gr-textbox button:hover {
    background-color: #c4161c;
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
