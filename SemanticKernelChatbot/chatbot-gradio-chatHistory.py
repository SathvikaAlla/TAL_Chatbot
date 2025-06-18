import asyncio
import logging
import uuid
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function
from azure.cosmos import CosmosClient
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
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
        
        
        chat_service = kernel.get_service("chat")
        chat_history = ChatHistory()
        print('Using NL2SQL Plugin')
        chat_history.add_user_message(f"""Convert to Cosmos DB SQL: user question - {question}
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
            - Do NOT use subqueries
            - Do not use AS and cast key names
            - For lamp compatibility: Use WHERE IS_DEFINED(c.lamps["lamp_name"]) to check if a specific lamp is supported, or WHERE IS_DEFINED(c.lamps) for any lamp support.
                                    
        Examples:
            - What is the price of 40063 : SELECT * FROM c WHERE c.artnr=40063
            - Give me converters with an output voltage range of exactly 2-25 : SELECT * FROM c WHERE c.output_voltage_v.min=2 AND c.output_voltage_v.max=25
            - Find converters with an input voltage range of exactly 90-264 : SELECT * FROM c WHERE c.nom_input_voltage_v.min = 90 AND c.nom_input_voltage_v.max = 264
            - Find converters that support a specific lamp type (e.g., "B4") : SELECT * FROM c WHERE IS_DEFINED(c.lamps["B4"])
            - Find converters that support any lamp (check for lamp compatibility) : SELECT * FROM c WHERE IS_DEFINED(c.lamps)
            - Find converters with a specific IP rating (e.g., 67): SELECT * FROM c WHERE c.ip = 67
            - List of 350mA converters compatible with Haloled: SELECT * FROM c WHERE IS_DEFINED(c.lamps["Haloled"]) AND c.type="350mA"
            - List 700mA drivers: SELECT * FROM c WHERE c.type="700mA"
            - Most efficient ip20 driver: SELECT TOP 1 FROM c WHERE c.ip=20 ORDER BY c.efficiency_full_load DESC
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


session_chat_histories = {}
async def handle_query(user_input: str, session_state:str):
    global session_chat_histories
    
    from semantic_kernel.contents import ChatHistoryTruncationReducer

    
    settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True)        
        )
    
    ARTNR_PATTERN = r'\b(?:\d{5}|\d{6})\b'
    
    prompt = f"""
    You are a product catalog customer service chatbot for TAL BV. Answer questions about converters, their specifications and lamps. Process this user query:
    {user_input}

    artnr Pattern: {ARTNR_PATTERN}
    artnrs are usually numbers like 40057 or 930565
    
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
    - To do this, use generate_sql NL2SQLPlugin 
    - Query contains schema keywords: price, type, ip, efficiency, size, class, strain relief, lifecycle,
    - Avoid using SQL generation for lamp related questions
    - Combining multiple conditions (AND/OR/NOT)
    - Needs complex filtering/sorting
    - Requesting technical specifications for a specific converter like "dimming type of converter [artnr]", "size of [artnr]"
    - You CANNOT INSERT DELETE or UPDATE. Return a message saying you cannot help with that immediately.
    
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

        if session_state not in session_chat_histories:
            chat_history = ChatHistoryTruncationReducer(
                system_message=prompt,
                target_count=3,
                threshold_count=2,
                auto_reduce=True
            )
            session_chat_histories[session_state] = chat_history
            
        else:
            chat_history = session_chat_histories[session_state]
        
        chat_history.add_user_message(user_input)


        chat_service = kernel.get_service("chat")
        result = await chat_service.get_chat_message_content(
                chat_history=chat_history,
                settings=settings,
                kernel=kernel,
            )
        chat_history.add_assistant_message(str(result))
        
        return str(result)
        
    except (KeyError, IndexError, AttributeError) as ex:
        logger.error(ex)
        pass
    
    except Exception as e:
        logger.error(e)
        raise

import gradio as gr

# Create a custom theme based on your brand colors
custom_theme = gr.themes.Base(
    primary_hue="red",
    secondary_hue="amber",
    font=[gr.themes.GoogleFont('Inter'), 'ui-sans-serif', 'system-ui', 'sans-serif'],
    font_mono=[gr.themes.GoogleFont('Roboto Mono'), 'ui-monospace', 'Consolas', 'monospace'],
)

# Minimal CSS for positioning only (avoiding styling)
minimal_css = """
#chatbot-toggle-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 10001;
}

#theme-toggle-btn {
    position: fixed !important;
    top: 20px;
    right: 20px;
    z-index: 10002;
    border-radius: 50% !important;
    width: 50px !important;
    height: 50px !important;
    min-width: 50px !important;
}

#chatbot-panel {
    position: fixed;
    bottom: 5vh;  
    right: 2vw;
    z-index: 10000;
    width: 95vw;
    max-width: 600px;
    height: 90vh;
    max-height: 700px;
}

#chat-header {
    width: calc(100% + 20px);
    box-sizing: border-box;
    margin: 0 -10px;
    margin-bottom: -7px !important;
}

.gr-chatbot {
    margin-top: -7px;
    width: 100%;
    box-sizing: border-box;
}

#chat-header img {
    border-radius: 50%;
    width: 50px;
    height: 50px;
    filter: brightness(0) invert(1);
}

#chatbot-toggle-btn {
        right: 30px;
        bottom: 30px;
        width: 48px;
        height: 48px;
        font-size: 24px;
    }

@media (max-width: 600px) {
    #chatbot-panel {
        width: 100vw;
        height: 100vh;
        right: 0;
        bottom: 0;
    }

    #theme-toggle-btn {
        top: 15px;
        right: 15px;
        width: 45px !important;
        height: 45px !important;
    }

"""
def format_faq_question(question):
    """Format FAQ questions with proper capitalization and punctuation"""
    # Remove extra whitespace
    question = question.strip()
    
    # Capitalize first letter
    if question:
        question = question[0].upper() + question[1:]
    
    # Handle specific terms that should be capitalized
    replacements = {
        'ma ': 'mA ',  # milliamps
        'haloled': 'Haloled',
        'boa ': 'BOA ',
        'eur': 'EUR',
        'v ': 'V ',  # volts
        'dali': 'DALI',
        'ip': 'IP'
    }
    
    for old, new in replacements.items():
        question = question.replace(old, new)
    
    # Add question mark if it's a question and doesn't end with punctuation
    question_words = ['what', 'which', 'how', 'where', 'when', 'why', 'can', 'do', 'does']
    if any(question.lower().startswith(word) for word in question_words):
        if not question.endswith(('?', '.', '!')):
            question += '?'
    
    return question

panel_visible = False

async def get_chatbot_examples():
    """Fetch FAQs and format them as Gradio chatbot examples"""
    try:
        # Get your chat memory plugin instance
        get_faqs_func = kernel.get_function("ChatMemoryPlugin", "get_semantic_faqs")
        
        # Call the function to get FAQs
        result = await get_faqs_func.invoke(kernel=kernel, limit=6, threshold=0.1)
        faqs = result.value if hasattr(result, 'value') else result
        
        # Format as Gradio examples
        examples = []
        for faq in faqs:
            faq = format_faq_question(faq)
            examples.append({
                "text": faq,
                "display_text": faq
            })
        
        return examples
    except Exception as e:
        logger.error(f"Failed to load FAQ examples: {str(e)}")
        return []
    
def get_examples_sync():
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(get_chatbot_examples())
    except:
        # If no event loop, create one
        return asyncio.run(get_chatbot_examples())
    
def toggle_panel():
    global panel_visible
    panel_visible = not panel_visible
    return gr.Column(visible=panel_visible)

# Apply the custom theme to your Blocks
with gr.Blocks(theme=custom_theme, css=minimal_css) as demo:
    faqs = gr.State(get_examples_sync())

    session_id = gr.State(str(uuid.uuid4()))

    # Toggle button
    toggle_btn = gr.Button(
        "💬", 
        elem_id="chatbot-toggle-btn",
        variant="primary",
        size="sm"
    )
    
    theme_toggle = gr.Button(
                "🌙",
                elem_id="theme-toggle-btn",
                variant="secondary",
                scale=0,
                min_width=50
    )

    # Chat panel
    chat_panel = gr.Column(visible=panel_visible, elem_id="chatbot-panel")
    
    with chat_panel:
        # Header - Remove the gr.Row wrapper and place directly in the column
        gr.HTML("""
            <div id='chat-header' style='
                background-color: var(--button-primary-background-fill);
                color: var(--button-primary-text-color);
                padding: 30px;
                font-weight: bold;
                font-size: 30px;
                display: flex;
                align-items: center;
                box-sizing: border-box;
                border-radius: var(--radius-md);'>
                <img src="https://www.svgrepo.com/download/490283/pixar-lamp.svg" 
                    style="width: 50px; height: 50px; border-radius: 50%; margin-right: 15px; filter: brightness(0) invert(1);" />
                Lofty the TAL Bot
            </div>
        """)

        # Chatbot with theme styling
        chatbot = gr.Chatbot(
            type="messages",
            height=400,
            show_copy_button=True,
            container=False,
            resizable=True,
            examples=faqs.value
        )
        
        # Input with theme styling
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Type your question here...",
                container=False,
                scale=4
            )

            send = gr.Button(
                "Send", 
                variant="primary",
                scale=1
            )
    def toggle_theme():
        # This uses Gradio's built-in JavaScript functionality
        return gr.update(), gr.update()

    theme_toggle.click(
        fn=None,
        js="""
        () => {
            // Toggle dark mode using Gradio's built-in functionality
            const isDark = document.body.classList.contains('dark');
            if (isDark) {
                document.body.classList.remove('dark');
                // Update button text
                const buttons = document.querySelectorAll('button');
                buttons.forEach(btn => {
                    if (btn.textContent.trim() === '☀️') {
                        btn.textContent = '🌙';
                    }
                });
                localStorage.setItem('gradio-theme', 'light');
            } else {
                document.body.classList.add('dark');
                // Update button text
                const buttons = document.querySelectorAll('button');
                buttons.forEach(btn => {
                    if (btn.textContent.trim() === '🌙') {
                        btn.textContent = '☀️';
                    }
                });
                localStorage.setItem('gradio-theme', 'dark');
            }
        }
        """
    )

    # Initialize theme on load
    demo.load(
        fn=None,
        js="""
        () => {
            // Check saved theme preference
            const savedTheme = localStorage.getItem('gradio-theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
                document.body.classList.add('dark');
                // Update button text
                setTimeout(() => {
                    const buttons = document.querySelectorAll('button');
                    buttons.forEach(btn => {
                        if (btn.textContent.trim() === '🌙') {
                            btn.textContent = '☀️';
                        }
                    });
                }, 100);
            }
        }
        """
    )

    def handle_example_select(evt: gr.SelectData):
        """Handle when user clicks on an example"""
        examples = faqs.value
        if evt.index < len(examples):
            selected_example = examples[evt.index]
            return selected_example.get("text", "")
        return ""

    # Connect the example_select event to populate the textbox
    chatbot.example_select(
        fn=handle_example_select,
        outputs=msg
    )

    # Your existing event handlers
    async def respond(message, chat_history):
        response = await handle_query(message, session_id.value)
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": response})
        return "", chat_history

    send.click(respond, [msg, chatbot], [msg, chatbot])
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    toggle_btn.click(toggle_panel, outputs=chat_panel)

demo.launch()
