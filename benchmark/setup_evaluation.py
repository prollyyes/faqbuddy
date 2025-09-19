#!/usr/bin/env python3
"""
Setup Script for Comprehensive RAG Evaluation
=============================================

This script sets up the evaluation environment and checks for required dependencies.
"""

import sys
import subprocess
import pkg_resources
from pathlib import Path

REQUIRED_PACKAGES = [
    'sentence-transformers>=2.0.0',
    'datasets>=2.0.0',
    'scikit-learn>=1.0.0',
    'numpy>=1.20.0',
    'pandas>=1.3.0'
]

OPTIONAL_PACKAGES = [
    'ragas>=0.1.0'  # For RAGAS evaluation
]

def check_python_version():
    """Check if Python version is adequate."""
    if sys.version_info < (3, 8):
        print("========== Python 3.8 or higher is required ==========")
        return False
    
    print(f"========== Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} ==========")
    return True

def check_package(package_spec):
    """Check if a package is installed and meets version requirements."""
    try:
        pkg_resources.require([package_spec])
        return True
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
        return False

def install_package(package_spec):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_spec])
        return True
    except subprocess.CalledProcessError:
        return False

def setup_directories():
    """Create required directories."""
    directories = [
        'benchmark/data',
        'benchmark/logs', 
        'benchmark/eval_results'
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"========== Created directory: {dir_path} ==========")

def create_basic_testset():
    """Create a basic testset if it doesn't exist."""
    testset_path = Path("benchmark/data/testset.jsonl")
    
    if testset_path.exists():
        print(f"========== Testset already exists: {testset_path} ==========")
        return
    
    # Create basic testset from existing data if available
    existing_testset = Path("benchmark/data/testset.jsonl")
    if not existing_testset.exists():
        # Create minimal example testset
        basic_testset = [
            {"question": "Quali corsi insegna il prof Lenzerini?", "ground_truth": "Basi di Dati"},
            {"question": "Come si chiama di nome il prof Lenzerini?", "ground_truth": "Maurizio"},
            {"question": "Da quanti crediti è il corso di Basi di Dati?", "ground_truth": "6"}
        ]
        
        with open(testset_path, 'w', encoding='utf-8') as f:
            for item in basic_testset:
                f.write(f"{item}\n".replace("'", '"'))
        
        print(f"========== Created basic testset: {testset_path} ==========")

def main():
    """Main setup function."""
    print("========== Setting up Comprehensive RAG Evaluation Environment ==========")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check and install required packages
    print("\n========== Checking required packages... ==========")
    missing_required = []
    
    for package in REQUIRED_PACKAGES:
        if check_package(package):
            print(f"========== {package} ==========")
        else:
            print(f"========== {package} - Missing ==========")
            missing_required.append(package)
    
    # Install missing required packages
    if missing_required:
        print(f"\n========== Installing {len(missing_required)} missing packages... ==========")
        for package in missing_required:
            print(f"   Installing {package}...")
            if install_package(package):
                print(f"    ========= Installed {package} ==========")
            else:
                print(f"    ========= Failed to install {package} ==========")
                return 1
    
    # Check optional packages
    print("\n========== Checking optional packages... ==========")
    for package in OPTIONAL_PACKAGES:
        if check_package(package):
            print(f"========== {package} ==========")
        else:
            print(f"==========  {package} - Optional, install with: pip install {package}")
    
    # Setup directories
    print("\n========== Setting up directories... ==========")
    setup_directories()
    
    # Create basic testset
    print("\n========== Setting up test data... ==========")
    create_basic_testset()
    
    # Final verification
    print("\n========== Final verification... ==========")
    
    # Check if evaluation modules can be imported
    try:
        sys.path.insert(0, str(Path("benchmark/eval")))
        import enhanced_metrics
        import enhanced_trace_generator
        import comprehensive_evaluator
        print("========== All evaluation modules can be imported ==========")
    except ImportError as e:
        print(f"========== Import error: {e} ==========")
        return 1
    
    print("\n========== Setup completed successfully! ==========")
    print("\n========== Next steps: ==========")
    print("1. Review the testset in benchmark/data/testset.jsonl")
    print("2. Run: python benchmark/run_comprehensive_evaluation.py --mode full")
    print("3. Check results in benchmark/eval_results/")
    print("\n========== See benchmark/README_COMPREHENSIVE_EVALUATION.md for detailed usage ==========")
    
    return 0

if __name__ == "__main__":
    exit(main())
