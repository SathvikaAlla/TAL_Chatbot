# import json
# import re
# import gradio as gr
# from gpt4all import GPT4All

# # --- Your existing code for data loading and functions ---
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
#     return response.strip()

# # --- Gradio Blocks UI ---
# with gr.Blocks(title="TAL LED Converter Chatbot", css=".container { max-width: 480px; }") as demo:
#     with gr.Column(elem_classes="container"):
#         gr.Markdown("## TAL LED Converter Chatbot")
#         gr.Markdown("Ask about TAL LED converters by article number.")
#         user_input = gr.Textbox(label="Question", placeholder="e.g. 'What is the price of 40025?'", lines=2)
#         output = gr.Textbox(label="Bot Response", interactive=False)
#         btn = gr.Button("Ask")
#         btn.click(chat_with_converter, inputs=user_input, outputs=output)

# if __name__ == "__main__":
#     demo.launch()


import json
import re
import gradio as gr
from gpt4all import GPT4All

# Load JSON data once
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

# Toggle function that flips the boolean state
def toggle_visibility(current_state):
    new_state = not current_state
    return new_state, gr.update(visible=new_state)

custom_css = """
#chatbot-toggle-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 10001;
    background: #4CAF50;
    color: white;
    border-radius: 50%;
    width: 64px;
    height: 64px;
    border: none;
    font-size: 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    cursor: pointer;
}
#chatbot-panel {
    position: fixed;
    bottom: 110px;
    right: 30px;
    z-index: 10000;
    width: 400px;
    max-width: 90vw;
    background: white;
    border-radius: 16px;
    box-shadow: 0 2px 24px rgba(0,0,0,0.25);
    padding: 16px;
}
"""

with gr.Blocks(css=custom_css) as demo:
    visibility_state = gr.State(False)  # Initially hidden

    chatbot_toggle = gr.Button("💬", elem_id="chatbot-toggle-btn")

    with gr.Column(visible=False, elem_id="chatbot-panel") as chatbot_panel:
        gr.Markdown("## TAL LED Converter Chatbot")
        gr.Markdown("Ask about TAL LED converters by article number.")
        user_input = gr.Textbox(label="Question", placeholder="e.g. 'What is the price of 40025?'", lines=2)
        output = gr.Textbox(label="Bot Response", interactive=False)
        btn = gr.Button("Ask")
        btn.click(chat_with_converter, inputs=user_input, outputs=output)

    # On toggle button click, update the visibility state and panel visibility
    chatbot_toggle.click(
        fn=toggle_visibility,
        inputs=visibility_state,
        outputs=[visibility_state, chatbot_panel]
    )

    # The outputs list means:
    # - first output updates the state variable (boolean)
    # - second output updates the chatbot_panel visibility

if __name__ == "__main__":
    demo.launch()

