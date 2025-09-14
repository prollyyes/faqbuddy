"""
Model Switcher for FAQBuddy
Manages switching between Gemma and Mistral models to avoid GPU memory conflicts.
Only one model is loaded at a time to prevent segmentation faults.
"""

from src.utils.llm_gemma import load_gemma_model, unload_gemma_model, ensure_gemma_loaded
from src.utils.llm_mistral import load_mistral_model, unload_mistral_model, ensure_mistral_loaded

class ModelSwitcher:
    """Manages switching between Gemma and Mistral models"""
    
    def __init__(self):
        self.current_model = None  # 'gemma', 'mistral', or None
        print("🔄 Model Switcher initialized - models will be loaded on-demand")
    
    def switch_to_gemma(self):
        """Switch to Gemma model, unloading Mistral if loaded"""
        if self.current_model == 'gemma':
            return True  # Already using Gemma
        
        print("🔄 Switching to Gemma model...")
        
        # Unload Mistral if it's currently loaded
        if self.current_model == 'mistral':
            unload_mistral_model()
            # Add a small delay to ensure GPU memory is fully freed
            import time
            time.sleep(2)
        
        # Load Gemma
        if load_gemma_model():
            self.current_model = 'gemma'
            print("✅ Successfully switched to Gemma model")
            return True
        else:
            print("❌ Failed to switch to Gemma model")
            return False
    
    def switch_to_mistral(self):
        """Switch to Mistral model, unloading Gemma if loaded"""
        if self.current_model == 'mistral':
            return True  # Already using Mistral
        
        print("🔄 Switching to Mistral model...")
        
        # Unload Gemma if it's currently loaded
        if self.current_model == 'gemma':
            unload_gemma_model()
            # Add a small delay to ensure GPU memory is fully freed
            import time
            time.sleep(2)
        
        # Load Mistral
        if load_mistral_model():
            self.current_model = 'mistral'
            print("✅ Successfully switched to Mistral model")
            return True
        else:
            print("❌ Failed to switch to Mistral model")
            return False
    
    def ensure_gemma(self):
        """Ensure Gemma is loaded for T2SQL operations"""
        if self.current_model != 'gemma':
            return self.switch_to_gemma()
        return True
    
    def ensure_mistral(self):
        """Ensure Mistral is loaded for RAG operations"""
        if self.current_model != 'mistral':
            return self.switch_to_mistral()
        return True
    
    def unload_all(self):
        """Unload all models to free GPU memory"""
        print("🔄 Unloading all models...")
        if self.current_model == 'gemma':
            unload_gemma_model()
        elif self.current_model == 'mistral':
            unload_mistral_model()
        self.current_model = None
        print("✅ All models unloaded")
    
    def get_current_model(self):
        """Get the currently loaded model"""
        return self.current_model

# Global model switcher instance
model_switcher = ModelSwitcher()

def switch_to_gemma():
    """Switch to Gemma model for T2SQL operations"""
    return model_switcher.switch_to_gemma()

def switch_to_mistral():
    """Switch to Mistral model for RAG operations"""
    return model_switcher.switch_to_mistral()

def ensure_gemma_loaded():
    """Ensure Gemma is loaded for T2SQL operations"""
    return model_switcher.ensure_gemma()

def ensure_mistral_loaded():
    """Ensure Mistral is loaded for RAG operations"""
    return model_switcher.ensure_mistral()

def unload_all_models():
    """Unload all models to free GPU memory"""
    return model_switcher.unload_all()

def get_current_model():
    """Get the currently loaded model"""
    return model_switcher.get_current_model()
