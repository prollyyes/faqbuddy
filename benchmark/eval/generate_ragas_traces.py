import json
import sys
from pathlib import Path

# Setup imports
sys.path.insert(0, str(Path(__file__).parent))  # Add eval directory for import_utils
from import_utils import setup_backend_imports, load_env_file, get_benchmark_paths
setup_backend_imports()
load_env_file()

from rag.rag_pipeline_v2 import RAGv2Pipeline

# Get paths
paths = get_benchmark_paths()
testset_path = paths['testset_file']

with testset_path.open("r") as f:
    testset = [json.loads(line) for line in f]

pipeline = RAGv2Pipeline()

records = []
for item in testset:
    question = item["question"]
    ground_truth = item.get("ground_truth", "")
    result = pipeline.answer(question)
    answer = result.get("answer", "")
    contexts = [doc.get("text", "") for doc in result.get("retrieval_results", []) if doc.get("text")]
    records.append({
        "question": question,
        "ground_truth": ground_truth,
        "answer": answer,
        "contexts": contexts
    })

out_dir = paths['benchmark_logs_dir']
out_dir.mkdir(exist_ok=True)
with (out_dir / "baseline.jsonl").open("w") as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")