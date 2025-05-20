import json
from typing import Dict, Any

# Path to your JSON file
JSON_FILE_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"

# Load the existing JSON data
def load_json(path=JSON_FILE_PATH) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Save JSON data back to file
def save_json(data: Dict[str, Any], path=JSON_FILE_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Add a new converter
def add_converter(converter_id: str, converter_info: Dict[str, Any]):
    data = load_json()
    if converter_id in data:
        return f"Converter {converter_id} already exists. Use update to modify it."
    data[converter_id] = converter_info
    save_json(data)
    return f"Converter {converter_id} added successfully."

# Delete a converter
def delete_converter(converter_id: str):
    data = load_json()
    if converter_id not in data:
        return f"Converter {converter_id} does not exist."
    del data[converter_id]
    save_json(data)
    return f"Converter {converter_id} deleted successfully."

# Update an existing converter
def update_converter(converter_id: str, updated_info: Dict[str, Any]):
    data = load_json()
    if converter_id not in data:
        return f"Converter {converter_id} does not exist. Use add to create it."
    data[converter_id].update(updated_info)
    save_json(data)
    return f"Converter {converter_id} updated successfully."

# Add or update a lamp in a converter
def add_or_update_lamp(converter_id: str, lamp_name: str, lamp_info: Dict[str, Any]):
    data = load_json()
    if converter_id not in data:
        return f"Converter {converter_id} does not exist."
    lamps = data[converter_id].get("lamps", {})
    lamps[lamp_name] = lamp_info
    data[converter_id]["lamps"] = lamps
    save_json(data)
    return f"Lamp '{lamp_name}' added/updated successfully in converter {converter_id}."

# Delete a lamp from a converter
def delete_lamp(converter_id: str, lamp_name: str):
    data = load_json()
    if converter_id not in data:
        return f"Converter {converter_id} does not exist."
    lamps = data[converter_id].get("lamps", {})
    if lamp_name not in lamps:
        return f"Lamp '{lamp_name}' does not exist in converter {converter_id}."
    del lamps[lamp_name]
    data[converter_id]["lamps"] = lamps
    save_json(data)
    return f"Lamp '{lamp_name}' deleted successfully from converter {converter_id}."

# Example usage
if __name__ == "__main__":
    # Add a new converter example
    new_converter = {
        "TYPE": "24V DC",
        "ARTNR": 40099,
        "CONVERTER DESCRIPTION:": "LEDCONVERTER 24V 30W IP20",
        "lamps": {},
        "Listprice": 75.0,
        "pdf_link": "https://example.com/40099.pdf"
    }
    print(add_converter("24V DC - 40099", new_converter))

    # Update a converter example
    print(update_converter("24V DC - 40025", {"Listprice": 65.0}))

    # Add or update a lamp example
    lamp_info = {"min": 1, "max": 2}
    print(add_or_update_lamp("24V DC - 40025", "m LEDLINE ultra power 25W", lamp_info))

    # Delete a lamp example
    print(delete_lamp("24V DC - 40025", "m LEDLINE high power 14,4W"))

    # Delete a converter example
    print(delete_converter("24V DC - 40099"))
