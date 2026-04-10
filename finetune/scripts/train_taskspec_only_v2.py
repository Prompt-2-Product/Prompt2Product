import os
import torch
import matplotlib.pyplot as plt
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig
from trl import SFTTrainer, SFTConfig

# Paths - Updated to v2 to prevent overriding
BASE_MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "fine_tune_dataset", "taskspec_only")
TRAIN_FILE = os.path.join(DATA_DIR, "train.jsonl")
VAL_FILE = os.path.join(DATA_DIR, "val.jsonl")
# Changed directory name here
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "finetune", "outputs", "qwen_taskspec_only_lora_v2")
LOGGING_DIR = os.path.join(PROJECT_ROOT, "finetune", "logs")

MAX_LENGTH = 1024

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Improved Tokenizer & Template Handling
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Official ChatML template for Qwen2.5
    def format_chat_template(example):
        return {"text": tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)}

    dataset = load_dataset("json", data_files={"train": TRAIN_FILE, "validation": VAL_FILE})
    dataset = dataset.map(format_chat_template)

    # 2. Model Configuration
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, 
        bnb_4bit_quant_type="nf4", 
        bnb_4bit_compute_dtype=torch.float16, 
        bnb_4bit_use_double_quant=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, 
        quantization_config=bnb_config, 
        device_map="auto", 
        trust_remote_code=True
    )
    model.gradient_checkpointing_enable()
    model.config.use_cache = False

    # 3. Targeted LoRA (Added MLP layers for better reasoning preservation)
    peft_config = LoraConfig(
        r=8, 
        lora_alpha=16, 
        lora_dropout=0.1, 
        bias="none", 
        task_type="CAUSAL_LM", 
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj"] 
    )

    # 4. Refined Training Config for 50 examples
    sft_config = SFTConfig(
        output_dir=OUTPUT_DIR, 
        num_train_epochs=8,               # Prevent overfitting on tiny data
        per_device_train_batch_size=1, 
        gradient_accumulation_steps=4,
        eval_strategy="steps", 
        eval_steps=10,                    
        save_strategy="steps", 
        save_steps=10,
        logging_steps=5,
        learning_rate=2e-5,               
        weight_decay=0.05,                
        warmup_steps=5, 
        lr_scheduler_type="cosine",
        report_to="none", 
        load_best_model_at_end=True,      
        metric_for_best_model="eval_loss",
        optim="paged_adamw_8bit", 
        dataset_text_field="text", 
        max_length=MAX_LENGTH,
        packing=False                     
    )

    trainer = SFTTrainer(
        model=model, 
        args=sft_config, 
        train_dataset=dataset["train"], 
        eval_dataset=dataset["validation"], 
        processing_class=tokenizer, 
        peft_config=peft_config
    )
    
    trainer.train()
    
    # --- Plotting ---
    log_history = trainer.state.log_history
    train_loss = [x['loss'] for x in log_history if 'loss' in x]
    train_steps = [x['step'] for x in log_history if 'loss' in x]
    eval_loss = [x['eval_loss'] for x in log_history if 'eval_loss' in x]
    eval_steps = [x['step'] for x in log_history if 'eval_loss' in x]

    plt.figure(figsize=(10, 6))
    plt.plot(train_steps, train_loss, label="Training Loss")
    if eval_loss:
        plt.plot(eval_steps, eval_loss, label="Evaluation Loss", marker='o')
    plt.title(f"Fine-tuning Loss v2: {BASE_MODEL}")
    plt.xlabel("Step")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)
    
    os.makedirs(LOGGING_DIR, exist_ok=True)
    # Changed plot filename here
    plot_path = os.path.join(LOGGING_DIR, "taskspec_optimized_v2_loss.png")
    plt.savefig(plot_path)
    print(f"v2 Loss plot saved to: {plot_path}")
    
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__": 
    main()