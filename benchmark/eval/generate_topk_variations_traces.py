"""
Generate Top-K Variations traces for benchmarking
=================================================

This script generates test traces for full advanced setup with different top-k values
and MAX_CHUNKS configurations:
- Top-K values: 10, 20, 50, 75
- MAX_CHUNKS values: 3, 5, 7
- All advanced features enabled
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

# Set environment variables for full advanced configuration
os.environ["RERANKER_ENABLED"] = "true"
os.environ["WEB_SEARCH_ENHANCEMENT"] = "true"
os.environ["HALLUCINATION_GUARDS"] = "true"
os.environ["SCHEMA_AWARE_CHUNKING"] = "true"
os.environ["INSTRUCTOR_XL_EMBEDDINGS"] = "true"

from backend.src.rag.rag_pipeline_v2 import RAGv2Pipeline

def generate_topk_variations_traces():
    """Generate top-k variations traces for evaluation."""
    print("🔧 Generating Top-K Variations traces...")
    print("📋 Configuration:")
    print("   - All advanced features: ✅ Enabled")
    print("   - Top-K values: [10, 20, 50, 75]")
    print("   - MAX_CHUNKS values: [3, 5, 7]")
    print("   - Total combinations: 12")
    
    # Load test dataset
    testset_path = Path("benchmark/data/testset.jsonl")
    with testset_path.open("r") as f:
        testset = [json.loads(line) for line in f]
    
    print(f"📊 Loaded {len(testset)} test questions")
    
    # Define test configurations
    top_k_values = [10, 20, 50, 75]
    max_chunks_values = [3, 5, 7]
    
    out_dir = Path("benchmark/logs")
    out_dir.mkdir(exist_ok=True)
    
    all_results = {}
    
    for top_k in top_k_values:
        for max_chunks in max_chunks_values:
            config_name = f"topk_{top_k}_chunks_{max_chunks}"
            print(f"\n🔍 Testing configuration: {config_name}")
            print(f"   Top-K: {top_k}, MAX_CHUNKS: {max_chunks}")
            
            # Initialize pipeline with specific configuration
            pipeline = RAGv2Pipeline(top_k=top_k)
            
            # Override MAX_CONTEXT_TOKENS based on max_chunks
            # This is a rough approximation - you might need to adjust based on your actual implementation
            max_context_tokens = max_chunks * 400  # Assuming ~400 tokens per chunk
            os.environ["MAX_CONTEXT_TOKENS"] = str(max_context_tokens)
            
            records = []
            for i, item in enumerate(testset, 1):
                question = item["question"]
                ground_truth = item.get("ground_truth", "")
                
                print(f"   🔍 Processing question {i}/{len(testset)}: {question}")
                
                try:
                    result = pipeline.answer(question)
                    answer = result.get("answer", "")
                    contexts = [doc.get("text", "") for doc in result.get("retrieval_results", []) if doc.get("text")]
                    
                    # Limit contexts to max_chunks
                    contexts = contexts[:max_chunks]
                    
                    record = {
                        "question": question,
                        "ground_truth": ground_truth,
                        "answer": answer,
                        "contexts": contexts,
                        "config": config_name,
                        "top_k": top_k,
                        "max_chunks": max_chunks,
                        "max_context_tokens": max_context_tokens,
                        "features_used": result.get("features_used", {}),
                        "retrieval_stats": result.get("retrieval_stats", {}),
                        "retrieved_documents": result.get("retrieved_documents", 0),
                        "actual_contexts_used": len(contexts)
                    }
                    
                    records.append(record)
                    print(f"      ✅ Generated answer ({len(answer)} chars, {len(contexts)} contexts)")
                    
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    # Still add a record for failed cases
                    records.append({
                        "question": question,
                        "ground_truth": ground_truth,
                        "answer": f"Error: {str(e)}",
                        "contexts": [],
                        "config": config_name,
                        "top_k": top_k,
                        "max_chunks": max_chunks,
                        "max_context_tokens": max_context_tokens,
                        "error": str(e)
                    })
            
            # Save results for this configuration
            output_file = out_dir / f"{config_name}.jsonl"
            
            with output_file.open("w") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
            # Calculate statistics for this configuration
            successful = len([r for r in records if "error" not in r])
            success_rate = successful / len(records) if records else 0
            
            all_results[config_name] = {
                "output_file": str(output_file),
                "total_questions": len(records),
                "successful_questions": successful,
                "success_rate": success_rate,
                "top_k": top_k,
                "max_chunks": max_chunks,
                "max_context_tokens": max_context_tokens
            }
            
            print(f"   ✅ {config_name} traces saved to {output_file}")
            print(f"   📊 Generated {len(records)} traces")
            print(f"   📈 Success rate: {successful}/{len(records)} ({success_rate*100:.1f}%)")
    
    # Save summary of all configurations
    summary_file = out_dir / "topk_variations_summary.json"
    with summary_file.open("w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ All Top-K variations completed!")
    print(f"📊 Summary saved to {summary_file}")
    print(f"📈 Total configurations tested: {len(all_results)}")
    
    # Print overall statistics
    total_questions = sum(r["total_questions"] for r in all_results.values())
    total_successful = sum(r["successful_questions"] for r in all_results.values())
    overall_success_rate = total_successful / total_questions if total_questions > 0 else 0
    
    print(f"📈 Overall success rate: {total_successful}/{total_questions} ({overall_success_rate*100:.1f}%)")
    
    # Print best performing configurations
    sorted_configs = sorted(all_results.items(), key=lambda x: x[1]["success_rate"], reverse=True)
    print(f"\n🏆 Top 3 performing configurations:")
    for i, (config_name, stats) in enumerate(sorted_configs[:3], 1):
        print(f"   {i}. {config_name}: {stats['success_rate']*100:.1f}% success rate")
    
    return all_results

if __name__ == "__main__":
    generate_topk_variations_traces()
