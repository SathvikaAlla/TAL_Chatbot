from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder, FileSearchTool
from datetime import datetime
import readline  # For input history and better CLI experience

# Initialize client and resources
project = AIProjectClient(
    endpoint="https://tal-chatbot-resource2.services.ai.azure.com/api/projects/tal-chatbot",
    credential=DefaultAzureCredential(),
)

class ChatBot:
    def __init__(self):
        # Upload file and create vector store
        self.file = project.agents.files.upload(
            file_path="/Users/sathvika/MCT/SEM-4/industry-project/TAL_Chatbot-1/converters_with_links_and_pricelist.json",
            purpose="assistants"
        )
        self.vector_store = project.agents.vector_stores.create_and_poll(
            file_ids=[self.file.id],
            name=f"vector_store_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        # Create file search tool and agent
        self.file_search = FileSearchTool(vector_store_ids=[self.vector_store.id])
        self.agent = project.agents.create_agent(
            model="gpt-4o-mini",
            name=f"converter_assistant_{datetime.now().strftime('%H%M%S')}",
            instructions=(
                "You are a helpful technical assistant for TAL BV and assist users in finding information."
                "Use the provided documentation to answer questions accurately. "),
            tools=self.file_search.definitions,
            tool_resources=self.file_search.resources,
        )
        self.thread = project.agents.threads.create()
        self.history = []

    def _process_message(self, user_input):
        try:
            # Add user message to thread
            project.agents.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=user_input
            )
            
            # Run the agent
            run = project.agents.runs.create_and_process(
                thread_id=self.thread.id,
                agent_id=self.agent.id
            )

            if run.status == "failed":
                return f"⚠️ Error: {run.last_error.message}"

            # Get agent response
            messages = project.agents.messages.list(
                thread_id=self.thread.id,
                order=ListSortOrder.ASCENDING
            )
            
            all_messages = list(messages)
            return next(
                msg.text_messages[-1].text.value 
                for msg in reversed(all_messages) 
                if msg.run_id == run.id and msg.text_messages
            )
            
        except Exception as e:
            return f"🚨 Error processing request: {str(e)}"

    def start_chat(self):
        print("🟢 Welcome to Converter Assistant!")
        print("Type 'exit' to end the conversation\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                print("\n🤖 Assistant is thinking...")
                response = self._process_message(user_input)
                
                # Update history and display
                self.history.append(f"You: {user_input}")
                self.history.append(f"Assistant: {response}")
                
                print(f"\n🤖 Assistant: {response}\n")
                print("―――――――――――――――――――――――――――――――――――")

            except KeyboardInterrupt:
                print("\n🛑 Session ended by user")
                break

        self.cleanup()

    def cleanup(self):
        project.agents.vector_stores.delete(self.vector_store.id)
        project.agents.files.delete(file_id=self.file.id)
        project.agents.delete_agent(self.agent.id)
        print("\n🔴 Agent session ended. Resources cleaned up.")

if __name__ == "__main__":
    bot = ChatBot()
    bot.start_chat()
