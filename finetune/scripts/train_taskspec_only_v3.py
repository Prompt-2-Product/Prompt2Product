import os
import torch
import matplotlib.pyplot as plt
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    EarlyStoppingCallback, # Added for v3
)
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig

# Paths - Updated to v3
BASE_MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "fine_tune_dataset", "taskspec_only")
TRAIN_FILE = os.path.join(DATA_DIR, "train.jsonl")
VAL_FILE = os.path.join(DATA_DIR, "val.jsonl")
# v3 Output directory
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_only_lora_v3")
LOGGING_DIR = os.path.join(PROJECT_ROOT, "finetune", "logs")

MAX_LENGTH = 1024

def format_example(example):
    messages = example["messages"]
    text_parts = []
    for msg in messages:
        role = msg["role"].strip().lower()
        content = msg["content"].strip()
        if role == "system": text_parts.append(f"<|system|>\n{content}")
        elif role == "user": text_parts.append(f"<|user|>\n{content}")
        elif role == "assistant": text_parts.append(f"<|assistant|>\n{content}")
    return {"text": "\n".join(text_parts)}

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dataset = load_dataset("json", data_files={"train": TRAIN_FILE, "validation": VAL_FILE})
    dataset["train"] = dataset["train"].map(format_example)
    dataset["validation"] = dataset["validation"].map(format_example)

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None: tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, 
        bnb_4bit_quant_type="nf4", 
        bnb_4bit_compute_dtype=torch.float32, 
        bnb_4bit_use_double_quant=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, 
        quantization_config=bnb_config, 
        device_map="auto", 
        low_cpu_mem_usage=True, 
        trust_remote_code=True
    )
    model.gradient_checkpointing_enable()
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=8, 
        lora_alpha=16, 
        lora_dropout=0.05, 
        bias="none", 
        task_type="CAUSAL_LM", 
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
    )

    sft_config = SFTConfig(
        output_dir=OUTPUT_DIR, 
        num_train_epochs=30, 
        per_device_train_batch_size=1, 
        gradient_accumulation_steps=4,
        eval_strategy="steps", 
        eval_steps=10,             # Check every 10 steps for early stopping
        save_strategy="steps", 
        save_steps=10,             # Matches eval_steps
        logging_steps=5,
        learning_rate=1e-4, 
        weight_decay=0.01, 
        warmup_steps=10, 
        lr_scheduler_type="cosine",
        report_to="none", 
        save_total_limit=2, 
        load_best_model_at_end=True, # Best checkpoint will be loaded automatically
        metric_for_best_model="eval_loss",
        optim="paged_adamw_8bit", 
        dataset_text_field="text", 
        max_length=MAX_LENGTH
    )

    # Added EarlyStoppingCallback with a patience of 3 evaluation cycles
    trainer = SFTTrainer(
        model=model, 
        args=sft_config, 
        train_dataset=dataset["train"], 
        eval_dataset=dataset["validation"], 
        processing_class=tokenizer, 
        peft_config=peft_config,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)] 
    )

    trainer.train()
    
    # --- Plotting v3 ---
    log_history = trainer.state.log_history
    train_loss = [x['loss'] for x in log_history if 'loss' in x]
    train_steps = [x['step'] for x in log_history if 'loss' in x]
    eval_loss = [x['eval_loss'] for x in log_history if 'eval_loss' in x]
    eval_steps = [x['step'] for x in log_history if 'eval_loss' in x]

    plt.figure(figsize=(10, 6))
    plt.plot(train_steps, train_loss, label="Training Loss")
    if eval_loss:
        plt.plot(eval_steps, eval_loss, label="Evaluation Loss", marker='o')
    plt.title("Fine-tuning Loss v3 (with Early Stopping)")
    plt.xlabel("Step")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)
    
    os.makedirs(LOGGING_DIR, exist_ok=True)
    # Saved as v3
    plot_path = os.path.join(LOGGING_DIR, "taskspec_v3_early_stopping_loss.png")
    plt.savefig(plot_path)
    print(f"v3 results saved to: {OUTPUT_DIR}")
    print(f"v3 Loss plot saved to: {plot_path}")
    
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__": main()