from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset

# Load your dataset
dataset = load_dataset("json", data_files="/Users/alessiacolumban/TAL_Chatbot/ChatbotHugg/chatbot_data.json", split="train")

# Use GPT-2 Small
model_id = "gpt2"
model = AutoModelForCausalLM.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token

# Tokenization function for prompt-response pairs
def tokenize_function(example):
    text = f"User: {example['prompt']}\nAssistant: {example['response']}{tokenizer.eos_token}"
    tokenized = tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=256,  # Adjust max_length as needed
    )
    tokenized["labels"] = tokenized["input_ids"]
    return tokenized

# Tokenize the dataset
tokenized_dataset = dataset.map(tokenize_function, batched=False)

# Training arguments
training_args = TrainingArguments(
    output_dir="./results",
    per_device_train_batch_size=2,
    num_train_epochs=30,
    save_steps=1000,
    logging_dir="./logs",
    logging_steps=100,
    fp16=False,  # Set to True if your GPU supports mixed precision
    save_total_limit=2,
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# Train the model
trainer.train()

# Save the model and tokenizer
trainer.save_model("./results")
tokenizer.save_pretrained("./results")