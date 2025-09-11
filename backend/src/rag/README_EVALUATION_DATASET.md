# RAG Pipeline Evaluation Dataset Creation

This directory contains scripts to extract data from your Pinecone database and create a comprehensive dataset for generating 200 ground truths to evaluate your RAG pipeline performance.

## Overview

The evaluation dataset creation process consists of two main steps:

1. **Data Extraction**: Extract all relevant data from Pinecone namespaces
2. **Prompt Generation**: Create a comprehensive prompt for GPT-5 to generate ground truths

## Quick Start

### Option 1: Complete Pipeline (Recommended)

Run the complete pipeline with default settings:

```bash
cd /home/edd/Documents/projects/faqbuddy/backend/src/rag
python create_evaluation_dataset.py
```

This will:
- Extract up to 5,000 vectors from each Pinecone namespace
- Create a formatted evaluation dataset
- Generate a comprehensive prompt for GPT-5
- Create a template for manual ground truth creation

### Option 2: Custom Configuration

```bash
# Extract more data per namespace
python create_evaluation_dataset.py --max-vectors 10000 --num-questions 200

# Specify custom output directory
python create_evaluation_dataset.py --output-dir ./my_evaluation_data

# Only extract data, skip prompt generation
python create_evaluation_dataset.py --extract-only
```

### Option 3: Use Existing Dataset

If you already have an evaluation dataset and want to regenerate prompts:

```bash
python create_evaluation_dataset.py --skip-extraction --dataset-path ./existing_dataset.json
```

## Scripts Overview

### 1. `create_evaluation_dataset.py` (Main Script)
- **Purpose**: Complete pipeline runner
- **Usage**: `python create_evaluation_dataset.py [options]`
- **Features**: Combines extraction and prompt generation

### 2. `extract_pinecone_for_evaluation.py`
- **Purpose**: Extract data from all Pinecone namespaces
- **Usage**: `python extract_pinecone_for_evaluation.py [options]`
- **Features**: 
  - Extracts from all available namespaces
  - Preserves metadata and text content
  - Handles large datasets with pagination
  - Creates structured JSON output

### 3. `generate_ground_truths.py`
- **Purpose**: Generate prompts for ground truth creation
- **Usage**: `python generate_ground_truths.py --dataset <dataset.json> [options]`
- **Features**:
  - Analyzes dataset content
  - Creates comprehensive GPT-5 prompts
  - Generates templates for manual creation

## Output Files

The pipeline creates several files in the output directory:

### Data Files
- `pinecone_raw_data_YYYYMMDD_HHMMSS.json`: Raw extracted data from Pinecone
- `evaluation_dataset_YYYYMMDD_HHMMSS.json`: Formatted dataset for evaluation

### Prompt Files
- `gpt5_prompt_YYYYMMDD_HHMMSS.md`: Comprehensive prompt for GPT-5
- `ground_truth_template_YYYYMMDD_HHMMSS.json`: Template for manual creation

## Pinecone Configuration

The scripts automatically detect and extract from all configured namespaces:

### RAGv2 Namespaces
- `documents_v2`: Document-based content
- `db_v2` or `per_row`: Database content (depending on configuration)
- `pdf_v2`: PDF document content

### Existing Namespaces
- `documents`: Legacy document namespace
- `db`: Legacy database namespace

### Advanced Namespaces
- `contextual_db`: Advanced contextual database content (if enabled)

## Ground Truth Generation

### Using GPT-5

1. Open the generated `gpt5_prompt_YYYYMMDD_HHMMSS.md` file
2. Copy the entire prompt content
3. Paste it into GPT-5 with the instruction to generate 200 question-answer pairs
4. Save the output as `ground_truths_YYYYMMDD_HHMMSS.json`

### Manual Creation

1. Use the `ground_truth_template_YYYYMMDD_HHMMSS.json` file
2. Fill in the `ground_truths` array with question-answer pairs
3. Follow the format specified in the template

## Ground Truth Format

Each ground truth entry should include:

```json
{
  "id": "gt_001",
  "question": "Qual è la procedura per iscriversi al corso di laurea?",
  "expected_answer": "La procedura di iscrizione include...",
  "context_documents": ["doc_id_1", "doc_id_2"],
  "question_type": "procedural",
  "difficulty": "medium",
  "domain": "academic",
  "keywords": ["iscrizione", "laurea", "procedura"],
  "reasoning": "This question tests procedural knowledge retrieval"
}
```

## Question Distribution

The generated ground truths should follow this distribution:

### Question Types (25% each)
- **Factual**: Direct facts, definitions, specific information
- **Procedural**: How-to questions, step-by-step processes
- **Comparative**: Comparing different options or procedures
- **Analytical**: Complex questions requiring synthesis

### Difficulty Levels (33% each)
- **Easy**: Simple, direct questions
- **Medium**: Questions requiring context
- **Hard**: Complex questions requiring deep understanding

### Domains
- **Academic**: Course information, degree programs
- **Administrative**: Registration, enrollment procedures
- **Procedural**: Step-by-step processes, deadlines

## Requirements

### Environment Variables
Make sure these are set in your `.env` file:
```
PINECONE_API_KEY=your_pinecone_api_key
```

### Python Dependencies
The scripts use existing dependencies from your RAG pipeline:
- `pinecone-client`
- `python-dotenv`
- `tqdm`
- `json`

## Troubleshooting

### Common Issues

1. **Pinecone Connection Error**
   - Verify `PINECONE_API_KEY` is set correctly
   - Check internet connection
   - Ensure Pinecone index exists

2. **Empty Namespaces**
   - Some namespaces might be empty
   - Check your Pinecone index stats
   - Verify namespace names in configuration

3. **Large Dataset Handling**
   - Use `--max-vectors` to limit extraction
   - The script handles pagination automatically
   - Monitor memory usage for very large datasets

4. **Permission Errors**
   - Ensure write permissions for output directory
   - Check file system space availability

### Performance Tips

1. **For Large Datasets**
   - Start with `--max-vectors 1000` for testing
   - Increase gradually based on your needs
   - Monitor extraction progress

2. **Memory Optimization**
   - The scripts process data in batches
   - Close other applications if needed
   - Consider using a machine with more RAM for very large datasets

## Next Steps

After creating your ground truths:

1. **Validate Ground Truths**: Review generated questions for quality
2. **Test RAG Pipeline**: Use the ground truths to evaluate your pipeline
3. **Benchmark Performance**: Measure retrieval accuracy and answer quality
4. **Iterate**: Use results to improve your RAG pipeline

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the script output for error messages
3. Verify your Pinecone configuration
4. Check that all required dependencies are installed
