#!/usr/bin/env python3
"""
FAQBuddy Setup Wizard
A clean, efficient setup system for FAQBuddy RAG application.
"""

import os
import sys
import subprocess
import time
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load existing .env if it exists
load_dotenv()

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
    UNDERLINE = '\033[4m'

def print_header(title):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}{Colors.ENDC}")

def print_step(step_num, total_steps, description):
    """Print a formatted step."""
    print(f"\n{Colors.OKBLUE}📋 Step {step_num}/{total_steps}: {description}{Colors.ENDC}")
    print("-" * 40)

def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_info(message):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

def get_user_choice(prompt, options, default=None):
    """Get user choice from a list of options."""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"   {i}. {option}")
    
    while True:
        try:
            choice = input(f"\nEnter your choice (1-{len(options)})" + 
                          (f" [default: {default}]" if default else "") + ": ").strip()
            
            if not choice and default:
                return default
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                return choice_num
            else:
                print_error(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print_error("Please enter a valid number")

def check_python_version():
    """Check if Python version is compatible."""
    print_step(1, 6, "Checking Python Version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_environment_file():
    """Set up the .env file with required environment variables."""
    print_step(2, 6, "Setting up Environment File")
    
    env_file = Path(".env")
    env_content = {}
    
    # Check if .env already exists
    if env_file.exists():
        print_info("Found existing .env file")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_content[key] = value
    
    # Required environment variables
    required_vars = {
        "DB_NEON_NAME": "Neon Database Name",
        "DB_NEON_USER": "Neon Database Username", 
        "DB_NEON_PASSWORD": "Neon Database Password",
        "DB_NEON_HOST": "Neon Database Host",
        "DB_NEON_PORT": "Neon Database Port (default: 5432)",
        "PINECONE_API_KEY": "Pinecone API Key"
    }
    
    print_info("Please provide the following database credentials:")
    print_warning("You can skip any field by pressing Enter to keep existing value")
    
    for var, description in required_vars.items():
        current_value = env_content.get(var, "")
        if current_value and var != "DB_NEON_PORT":
            print(f"   {description}: {current_value} (current)")
            continue
        
        if var == "DB_NEON_PORT":
            default_port = current_value or "5432"
            value = input(f"   {description} [{default_port}]: ").strip()
            if not value:
                value = default_port
        else:
            value = input(f"   {description}: ").strip()
        
        if value:
            env_content[var] = value
    
    # Add legacy database variables for compatibility
    env_content.update({
        "DB_NAME": env_content.get("DB_NEON_NAME", ""),
        "DB_USER": env_content.get("DB_NEON_USER", ""),
        "DB_PASSWORD": env_content.get("DB_NEON_PASSWORD", ""),
        "DB_HOST": env_content.get("DB_NEON_HOST", ""),
        "DB_PORT": env_content.get("DB_NEON_PORT", "5432")
    })
    
    # Write .env file
    try:
        with open(env_file, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        print_success(".env file created/updated successfully")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False

def test_database_connection():
    """Test connection to the Neon database."""
    print_step(3, 6, "Testing Database Connection")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv("DB_NEON_HOST"),
            port=os.getenv("DB_NEON_PORT", "5432"),
            database=os.getenv("DB_NEON_NAME"),
            user=os.getenv("DB_NEON_USER"),
            password=os.getenv("DB_NEON_PASSWORD"),
            sslmode="require"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        print_success(f"Database connection successful (PostgreSQL {version[0]})")
        return True
        
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_warning("Please check your database credentials in the .env file")
        return False

def download_models():
    """Download required AI models."""
    print_step(4, 6, "Setting up AI Models")
    
    models_dir = Path("backend/models")
    models_dir.mkdir(exist_ok=True)
    
    # Required models
    models = {
        "mistral-7b-instruct-v0.2.Q4_K_M.gguf": {
            "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "size": "4.1GB",
            "description": "Mistral 7B Instruct (Main LLM for generation)"
        }
    }
    
    for model_name, model_info in models.items():
        model_path = models_dir / model_name
        
        if model_path.exists():
            print_success(f"{model_name} already exists")
            continue
        
        print_info(f"Downloading {model_name} ({model_info['size']})...")
        print_warning("This may take several minutes depending on your internet connection")
        
        try:
            response = requests.get(model_info["url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
            
            print(f"\n   {Colors.OKGREEN}✅ Downloaded {model_name}{Colors.ENDC}")
            
        except Exception as e:
            print_error(f"Failed to download {model_name}: {e}")
            if model_path.exists():
                model_path.unlink()
            return False
    
    print_success("All models downloaded successfully")
    return True

def update_vector_database():
    """Update Pinecone vector database."""
    print_step(5, 6, "Setting up Vector Database")
    
    choice = get_user_choice(
        "Do you want to update the Pinecone vector database?",
        ["Yes - Update vector database", "No - Skip for now"],
        default=1
    )
    
    if choice == 2:
        print_info("Skipping vector database update")
        return True
    
    try:
        print_info("Updating Pinecone vector database...")
        print_warning("This may take a few minutes")
        
        # Run the vector database update script
        result = subprocess.run([
            sys.executable, "backend/src/rag/update_pinecone_from_neon.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Vector database updated successfully")
            return True
        else:
            print_error(f"Vector database update failed: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Error updating vector database: {e}")
        return False

def install_dependencies():
    """Install Python and Node.js dependencies."""
    print_step(6, 6, "Installing Dependencies")
    
    # Install Python dependencies
    print_info("Installing Python dependencies...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "backend/src/requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Python dependencies installed")
        else:
            print_error(f"Failed to install Python dependencies: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error installing Python dependencies: {e}")
        return False
    
    # Install Node.js dependencies
    print_info("Installing Node.js dependencies...")
    try:
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print_error("Frontend directory not found")
            return False
        
        result = subprocess.run(["npm", "install"], cwd=frontend_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("Node.js dependencies installed")
        else:
            print_error(f"Failed to install Node.js dependencies: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error installing Node.js dependencies: {e}")
        return False
    
    return True

def show_launch_instructions():
    """Show instructions for launching the application."""
    print_header("Setup Complete! 🎉")
    
    print_success("FAQBuddy has been set up successfully!")
    print_info("To launch the application, you need to start both the backend and frontend servers:")
    
    print(f"\n{Colors.BOLD}Backend Server:{Colors.ENDC}")
    print("   cd backend")
    print("   python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
    print("   URL: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    
    print(f"\n{Colors.BOLD}Frontend Server:{Colors.ENDC}")
    print("   cd frontend")
    print("   npm run dev")
    print("   URL: http://localhost:3000")
    
    print(f"\n{Colors.WARNING}Note:{Colors.ENDC} Keep both servers running for the application to work properly.")
    print(f"\n{Colors.OKCYAN}For help and documentation, check the project repository.{Colors.ENDC}")

def main():
    """Main setup function."""
    print_header("FAQBuddy Setup Wizard")
    
    print_info("This wizard will help you set up FAQBuddy with all necessary components.")
    print_info("The setup includes:")
    print("   • Environment configuration")
    print("   • Database connection testing")
    print("   • AI model downloads")
    print("   • Vector database setup")
    print("   • Dependency installation")
    
    # Check Python version
    if not check_python_version():
        return
    
    # Set up environment file
    if not setup_environment_file():
        return
    
    # Test database connection
    if not test_database_connection():
        return
    
    # Download models
    if not download_models():
        return
    
    # Update vector database
    if not update_vector_database():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Show launch instructions
    show_launch_instructions()

if __name__ == "__main__":
    main() 