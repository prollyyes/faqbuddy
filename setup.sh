#!/bin/bash

set -e

echo ""
echo "📦 FAQBuddy Project Setup"
echo "=========================="
echo ""

# Check if a Python environment is already active
if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
  echo "✅ Detected active Conda environment: $CONDA_DEFAULT_ENV"
  active_env=conda

elif [[ -n "$VIRTUAL_ENV" ]]; then
  echo "✅ Detected active Python venv: $VIRTUAL_ENV"
  active_env=venv

else
  echo "Choose your Python environment setup:"
  echo "1. Create and use a Python 3.9 virtual environment (venv)"
  echo "2. Create and use a new Conda environment (Python 3.9)"
  echo "3. Use an existing Conda environment"
  echo ""
  read -p "Select [1-3]: " env_choice

  if [[ "$env_choice" == "1" ]]; then
    echo "🔧 Creating Python 3.9 virtual environment..."
    if ! command -v python3.9 &> /dev/null; then
      echo "❌ Python 3.9 not found. Installing with Homebrew..."
      brew install python@3.9
      export PATH="/opt/homebrew/opt/python@3.9/bin:$PATH"
    fi
    python3.9 -m venv venv
    source venv/bin/activate
    active_env=venv

  elif [[ "$env_choice" == "2" ]]; then
    read -p "Enter a name for your Conda environment: " ENV_NAME
    echo "🔧 Creating Conda environment '$ENV_NAME' with Python 3.9..."
    conda create -y -n "$ENV_NAME" python=3.9
    echo "⚠️  Please activate it manually now using:"
    echo "    conda activate $ENV_NAME"
    exit 0

  elif [[ "$env_choice" == "3" ]]; then
    read -p "Enter the name of your existing Conda environment: " ENV_NAME
    echo "⚠️  Please activate it manually now using:"
    echo "    conda activate $ENV_NAME"
    exit 0

  else
    echo "❌ Invalid choice. Exiting."
    exit 1
  fi
fi

# Step 2: Install backend dependencies
echo "📂 Changing to backend and installing requirements..."
cd backend
pip install -r src/requirements.txt

# Step 3: Prompt to download GGUF models
read -p "❓ Do you want to download the GGUF models now? (y/n): " download_models

if [[ "$download_models" == "y" || "$download_models" == "Y" ]]; then
  echo "📁 Creating models directory..."
  mkdir -p models

  echo "⬇️  Downloading Gemma 3B IT Q4_1..."
  curl -L -o models/gemma-3-4b-it-Q4_1.gguf \
    "https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_1.gguf?download=true"

  echo "⬇️  Downloading Mistral 7B Instruct Q4_K_M..."
  curl -L -o models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
    "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf?download=true"

  echo "✅ Models downloaded to backend/models"
else
  echo "⏩ Skipping model download."
fi

# Step 4: Ask if user wants to create .env
read -p "❓ Do you want to create the .env file now? (y/n): " create_env_file

if [[ "$create_env_file" == "y" || "$create_env_file" == "Y" ]]; then
  echo "🛠️  Creating .env file..."
  cat > ../.env <<EOF
PINECONE_API_KEY=your_api_key
PINECONE_HOST=your_host_url
PINECONE_INDEX=your_index_name
DB_USER=db_user
DB_PASSWORD=pwd
DB_NAME=faqbuddy_db
DB_HOST=localhost
DB_PORT=5433
EOF
  echo "✅ .env file created in project root."
else
  echo "⏩ Skipping .env file creation."
fi

# Step 5: Set PYTHONPATH
echo "🌐 Setting PYTHONPATH..."

export PYTHONPATH=$(pwd)

# Step 6: Manual DB reminder
echo "⚠️  Manual DB setup required. See /db/README.md"

# Step 7: Prepare ML and RAG models
echo "⚙️  Creating ML model and indexing documents..."
cd src
python switcher/create_MLmodel.py
python rag/embed_and_index.py

# Step 8: Run backend tests
echo "🧪 Running backend tests..."
cd ..
python tests/test_ml.py
python -m pytest -s tests/test_pipeline.py
python src/rag/test_rag.py

# Step 9: Final instructions
echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the backend:"
[[ "$active_env" == "venv" ]] && echo "  source venv/bin/activate"
[[ "$active_env" == "conda" ]] && echo "  conda activate $CONDA_DEFAULT_ENV"
echo "  cd backend/src"
echo "  export PYTHONPATH=\$(pwd)"
echo "  uvicorn main:app --reload"
echo ""
echo "To run the frontend:"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"
