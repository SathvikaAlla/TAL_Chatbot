import os
import gradio as gr
from datetime import datetime
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder, FileSearchTool

# --- Custom CSS ---
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

# --- Agent Manager Class ---
class AgentManager:
    def __init__(self, endpoint, file_path):
        self.project = AIProjectClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
        )
        self.file = self.project.agents.files.upload(
            file_path=file_path,
            purpose="assistants"
        )
        self.vector_store = self.project.agents.vector_stores.create_and_poll(
            file_ids=[self.file.id],
            name=f"vector_store_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        self.file_search = FileSearchTool(vector_store_ids=[self.vector_store.id])
        self.agent = self.project.agents.create_agent(
            model="gpt-4o-mini",
            name=f"converter_assistant_{datetime.now().strftime('%H%M%S')}",
            instructions=(
                "You are a helpful technical assistant for TAL BV and assist users in finding information. "
                "Use the provided documentation to answer questions accurately."
            ),
            tools=self.file_search.definitions,
            tool_resources=self.file_search.resources,
        )
        self.thread = self.project.agents.threads.create()

    def process_message(self, user_message):
        self.project.agents.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=user_message
        )
        run = self.project.agents.runs.create_and_process(
            thread_id=self.thread.id,
            agent_id=self.agent.id
        )
        if run.status == "failed":
            return f"⚠️ Error: {run.last_error.message}"
        messages = self.project.agents.messages.list(
            thread_id=self.thread.id,
            order=ListSortOrder.ASCENDING
        )
        all_messages = list(messages)
        return next(
            msg.text_messages[-1].text.value
            for msg in reversed(all_messages)
            if msg.run_id == run.id and msg.text_messages
        )

    def cleanup(self):
        self.project.agents.vector_stores.delete(self.vector_store.id)
        self.project.agents.files.delete(file_id=self.file.id)
        self.project.agents.delete_agent(self.agent.id)

# --- Initialize Agent Manager ---
# Update these paths and endpoint for your environment!
ENDPOINT = "https://tal-chatbot-resource2.services.ai.azure.com/api/projects/tal-chatbot"
FILE_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"
agent_manager = AgentManager(ENDPOINT, FILE_PATH)

# --- Gradio Chat Function ---
def tal_agent_chatbot(user_message, history):
    response = agent_manager.process_message(user_message)
    history = history or []
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response})
    return history, history, ""

# --- UI and Visibility ---
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
            fn=tal_agent_chatbot,
            inputs=[msg, history],
            outputs=[chat, history, msg]
        )
        msg.submit(
            fn=tal_agent_chatbot,
            inputs=[msg, history],
            outputs=[chat, history, msg]
        )

    chatbot_toggle.click(
        fn=toggle_visibility,
        inputs=visibility_state,
        outputs=[visibility_state, chatbot_panel]
    )

if __name__ == "__main__":
    try:
        demo.launch()
    except KeyboardInterrupt:
        print("\nCleaning up resources...")
        agent_manager.cleanup()
        print("Done.")
