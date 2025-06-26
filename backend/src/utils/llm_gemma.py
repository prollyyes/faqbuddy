import os
from llama_cpp import Llama

gemma_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'gemma-3-4b-it-Q4_1.gguf'))

llm_gemma = Llama(
    model_path=gemma_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=-1,
    verbose=False
)