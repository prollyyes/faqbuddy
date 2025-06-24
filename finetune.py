import torch
import multiprocessing as mp
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
from datasets import load_dataset

MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.3"
DATASET_PATH = "sql_dataset_dedup.jsonl"  # punta al tuo dataset JSONL


def main():
    """Fine‑tuning QLoRA su Windows con protezione multiprocessing."""

    # 1️⃣ Quantizzazione 4‑bit
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )

    # 2️⃣ Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # 3️⃣ Modello quantizzato
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",
        quantization_config=bnb_config,
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )

    # 4️⃣ Prepara LoRA
    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.1,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)

    # 5️⃣ Dataset
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")

    def preprocess(example):
        text = f"{example['input']}\n### Response:\n{example['output']}"
        toks = tokenizer(text, truncation=True, max_length=512, padding=False)
        return {
            "input_ids": toks["input_ids"],
            "attention_mask": toks["attention_mask"],
            "labels": toks["input_ids"].copy(),
        }

    tokenized_dataset = dataset.map(
        preprocess,
        remove_columns=dataset.column_names,  # elimina le colonne stringa
        num_proc=1,  # evita subprocess extra su Windows
    )

    # 6️⃣ Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # 7️⃣ TrainingArguments
    training_args = TrainingArguments(
        output_dir="./mistral_sql_lora",
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        logging_steps=10,
        save_strategy="epoch",
        fp16=True,
        remove_unused_columns=True,
        dataloader_num_workers=0,  # nessun worker extra
        optim="paged_adamw_8bit",
        report_to="none",
    )

    # 8️⃣ Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    trainer.train()


if __name__ == "__main__":
    # Windows usa "spawn" di default; set explicit e proteggi l'entry‑point
    mp.set_start_method("spawn", force=True)
    main()
