# Ground Truth Annotation Guide

## Overview

This guide helps you create high-quality ground truth data for comprehensive RAG evaluation. The system has already created basic ground truth with AI suggestions - you need to refine it for optimal results.

## Current Ground Truth Status

**Basic Structure Created**: `data/ground_truth_enhanced.json`
- 10 queries with basic categorization
- AI-suggested query types and table classifications
- Initial section mappings

## What You Need to Refine

### 1. **relevant_chunk_ids** (Most Important)
Currently empty `[]` - these are crucial for Recall@k, MRR, and nDCG metrics.

**How to find chunk IDs:**
- Run a test query through your RAG system
- Note which retrieved chunks correctly answer the question
- Copy their chunk IDs to the ground truth

**Example Process:**
```bash
# Test a query to see what chunks are retrieved
python backend/src/main.py  # Interactive mode
> Quali corsi insegna il prof Lenzerini?
# Note the chunk IDs of correct results
```

### 2. **relevant_sections** 
Currently AI-suggested. Review and refine based on your document structure.

**Common Section Types:**
- "Offerta Formativa" (Course offerings)
- "Docenti" (Faculty)
- "Corsi" (Courses)
- "Iscrizione" (Enrollment)
- "Tasse" (Fees)
- "Calendario" (Calendar)

### 3. **is_table_query**
AI has suggested classifications. Verify:
- `true`: Queries asking for lists, structured data, contact info
- `false`: Procedural questions, explanations, how-to

### 4. **query_type**
AI has suggested types. Common types:
- `list`: "Quali corsi...", "Elenca...", "Mostra..."
- `factual`: Simple fact lookup
- `procedural`: "Come...", "Quando...", "Dove..."
- `contact`: Email, phone, address requests
- `calculation`: Credit hours, costs

## Annotation Workflow

### Step 1: Generate Test Traces (Optional but Recommended)
```bash
# Generate a single configuration to see what chunks are retrieved
python benchmark/run_comprehensive_evaluation.py --mode generate-only --configurations baseline
# This will show you actual chunk IDs for each query
```

### Step 2: Manual Refinement
Edit `data/ground_truth_enhanced.json`:

```json
{
  "query_id": "q_1",
  "question": "Quali corsi insegna il prof Lenzerini?",
  "ground_truth_answer": "Basi di Dati",
  "relevant_chunk_ids": [
    "doc_123_chunk_5",     // ADD: Actual chunk IDs that should be retrieved
    "doc_124_chunk_2"      // ADD: Get these from test runs
  ],
  "relevant_sections": [
    "Offerta Formativa",   // VERIFY: Check against your document structure
    "Docenti"             // VERIFY: Adjust as needed
  ],
  "is_table_query": true,   // VERIFY: AI suggested, but check if correct
  "query_type": "list",     // VERIFY: AI suggested, but refine if needed
  "confidence": 0.9         // INCREASE: After manual verification
}
```

### Step 3: Quality Validation
```bash
# Validate your annotations
python benchmark/eval/ground_truth_creator.py --mode validate --input data/ground_truth_enhanced.json
```

## Quality Guidelines

### High-Quality Ground Truth Characteristics:
1. **Complete chunk IDs**: Every relevant chunk for each query
2. **Accurate classifications**: Correct table_query and query_type
3. **Comprehensive sections**: All relevant document sections
4. **High confidence**: 0.8+ after manual review

### Query Type Examples:

**List Queries** (is_table_query: true):
- "Quali corsi insegna il prof X?"
- "Elenca tutti i professori"
- "Mostra i contatti del dipartimento"

**Factual Queries** (is_table_query: false):
- "Come si chiama di nome il prof X?"
- "Da quanti crediti è il corso Y?"

**Procedural Queries** (is_table_query: false):
- "Come ci si iscrive?"
- "Quando scadono le tasse?"
- "Dove si trova l'ufficio?"

## Quick Start Options

### Option A: Minimal Effort (Good Results)
1. Keep AI suggestions as-is
2. Add 2-3 chunk IDs per query (run test queries)
3. Set confidence to 0.7
4. Run evaluation

### Option B: High Quality (Best Results)
1. Test each query manually
2. Identify all relevant chunks
3. Verify classifications
4. Add comprehensive section mappings
5. Set confidence to 0.9+
6. Run evaluation

### Option C: Incremental (Recommended)
1. Start with Option A
2. Run initial evaluation
3. Analyze results and failure cases
4. Refine ground truth for problematic queries
5. Re-run evaluation

## Expected Time Investment

- **Minimal (Option A)**: 30-45 minutes
- **High Quality (Option B)**: 2-3 hours
- **Incremental (Option C)**: 1 hour initial + refinement cycles

## Running the Full Evaluation

Once your ground truth is ready:

```bash
# Full evaluation with your refined ground truth
python benchmark/run_comprehensive_evaluation.py --mode full

# Results will include all advanced metrics:
# - Recall@k, MRR, nDCG@k
# - Table-aware metrics
# - Coverage and diversity
# - False-positive analysis
# - RAGAS metrics
```

## Tips for Success

1. **Start small**: Perfect 3-4 queries first, then apply patterns
2. **Use actual system**: Run test queries to see real retrieval results
3. **Be conservative**: Better to underestimate than overestimate relevance
4. **Document patterns**: Note common chunk ID patterns for efficiency
5. **Iterate**: Start with basic, evaluate, refine based on results

Your ground truth quality directly impacts the meaningfulness of all retrieval metrics!
