#!/usr/bin/env python3
"""
Local Backend Runner for FAQBuddy
Optimized for RAM usage instead of VRAM
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Set up environment variables for local development."""
    # Set Python path to the backend directory (not src)
    backend_dir = Path(__file__).parent / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(backend_dir)
    os.environ["MODE"] = "local"  # Use local database mode
    
    print(f"✅ Python path set to: {backend_dir}")

def run_backend():
    """Run the FastAPI backend locally."""
    backend_dir = Path(__file__).parent / "backend"
    
    print("🚀 Starting FAQBuddy Backend locally...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📊 API docs will be at: http://localhost:8000/docs")
    print("🆓 Using RAM instead of VRAM for LLM models")
    print("💾 Expected RAM usage: ~4-8GB (depending on model size)")
    print("🎯 VRAM usage: 0GB (all processing in RAM)")
    print("-" * 60)
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Run uvicorn
    cmd = [
        "uvicorn", 
        "src.api.API:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload",
        "--log-level", "info"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running backend: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    setup_environment()
    exit_code = run_backend()
    sys.exit(exit_code)
