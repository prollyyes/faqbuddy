from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1", device_map="auto", load_in_4bit=True)
model = PeftModel.from_pretrained(model, "./mistral_sql_lora")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")
