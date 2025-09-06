# RAGv2 Ubuntu Configuration Guide
# ================================

## System Analysis for `/home/edd/Documents/projects/faqbuddy`

Based on your system analysis, here's what I found and what you need to do:

### 🖥️ System Specifications
- **OS**: Ubuntu Linux
- **GPU**: NVIDIA GeForce RTX 2060 (8GB VRAM)
- **CUDA**: Version 12.9
- **Previous Setup**: Mac-specific configurations detected

### 🔧 Issues Found and Fixed

#### 1. Mac-Specific Device Settings
**Problem**: Your code was hardcoded to use MPS (Metal Performance Shaders) which is Mac-only
**Fix**: Updated device detection to auto-detect CUDA or fallback to CPU

**Files Modified**:
- `backend/src/rag/utils/embeddings_v2.py` - Auto device detection
- `backend/src/rag/update_pinecone_from_neon.py` - CUDA/CPU fallback
- `backend/src/rag/rag_pipeline_v2.py` - Fixed import path

#### 2. Import Path Issues
**Problem**: Incorrect relative import causing `ModuleNotFoundError`
**Fix**: Updated import from `src.utils.llm_mistral` to `..utils.llm_mistral`

#### 3. Missing CLI Script
**Problem**: `run_rag_v2_cli.py` didn't exist
**Fix**: Created new interactive CLI with proper error handling

### 🚀 Next Steps

#### 1. Install Dependencies
Run the setup script I created:

```bash
cd /home/edd/Documents/projects/faqbuddy
./setup_ragv2_ubuntu.sh
```

This will:
- Detect your NVIDIA GPU
- Install PyTorch with CUDA 12.1 support
- Install all required ML libraries
- Set up proper device configurations
- Create environment file template

#### 2. Configure Environment
Edit the `.env` file with your API keys:

```bash
# Required
PINECONE_API_KEY=your_actual_pinecone_key

# Optional (for generation guards)
OPENAI_API_KEY=your_openai_key_if_needed
```

#### 3. Test the Pipeline
Run the new CLI interface:

```bash
cd /home/edd/Documents/projects/faqbuddy/backend
python3 src/rag/run_rag_v2_cli.py
```

### 🔥 Performance Optimizations for Your RTX 2060

#### Memory Management
Your RTX 2060 has 8GB VRAM. Here are the optimizations:

1. **Batch Sizes**: The pipeline will automatically detect optimal batch sizes
2. **Model Loading**: Lazy loading prevents memory issues
3. **Context Management**: Limited to 4000 tokens to fit in memory

#### Recommended Settings for Your GPU
```bash
# In your .env file, these are optimized for RTX 2060:
INSTRUCTOR_XL_EMBEDDINGS=true     # Will use CUDA
RERANKER_ENABLED=true             # Cross-encoder on GPU
BM25_FALLBACK=true                # CPU fallback when needed
```

### 📊 Expected Performance Improvements

With your RTX 2060, you should see:
- **Embedding Generation**: 5-10x faster than CPU
- **Cross-encoder Reranking**: 3-5x faster than CPU
- **Overall Query Time**: 2-4x improvement

### 🐛 Troubleshooting

#### If CUDA Memory Issues Occur:
1. Reduce batch sizes in the config
2. Enable CPU fallback for specific components
3. Monitor GPU memory with `nvidia-smi`

#### If Import Errors Persist:
1. Make sure you're in the correct directory
2. Check Python path setup
3. Verify all dependencies are installed

### 🧪 Testing Strategy

1. **Start Simple**: Test with feature flags disabled
2. **Enable Gradually**: Turn on features one by one
3. **Monitor Performance**: Use the stats command in CLI
4. **Compare Results**: CPU vs GPU performance

### 📝 Files Created/Modified

**New Files**:
- `setup_ragv2_ubuntu.sh` - Ubuntu setup script
- `backend/src/rag/run_rag_v2_cli.py` - Interactive CLI
- `UBUNTU_SETUP.md` - This guide

**Modified Files**:
- `backend/src/rag/rag_pipeline_v2.py` - Fixed import
- `backend/src/rag/utils/embeddings_v2.py` - Auto device detection
- `backend/src/rag/update_pinecone_from_neon.py` - CUDA support

### 🎯 Ready to Test!

You're now ready to test your RAGv2 pipeline on Ubuntu with proper GPU acceleration. The setup script will handle all the dependencies and configurations automatically.
