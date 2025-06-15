import logging
import uuid
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
from plugins.chatMemoryPlugin import ChatMemoryPlugin
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


class NL2SQLPlugin:
    @kernel_function(name="generate_sql", description="Generate Cosmos DB SQL query")
    async def generate_sql(self, question: str) -> str:
        sql = await self._generate_sql_helper(question)
        # Block DML commands first
        if any(command in sql.upper() for command in ["DELETE", "UPDATE", "INSERT", "SET"]):
            return "Invalid operation"

        if "FROM converters c" in sql:
            sql = sql.replace("FROM converters c", "FROM c")
        if "SELECT *" not in sql and "FROM c" in sql:
            sql = sql.replace("SELECT c.*,", "SELECT *")
            sql = sql.replace("SELECT c.*", "SELECT *")
            sql = sql.replace("SELECT c", "SELECT *")
        

        return sql
    
    async def _generate_sql_helper(self, question: str) -> str:
        from semantic_kernel.contents import ChatHistory
        
        chat_service = kernel.get_service("chat")
        chat_history = ChatHistory()
        chat_history.add_user_message(f"""Convert to Cosmos DB SQL: {question}
        Collection: converters (alias 'c')
        Fields:
            - c.type (e.g., '350mA','180mA','700mA','24V DC','48V') - for queries related to current (mA) always refer to c.type 
            - c.artnr (numeric (int) article number e.g., 930546)
            - c.output_voltage_v: dictionary with min/max values for output voltage
            - c.output_voltage_v.min (e.g., 15)
            - c.output_voltage_v.max (e.g., 40)
            - c.nom_input_voltage_v: dictionary with min/max values for input voltage
            - c.nom_input_voltage_v.min (e.g., 198)
            - c.nom_input_voltage_v.max (e.g., 264)
            - c.lamps: dictionary with min/max values for lamp types for this converter
            - c.lamps["lamp_name"].min (e.g., 1)
            - c.lamps["lamp_name"].max (e.g., 10)
            - c.class (safety class)
            - c.dimmability (e.g. if not dimmable 'NOT DIMMABLE'. if supports dimming, 'DALI/TOUCHDIM','MAINS DIM LC', '1-10V','CASAMBI' etc)
            - c.listprice (e.g., 58)
            - c.size (e.g., '150x30x30')
            - c.dimlist_type (e.g., 'DALI')
            - c.pdf_link (link to product PDF)
            - c.converter_description (e.g., 'POWERLED CONVERTER REMOTE 180mA 8W IP20 1-10V')
            - c.ip (Ingress Protection, integer values e.g., 20,67)
            - c.efficiency_full_load (e.g., 0.9)
            - c.name (e.g., 'Power Converter 350mA')
            - c.unit (e.g., 'PC')
            - c.strain_relief (e.g., "NO", "YES")
        Example document for reference:
        c = {{
            "id": "8797fff0-e0a8-4e23-aad0-06209881b1d3",
            "type": "350mA",
            "artnr": 984500,
            "converter_description": "POWERLED CONVERTER REMOTE 350mA 18W IP20 DALI/TOUCHDIM",
            "strain_relief": "YES",
            "location": "INDOOR",
            "dimmability": "DALI/TOUCHDIM",
            "ccr_amplitude": "YES",
            "efficiency_full_load": 0.85,
            "ip": 20,
            "class": 2,
            "nom_input_voltage_v": {{"min": 220, "max": 240}},
            "output_voltage_v": {{"min": 9, "max": 52}},
            "barcode": "54 15233 15690 8",
            "name": "POWERLED REMOTE CONVERTER (18.2W) TOUCH DALI DIM 350mA",
            "listprice": 47,
            "unit": "PC",
            "pdf_link": "...",
            "lamps": {{
                "Single led XPE": {{"min": 3, "max": 15}},
                "Thinksmall/floorspot WC luxeon MX": {{"min": 1, "max": 4}},
                "*MIX 6 monocolor": {{"min": 1, "max": 2}},
                "Cedrus quantum": {{"min": 1, "max": 2}},
                "*MIX 6 halosphere": {{"min": 1, "max": 2}},
                "MIX 13 monocolor": {{"min": 1, "max": 1}},
                "MIX 13 halosphere": {{"min": 1, "max": 1}},
                "ORBITAL monocolor": {{"min": 1, "max": 1}},
                "ORBITAL halosphere": {{"min": 1, "max": 1}},
                "Beaufort²": {{"min": 1, "max": 1}},
                "Beaufort": {{"min": 1, "max": 1}},
                "Haloled": {{"min": 1, "max": 4}},
                "B4": {{"min": 1, "max": 4}},
                "MIX 26 monocolor": {{"min": 1, "max": 1}},
                "*BOA WC": {{"min": 1, "max": 5}}
            }},
            "size": "160*42*30"
        }}
        SQL Guidelines (if needed):
            - Always use SELECT * and never individual fields
            - When current like 350mA is detected, always query the c.type field
            - Always refer to fields in SELECT or WHERE clause using c.<field_name>
            - Do NOT use LIMIT. Instead use TOP <value> in SELECT statement like SELECT TOP 1 instead of LIMIT 1
            - For exact matches use: WHERE c.[field] = value
            - For ranges use: WHERE c.[field].min = X AND c.[field].max = Y
            - Check for dimmability support by using either != "NOT DIMMABLE" or = "NOT DIMMABLE"
            - Do not use AS and cast key names
            - For lamp compatibility: Use WHERE IS_DEFINED(c.lamps["lamp_name"]) to check if a specific lamp is supported, or WHERE IS_DEFINED(c.lamps) for any lamp support.
                                    
        Examples:
            - What is the price of 40063 : SELECT * FROM c WHERE c.artnr=40063
            - Give me converters with an output voltage range of exactly 2-25 : SELECT * FROM c WHERE c.output_voltage_v.min=2 AND c.output_voltage_v.max=25
            - Find converters with an input voltage range of exactly 90-264 : SELECT * FROM c WHERE c.nom_input_voltage_v.min = 90 AND c.nom_input_voltage_v.max = 264
            - Find converters that support a specific lamp type (e.g., "B4") : SELECT * FROM c WHERE IS_DEFINED(c.lamps["B4"])
            - Find converters that support any lamp (check for lamp compatibility) : SELECT * FROM c WHERE IS_DEFINED(c.lamps)
            - Find converters with a specific IP rating (e.g., 67): SELECT * FROM c WHERE c.ip = 67
            - List of 350mA converters compatible with Haloled: SELECT * FROM c WHERE IS_DEFINED(c.lamps["Haloled"]) ANlist oD c.type="350mA"
            - List 700mA drivers: SELECT * FROM c WHERE c.type="700mA"
        Return ONLY SQL without explanations""")
                
        response = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=AzureChatPromptExecutionSettings()
        )
        
        return str(response)


