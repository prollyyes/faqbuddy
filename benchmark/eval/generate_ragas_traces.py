import json
import sys
from pathlib import Path
# add the project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from backend.src.rag.rag_pipeline_v2 import RAGv2Pipeline

testset_path = Path("benchmark/data/testset.jsonl")
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

out_dir = Path("benchmark/logs")
out_dir.mkdir(exist_ok=True)
with (out_dir / "baseline.jsonl").open("w") as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")