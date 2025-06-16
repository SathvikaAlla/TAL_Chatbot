# import json
# from mlx_lm.utils import convert_ollama_to_mlx

# def convert_chat_data(input_path, output_path):
#     with open(input_path) as f:
#         data = json.load(f)
    
#     mlx_data = []
#     for item in data:
#         messages = [{"role": m["role"], "content": m["content"]} for m in item["messages"]]
#         mlx_data.append({"messages": messages})
    
#     convert_ollama_to_mlx(mlx_data, output_path)

# convert_chat_data("OllamaChatbot/formatted_data/train_data.jsonl", "mlx_train_data.jsonl")
import json
from pathlib import Path

def convert_to_mlx_format(input_path, output_dir):
    # Load your formatted data
    with open(input_path) as f:
        ollama_data = [json.loads(line) for line in f]
    
    # Convert to MLX-compatible format
    mlx_data = []
    for item in ollama_data:
        if "messages" in item:
            # Multi-turn conversation format
            mlx_data.append({
                "messages": [
                    {"role": "user", "content": item["messages"][0]["content"]},
                    {"role": "assistant", "content": item["messages"][1]["content"]}
                ]
            })
        elif "text" in item:
            # Single-turn instruction format
            mlx_data.append({"text": item["text"]})
    
    # Save as JSONL
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "train_data.jsonl", "w") as f:
        for item in mlx_data:
            f.write(json.dumps(item) + "\n")

if __name__ == "__main__":
    convert_to_mlx_format(
        input_path="/Users/alessiacolumban/TAL_Chatbot/OllamaChatbot/formatted_data/train_data.jsonl",
        output_dir="mlx_data"
    )
    print("Data converted successfully to MLX format in 'mlx_data' directory")
