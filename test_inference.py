from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

model_name = "mistralai/Mistral-7B-Instruct-v0.3"
lora_path = "./mistral_sql_lora"  # cartella con i checkpoint LoRA

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="float16"
)

tok = AutoTokenizer.from_pretrained(model_name)
base = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    quantization_config=bnb_config
)
model = PeftModel.from_pretrained(base, lora_path)
model = model.merge_and_unload()  # opzionale: fonde LoRA nel backbone

prompt = "Elenca i clienti che non hanno ordini."
inputs = tok(prompt, return_tensors="pt").to("cuda")
out = model.generate(**inputs, max_new_tokens=128)
print(tok.decode(out[0], skip_special_tokens=True))