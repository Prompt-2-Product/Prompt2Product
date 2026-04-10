import os
import re
import json
import torch
import argparse
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# =========================
# Config & Prompts
# =========================
PROMPTS = {
    "fitness": """<|system|>
Generate valid TaskSpec JSON only. Do not output markdown, comments, or explanation.
<|user|>
Build an AI-powered fitness tracking application that integrates with smartwatches to track activities, provides personalized workout plans based on biometric data, and allows users to participate in community social challenges with leaderboards.
<|assistant|>
""",
    "ecommerce": """<|system|>
Generate valid TaskSpec JSON only. Do not output markdown, comments, or explanation.
<|user|>
Build a multi-vendor e-commerce platform where sellers can manage inventory and shipping, customers can browse, review products, and place orders with real-time tracking, and admins can handle disputes and refunds.
<|assistant|>
""",
    "library": """<|system|>
Generate valid TaskSpec JSON only. Do not output markdown, comments, or explanation.
<|user|>
Build a library portal where students can search books, issue books, and view due dates.
<|assistant|>
"""
}

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

CONFIGS = {
    "base": {
        "base_model": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "adapter_path": None
    },
    "old": {
        "base_model": "Qwen/Qwen2.5-Coder-3B",
        "adapter_path": os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_repair_lora")
    },
    "v2": {
        "base_model": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "adapter_path": os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_repair_lora_v2")
    },
    "taskspec_only": {
        "base_model": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "adapter_path": os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_only_lora")
    },
    "taskspec_only_v2": {
        "base_model": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "adapter_path": os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_only_lora_v2")
    },
    "taskspec_only_v3": {
        "base_model": "Qwen/Qwen2.5-Coder-3B-Instruct",
        "adapter_path": os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_only_lora_v3")
    }
}


def extract_first_json(text: str):
    """
    Try to extract the first full JSON object from generated text.
    Returns the JSON string if found, else None.
    """
    start = text.find("{")
    if start == -1:
        return None

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
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i + 1]

    return None


def clean_generated_text(text: str) -> str:
    """
    Remove obvious extra chat continuation markers after generation.
    """
    stop_markers = [
        "<|user|>",
        "<|system|>",
        "<|assistant|><|endoftext|>",
        "<|endoftext|>",
        "Human:",
        "Assistant:"
    ]

    cleaned = text
    cut_positions = []

    for marker in stop_markers:
        pos = cleaned.find(marker)
        if pos != -1:
            cut_positions.append(pos)

    if cut_positions:
        cleaned = cleaned[:min(cut_positions)]

    return cleaned.strip()


def main():
    parser = argparse.ArgumentParser(description="Test TaskSpec Repair Adapters")
    parser.add_argument("--model_type", type=str, choices=["base", "old", "v2", "taskspec_only", "taskspec_only_v2", "taskspec_only_v3"], required=True, help="Model configuration to test")
    parser.add_argument("--prompt_type", type=str, choices=["fitness", "ecommerce", "library"], help="Prompt to test (required if not using --all_prompts)")
    parser.add_argument("--all_prompts", action="store_true", help="Test all prompts in the PROMPTS dictionary")
    parser.add_argument("--output_dir", type=str, help="Directory to save output files")
    parser.add_argument("--max_new_tokens", type=int, default=1024, help="Maximum new tokens to generate")
    args = parser.parse_args()

    if not args.all_prompts and not args.prompt_type:
        parser.error("--prompt_type is required unless --all_prompts is specified")

    config = CONFIGS[args.model_type]
    
    prompts_to_test = PROMPTS if args.all_prompts else {args.prompt_type: PROMPTS[args.prompt_type]}

    print(f"Testing Model: {args.model_type}")
    print(f"Base Model: {config['base_model']}")
    print(f"Adapter: {config['adapter_path'] if config['adapter_path'] else 'None'}")
    print(f"Prompt: {args.prompt_type}\n")

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config["base_model"], trust_remote_code=True)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "left"

    print("Loading model in 4-bit...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float32,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        config["base_model"],
        quantization_config=bnb_config,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )

    if config["adapter_path"]:
        print(f"Loading adapter: {config['adapter_path']}")
        model = PeftModel.from_pretrained(model, config["adapter_path"])

    model.eval()

    for p_name, p_text in prompts_to_test.items():
        print(f"\n--- Testing Prompt: {p_name} ---")
        
        inputs = tokenizer(p_text, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        input_length = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                top_k=None,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=True,
            )

        generated_ids = outputs[0][input_length:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=False)
        generated_text = clean_generated_text(generated_text)

        extracted_json = extract_first_json(generated_text)

        output_content = []
        output_content.append(f"Testing Model: {args.model_type}")
        output_content.append(f"Base Model: {config['base_model']}")
        output_content.append(f"Adapter: {config['adapter_path'] if config['adapter_path'] else 'None'}")
        output_content.append(f"Prompt: {p_name}\n")
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
        print(full_output)

        if args.output_dir:
            os.makedirs(args.output_dir, exist_ok=True)
            output_filename = os.path.join(args.output_dir, f"{args.model_type}_{p_name}.txt")
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(full_output)
            print(f"Results saved to: {output_filename}")


if __name__ == "__main__":
    main()