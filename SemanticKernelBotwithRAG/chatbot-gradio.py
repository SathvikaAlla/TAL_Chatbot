import logging
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from azure.cosmos import CosmosClient
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from models.converterModels import PowerConverter  
from plugins.converterPlugin import ConverterPlugin
import os
import gradio as gr

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("kernel")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s"
))
logger.addHandler(handler)


# Initialize Semantic Kernel
kernel = Kernel()

# Add Azure OpenAI Chat Service
kernel.add_service(AzureChatCompletion(
    service_id="chat",
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY")
))
allowed_fields = [
    "id","artnr","type", "converter_description","strain_relief","location","dimmability","efficiency_full_load",
    "ip","class","nom_input_voltage_v.min","nom_input_voltage_v.max","output_voltage_v.min","output_voltage_v.max",
    "name","listprice","unit","lifecycle","lamps","size"
]
# SQL Generation Plugin
class NL2SQLPlugin:
    @kernel_function(name="generate_sql", description="Generate Cosmos DB SQL query")
    async def generate_sql(self, question: str) -> str:
        sql = await self._generate_sql_helper(question)
        # Block DML commands first
        if any(command in sql.upper() for command in ["DELETE", "UPDATE", "INSERT"]):
            return ""
        
        # # Validate fields before proceeding
        # if not self._validate_fields(sql, allowed_fields):
        #     return "ERROR: Query contains invalid fields"
        
        if "FROM converters c" in sql:
            sql = sql.replace("FROM converters c", "FROM c")
        if "SELECT *" not in sql and "FROM c" in sql:
            sql = sql.replace("SELECT c.*,", "SELECT *")
            sql = sql.replace("SELECT c.*", "SELECT *")
            sql = sql.replace("SELECT c", "SELECT *")
        
        logger.info(f"finalSQL {sql}")

        return sql
    
    async def _generate_sql_helper(self, question: str) -> str:
        from semantic_kernel.contents import ChatHistory
        
        chat_service = kernel.get_service("chat")
        chat_history = ChatHistory()
        chat_history.add_user_message(f"""Convert to Cosmos DB SQL: {question}
            Collection: converters (alias 'c')
            Fields:
                - type (e.g., '350mA')
                - artnr (numeric (int) article number e.g., 930546)
                - output_voltage_v: dictionary with min/max values for output voltage
                - output_voltage_v.min (e.g., 15)
                - output_voltage_v.max (e.g., 40)
                - nom_input_voltage_v: dictionary with min/max values for input voltage
                - nom_input_voltage_v.min (e.g., 198)
                - nom_input_voltage_v.max (e.g., 264)
                - lamps: dictionary with min/max values for lamp types for this converter
                - lamps["lamp_name"].min (e.g., 1)
                - lamps["lamp_name"].max (e.g., 10)
                - class (safety class)
                - dimmability (e.g. if not dimmable 'NOT DIMMABLE'. if supports dimming, 'DALI/TOUCHDIM','MAINS DIM LC' etc)
                - listprice (e.g., 58)
                - lifecycle (e.g., 'Active')
                - size (e.g., '150x30x30')
                - dimlist_type (e.g., 'DALI')
                - pdf_link (link to product PDF)
                - converter_description (e.g., 'POWERLED CONVERTER REMOTE 180mA 8W IP20 1-10V')
                - ip (Ingress Protection, integer values e.g., 20,67)
                - efficiency_full_load (e.g., 0.9)
                - name (e.g., 'Power Converter 350mA')
                - unit (e.g., 'PC')
                - strain_relief (e.g., "NO", "YES")
            SQL Guidelines (if needed):
                - Always use SELECT * and never individual fields
                - Always refer to fields in WHERE clause using c.<field_name>
                - For exact matches use: WHERE c.[field] = value
                - For ranges use: WHERE c.[field].min = X AND c.[field].max = Y
                - Check for dimmability support by using either !="NOT DIMMABLE" or ="NOT DIMMABLE"
                - Do not use AS and cast key names
            Return ONLY SQL without explanations""")
        
        response = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=AzureChatPromptExecutionSettings()
        )
        logger.info(f"Response dB schema{response}")
        
        return str(response)
    

