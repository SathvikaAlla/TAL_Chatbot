import json
from openai import AzureOpenAI

# Load your JSON
with open("converters_with_links_and_pricelist.json", "r") as f:
    data = json.load(f)

client = AzureOpenAI(
    api_key="<YOUR_AZURE_OPENAI_KEY>",
    api_version="2024-02-01",
    azure_endpoint="<YOUR_AZURE_OPENAI_ENDPOINT>"
)

for key, doc in data.items():
    doc["id"] = key  # Add unique ID
    text = f"{doc.get('TYPE', '')} {doc.get('CONVERTER DESCRIPTION:', '')} {doc.get('Name', '')}"
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
        dimensions=1536
    )
    doc["vector"] = response.data[0].embedding

# Save the updated JSON
with open("converters_with_vectors.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
