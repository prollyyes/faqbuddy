# RAG Benchmark Boilerplate

A minimal setup to benchmark a Retrieval‑Augmented Generation (RAG) system
before and after changes (e.g., switching to row‑level vectors + graph).

## What’s inside

```
rag_bench/
├── data/
│   └── testset.jsonl      # Gold or synthetic Q‑A pairs + ground‑truth docs
├── eval/
│   ├── __init__.py
│   └── run_ragas.py       # Offline batch evaluation script
├── requirements.txt       # Pin versions for reproducibility
└── README.md
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Generate or collect your test traces (baseline.jsonl, variant.jsonl)
python eval/run_ragas.py --records logs/baseline.jsonl --out baseline_metrics.json
```

The script prints faithfulness, context‑recall and answer‑relevancy, and saves
the full metric JSON so you can compare runs in MLflow or W&B.

## JSONL schemas

### Test set (`data/testset.jsonl`)

```jsonc
{
  "question": "Which courses is Prof. Rossi teaching this fall?",
  "ground_truth": "CS101, CS305",
  "contexts": [
    "Professor Maria Rossi teaches CS101 Intro to Programming...",
    "Professor Maria Rossi teaches CS305 Databases..."
  ]
}
```

### Inference trace (`logs/*.jsonl`)

This is what your app should log per user turn:

```jsonc
{
  "question": "...",
  "contexts": ["doc snippet 1", "doc snippet 2", "..."],
  "answer": "LLM reply here",
  "ground_truth": "optional if known"
}
```

## Extend

* Add more `ragas.metrics.*` in `eval/run_ragas.py`.
* Replace RAGAS with DeepEval or TruLens by dropping in their imports.
* Wire the script into CI via GitHub Actions.