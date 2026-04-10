import os
import re
import json
import torch
import ast
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# =========================
# Config
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASE_MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
ADAPTER_PATH = os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_only_lora_v3")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "Code spec Generator")
PROMPTS_FILE = os.path.join(os.path.dirname(__file__), "prompts.txt")

def extract_first_json(text: str):
    start = text.find("{")
    if start == -1: return None
    brace_count = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == "{": brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0: return text[start:i + 1]
    return None

def clean_generated_text(text: str) -> str:
    stop_markers = ["<|user|>", "<|system|>", "<|assistant|><|endoftext|>", "<|endoftext|>", "Human:", "Assistant:"]
    cleaned = text
    cut_positions = []
    for marker in stop_markers:
        pos = cleaned.find(marker)
        if pos != -1: cut_positions.append(pos)
    if cut_positions: cleaned = cleaned[:min(cut_positions)]
    return cleaned.strip()

def load_prompts(filepath):
    print(f"Loading prompts from {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    # Clean up potential trailing characters after the last dict entry
    if content.endswith(".") : content = content[:-1].strip()
    if content.endswith(","): content = content[:-1].strip()
    
    # Wrap in braces to make it a valid Python dictionary literal
    dict_str = "{" + content + "}"
    try:
        return ast.literal_eval(dict_str)
    except Exception as e:
        print(f"Error parsing prompts.txt: {e}")
        # Fallback: very simple regex attempt if ast fails
        # (Though with the user's current content, ast.literal_eval should work)
        raise

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    prompts = load_prompts(PROMPTS_FILE)
    
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None: tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    print("Loading model in 4-bit...")
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

    print(f"Loading adapter from {ADAPTER_PATH}...")
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    model.eval()

    for p_name, p_text in prompts.items():
        print(f"\n--- Generating for: {p_name} ---")
        
        inputs = tokenizer(p_text, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        input_length = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024, # Using the 1024 token limit we found necessary
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=True,
            )

        generated_ids = outputs[0][input_length:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=False)
        generated_text = clean_generated_text(generated_text)
        extracted_json = extract_first_json(generated_text)

        output_content = []
        output_content.append(f"Prompt Category: {p_name}")
        output_content.append(f"Model: {ADAPTER_PATH}")
        output_content.append("\n===== RAW GENERATED TEXT =====\n")
        output_content.append(generated_text if generated_text else "[EMPTY OUTPUT]")

        if extracted_json:
            output_content.append("\n===== EXTRACTED JSON =====\n")
            output_content.append(extracted_json)
            try:
                parsed = json.loads(extracted_json)
                output_content.append("\n===== JSON VALIDITY =====\n")
                output_content.append("Valid JSON")
                output_content.append("\n===== PRETTY JSON =====\n")
                output_content.append(json.dumps(parsed, indent=2, ensure_ascii=False))
            except json.JSONDecodeError as e:
                output_content.append("\n===== JSON VALIDITY =====\n")
                output_content.append("Invalid JSON")
                output_content.append(f"JSON parse error: {e}")
        else:
            output_content.append("\nNo JSON object could be extracted")

        full_output = "\n".join(output_content)
        
        output_filename = os.path.join(OUTPUT_DIR, f"v3_{p_name}.txt")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(full_output)
        print(f"Results saved to: {output_filename}")

if __name__ == "__main__":
    main()