# Register plugins
kernel.add_plugin(ConverterPlugin(logger=logger), "CosmosDBPlugin")
kernel.add_plugin(NL2SQLPlugin(), "NL2SQLPlugin")

# Updated query handler using function calling
async def handle_query(user_input: str):
    
    settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True)        
        )
    
    prompt = f"""
    You are a converter database expert. Process this user query:
    {user_input}
    
    Available functions:
    - generate_sql: Creates SQL queries (use only for complex queries or schema keywords)
    - query_converters: Executes SQL queries
    - get_compatible_lamps: Simple artnr-based lamp queries
    - get_converters_by_lamp_type: Simple lamp type searches
    - get_lamp_limits: Simple artnr+lamp combinations
    - RAG_search: questions about dimmability or current (if query contains mains c, dali, 350mA, dali drivers, dimming)
    
    Decision Flow:
    1. Identify synonyms :
        output voltage = voltage forward = forward voltage = Vf
        Driver = ledconverter = converter = power supply = gear
        lamps = luminares

    2. Use simple functions if query matches these patterns:
       - "lamps for [artnr]" → get_compatible_lamps
       - "converters for [lamp type]" → get_converters_by_lamp_type
       - "min/max [lamp] for [artnr]" → get_lamp_limits
    
    3. Use SQL generation ONLY when:
       - Query contains schema keywords: voltage, price, type, ip, efficiency, size, class
       - Combining multiple conditions (AND/OR/NOT)
       - Needs complex filtering/sorting
       - Requesting technical specifications
    
    Examples:
    User: "Show IP67 converters under €100" → generate_sql
    User: "What lamps are compatible with 930560?" → get_compatible_lamps
    User: "What converters are compatible with haloled lamps?" → get_converters_by_lamp_type
    User: "Voltage range for 930562" → generate_sql
    """
    
    result = await kernel.invoke_prompt(
        prompt=prompt,
        settings=settings
    )
    
    return str(result)

# Example usage
async def main():

   while True:
        try:
            query = input("User: ")
            if query.lower() in ["exit", "quit"]:
                break

            response = await handle_query(query)
            print(response)
            
        except KeyboardInterrupt:
            break



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
    width: 600px;
    height: 700px;
    background-color: #ffffff;
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between; /* keep input box pinned at the bottom */
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
    border-top: 1px solid #eee;
    padding: 10px;
    background-color: #fff;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.gr-textbox textarea {
    flex: 1;
    resize: none;
    padding: 10px;
    background-color: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-family: inherit;
    font-size: 14px;
}

footer {
    display: none !important;
}
"""
panel_visible = False

def toggle_panel():
    global panel_visible
    panel_visible = not panel_visible
    return gr.Column(visible=panel_visible)

with gr.Blocks(css=custom_css) as demo:
    # Toggle button (floating action button)
    toggle_btn = gr.Button("💬", elem_id="chatbot-toggle-btn")

    # Chat panel (initially hidden)
    chat_panel = gr.Column(visible=panel_visible, elem_id="chatbot-panel")
    with chat_panel:
        # Chat header
        with gr.Row(elem_id="chat-header"):
            gr.HTML("""
                <div id='chat-header'>
                    <img src="https://www.svgrepo.com/download/490283/pixar-lamp.svg" />
                    Lofty the TAL Bot
                </div>
            """)
        # Chatbot and input
        chatbot = gr.Chatbot(elem_id="gr-chatbot", type="messages")
        msg = gr.Textbox(placeholder="Type your question here...", elem_id="gr-textbox")
        clear = gr.ClearButton([msg, chatbot])


    # Function to handle messages
    async def respond(message, chat_history):
        response = await handle_query(message)
        # Convert existing history to OpenAI format if it's in tuples
        
        # Add new messages
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": response})
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    toggle_btn.click(toggle_panel, outputs=chat_panel)

demo.launch(share=True)