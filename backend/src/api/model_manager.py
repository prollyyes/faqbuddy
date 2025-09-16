import time
from utils.llm_mistral import load_mistral_model, unload_mistral_model
from utils.llm_gemma import load_gemma_model, unload_gemma_model
import gc

class ModelManager:
    """A centralized manager for loading and unloading ML models."""
    
    def __init__(self):
        self.current_model = None  # 'mistral' or 'gemma'

    def load_mistral(self):
        """Switches to the Mistral model, unloading Gemma if necessary."""
        if self.current_model == 'mistral':
            print("MANAGER: Mistral already loaded.")
            return True
        
        if self.current_model == 'gemma':
            self.unload_gemma()
            print("MANAGER: Cooldown period after unloading Gemma...")
            time.sleep(2)  # Cooldown to ensure resources are released

        print("MANAGER: Loading Mistral model...")
        if load_mistral_model():
            self.current_model = 'mistral'
            return True
        return False

    def unload_mistral(self):
        """Unload the Mistral model."""
        if self.current_model == 'mistral':
            print("MANAGER: Unloading Mistral model...")
            unload_mistral_model()
            self.current_model = None
            gc.collect()

    def load_gemma(self):
        """Switches to the Gemma model, unloading Mistral if necessary."""
        if self.current_model == 'gemma':
            print("MANAGER: Gemma already loaded.")
            return True

        if self.current_model == 'mistral':
            self.unload_mistral()
            print("MANAGER: Cooldown period after unloading Mistral...")
            time.sleep(2)  # Cooldown to ensure resources are released

        print("MANAGER: Loading Gemma model...")
        if load_gemma_model():
            self.current_model = 'gemma'
            return True
        return False

    def unload_gemma(self):
        """Unload the Gemma model."""
        if self.current_model == 'gemma':
            print("MANAGER: Unloading Gemma model...")
            unload_gemma_model()
            self.current_model = None
            gc.collect()
            
    def unload_all(self):
        """Unload all models."""
        print("MANAGER: Unloading all models...")
        if self.current_model == 'mistral':
            self.unload_mistral()
        if self.current_model == 'gemma':
            self.unload_gemma()
        self.current_model = None

# Global instance
model_manager = ModelManager()
