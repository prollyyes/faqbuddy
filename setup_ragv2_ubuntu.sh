#!/bin/bash
# RAGv2 Ubuntu Setup Script
# =========================
# This script sets up the RAGv2 pipeline for Ubuntu/Linux systems
# with proper CUDA detection and package installation

set -e

echo "🚀 RAGv2 Ubuntu Setup Script"
echo "============================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
# Convert version to comparable format (e.g., 3.11 -> 311, 3.8 -> 38)
version_num=$(echo "$python_version" | sed 's/\.//')
if [[ $version_num -ge 38 ]]; then
    print_success "Python $python_version is compatible"
else
    print_error "Python 3.8+ required, found $python_version"
    exit 1
fi

# Check for NVIDIA GPU
print_status "Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    gpu_info=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)
    print_success "NVIDIA GPU detected: $gpu_info"
    
    # Check CUDA version
    cuda_version=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9.]+')
    print_success "CUDA Version: $cuda_version"
    
    USE_CUDA=true
else
    print_warning "No NVIDIA GPU detected, will use CPU"
    USE_CUDA=false
fi

# Check if conda is available
if ! command -v conda &> /dev/null; then
    print_error "Conda not found. Please install Anaconda or Miniconda first."
    exit 1
fi

# Check if we're in a conda environment
if [[ -z "$CONDA_DEFAULT_ENV" ]] || [[ "$CONDA_DEFAULT_ENV" == "base" ]]; then
    print_warning "Not in a conda environment (or using base environment)"
    read -p "Do you want to create a new conda environment? (y/n): " create_env
    
    if [[ $create_env == "y" || $create_env == "Y" ]]; then
        print_status "Creating conda environment 'ragv2'..."
        conda create -n ragv2 python=3.11 -y
        
        print_success "Conda environment 'ragv2' created successfully!"
        print_warning "Please activate the environment and re-run this script:"
        echo ""
        echo "  conda activate ragv2"
        echo "  ./setup_ragv2_ubuntu.sh"
        echo ""
        exit 0
    else
        print_warning "Continuing with current environment: $CONDA_DEFAULT_ENV"
    fi
else
    print_success "Conda environment detected: $CONDA_DEFAULT_ENV"
fi

# Update pip
print_status "Updating pip..."
python3 -m pip install --upgrade pip

# Install PyTorch based on CUDA availability
print_status "Installing PyTorch..."
if [[ $USE_CUDA == true ]]; then
    print_status "Installing PyTorch with CUDA support using conda..."
    # Use conda-forge for PyTorch with CUDA (better compatibility)
    conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
else
    print_status "Installing PyTorch CPU-only version using conda..."
    conda install pytorch torchvision torchaudio cpuonly -c pytorch -y
fi

# Install other ML dependencies
print_status "Installing ML dependencies..."
# Use conda for core ML packages (better dependency resolution)
conda install -c conda-forge \
    scikit-learn \
    pandas \
    numpy \
    -y

# Use pip for specialized packages
python3 -m pip install \
    transformers>=4.52.0 \
    sentence-transformers>=2.5.0 \
    accelerate>=1.8.0 \
    datasets>=3.6.0 \
    huggingface-hub>=0.33.0

# Install RAG-specific dependencies
print_status "Installing RAG dependencies..."
python3 -m pip install \
    pinecone-client \
    rank-bm25>=0.2.2 \
    python-dotenv>=1.1.0 \
    scikit-learn>=1.6.0

# Install other required dependencies
print_status "Installing other dependencies..."
# Use conda for some packages
conda install -c conda-forge \
    requests \
    beautifulsoup4 \
    -y

# Use pip for the rest
python3 -m pip install \
    fastapi>=0.115.0 \
    uvicorn>=0.34.0 \
    PyMuPDF>=1.26.0

# Verify installations
print_status "Verifying installations..."

# Test PyTorch
python3 -c "
import torch
print(f'✅ PyTorch {torch.__version__} installed')
print(f'✅ CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ CUDA device: {torch.cuda.get_device_name(0)}')
"

# Test other key packages
python3 -c "
try:
    import transformers
    print(f'✅ Transformers {transformers.__version__} installed')
    
    import sentence_transformers
    print(f'✅ Sentence Transformers {sentence_transformers.__version__} installed')
    
    import pinecone
    print(f'✅ Pinecone client installed')
    
    print('✅ All key dependencies verified')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Create environment file template if it doesn't exist
ENV_FILE="../.env"
if [[ ! -f $ENV_FILE ]]; then
    print_status "Creating .env template..."
    cat > $ENV_FILE << EOF
# RAGv2 Environment Configuration
# ===============================

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here

# Feature Flags (set to true/false)
SCHEMA_AWARE_CHUNKING=true
INSTRUCTOR_XL_EMBEDDINGS=true
RERANKER_ENABLED=true
BM25_FALLBACK=true
HALLUCINATION_GUARDS=false
WEB_SEARCH_ENHANCEMENT=true
OBSERVABILITY_ENABLED=true

# Optional: OpenAI for generation guards
OPENAI_API_KEY=your_openai_api_key_here
EOF
    print_success "Created .env template at $ENV_FILE"
    print_warning "Please edit $ENV_FILE and add your API keys"
else
    print_success ".env file already exists"
fi

print_success "Setup complete! 🎉"
echo ""
echo "Next steps:"
if [[ "$CONDA_DEFAULT_ENV" == "ragv2" ]]; then
    echo "1. Edit the .env file and add your API keys"
    echo "2. Test the RAGv2 pipeline with: python3 src/rag/run_rag_v2_cli.py"
else
    echo "1. Activate the conda environment: conda activate $CONDA_DEFAULT_ENV"
    echo "2. Edit the .env file and add your API keys"
    echo "3. Test the RAGv2 pipeline with: python3 src/rag/run_rag_v2_cli.py"
fi
echo ""
if [[ $USE_CUDA == true ]]; then
    echo "🚀 Your system is configured for GPU acceleration!"
else
    echo "🖥️ Your system will use CPU (consider getting a GPU for better performance)"
fi
echo ""
echo "💡 Environment: $CONDA_DEFAULT_ENV"
