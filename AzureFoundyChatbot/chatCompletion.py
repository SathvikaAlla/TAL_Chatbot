from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

project = AIProjectClient(
    endpoint="https://tal-chatbot-resource2.services.ai.azure.com/api/projects/tal-chatbot",
    credential=DefaultAzureCredential(),
)

models = project.inference.get_azure_openai_client(api_version="2025-04-01-preview")
response = models.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful writing assistant"},
        {"role": "user", "content": "Write me a poem about flowers"},
    ],
)

print(response.choices[0].message.content)