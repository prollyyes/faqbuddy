from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, BitsAndBytesConfig
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
import torch

MODEL_NAME = "mistralai/Mistral-7B-v0.1"
DATASET_PATH = "sql_dataset_dedup.jsonl"

# 1. Dataset
dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

# 2. Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

def tokenize(example):
    prompt = f"### Istruzione:\n{example['instruction']}\n\n### Input:\n{example['input']}\n\n### Risposta:\n{example['output']}"
    tokens = tokenizer(prompt, truncation=True, padding="max_length", max_length=512)
    tokens["labels"] = tokens["input_ids"].copy()
    return tokens

tokenized = dataset.map(tokenize)

# 3. Load model with device_map='auto'
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",  # lascia gestire a HF Accelerate (usa anche MPS)
    torch_dtype=torch.float16,  # usa precisione più leggera
    trust_remote_code=True
)

# 4. PEFT
model = prepare_model_for_kbit_training(model)

peft_config = LoraConfig(
    r=8,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, peft_config)

# 5. TrainingArguments (ATTENZIONE: fp16 va disabilitato su MPS)
training_args = TrainingArguments(
    output_dir="./mistral_sql_lora",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    logging_steps=10,
    num_train_epochs=3,
    learning_rate=2e-4,
    save_strategy="epoch",
    remove_unused_columns=False,
    bf16=False,
    fp16=False  # ⚠️ SU MPS NON VA ABILITATO
)

# 6. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    tokenizer=tokenizer
)

trainer.train()
