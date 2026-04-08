import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# =========================
# Config
# =========================
BASE_MODEL = "Qwen/Qwen2.5-Coder-3B"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ADAPTER_PATH = os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_repair_lora")

USE_ADAPTER = True   # True = test fine-tuned model, False = test base model only

PROMPT = """<|system|>
Generate valid TaskSpec JSON only. Do not output markdown, comments, or explanation.
<|user|>
Build an AI-powered fitness tracking application that integrates with smartwatches to track activities, provides personalized workout plans based on biometric data, and allows users to participate in community social challenges with leaderboards.
<|assistant|>
"""

def main():
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading base model...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float32,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )

    if USE_ADAPTER:
        print("Loading adapter...")
        model = PeftModel.from_pretrained(model, ADAPTER_PATH)

    model.eval()

    inputs = tokenizer(PROMPT, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=400,
            do_sample=False,
            temperature=1.0,
            top_p=1.0,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    result = tokenizer.decode(outputs[0], skip_special_tokens=False)
    print("\n===== MODEL OUTPUT =====\n")
    print(result)


if __name__ == "__main__":
    main()