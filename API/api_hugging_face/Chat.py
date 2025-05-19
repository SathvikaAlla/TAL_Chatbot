
# import json
# import re
# from gpt4all import GPT4All

# # Load your JSON data once at the start
# with open("DataPrep/converters_with_links_and_pricelist.json", "r", encoding="utf-8") as f:
#     converters = json.load(f)

# def find_converter_by_artnr(artnr):
#     artnr_str = str(artnr)
#     for key, info in converters.items():
#         if artnr_str in key:
#             return info
#     return None

# def build_prompt(converter_info, user_question):
#     pdf_link = converter_info.get('pdf_link', None)
#     # Markdown-style clickable link (works in many terminals and UIs)
#     pdf_link_text = f"[Specification Sheet PDF]({pdf_link})" if pdf_link else "No specification sheet PDF available."

#     context = f"""
# Converter Type: {converter_info.get('TYPE', 'N/A')}
# ARTNR: {converter_info.get('ARTNR', 'N/A')}
# Description: {converter_info.get('CONVERTER DESCRIPTION:', 'N/A')}
# Price: €{converter_info.get('Listprice', 'N/A')}
# Specification Sheet: {pdf_link_text}
# Lamps info:
# """
#     lamps = converter_info.get("lamps", {})
#     for lamp_name, lamp_values in lamps.items():
#         context += f"  - {lamp_name}: min {lamp_values.get('min', 'N/A')}, max {lamp_values.get('max', 'N/A')}\n"

#     prompt = f"""
# You are a helpful assistant specialized in LED converters. Here is the converter data:
# {context}

# Answer the following question clearly and concisely:
# {user_question}
# """
#     return prompt

# # Load GPT4All model once (adjust path if needed)
# model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# def chat_with_converter(user_question):
#     artnr_match = re.search(r'\b(\d{4,6})\b', user_question)
#     if not artnr_match:
#         return "Please specify the article number (ARTNR) of the converter you want to ask about."

#     artnr = artnr_match.group(1)
#     converter_info = find_converter_by_artnr(artnr)
#     if not converter_info:
#         return f"Sorry, no converter found with article number {artnr}."

#     prompt = build_prompt(converter_info, user_question)

#     with model.chat_session() as chat:
#         response = chat.generate(prompt, max_tokens=512)

#     return response

# if __name__ == "__main__":
#     print("Welcome to the LED Converter Chatbot! Ask me about converters by article number.")
#     print("Type 'exit' or 'quit' to stop.")
#     while True:
#         user_input = input("You: ")
#         if user_input.strip().lower() in ["exit", "quit"]:
#             print("Goodbye!")
#             break
#         answer = chat_with_converter(user_input)
#         print("Bot:", answer)
import json
import re
import gradio as gr
from gpt4all import GPT4All

# Load your JSON data once at the start
with open("DataPrep/converters_with_links_and_pricelist.json", "r", encoding="utf-8") as f:
    converters = json.load(f)

def find_converter_by_artnr(artnr):
    artnr_str = str(artnr)
    for key, info in converters.items():
        if artnr_str in key:
            return info
    return None

def build_prompt(converter_info, user_question):
    pdf_link = converter_info.get('pdf_link', None)
    pdf_link_text = f"[Specification Sheet PDF]({pdf_link})" if pdf_link else "No specification sheet PDF available."

    context = f"""
Converter Type: {converter_info.get('TYPE', 'N/A')}
ARTNR: {converter_info.get('ARTNR', 'N/A')}
Description: {converter_info.get('CONVERTER DESCRIPTION:', 'N/A')}
Price: €{converter_info.get('Listprice', 'N/A')}
Specification Sheet: {pdf_link_text}
Lamps info:
"""
    lamps = converter_info.get("lamps", {})
    for lamp_name, lamp_values in lamps.items():
        context += f"  - {lamp_name}: min {lamp_values.get('min', 'N/A')}, max {lamp_values.get('max', 'N/A')}\n"

    prompt = f"""
You are a helpful assistant specialized in LED converters. Here is the converter data:
{context}

Answer the following question clearly and concisely:
{user_question}
"""
    return prompt

# Load GPT4All model once (adjust path if needed)
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

def chat_with_converter(user_question):
    artnr_match = re.search(r'\b(\d{4,6})\b', user_question)
    if not artnr_match:
        return "Please specify the article number (ARTNR) of the converter you want to ask about."

    artnr = artnr_match.group(1)
    converter_info = find_converter_by_artnr(artnr)
    if not converter_info:
        return f"Sorry, no converter found with article number {artnr}."

    prompt = build_prompt(converter_info, user_question)

    with model.chat_session() as chat:
        response = chat.generate(prompt, max_tokens=512)

    return response.strip()

# Gradio interface function
def gradio_chat(user_input):
    return chat_with_converter(user_input)

# Build Gradio interface
iface = gr.Interface(
    fn=gradio_chat,
    inputs=gr.Textbox(lines=2, placeholder="Ask about a converter by article number, e.g. 'What is the price of 40025?'"),
    outputs="text",
    title="TAL LED Converter Chatbot",
    description="Ask about TAL LED converters by article number. Get price, PDF spec sheet, lamp info, and more."
)

if __name__ == "__main__":
    iface.launch()
