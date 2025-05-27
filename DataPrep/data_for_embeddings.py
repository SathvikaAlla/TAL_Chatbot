import json

# Read the original JSON file
with open('/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Transform the data
documents = []
for key, value in data.items():
    value["id"] = key  # Add the 'id' field (required by Cosmos DB)
    documents.append(value)

# Save the transformed data
with open('transformed_products.json', 'w', encoding='utf-8') as f:
    json.dump(documents, f, indent=2, ensure_ascii=False)

print("Transformation complete. Output saved to 'transformed_products.json'.")
