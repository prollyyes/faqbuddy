#!/usr/bin/env python3
"""
Timeout-Resistant RAGAS Evaluation (pandas-based)
=================================================

- Reads JSONL records with fields: question, answer, contexts[, ground_truth]
- Cleans/limits contexts and answers to reduce cost/timeouts
- Evaluates RAGAS metrics with timeout protection
- Aggregates scores correctly using pandas (weighted by number of samples)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import signal
from contextlib import contextmanager
import os

from dotenv import load_dotenv
load_dotenv()

# Configure RAGAS to use OpenAI API from env
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# --- Imports with guard
try:
    import pandas as pd
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness, 
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness,
        answer_similarity
    )
    print("✅ Imports successful (ragas, datasets, pandas)")
    print("📊 Available metrics: faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness, answer_similarity")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("💡 Make sure you have the latest ragas version: pip install ragas --upgrade")
    sys.exit(1)


# --- Timeout handling
@contextmanager
def timeout_handler(seconds: int):
    def _raise_timeout(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    old = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# --- I/O + cleaning
def load_records_safe(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if all(k in rec for k in ["question", "answer", "contexts"]):
                    records.append(rec)
                else:
                    print(f"⚠️  Skipping invalid record at line {line_num}")
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON error at line {line_num}: {e}")
    return records


def prepare_dataset_safe(records: List[Dict[str, Any]],
                         max_contexts: int = 5,
                         max_context_chars: int = 2000,
                         max_answer_chars: int = 3000) -> Dataset:
    cleaned: List[Dict[str, Any]] = []
    for i, rec in enumerate(records):
        try:
            contexts = rec.get("contexts", []) or []
            # keep only non-empty strings
            contexts = [c for c in contexts if isinstance(c, str) and c.strip()]
            if not contexts:
                print(f"⚠️  Skipping record {i+1}: No contexts")
                continue

            # limit number and size of contexts
            contexts = [c[:max_context_chars] for c in contexts[:max_contexts]]

            answer = (rec.get("answer") or "").strip()
            if not answer:
                print(f"⚠️  Skipping record {i+1}: Empty answer")
                continue
            if len(answer) > max_answer_chars:
                answer = answer[:max_answer_chars] + "..."

            cleaned.append({
                "question": rec["question"],
                "answer": answer,
                "contexts": contexts,
                # ground_truth is optional for the two metrics we use
                "ground_truth": rec.get("ground_truth", "")
            })
        except Exception as e:
            print(f"⚠️  Error processing record {i+1}: {e}")
    print(f"📊 Cleaned dataset: {len(cleaned)}/{len(records)} records")
    return Dataset.from_list(cleaned)


# --- RAGAS evaluation (pandas-based extraction)
def run_ragas_with_timeout(dataset: Dataset, timeout_seconds: int = 300
                           ) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Returns:
      - df: per-sample metric DataFrame (columns: faithfulness, answer_relevancy, context_precision, ...)
      - agg: dict with aggregated means
    """
    # Comprehensive RAGAS metrics for thesis evaluation
    metrics = [
        faithfulness,           # How factually accurate is the answer?
        answer_relevancy,       # How relevant is the answer to the question?
        context_precision,      # How precise is the retrieved context?
        context_recall,         # How much of the relevant context was retrieved?
        answer_correctness,     # How correct is the answer compared to ground truth?
        answer_similarity       # How similar is the answer to ground truth?
    ]
    
    metric_names = [m.name for m in metrics]
    print(f"⏱️ Running comprehensive RAGAS evaluation (timeout: {timeout_seconds}s, n={len(dataset)})...")
    print(f"📊 Evaluating metrics: {', '.join(metric_names)}")
    
    with timeout_handler(timeout_seconds):
        result = evaluate(dataset, metrics=metrics)
        df = result.to_pandas()  # one row per sample; columns are metrics
        
        # make sure expected columns exist
        missing = [c for c in metric_names if c not in df.columns]
        if missing:
            raise RuntimeError(f"RAGAS did not return expected columns: {missing}")

        # aggregated means
        agg = {m: float(df[m].mean()) for m in metric_names}
        return df, agg


