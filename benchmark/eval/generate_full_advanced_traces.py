"""
Generate Full Advanced RAG traces for benchmarking
=================================================

This script generates test traces for the full advanced RAG setup:
- All features enabled (re-ranking, web enhancement, guards, etc.)
- Uses the AdvancedRAGPipeline with all components
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

from backend.src.rag.advanced_rag_pipeline import AdvancedRAGPipeline

def generate_full_advanced_traces():
    """Generate full advanced RAG traces for evaluation."""
    print("🔧 Generating Full Advanced RAG traces...")
    print("📋 Configuration:")
    print("   - Re-ranking: ✅ Enabled")
    print("   - Web enhancement: ✅ Enabled") 
    print("   - Generation guards: ✅ Enabled")
    print("   - Schema-aware chunking: ✅ Enabled")
    print("   - Enhanced embeddings: ✅ Enabled")
    print("   - Query understanding: ✅ Enabled")
    print("   - Advanced prompt engineering: ✅ Enabled")
    print("   - Answer verification: ✅ Enabled")
    print("   - Full Advanced RAG Pipeline: ✅")
    
    # Load test dataset
    testset_path = Path("benchmark/data/testset.jsonl")
    with testset_path.open("r") as f:
        testset = [json.loads(line) for line in f]
    
    print(f"📊 Loaded {len(testset)} test questions")
    
    # Initialize full advanced pipeline
    pipeline = AdvancedRAGPipeline()
    
    records = []
    for i, item in enumerate(testset, 1):
        question = item["question"]
        ground_truth = item.get("ground_truth", "")
        
        print(f"🔍 Processing question {i}/{len(testset)}: {question}")
        
        try:
            result = pipeline.answer(question)
            answer = result.answer
            contexts = [doc.get("text", "") for doc in result.retrieval_results if doc.get("text")]
            
            record = {
                "question": question,
                "ground_truth": ground_truth,
                "answer": answer,
                "contexts": contexts,
                "config": "full_advanced",
                "features_used": result.features_used,
                "query_analysis": {
                    "intent": result.query_analysis.intent.value,
                    "complexity": result.query_analysis.complexity.value,
                    "entities": result.query_analysis.entities,
                    "requires_reasoning": result.query_analysis.requires_reasoning,
                    "confidence": result.query_analysis.confidence
                },
                "verification_result": {
                    "is_verified": result.verification_result.is_verified,
                    "confidence_score": result.verification_result.confidence_score,
                    "fact_check_score": result.verification_result.fact_check_score,
                    "hallucination_risk": result.verification_result.hallucination_risk
                },
                "processing_time": result.processing_time,
                "confidence_score": result.confidence_score,
                "retrieved_documents": len(result.retrieval_results)
            }
            
            records.append(record)
            print(f"   ✅ Generated answer ({len(answer)} chars, confidence: {result.confidence_score:.3f})")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Still add a record for failed cases
            records.append({
                "question": question,
                "ground_truth": ground_truth,
                "answer": f"Error: {str(e)}",
                "contexts": [],
                "config": "full_advanced",
                "error": str(e)
            })
    
    # Save results
    out_dir = Path("benchmark/logs")
    out_dir.mkdir(exist_ok=True)
    output_file = out_dir / "full_advanced.jsonl"
    
    with output_file.open("w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"\n✅ Full Advanced RAG traces saved to {output_file}")
    print(f"📊 Generated {len(records)} traces")
    
    # Print summary statistics
    successful = len([r for r in records if "error" not in r])
    if successful > 0:
        avg_confidence = sum(r.get("confidence_score", 0) for r in records if "error" not in r) / successful
        verified_count = sum(1 for r in records if r.get("verification_result", {}).get("is_verified", False))
        print(f"📈 Success rate: {successful}/{len(records)} ({successful/len(records)*100:.1f}%)")
        print(f"📈 Average confidence: {avg_confidence:.3f}")
        print(f"📈 Verification rate: {verified_count}/{successful} ({verified_count/successful*100:.1f}%)")
    else:
        print(f"📈 Success rate: 0/{len(records)} (0.0%)")
    
    return output_file

if __name__ == "__main__":
    generate_full_advanced_traces()
