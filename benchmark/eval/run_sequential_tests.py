"""
Sequential RAG Testing Script
============================

This script runs all RAG pipeline tests sequentially to manage VRAM usage.
Perfect for running in the background while working on your thesis.

Each test runs completely before starting the next one, with proper cleanup.
"""

import subprocess
import sys
import time
import gc
from pathlib import Path
from datetime import datetime

def run_sequential_test(script_path, description, test_number, total_tests):
    """Run a single test script with proper cleanup."""
    print(f"\n{'='*80}")
    print(f"🚀 TEST {test_number}/{total_tests}: {description}")
    print(f"📁 Script: {script_path.name}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ TEST {test_number} COMPLETED SUCCESSFULLY")
            print(f"⏱️  Duration: {duration:.2f} seconds")
            
            # Show key output
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                # Show last few lines with key info
                for line in lines[-5:]:
                    if any(keyword in line.lower() for keyword in ['success', 'generated', 'saved', 'traces']):
                        print(f"📊 {line}")
            
            return True
        else:
            print(f"❌ TEST {test_number} FAILED")
            print(f"⏱️  Duration: {duration:.2f} seconds")
            print(f"🚨 Return code: {result.returncode}")
            
            if result.stderr:
                print("🚨 Error output:")
                for line in result.stderr.strip().split('\n')[-10:]:  # Last 10 lines
                    print(f"   {line}")
            
            return False
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ TEST {test_number} FAILED WITH EXCEPTION")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🚨 Exception: {e}")
        return False
    
    finally:
        # Force garbage collection to free memory
        gc.collect()
        print(f"🧹 Memory cleanup completed")

def main():
    """Run all RAG tests sequentially."""
    print("🧪 SEQUENTIAL RAG PIPELINE TESTING")
    print("=" * 80)
    print("This script will run all RAG tests sequentially to manage VRAM usage.")
    print("Perfect for running in the background while working on your thesis.")
    print("=" * 80)
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    
    # Define all test scripts in order of increasing complexity
    tests = [
        {
            "script": script_dir / "generate_baseline_rag_traces.py",
            "description": "Baseline RAG (no enhancements) - Lightest test"
        },
        {
            "script": script_dir / "generate_rag_reranking_traces.py", 
            "description": "RAG + Re-ranking - Medium complexity"
        },
        {
            "script": script_dir / "generate_rag_web_traces.py",
            "description": "RAG + Web Enhancement - Medium complexity"
        },
        {
            "script": script_dir / "generate_full_advanced_traces.py",
            "description": "Full Advanced RAG - Highest complexity"
        },
        {
            "script": script_dir / "generate_topk_variations_traces.py",
            "description": "Top-K Variations (12 combinations) - Longest test"
        }
    ]
    
    # Track results
    results = {}
    total_start_time = time.time()
    successful_tests = 0
    
    print(f"📋 Total tests to run: {len(tests)}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💡 Estimated total time: {len(tests) * 5} minutes (rough estimate)")
    
    # Run each test sequentially
    for i, test in enumerate(tests, 1):
        if test["script"].exists():
            success = run_sequential_test(
                test["script"], 
                test["description"], 
                i, 
                len(tests)
            )
            results[test["description"]] = success
            
            if success:
                successful_tests += 1
                print(f"✅ Test {i} completed successfully")
            else:
                print(f"❌ Test {i} failed - continuing with next test")
            
            # Add a small delay between tests for system stability
            if i < len(tests):
                print(f"⏳ Waiting 10 seconds before next test...")
                time.sleep(10)
        else:
            print(f"❌ Script not found: {test['script']}")
            results[test["description"]] = False
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print final summary
    print(f"\n{'='*80}")
    print("📊 FINAL TESTING SUMMARY")
    print(f"{'='*80}")
    print(f"⏰ Total duration: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
    print(f"📋 Total tests: {len(tests)}")
    print(f"✅ Successful: {successful_tests}")
    print(f"❌ Failed: {len(tests) - successful_tests}")
    print(f"📈 Success rate: {successful_tests/len(tests)*100:.1f}%")
    
    print(f"\n📋 Individual Results:")
    for i, (description, success) in enumerate(results.items(), 1):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {i}. {status} {description}")
    
    # Check output files
    logs_dir = Path("benchmark/logs")
    if logs_dir.exists():
        output_files = list(logs_dir.glob("*.jsonl"))
        print(f"\n📁 Generated output files ({len(output_files)}):")
        for file in sorted(output_files):
            file_size = file.stat().st_size / 1024  # Size in KB
            print(f"   📄 {file.name} ({file_size:.1f} KB)")
    
    if successful_tests == len(tests):
        print(f"\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"📊 You can now run the comprehensive evaluation:")
        print(f"   python eval/run_comprehensive_evaluation.py")
    elif successful_tests > 0:
        print(f"\n⚠️  {successful_tests}/{len(tests)} tests completed successfully.")
        print(f"📊 You can still run evaluation on the successful tests.")
    else:
        print(f"\n❌ All tests failed. Check the error messages above.")
        return 1
    
    print(f"\n💡 Next steps:")
    print(f"   1. Review the generated trace files in benchmark/logs/")
    print(f"   2. Run comprehensive evaluation: python eval/run_comprehensive_evaluation.py")
    print(f"   3. Analyze results for your thesis")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