def main():
    parser = argparse.ArgumentParser(description="Run timeout-resistant RAGAS evaluation (pandas-based)")
    parser.add_argument("--records", required=True, help="Path to JSONL trace file")
    parser.add_argument("--out", default="ragas_results.json", help="Output JSON for aggregated results")
    parser.add_argument("--csv", default=None, help="Optional CSV path for per-sample metrics")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout (seconds) per batch evaluation")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    args = parser.parse_args()

    print("🔍 Loading and cleaning records...")
    records = load_records_safe(Path(args.records))
    if not records:
        print("❌ No valid records found")
        return 1

    total = len(records)
    batch_size = max(1, args.batch_size)
    n_batches = (total - 1) // batch_size + 1
    print(f"📦 Records: {total} | Batch size: {batch_size} | Batches: {n_batches}")

    # Accumulators
    all_rows: List[pd.DataFrame] = []
    # for weighted aggregation across batches - all 6 comprehensive metrics
    sum_metrics = {
        "faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "context_precision": 0.0,
        "context_recall": 0.0,
        "answer_correctness": 0.0,
        "answer_similarity": 0.0
    }
    n_samples_total = 0
    batches_ok = 0

    for i in range(0, total, batch_size):
        batch_idx = i // batch_size + 1
        batch = records[i:i + batch_size]
        print(f"\n🔄 Processing batch {batch_idx}/{n_batches} ({len(batch)} records)")

        try:
            ds = prepare_dataset_safe(batch)
            if len(ds) == 0:
                print("⚠️ Empty batch after cleaning, skipping…")
                continue

            df, agg = run_ragas_with_timeout(ds, args.timeout)
            # track rows for CSV (optional)
            # keep original indexing across whole file
            df = df.reset_index(drop=True)
            all_rows.append(df)

            # weighted sum
            n_samples = len(df)
            for k in sum_metrics:
                sum_metrics[k] += agg[k] * n_samples
            n_samples_total += n_samples

            batches_ok += 1
            print(f"✅ Batch done: n={n_samples}")
            print(f"   📊 Faithfulness: {agg['faithfulness']:.3f}, Answer Relevancy: {agg['answer_relevancy']:.3f}")
            print(f"   📊 Context Precision: {agg['context_precision']:.3f}, Context Recall: {agg['context_recall']:.3f}")
            print(f"   📊 Answer Correctness: {agg['answer_correctness']:.3f}, Answer Similarity: {agg['answer_similarity']:.3f}")

        except TimeoutError:
            print("❌ RAGAS evaluation timed out for this batch")
        except Exception as e:
            print(f"❌ Batch failed: {e}")

    if batches_ok == 0 or n_samples_total == 0:
        print("\n❌ All batches failed or yielded zero samples")
        return 1

    # Final weighted means - comprehensive metrics
    final_results = {
        "faithfulness": sum_metrics["faithfulness"] / n_samples_total,
        "answer_relevancy": sum_metrics["answer_relevancy"] / n_samples_total,
        "context_precision": sum_metrics["context_precision"] / n_samples_total,
        "context_recall": sum_metrics["context_recall"] / n_samples_total,
        "answer_correctness": sum_metrics["answer_correctness"] / n_samples_total,
        "answer_similarity": sum_metrics["answer_similarity"] / n_samples_total,
        "samples_evaluated": n_samples_total,
        "batches_processed": batches_ok,
        "total_batches": n_batches,
        "success_rate": batches_ok / n_batches,
        # Composite scores for easier analysis
        "retrieval_quality": (sum_metrics["context_precision"] + sum_metrics["context_recall"]) / (2 * n_samples_total),
        "answer_quality": (sum_metrics["answer_correctness"] + sum_metrics["answer_similarity"]) / (2 * n_samples_total),
        "overall_score": (sum_metrics["faithfulness"] + sum_metrics["answer_relevancy"] + 
                         sum_metrics["context_precision"] + sum_metrics["context_recall"] +
                         sum_metrics["answer_correctness"] + sum_metrics["answer_similarity"]) / (6 * n_samples_total)
    }

    # Save aggregated JSON
    with open(args.out, "w") as f:
        json.dump(final_results, f, indent=2)
    print("\n✅ COMPREHENSIVE RAGAS EVALUATION COMPLETED")
    print("="*60)
    print("📊 FINAL RESULTS:")
    print(f"   Faithfulness: {final_results['faithfulness']:.3f}")
    print(f"   Answer Relevancy: {final_results['answer_relevancy']:.3f}")
    print(f"   Context Precision: {final_results['context_precision']:.3f}")
    print(f"   Context Recall: {final_results['context_recall']:.3f}")
    print(f"   Answer Correctness: {final_results['answer_correctness']:.3f}")
    print(f"   Answer Similarity: {final_results['answer_similarity']:.3f}")
    print("="*60)
    print("📈 COMPOSITE SCORES:")
    print(f"   Retrieval Quality: {final_results['retrieval_quality']:.3f}")
    print(f"   Answer Quality: {final_results['answer_quality']:.3f}")
    print(f"   Overall Score: {final_results['overall_score']:.3f}")
    print("="*60)
    print(f"💾 Saved aggregated JSON to: {args.out}")

    # Optional per-sample CSV
    if args.csv and all_rows:
        full_df = pd.concat(all_rows, ignore_index=True)
        # Keep only metric columns and (if present) identifiers
        metric_cols = [c for c in full_df.columns if c in (
            "faithfulness", "answer_relevancy", "context_precision", 
            "context_recall", "answer_correctness", "answer_similarity"
        )]
        # RAGAS may also include question/answer columns depending on version; save if present
        extra_cols = [c for c in ["question", "answer"] if c in full_df.columns]
        out_cols = extra_cols + metric_cols if metric_cols else full_df.columns.tolist()
        full_df[out_cols].to_csv(args.csv, index=False)
        print(f"🧾 Saved per-sample metrics CSV to: {args.csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
