#!/usr/bin/env python3
"""
FAQBuddy Server Launcher
Simple script to launch both backend and frontend servers.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}{Colors.ENDC}")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_info(message):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

def check_environment():
    """Check if .env file exists and has required variables."""
    env_file = Path(".env")
    if not env_file.exists():
        print_error(".env file not found. Please run setup_faqbuddy.py first.")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["DB_NEON_HOST", "DB_NEON_NAME", "DB_NEON_USER", "DB_NEON_PASSWORD", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print_error(f"Missing environment variables: {', '.join(missing_vars)}")
        print_info("Please run setup_faqbuddy.py to configure the environment.")
        return False
    
    return True

def start_backend_server():
    """Start the FastAPI backend server."""
    print_info("Starting backend server...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print_error("Backend directory not found")
        return None
    
    try:
        # Check if requirements are installed
        try:
            import fastapi
            import uvicorn
        except ImportError:
            print_error("Backend dependencies not installed. Please run setup_faqbuddy.py first.")
            return None
        
        # Start uvicorn server
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "src.main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], cwd=backend_dir)
        
        print_success("Backend server started")
        print_info("   URL: http://localhost:8000")
        print_info("   API Docs: http://localhost:8000/docs")
        
        return process
        
    except Exception as e:
        print_error(f"Failed to start backend server: {e}")
        return None

def start_frontend_server():
    """Start the Next.js frontend server."""
    print_info("Starting frontend server...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print_error("Frontend directory not found")
        return None
    
    try:
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            print_error("Frontend dependencies not installed. Please run setup_faqbuddy.py first.")
            return None
        
        # Start development server
        process = subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir)
        
        print_success("Frontend server started")
        print_info("   URL: http://localhost:3000")
        
        return process
        
    except Exception as e:
        print_error(f"Failed to start frontend server: {e}")
        return None

def wait_for_servers(backend_process, frontend_process):
    """Wait for servers to start and provide status."""
    print_info("Waiting for servers to start...")
    time.sleep(5)
    
    # Check if processes are still running
    if backend_process and backend_process.poll() is None:
        print_success("Backend server is running")
    else:
        print_error("Backend server failed to start")
    
    if frontend_process and frontend_process.poll() is None:
        print_success("Frontend server is running")
    else:
        print_error("Frontend server failed to start")

def signal_handler(signum, frame):
    """Handle Ctrl+C to gracefully stop servers."""
    print("\n\n🛑 Stopping servers...")
    
    if 'backend_process' in globals() and backend_process:
        backend_process.terminate()
        print_success("Backend server stopped")
    
    if 'frontend_process' in globals() and frontend_process:
        frontend_process.terminate()
        print_success("Frontend server stopped")
    
    print("👋 FAQBuddy stopped")
    sys.exit(0)

def main():
    """Main execution function."""
    print_header("FAQBuddy Server Launcher")
    
    # Check environment
    if not check_environment():
        return
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start backend server
    global backend_process
    backend_process = start_backend_server()
    if not backend_process:
        print_error("Failed to start backend server")
        return
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend server
    global frontend_process
    frontend_process = start_frontend_server()
    if not frontend_process:
        print_error("Failed to start frontend server")
        backend_process.terminate()
        return
    
    # Wait for servers to start
    wait_for_servers(backend_process, frontend_process)
    
    print_info("Both servers are running!")
    print_info("Press Ctrl+C to stop both servers")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
            # Check if processes are still running
            if backend_process.poll() is not None:
                print_error("Backend server stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print_error("Frontend server stopped unexpectedly")
                break
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main() 