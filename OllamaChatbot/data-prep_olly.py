# 1. Data Preparation Script (prepare_data.py)
import json
from datasets import Dataset

def format_conversations(input_file, output_file):
    with open(input_file) as f:
        tech_data = json.load(f)

    conversations = []
    for product_id, specs in tech_data.items():
        # Basic Q&A pairs
        conversations.append({
            "messages": [
                {"role": "user", "content": f"What is the output voltage of {specs['CONVERTER DESCRIPTION:']}?"},
                {"role": "assistant", "content": f"The output voltage is {specs['OUTPUT VOLTAGE (V)']}V."}
            ]
        })
        
        # Compatibility questions
        if 'lamps' in specs:
            for lamp_type, details in specs['lamps'].items():
                conversations.append({
                    "messages": [
                        {"role": "user", "content": f"How many {lamp_type} can I use with {specs['ARTNR']}?"},
                        {"role": "assistant", "content": f"You can use between {details['min']} and {details['max']} units."}
                    ]
                })

    # Save formatted data
    dataset = Dataset.from_list(conversations)
    dataset.save_to_disk(output_file)

if __name__ == "__main__":
    format_conversations("/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json", "OllamaChatbot/formatted_data")
