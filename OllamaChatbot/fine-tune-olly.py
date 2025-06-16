# from transformers import AutoModelForCausalLM, AutoTokenizer  # Added missing import
# import mlx.core as mx
# from mlx.utils import tree_unflatten
# from transformers import AutoTokenizer, TrainingArguments
# from datasets import load_from_disk

# # Load data
# dataset = load_from_disk("/Users/alessiacolumban/TAL_Chatbot/OllamaChatbot/formatted_data")

# # Load model (Llama 3 8B example)
# model, tokenizer = AutoModelForCausalLM.from_pretrained(
#     "meta-llama/Meta-Llama-3-8B-Instruct",
#     trust_remote_code=True,
#     device_map="auto",  # Uses Apple Neural Engine
# )
# tokenizer.pad_token = tokenizer.eos_token

# # MLX training setup
# def train():
#     # Convert model to MLX format
#     mx_model = mx.eval(model)
    
#     # Training loop
#     for batch in dataset:
#         inputs = tokenizer(batch["text"], return_tensors="np", padding=True)
#         outputs = mx_model(**inputs)
#         loss = outputs.loss
#         loss.backward()
#         # Update weights using MLX optimizers

# # Save adapted model
# mx.save("tal-finetuned-mlx", mx_model.parameters())
import json
from datasets import Dataset, DatasetDict
import random

SYSTEM_PROMPT = "You are an expert assistant for TAL LED converters. Always provide accurate technical specifications from official documentation."

def format_conversations(input_file):
    with open(input_file) as f:
        tech_data = json.load(f)

    conversations = []
    
    for product_id, specs in tech_data.items():
        # Base context
        context = f"Product: {specs['CONVERTER DESCRIPTION:']}\n" \
                  f"Input Voltage: {specs['NOM. INPUT VOLTAGE (V)']}\n" \
                  f"Output Voltage: {specs['OUTPUT VOLTAGE (V)']}V\n" \
                  f"Dimming: {specs['DIMMABILITY']}\n" \
                  f"IP Rating: IP{specs['IP']}"

        # Multi-turn conversation template
        conversations.append({
            "text": f"<s>[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n" \
                    f"What are the key specifications for {product_id}? [/INST] " \
                    f"{context}</s>"
        })

        # Parameter variations
        voltage_questions = [
            f"What's the output voltage for {product_id}?",
            f"Can you confirm the Vout for {specs['CONVERTER DESCRIPTION:']}?",
            f"Voltage specification for {product_id}:"
        ]
        
        for question in voltage_questions:
            conversations.append({
                "text": f"<s>[INST] {question} [/INST] " \
                        f"Output voltage: {specs['OUTPUT VOLTAGE (V)']}V</s>"
            })

        # Compatibility analysis
        if 'lamps' in specs:
            for lamp_type, details in specs['lamps'].items():
                conversations.append({
                    "text": f"<s>[INST] What's the max quantity of {lamp_type} " \
                            f"supported by {product_id}? [/INST] " \
                            f"Maximum supported: {details['max']} units</s>"
                })

    # Create train/validation split
    random.shuffle(conversations)
    split_idx = int(0.8 * len(conversations))
    
    return DatasetDict({
        "train": Dataset.from_list(conversations[:split_idx]),
        "validation": Dataset.from_list(conversations[split_idx:])
    })

if __name__ == "__main__":
    dataset = format_conversations("/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json")
    dataset.save_to_disk("formatted_data")
    dataset["train"].to_json("train_data.jsonl", orient="records", lines=True)
    dataset["validation"].to_json("val_data.jsonl", orient="records", lines=True)
