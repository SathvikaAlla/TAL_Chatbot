import json
import uuid
import re
import math

def clean_key(key: str) -> str:
    """Cleans keys to be Cosmos DB compatible."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', key)

def is_json_compatible(value):
    """Checks if a value is valid JSON (and Cosmos DB safe)."""
    if isinstance(value, float):
        return math.isfinite(value)  # Rejects NaN, inf
    if isinstance(value, (str, int, bool)) or value is None:
        return True
    if isinstance(value, (list, dict)):
        return True
    return False

def fix_document(doc: dict) -> dict:
    """Cleans a document for Cosmos DB storage."""
    # Ensure 'id' field exists and is a string
    if 'id' not in doc or not isinstance(doc['id'], str):
        doc['id'] = str(uuid.uuid4())

    cleaned_doc = {}

    for key, value in doc.items():
        new_key = clean_key(key)

        # Recursively clean nested dictionaries
        if isinstance(value, dict):
            value = fix_document(value)
        elif isinstance(value, list):
            value = [fix_document(v) if isinstance(v, dict) else v for v in value]

        # Replace NaN, Infinity, etc.
        if not is_json_compatible(value):
            value = None

        cleaned_doc[new_key] = value

    return cleaned_doc

def process_json(input_path: str, output_path: str):
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Fix trailing commas
    raw_text = re.sub(r',\s*([}\]])', r'\1', raw_text)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return

    # Ensure top-level is a list of objects
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        print("Top-level JSON must be an array of objects or a single object.")
        return

    cleaned = [fix_document(doc) for doc in data if isinstance(doc, dict)]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, indent=2)

    print(f"Fixed {len(cleaned)} documents. Output saved to {output_path}")

# USAGE
input_path = "/Users/alessiacolumban/TAL_Chatbot/transformed_products.json"
output_path = "cleaned_converters.json"
process_json(input_path, output_path)
