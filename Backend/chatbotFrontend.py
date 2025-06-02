
import gradio as gr

def simple_tal_bot(user_message, history):
    if history is None:
        history = []
    response = "Thanks for your message! A TAL advisor will be with you shortly. In the meantime, feel free to leave your email so we can follow up."
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response})
    return history, history

# Toggle function to flip visibility state
def toggle_visibility(current_state):
    new_state = not current_state
    return new_state, gr.update(visible=new_state)

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

with gr.Blocks(css=custom_css) as demo:
    visibility_state = gr.State(False)  # Initially hidden
    history = gr.State([])  # Define history state to store chat history

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

        # Use the defined history state
        send.click(fn=simple_tal_bot, inputs=[msg, history], outputs=[chat, history])
        msg.submit(fn=simple_tal_bot, inputs=[msg, history], outputs=[chat, history])

    # On toggle button click, update the visibility state and panel visibility
    chatbot_toggle.click(
        fn=toggle_visibility,
        inputs=visibility_state,
        outputs=[visibility_state, chatbot_panel]
    )

if __name__ == "__main__":
    demo.launch()