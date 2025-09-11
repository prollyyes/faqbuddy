#!/bin/bash
# Setup script for RAG Evaluation Dataset Extractor
# This script makes all Python files executable and sets up the environment

echo "🚀 Setting up RAG Evaluation Dataset Extractor"
echo "=" * 50

# Make Python scripts executable
echo "📝 Making Python scripts executable..."
chmod +x *.py

# Check if .env file exists (from benchmark/extractor/, root is ../../)
if [ ! -f "../../.env" ]; then
    echo "⚠️  Warning: .env file not found in root directory"
    echo "   Please ensure PINECONE_API_KEY is set in ../../.env"
else
    echo "✅ Found .env file in root directory"
fi

# Check Python dependencies
echo "📦 Checking Python dependencies..."
python3 -c "import pinecone, dotenv, tqdm" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ All required Python packages are installed"
else
    echo "❌ Some Python packages are missing"
    echo "   Please install them with: pip install -r requirements.txt"
fi

echo ""
echo "🎯 Setup completed!"
echo ""
echo "Quick start commands:"
echo "  # Extract specific namespaces (advanced_db, pdf_v2):"
echo "  python extract_specific_namespaces.py"
echo ""
echo "  # Run complete pipeline:"
echo "  python create_evaluation_dataset.py"
echo ""
echo "For more information, see README.md"
