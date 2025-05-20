
# import json
# import re
# import uuid
# import gradio as gr
# from gpt4all import GPT4All

# # Import your database handler
# from database import ChatDatabase

# # Initialize DB handler
# db = ChatDatabase()

# # Load JSON data once
# with open("/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json", "r", encoding="utf-8") as f:
#     converters = json.load(f)

# def find_converter_by_artnr(artnr):
#     artnr_str = str(artnr)
#     for key, info in converters.items():
#         if artnr_str in key:
#             return info
#     return None

# def build_prompt_with_history(converter_info, user_question, conversation_history):
#     pdf_link = converter_info.get('pdf_link', None)
#     pdf_link_text = f"[Specification Sheet PDF]({pdf_link})" if pdf_link else "No specification sheet PDF available."

#     lamps = converter_info.get("lamps", {})
#     lamps_info = ""
#     for lamp_name, lamp_values in lamps.items():
#         lamps_info += f"- {lamp_name}: min {lamp_values.get('min', 'N/A')}, max {lamp_values.get('max', 'N/A')}\n"

#     # Format conversation history as dialogue
#     history_text = ""
#     for sender, message in conversation_history:
#         prefix = "User" if sender == "user" else "Assistant"
#         history_text += f"{prefix}: {message}\n"

#     prompt = f"""
# You are a knowledgeable and friendly TAL LED lighting assistant.

# Converter details:
# Type: {converter_info.get('TYPE', 'N/A')}
# ARTNR: {converter_info.get('ARTNR', 'N/A')}
# Description: {converter_info.get('CONVERTER DESCRIPTION:', 'N/A')}
# Price: €{converter_info.get('Listprice', 'N/A')}
# Specification Sheet: {pdf_link_text}
# Lamps:
# {lamps_info}

# Conversation history:
# {history_text}

# User's new question:
# {user_question}

# Please answer clearly and politely.
# """
#     return prompt

# model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# def chat_with_converter(user_question, conversation_history):
#     artnr_match = re.search(r'\b(\d{4,6})\b', user_question)
#     if not artnr_match:
#         return ("Please specify the article number (ARTNR) of the converter you want to ask about. "
#                 "I can help you with prices, specs, and lamp info for TAL LED converters.")
#     artnr = artnr_match.group(1)
#     converter_info = find_converter_by_artnr(artnr)
#     if not converter_info:
#         return f"Sorry, I couldn't find any converter with article number {artnr}. Please check and try again."
#     prompt = build_prompt_with_history(converter_info, user_question, conversation_history)
#     with model.chat_session() as chat:
#         response = chat.generate(prompt, max_tokens=512)
#     return response.strip()

# def gradio_chat(user_input, session_id):
#     if not session_id:
#         session_id = str(uuid.uuid4())

#     conversation_id = db.get_or_create_conversation(session_id)

#     # Save user message
#     db.save_message(conversation_id, "user", user_input)

#     # Get full conversation history (user + bot messages)
#     history = db.get_conversation_history(conversation_id)

#     # Generate bot response with conversation history
#     bot_response = chat_with_converter(user_input, history)

#     # Save bot response
#     db.save_message(conversation_id, "bot", bot_response)

#     return bot_response, session_id

# def toggle_visibility(current_state):
#     new_state = not current_state
#     return new_state, gr.update(visible=new_state)

# custom_css = """
# #chatbot-toggle-btn {
#     position: fixed;
#     bottom: 30px;
#     right: 30px;
#     z-index: 10001;
#     background: #4CAF50;
#     color: white;
#     border-radius: 50%;
#     width: 64px;
#     height: 64px;
#     border: none;
#     font-size: 18px;
#     box-shadow: 0 2px 8px rgba(0,0,0,0.2);
#     cursor: pointer;
# }
# #chatbot-panel {
#     position: fixed;
#     bottom: 110px;
#     right: 30px;
#     z-index: 10000;
#     width: 400px;
#     max-width: 90vw;
#     background: white;
#     border-radius: 16px;
#     box-shadow: 0 2px 24px rgba(0,0,0,0.25);
#     padding: 16px;
# }
# """

# with gr.Blocks(css=custom_css) as demo:
#     visibility_state = gr.State(False)  # Initially hidden
#     session_state = gr.State("")       # Holds session_id

#     chatbot_toggle = gr.Button("💬", elem_id="chatbot-toggle-btn")

