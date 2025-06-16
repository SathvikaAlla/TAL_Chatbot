from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder, FileSearchTool

project = AIProjectClient(
    endpoint="https://tal-chatbot-resource2.services.ai.azure.com/api/projects/tal-chatbot",
    credential=DefaultAzureCredential(),
)

# Upload file and create vector store
file = project.agents.files.upload(file_path="/Users/sathvika/MCT/SEM-4/industry-project/TAL_Chatbot-1/converters_with_links_and_pricelist.json", 
                                   purpose="assistants")
vector_store = project.agents.vector_stores.create_and_poll(file_ids=[file.id], name="my_vectorstore")

# Create file search tool and agent
file_search = FileSearchTool(vector_store_ids=[vector_store.id])
agent = project.agents.create_agent(
    model="gpt-4o-mini",
    name="my-assistant",
    instructions="You are a helpful assistant and can search information from uploaded files",
    tools=file_search.definitions,
    tool_resources=file_search.resources,
)

# Create thread and process user message
thread = project.agents.threads.create()
project.agents.messages.create(thread_id=thread.id, role="user", content="With which convertor can i use the most Haloled lamps?")
run = project.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

# Handle run status
if run.status == "failed":
    print(f"Run failed: {run.last_error}")

# Print thread messages
messages = project.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
for message in messages:
    if message.run_id == run.id and message.text_messages:
        print(f"{message.role}: {message.text_messages[-1].text.value}")

# Cleanup resources
project.agents.vector_stores.delete(vector_store.id)
project.agents.files.delete(file_id=file.id)
project.agents.delete_agent(agent.id)
print("Agent Deleted")