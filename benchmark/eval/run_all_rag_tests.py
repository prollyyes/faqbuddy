"""
Master script to run all RAG pipeline tests
==========================================

This script runs all the different RAG pipeline configurations for comprehensive benchmarking:
1. Baseline RAG (no enhancements)
2. RAG + Re-ranking
3. RAG + Web Enhancement
4. Full Advanced RAG
5. Top-K Variations (12 combinations)

All results are saved with descriptive filenames for easy analysis.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_script(script_path, description):
    """Run a test script and handle errors."""
    print(f"\n{'='*60}")
    print(f"🚀 Running: {description}")
    print(f"📁 Script: {script_path}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully in {duration:.2f}s")
            if result.stdout:
                print("📊 Output:")
                print(result.stdout)
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            if result.stderr:
                print("🚨 Error output:")
                print(result.stderr)
            if result.stdout:
                print("📊 Standard output:")
                print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ {description} failed with exception: {e}")
        return False

def main():
    """Run all RAG pipeline tests."""
    print("🧪 RAG Pipeline Comprehensive Testing Suite")
    print("=" * 60)
    print("This will run all RAG pipeline configurations for benchmarking:")
    print("1. Baseline RAG (no enhancements)")
    print("2. RAG + Re-ranking")
    print("3. RAG + Web Enhancement")
    print("4. Full Advanced RAG")
    print("5. Top-K Variations (12 combinations)")
    print("=" * 60)
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    
    # Define all test scripts
    tests = [
        {
            "script": script_dir / "generate_baseline_rag_traces.py",
            "description": "Baseline RAG (no re-ranking, no web, no guards)"
        },
        {
            "script": script_dir / "generate_rag_reranking_traces.py", 
            "description": "RAG + Re-ranking"
        },
        {
            "script": script_dir / "generate_rag_web_traces.py",
            "description": "RAG + Web Enhancement"
        },
        {
            "script": script_dir / "generate_full_advanced_traces.py",
            "description": "Full Advanced RAG (all features)"
        },
        {
            "script": script_dir / "generate_topk_variations_traces.py",
            "description": "Top-K Variations (12 combinations)"
        }
    ]
    
    # Track results
    results = {}
    total_start_time = time.time()
    
    for test in tests:
        if test["script"].exists():
            success = run_script(test["script"], test["description"])
            results[test["description"]] = success
        else:
            print(f"❌ Script not found: {test['script']}")
            results[test["description"]] = False
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TESTING SUMMARY")
    print(f"{'='*60}")
    
    successful_tests = sum(1 for success in results.values() if success)
    total_tests = len(results)
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
    print(f"Total duration: {total_duration:.2f}s")
    
    print(f"\n📋 Individual Results:")
    for description, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {description}")
    
    # Check output files
    logs_dir = Path("benchmark/logs")
    if logs_dir.exists():
        output_files = list(logs_dir.glob("*.jsonl"))
        print(f"\n📁 Generated output files ({len(output_files)}):")
        for file in sorted(output_files):
            print(f"   📄 {file.name}")
    
    if successful_tests == total_tests:
        print(f"\n🎉 All tests completed successfully!")
        print(f"📊 You can now run Ragas evaluation on the generated traces.")
        print(f"💡 Use: python eval/run_ragas.py --records logs/[filename].jsonl --out [results].json")
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
