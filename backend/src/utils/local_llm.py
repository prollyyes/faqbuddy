import os
from llama_cpp import Llama

mistral_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'mistral-7b-instruct-v0.2.Q4_K_M.gguf'))
gemma_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'gemma-3-4b-it-Q4_1.gguf'))

llm_mistral = Llama(
    model_path=mistral_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=-1,
    verbose=True
)

llm_gemma = Llama(
    model_path=gemma_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=-1,
    verbose=True
)