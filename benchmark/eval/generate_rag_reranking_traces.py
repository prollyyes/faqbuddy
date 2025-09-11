"""
Generate RAG + Re-ranking traces for benchmarking
================================================

This script generates test traces for RAG with re-ranking enabled:
- Re-ranking: ✅ Enabled
- No web enhancement
- No generation guards
- Pinecone + re-ranking + generation
"""

import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Set environment variables for RAG + re-ranking configuration
os.environ["RERANKER_ENABLED"] = "true"
os.environ["WEB_SEARCH_ENHANCEMENT"] = "false"
os.environ["HALLUCINATION_GUARDS"] = "false"
os.environ["SCHEMA_AWARE_CHUNKING"] = "false"
os.environ["INSTRUCTOR_XL_EMBEDDINGS"] = "false"

from backend.src.rag.rag_pipeline_v2 import RAGv2Pipeline

def generate_rag_reranking_traces():
    """Generate RAG + re-ranking traces for evaluation."""
    print("🔧 Generating RAG + Re-ranking traces...")
    print("📋 Configuration:")
    print("   - Re-ranking: ✅ Enabled")
    print("   - Web enhancement: ❌ Disabled") 
    print("   - Generation guards: ❌ Disabled")
    print("   - Schema-aware chunking: ❌ Disabled")
    print("   - Enhanced embeddings: ❌ Disabled")
    print("   - Pinecone + re-ranking + generation: ✅")
    
    # Load test dataset
    testset_path = Path("benchmark/data/testset.jsonl")
    with testset_path.open("r") as f:
        testset = [json.loads(line) for line in f]
    
    print(f"📊 Loaded {len(testset)} test questions")
    
    # Initialize pipeline with re-ranking
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
                "config": "rag_reranking",
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
                "config": "rag_reranking",
                "error": str(e)
            })
    
    # Save results
    out_dir = Path("benchmark/logs")
    out_dir.mkdir(exist_ok=True)
    output_file = out_dir / "rag_reranking.jsonl"
    
    with output_file.open("w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"\n✅ RAG + Re-ranking traces saved to {output_file}")
    print(f"📊 Generated {len(records)} traces")
    
    # Print summary statistics
    successful = len([r for r in records if "error" not in r])
    print(f"📈 Success rate: {successful}/{len(records)} ({successful/len(records)*100:.1f}%)")
    
    return output_file

if __name__ == "__main__":
    generate_rag_reranking_traces()
