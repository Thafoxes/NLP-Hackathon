import os

from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# Choose device
device = "cuda" if torch.cuda.is_available() else "cpu"

# Hugging Face API key and model
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")

huggingface_model = 'malaysia-ai/Malaysian-Llama-3.2-3B-Instruct'

# Required model files
required_files = [
    "special_tokens_map.json",
    "generation_config.json",
    "tokenizer_config.json",
    "model.safetensors",
    "eval_results.json",
    "tokenizer.model",
    "tokenizer.json",
    "config.json"
]

# Download model files
print("🔄 Downloading model files...")
for filename in required_files:
    download_location = hf_hub_download(
        repo_id=huggingface_model,
        filename=filename,
        token=HUGGING_FACE_API_KEY
    )
    print(f"✅ Downloaded: {filename}")

# Load model and tokenizer
print("🚀 Loading model and tokenizer...")
model = AutoModelForCausalLM.from_pretrained(huggingface_model, trust_remote_code=True).to(device)
tokenizer = AutoTokenizer.from_pretrained(huggingface_model)

# Create text generation pipeline
text_generation_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=0 if device == "cuda" else -1,
    max_length=1000
)

# Prompt user for input
while True:
    user_input = input("\n📝 Enter any message (or type 'exit' to quit): ")
    if user_input.lower() == 'exit':
        print("👋 Goodbye!")
        break

    response = text_generation_pipeline(user_input)
    print(response)
    print("\n🤖 Response:")
    print(response[0]['generated_text'])