# Register plugins
kernel.add_plugin(ConverterPlugin(logger=logger), "CosmosDBPlugin")
kernel.add_plugin(ChatMemoryPlugin(logger=logger), "ChatMemoryPlugin")
kernel.add_plugin(NL2SQLPlugin(), "NL2SQLPlugin")

# Updated query handler using function calling
async def handle_query(user_input: str):
    session_id = str(uuid.uuid4()) 
    
    settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True)        
        )
    
    ARTNR_PATTERN = r'\b\d{6}\b'
    
    prompt = f"""
    You are a product catalog customer service chatbot for TAL BV. Answer questions about converters, their specifications and lamps. Process this user query:
    {user_input}

    artnr Pattern: {ARTNR_PATTERN}
    
    Available functions:
    - generate_sql: Creates SQL queries (use only for complex queries or schema keywords)
    - query_converters: Executes SQL queries
    - get_compatible_lamps: Simple artnr-based lamp queries
    - get_converters_by_lamp_type: Simple lamp type searches
    - get_lamp_limits: Simple artnr+lamp combinations
    - get_converters_by_dimming: use when question contains dimming types WITHOUT artnr (if query contains mains c, dali, 1-10v, mains)
    - get_converters_by_voltage_current: use for questions about input or output voltage
    
    Decision Flow:
    1. Identify synonyms :
        output voltage = voltage forward = forward voltage = Vf
        Driver = ledconverter = converter = power supply = gear
        lamps = luminares
        ip = Ingress Protection and NOT INPUT VOLTAGE
    
    2. Check for explicit dimming types (dali/1-10V/mains/casambi):
        - If found → use get_converters_by_dimming
        - Include lamp_type parameter if lamp is mentioned

    3. Use simple functions if query matches these patterns:
    - "lamps for [artnr]" → get_compatible_lamps
    - "converters for [lamp type]" → get_converters_by_lamp_type
    - "min/max [lamp] for [artnr]", "most [lamp]/ least [lamp]" → get_lamp_limits
    - "drivers on 24V output" → get_converters_by_voltage_current
    - "drivers on 350ma"  → get_converters_by_voltage_current
    
    4. Use SQL generation ONLY when:
    - Query contains schema keywords: price, type, ip, efficiency, size, class, strain relief, lifecycle,
    - Avoid using SQL generation for lamp related questions
    - Combining multiple conditions (AND/OR/NOT)
    - Needs complex filtering/sorting
    - Requesting technical specifications for a specific converter like "dimming type of converter [artnr]", "size of [artnr]"
    
    5. NEVER
        - use get_converters_by_dimming when artnr Pattern is detected
        - use get_converters_by_lamp_type when dimming type like dali, mains is mentioned
        - use "ipXX" as input_voltage parameter in get_converters_by_voltage_current
        - interpret "ip" as input voltage (IP = Ingress Protection)
    
    6. For IP ratings:
        - Extract using regex: r'ip[\s]?(\d+)'
        - Use SQL: SELECT * FROM c WHERE c.ip = X
        - NEVER route to voltage-related functions
    
    6. If you cannot identify any relevant keywords, respond with a friendly message clarifying what you are and what they can ask for."
    7. If no results are recieved, give an apologetic reason. Never respond with SQL query suggestions.
    
    Examples:
    User: "Show IP67 converters under €100" → generate_sql
    User: "What lamps are compatible with 930560?" → get_compatible_lamps
    User: "List of 1p20 drivers for haloled single on track" → get_converters_by_lamp_type(lamp_type="haloled single on track") → inspect returned converters
    User: "List 700mA drivers with ip20 rating"  → get_converters_by_voltage_current(current = "700mA") → inspect returned converters
    User: "List of 350mA drivers" → get_converters_by_voltage_current(current = "350mA")
    User: "What converters are compatible with haloled lamps?" → get_converters_by_lamp_type
    User: "Voltage range for 930562" → generate_sql
    User: "Dimming type of 930581"  → generate_sql
    User: "List of dali drivers on 24V output?" → get_converters_by_dimming"
    User: 'List of 24V drivers for ledline medium power → get_converters_by_dimming(dimming_type=None, lamp_type="ledline medium power",voltage_current="24V")(or) get_converters_by_lamp_type(lamp_type="ledline medium power") → inspect returned converters '
    User: 'Which converter supports the most haloled lamps' → get_converters_by_lamp_type(lamp_type="haloled) → get_lamp_limits for each converter returned
    """
    try:
        result = await kernel.invoke_prompt(
            prompt=prompt,
            settings=settings
        )

        func_name = result.model_dump()["metadata"]["messages"]["messages"][2]["items"][0]["name"]
        print(func_name)
        log_func = kernel.get_function("ChatMemoryPlugin", "log_interaction")
        await log_func.invoke(
            kernel=kernel,
            session_id=session_id,
            question=user_input,
            function_used=func_name,
            answer=str(result)
        )
        
        return str(result)
    
    except Exception as e:
        # Handle errors properly
        error_func = kernel.get_function("ChatMemoryPlugin", "log_interaction")
        await error_func.invoke(
            kernel=kernel,
            session_id=session_id,
            question=user_input,
            function_used="error",
            answer=str(e)
        )
        raise

