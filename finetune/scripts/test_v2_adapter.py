import json
import torch
import random
from unsloth import FastLanguageModel, get_chat_template
from transformers import TextStreamer

# ─── 1. CONFIG ────────────────────────────────────────────────────────────
model_name = "GIKI_Coder_Final_v2_5"
max_seq_length = 8192

# ─── 2. LOAD ──────────────────────────────────────────────────────────────
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    max_seq_length=max_seq_length,
    load_in_4bit=True,
)
tokenizer = get_chat_template(tokenizer, chat_template="qwen-2.5")
FastLanguageModel.for_inference(model)

# ─── 3. DATASET ───────────────────────────────────────────────────────────
dataset_file = "Code-finetuning-dataset.json"
try:
    with open(dataset_file, "r") as f:
        data = json.load(f)
    random_example = random.choice(data)
    user_prompt = random_example["messages"][0]["content"]
    print(f"Selected Task: {user_prompt[:150]}...\n")
except FileNotFoundError:
    user_prompt = "Generate a complete production-ready web app for a Personal Finance Tracker."

# ─── 4. TOKENIZE ──────────────────────────────────────────────────────────
messages = [{"role": "user", "content": user_prompt}]

# Build input_ids AND attention_mask together — fixes the mask warning
encoded = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt",
    return_dict=True,          # ← returns both input_ids AND attention_mask
)
input_ids      = encoded["input_ids"].to("cuda")
attention_mask = encoded["attention_mask"].to("cuda")

input_len = input_ids.shape[1]
max_new_tokens = min(3500, max_seq_length - input_len - 10)

print(f"Input tokens:      {input_len}")
print(f"Max seq length:    {max_seq_length}")
print(f"New tokens budget: {max_new_tokens}")

if max_new_tokens <= 0:
    print("❌ Prompt exceeds max_seq_length. Choose a shorter example.")
    exit(1)

# ─── 5. GENERATE ──────────────────────────────────────────────────────────
streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

print("\n--- GENERATING (streaming) ---")
with torch.no_grad():
    outputs = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,  # ← fixes the attention mask warning
        max_new_tokens=max_new_tokens,
        # FIX: do NOT pass max_length — it conflicts with Unsloth's internal
        # max_length=32768 and causes the "Both max_new_tokens and max_length
        # seem to have been set" warning. max_new_tokens alone is enough.
        use_cache=True,
        do_sample=True,
        temperature=0.2,
        top_p=0.9,
        repetition_penalty=1.15,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        streamer=streamer,
    )

# ─── 6. DECODE ────────────────────────────────────────────────────────────
response = tokenizer.batch_decode(outputs, skip_special_tokens=False)[0]
clean_output = response.split("<|im_start|>assistant")[-1].split("<|im_end|>")[0].strip()

output_filename = "giki_coder_test_output.json"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(clean_output)

print(f"\n\nOutput length: {len(clean_output)} chars")
print(f"Saved to: {output_filename}")

# ─── 7. VALIDATE ──────────────────────────────────────────────────────────
try:
    parsed = json.loads(clean_output)
    print("\n✅ Valid JSON.")

    files = parsed.get("files", [])
    manifest = parsed.get("manifest", [])
    print(f"✅ Files generated: {len(files)}")
    print(f"✅ Manifest entries: {len(manifest)}")

    # Check manifest matches files
    file_paths = [f["path"] for f in files]
    missing_from_files = [m for m in manifest if m not in file_paths]
    if missing_from_files:
        print(f"⚠️  In manifest but not in files: {missing_from_files}")
    else:
        print("✅ All manifest entries have corresponding files.")

    # Check required files exist
    for required in ["requirements.txt", "main.py", "templates/base.html"]:
        status = "✅" if required in file_paths else "❌"
        print(f"{status} {required}")

    # Check no banned patterns made it into output
    full_text = json.dumps(parsed)
    banned = ["google.com/search", "bg-slate-", "bg-stone-", "Inter', sans", "Space Grotesk", "[cite"]
    for b in banned:
        if b in full_text:
            print(f"⚠️  Banned pattern found: '{b}'")

except json.JSONDecodeError as e:
    # Find exactly where it broke
    print(f"\n⚠️  JSON truncated at char ~{e.pos} / {len(clean_output)}")
    pct = round(e.pos / len(clean_output) * 100)
    print(f"   Completed ~{pct}% of output before cut-off.")
    print(f"   Error: {e.msg}")

    # Try to count how many files were completed
    completed_files = clean_output.count('"path":')
    print(f"   Files started: ~{completed_files}")
    print(f"\n   If budget was hit: raise max_new_tokens or pick a shorter TaskSpec.")
    print(f"   If EOS hit early: lower repetition_penalty to 1.05.")