#!/usr/bin/env python3
"""
Backend Server Launcher
======================

This script starts the FAQBuddy backend server with the correct configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the backend server."""
    print("=========== Starting FAQBuddy Backend Server ===========")
    print("=" * 50)
    
    # Get the project root directory
    project_root = Path(__file__).parent
    backend_src = project_root / "backend" / "src"
    
    # Check if we're in the right directory
    if not backend_src.exists():
        print("❌ Error: backend/src directory not found!")
        print(f"   Expected: {backend_src}")
        print(f"   Current: {project_root}")
        sys.exit(1)
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_src)
    env["CHAT_ENABLED"] = "true"  # Enable chat for local testing
    
    print(f"=========== Working directory: {backend_src} ===========")
    print(f"=========== Python path: {env['PYTHONPATH']} ===========")
    print(f"=========== Chat enabled: {env['CHAT_ENABLED']} ===========")
    print()
    
    # Change to backend/src directory
    os.chdir(backend_src)
    
    # Start the server
    print("================================================")
    print("=========== Starting uvicorn server... ===========")
    print("================================================")
    print("   Entrypoint: api.API:app")
    print("   Host: 0.0.0.0")
    print("   Port: 8000")
    print("   Reload: enabled")
    print()
    print("=========== Server will be available at: http://localhost:8000 ===========")
    print("=========== API docs will be available at: http://localhost:8000/docs ===========")
    print()
    print("=========== Press Ctrl+C to stop the server ===========")
    print("-" * 50)
    
    try:
        # Start uvicorn with the correct entrypoint
        subprocess.run([
            "uvicorn", 
            "api.API:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], env=env)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
