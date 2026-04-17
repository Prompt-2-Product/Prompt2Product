import os

# 1. SET HARD FLAGS BEFORE ANY IMPORTS
os.environ["UNSLOTH_DISABLE_AUTO_CHECK"] = "1"
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
import unsloth
import torch
import unsloth_zoo.tokenizer_utils

# 2. MONKEY PATCH TO SILENCE UNTRAINED TOKEN ERRORS
def bypassed_check(*args, **kwargs): return None
unsloth_zoo.tokenizer_utils.fix_untrained_tokens = bypassed_check

from unsloth import FastLanguageModel, get_chat_template, is_bfloat16_supported
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments, EarlyStoppingCallback, TrainerCallback
import matplotlib.pyplot as plt
import json

# 3. CONFIGURATION (Memory-safe for 12GB VRAM)
max_seq_length = 8192
# Using Instruct variant — ChatML tokens are already trained, no need for
# modules_to_save on embed_tokens/lm_head, saves 4-6GB VRAM
model_name = "Qwen/Qwen2.5-Coder-7B-Instruct"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    load_in_4bit = True,
    dtype = None,  # unsloth auto-selects bfloat16/float16
)

# 4. LORA SETUP
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    lora_alpha = 32,
    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
        # embed_tokens & lm_head NOT needed — Instruct model already has
        # trained ChatML embeddings. Adding them here costs 4-6GB VRAM for no gain.
    ],
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
)

# 5. DATASET & TEMPLATE
tokenizer = get_chat_template(tokenizer, chat_template = "qwen-2.5")
dataset = load_dataset("json", data_files={"train": "Code-finetuning-dataset.json"}, split="train")

def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
    tokenized = tokenizer(texts, truncation=True, max_length=max_seq_length, padding=False)
    return {
        "input_ids": tokenized["input_ids"],
        "attention_mask": tokenized["attention_mask"],
        "labels": tokenized["input_ids"].copy(),
    }

dataset = dataset.map(formatting_prompts_func, batched=True, remove_columns=dataset.column_names)
dataset = dataset.train_test_split(test_size=0.1)

# 6. LOSS TRACKING CALLBACK
class LossTrackerCallback(TrainerCallback):
    def __init__(self):
        self.train_losses = []   # (step, loss)
        self.eval_losses  = []   # (step, loss)

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return
        step = state.global_step
        if "loss" in logs:
            self.train_losses.append((step, logs["loss"]))
        if "eval_loss" in logs:
            self.eval_losses.append((step, logs["eval_loss"]))

    def plot_and_save(self, output_path="training_loss_curve.png"):
        if not self.train_losses:
            print("No loss data to plot.")
            return

        train_steps, train_vals = zip(*self.train_losses)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(train_steps, train_vals, label="Train Loss", color="#4C72B0", linewidth=1.5)

        if self.eval_losses:
            eval_steps, eval_vals = zip(*self.eval_losses)
            ax.plot(eval_steps, eval_vals, label="Eval Loss", color="#DD8452",
                    linewidth=2, marker="o", markersize=5)

        ax.set_xlabel("Step", fontsize=12)
        ax.set_ylabel("Loss", fontsize=12)
        ax.set_title("GIKI-Coder Fine-Tuning Loss (Qwen2.5-Coder-7B-Instruct)", fontsize=13)
        ax.legend(fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        print(f"--- Loss curve saved to '{output_path}' ---")

        # Also save raw numbers as JSON for later inspection
        json_path = output_path.replace(".png", ".json")
        with open(json_path, "w") as f:
            json.dump({"train": self.train_losses, "eval": self.eval_losses}, f, indent=2)
        print(f"--- Loss data saved to '{json_path}' ---")

loss_tracker = LossTrackerCallback()

# 7. SFT CONFIGURATION (Tuned for 12GB VRAM)
training_args = TrainingArguments(
    per_device_train_batch_size = 1,
    gradient_accumulation_steps = 8,
    warmup_steps = 10,
    max_steps = 100,
    learning_rate = 5e-5,
    fp16 = not is_bfloat16_supported(),
    bf16 = is_bfloat16_supported(),
    logging_steps = 1,
    optim = "adamw_8bit",
    weight_decay = 0.05,
    lr_scheduler_type = "cosine",
    seed = 3407,
    eval_strategy = "steps",
    eval_steps = 10,
    save_strategy = "steps",
    save_steps = 10,
    load_best_model_at_end = True,
    metric_for_best_model = "eval_loss",
    greater_is_better = False,
    output_dir = "outputs",
    report_to = "none",
    gradient_checkpointing = True,
    dataloader_pin_memory = False,
    dataloader_num_workers = 0,
)

# 8. TRAINER
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset["train"],
    eval_dataset = dataset["test"],
    dataset_text_field = None,
    max_seq_length = max_seq_length,
    args = training_args,
    callbacks = [
        EarlyStoppingCallback(early_stopping_patience=3),
        loss_tracker,
    ],
)

# 9. EXECUTE TRAINING
print("--- Starting GIKI-Coder v2.5 (Qwen2.5-Coder-7B-Instruct) ---")
trainer.train()

# 10. PLOT LOSS CURVE
loss_tracker.plot_and_save("training_loss_curve.png")

# 11. SAVE MODEL
model.save_pretrained("GIKI_Coder_Final_v2_5")
tokenizer.save_pretrained("GIKI_Coder_Final_v2_5")
print("--- Success! Model saved as 'GIKI_Coder_Final_v2_5' ---")