# # Example usage
# async def main():
#     # cm = ChatMemoryPlugin(logger)
#     # await cm.get_semantic_faqs()

#    while True:
#         try:
#             query = input("User: ")
#             if query.lower() in ["exit", "quit"]:
#                 break

#             response = await handle_query(query)
#             print(response)
            
#         except KeyboardInterrupt:
#             break


# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

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
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

#chatbot-panel {
    position: fixed;
    bottom: 10vw;
    right: 2vw;
    z-index: 10000;
    width: 95vw;
    max-width: 600px;
    height: 90vh;
    max-height: 700px;
    background-color: #ffffff;
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    font-family: 'Arial', sans-serif;
}

@media (max-width: 600px) {
    #chatbot-panel {
        width: 100vw;
        height: 100vh;
        right: 0;
        bottom: 0;
        border-radius: 0;
    }
    #chatbot-toggle-btn {
        right: 10px;
        bottom: 10px;
        width: 48px;
        height: 48px;
        font-size: 24px;
    }
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
        send = gr.Button("Send")
        # clear = gr.ClearButton([msg, chatbot])


    # Function to handle messages
    async def respond(message, chat_history):
        response = await handle_query(message)
        # Convert existing history to OpenAI format if it's in tuples
        
        # Add new messages
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": response})
        return "", chat_history
    send.click(respond, [msg, chatbot], [msg,chatbot])
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    toggle_btn.click(toggle_panel, outputs=chat_panel)

demo.launch()