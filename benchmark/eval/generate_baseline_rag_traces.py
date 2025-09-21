"""
Generate baseline RAG traces for benchmarking
============================================

This script generates test traces for the baseline RAG configuration:
- No re-ranking
- No web enhancement  
- No generation guards
- Just Pinecone + generation
"""

import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Setup imports
sys.path.insert(0, str(Path(__file__).parent))  # Add eval directory for import_utils
from import_utils import setup_backend_imports, load_env_file, get_benchmark_paths
setup_backend_imports()
load_env_file()

# Set environment variables for baseline configuration
os.environ["RERANKER_ENABLED"] = "false"
os.environ["WEB_SEARCH_ENHANCEMENT"] = "false"
os.environ["HALLUCINATION_GUARDS"] = "false"
os.environ["SCHEMA_AWARE_CHUNKING"] = "false"
os.environ["INSTRUCTOR_XL_EMBEDDINGS"] = "false"

from rag.rag_pipeline_v2 import RAGv2Pipeline

def generate_baseline_traces():
    """Generate baseline RAG traces for evaluation."""
    print("🔧 Generating baseline RAG traces...")
    print("📋 Configuration:")
    print("   - Re-ranking: ❌ Disabled")
    print("   - Web enhancement: ❌ Disabled") 
    print("   - Generation guards: ❌ Disabled")
    print("   - Schema-aware chunking: ❌ Disabled")
    print("   - Enhanced embeddings: ❌ Disabled")
    print("   - Just Pinecone + generation: ✅")
    
    # Load test dataset
    paths = get_benchmark_paths()
    testset_path = paths['testset_file']
    with testset_path.open("r") as f:
        testset = [json.loads(line) for line in f]
    
    print(f"📊 Loaded {len(testset)} test questions")
    
    # Initialize baseline pipeline
    pipeline = RAGv2Pipeline(top_k=5)
    
    records = []
    for i, item in enumerate(testset, 1):
        question = item["question"]
        ground_truth = item.get("ground_truth", "")
        
        print(f"🔍 Processing question {i}/{len(testset)}: {question}")
        
        try:
            result = pipeline.answer(question)
            answer = result.get("answer", "")
            contexts = [doc.get("text", "") for doc in result.get("retrieval_results", []) if doc.get("text")]
            
            record = {
                "question": question,
                "ground_truth": ground_truth,
                "answer": answer,
                "contexts": contexts,
                "config": "baseline_rag",
                "features_used": result.get("features_used", {}),
                "retrieval_stats": result.get("retrieval_stats", {}),
                "retrieved_documents": result.get("retrieved_documents", 0)
            }
            
            records.append(record)
            print(f"   ✅ Generated answer ({len(answer)} chars)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Still add a record for failed cases
            records.append({
                "question": question,
                "ground_truth": ground_truth,
                "answer": f"Error: {str(e)}",
                "contexts": [],
                "config": "baseline_rag",
                "error": str(e)
            })
    
    # Save results
    out_dir = paths['benchmark_logs_dir']
    out_dir.mkdir(exist_ok=True)
    output_file = out_dir / "baseline_rag.jsonl"
    
    with output_file.open("w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"\n✅ Baseline RAG traces saved to {output_file}")
    print(f"📊 Generated {len(records)} traces")
    
    # Print summary statistics
    successful = len([r for r in records if "error" not in r])
    print(f"📈 Success rate: {successful}/{len(records)} ({successful/len(records)*100:.1f}%)")
    
    return output_file

if __name__ == "__main__":
    generate_baseline_traces()
