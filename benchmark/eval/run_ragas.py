from dotenv import load_dotenv
load_dotenv(dotenv_path="/Users/Edoardo/Documents/Sapienza ING_INF/Thesis_Actual/faqbuddy/.env")

import argparse
import json
import pathlib
import sys
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy # no context_recall for now

def load_records(path: pathlib.Path):
    with path.open() as f:
        for line in f:
            yield json.loads(line)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", required=True, help="JSONL trace from your app")
    parser.add_argument("--out", default="metrics.json", help="Where to dump metric JSON")
    args = parser.parse_args()

    records = list(load_records(pathlib.Path(args.records)))
    if not records:
        print("No records loaded", file=sys.stderr); sys.exit(1)

    # Debug: Print first record
    print("First record:", records[0])
    print("Dataset columns:", list(records[0].keys()))

    # Convert to HuggingFace Dataset
    dataset = Dataset.from_list(records)

    metrics = [faithfulness, answer_relevancy] # no context_recall for now
    print("Using metrics:", [m.__class__.__name__ for m in metrics])
    
    result = evaluate(dataset, metrics=metrics)

    print("\n=== RAGAS scores ===")
    print(result)
    # Only keep the top-level float/int/str metrics (ignore lists/dicts that aren't serializable)
    main_scores = {}
    for k, v in result.__dict__.items():
        if isinstance(v, (float, int, str)):
            main_scores[k] = v

    pathlib.Path(args.out).write_text(json.dumps(main_scores, indent=2, ensure_ascii=False))
    print(f"\nSaved detailed metrics to {args.out}")

if __name__ == "__main__":
    main()