#     with gr.Column(visible=False, elem_id="chatbot-panel") as chatbot_panel:
#         gr.Markdown("## TAL LED Converter Chatbot")
#         gr.Markdown("Ask about TAL LED converters by article number.")
#         user_input = gr.Textbox(label="Question", placeholder="e.g. 'What is the price of 40025?'", lines=2)
#         output = gr.Textbox(label="Bot Response", interactive=False)
#         btn = gr.Button("Ask")
#         btn.click(gradio_chat, inputs=[user_input, session_state], outputs=[output, session_state])

#     chatbot_toggle.click(
#         fn=toggle_visibility,
#         inputs=visibility_state,
#         outputs=[visibility_state, chatbot_panel]
#     )

# if __name__ == "__main__":
#     demo.launch()


import json
import re
import uuid
import gradio as gr
from gpt4all import GPT4All

# Import your database handler
from database import ChatDatabase

# Initialize DB handler
db = ChatDatabase()

# Load JSON data once
with open("/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json", "r", encoding="utf-8") as f:
    converters = json.load(f)

def find_converter_by_artnr(artnr):
    artnr_str = str(artnr)
    for key, info in converters.items():
        if artnr_str in key:
            return info
    return None

def build_prompt_with_history(converter_info, user_question, conversation_history):
    pdf_link = converter_info.get('pdf_link', None)
    pdf_link_text = f"[Specification Sheet PDF]({pdf_link})" if pdf_link else "No specification sheet PDF available."

    lamps = converter_info.get("lamps", {})
    lamps_info = ""
    for lamp_name, lamp_values in lamps.items():
        lamps_info += f"- {lamp_name}: min {lamp_values.get('min', 'N/A')}, max {lamp_values.get('max', 'N/A')}\n"

    # Format conversation history as dialogue
    history_text = ""
    for sender, message in conversation_history:
        prefix = "User" if sender == "user" else "Assistant"
        history_text += f"{prefix}: {message}\n"

    prompt = f"""
You are a knowledgeable and friendly TAL LED lighting assistant.

Converter details:
Type: {converter_info.get('TYPE', 'N/A')}
ARTNR: {converter_info.get('ARTNR', 'N/A')}
Description: {converter_info.get('CONVERTER DESCRIPTION:', 'N/A')}
Price: €{converter_info.get('Listprice', 'N/A')}
Specification Sheet: {pdf_link_text}
Lamps:
{lamps_info}

Conversation history:
{history_text}

User's new question:
{user_question}

Please answer clearly and politely.
"""
    return prompt

model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

def chat_with_converter(user_question, conversation_history):
    artnr_match = re.search(r'\b(\d{4,6})\b', user_question)
    if not artnr_match:
        return ("Please specify the article number (ARTNR) of the converter you want to ask about. "
                "I can help you with prices, specs, and lamp info for TAL LED converters.")
    artnr = artnr_match.group(1)
    converter_info = find_converter_by_artnr(artnr)
    if not converter_info:
        return f"Sorry, I couldn't find any converter with article number {artnr}. Please check and try again."
    prompt = build_prompt_with_history(converter_info, user_question, conversation_history)
    with model.chat_session() as chat:
        response = chat.generate(prompt, max_tokens=512)
    return response.strip()

def gradio_chat(user_input, session_id):
    if not session_id:
        session_id = str(uuid.uuid4())

    conversation_id = db.get_or_create_conversation(session_id)

    # Save user message
    db.save_message(conversation_id, "user", user_input)

    # Get full conversation history (user + bot messages)
    history = db.get_conversation_history(conversation_id)

    # Generate bot response with conversation history
    bot_response = chat_with_converter(user_input, history)

    # Save bot response
    db.save_message(conversation_id, "bot", bot_response)

    return bot_response, session_id

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
    session_state = gr.State("")       # Holds session_id

    chatbot_toggle = gr.Button("💬", elem_id="chatbot-toggle-btn")

    with gr.Column(visible=False, elem_id="chatbot-panel") as chatbot_panel:
        gr.Markdown("## TAL LED Converter Chatbot")
        gr.Markdown("Ask about TAL LED converters by article number.")
        user_input = gr.Textbox(label="Question", placeholder="e.g. 'What is the price of 40025?'", lines=2)
        output = gr.Textbox(label="Bot Response", interactive=False)
        btn = gr.Button("Ask")
        btn.click(gradio_chat, inputs=[user_input, session_state], outputs=[output, session_state])

    chatbot_toggle.click(
        fn=toggle_visibility,
        inputs=visibility_state,
        outputs=[visibility_state, chatbot_panel]
    )

if __name__ == "__main__":
    demo.launch()
