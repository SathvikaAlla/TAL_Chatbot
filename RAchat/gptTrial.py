from openai import OpenAI
import json

# Initialize client with your API key
client = OpenAI(api_key="your-api-key")  # Replace with your actual OpenAI API key

# Step 1: Upload your training data
def upload_file(file_path):
    with open(file_path, "rb") as f:
        file = client.files.create(
            file=f,
            purpose="fine-tune"
        )
    return file.id

file_id = upload_file("your_data.jsonl")
print(f"File uploaded. File ID: {file_id}")

# Step 2: Start the fine-tuning job
def start_fine_tuning(file_id, model="gpt-3.5-turbo"):
    fine_tuning_job = client.fine_tuning.jobs.create(
        training_file=file_id,
        model=model
    )
    return fine_tuning_job.id

job_id = start_fine_tuning(file_id)
print(f"Fine-tuning job started. Job ID: {job_id}")

# Step 3: Monitor the job status
def check_job_status(job_id):
    job = client.fine_tuning.jobs.retrieve(job_id)
    return job.status

status = check_job_status(job_id)
print(f"Current job status: {status}")

# (Optional) Step 4: Wait for job to complete
import time

print("Waiting for fine-tuning to complete...")
while True:
    status = check_job_status(job_id)
    if status == "succeeded":
        print("Fine-tuning completed successfully!")
        # Retrieve the fine-tuned model name
        job = client.fine_tuning.jobs.retrieve(job_id)
        fine_tuned_model = job.fine_tuned_model
        print(f"Fine-tuned model name: {fine_tuned_model}")
        break
    elif status in ["failed", "cancelled"]:
        print(f"Fine-tuning job {status}.")
        break
    else:
        print(f"Status: {status}. Waiting...")
        time.sleep(60)  # Check every minute

# Step 5: Test your fine-tuned model (if job succeeded)
if status == "succeeded":
    print("\nTesting your fine-tuned model...\n")
    # Example prompt for chat completion
    response = client.chat.completions.create(
        model=fine_tuned_model,
        messages=[
            {"role": "user", "content": "How do I reset my password?"}
        ]
    )
    print("Assistant:", response.choices[0].message.content)
