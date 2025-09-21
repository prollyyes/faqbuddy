#!/usr/bin/env python3
"""
Import Utilities for Benchmark Scripts
=====================================

This module provides consistent import path handling for all benchmark scripts.
It ensures that all scripts can import from the backend modules regardless of
where they are run from.
"""

import sys
import os
from pathlib import Path
from typing import Optional

def setup_backend_imports():
    """
    Setup proper import paths for backend modules.
    
    This function should be called at the beginning of any benchmark script
    that needs to import from the backend.
    """
    # Get the project root (faqbuddy directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # benchmark/eval -> benchmark -> faqbuddy
    backend_src = project_root / "backend" / "src"
    
    # Add backend/src to Python path if not already there
    backend_src_str = str(backend_src)
    if backend_src_str not in sys.path:
        sys.path.insert(0, backend_src_str)
    
    # Also add project root for any absolute imports
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root, backend_src

def setup_benchmark_imports():
    """
    Setup proper import paths for benchmark modules.
    
    This allows importing benchmark modules from other benchmark scripts.
    """
    current_file = Path(__file__).resolve()
    benchmark_dir = current_file.parent.parent  # benchmark/eval -> benchmark
    benchmark_eval_dir = current_file.parent    # benchmark/eval
    
    # Add benchmark directories to Python path
    for path in [str(benchmark_dir), str(benchmark_eval_dir)]:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    return benchmark_dir, benchmark_eval_dir

def find_project_root() -> Path:
    """
    Find the project root directory by looking for characteristic files.
    
    Returns:
        Path to the project root directory
    """
    current = Path(__file__).resolve()
    
    # Look for characteristic files that indicate project root
    markers = [
        "backend/src/main.py",
        "frontend/package.json", 
        "README.md",
        ".env",
        "requirements.txt"
    ]
    
    # Walk up the directory tree
    for parent in [current.parent.parent.parent] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent
    
    # Fallback: assume we're in benchmark/eval and go up 2 levels
    return current.parent.parent.parent

def load_env_file(env_path: Optional[Path] = None):
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Optional path to .env file. If None, searches for it.
    """
    try:
        from dotenv import load_dotenv
        
        if env_path is None:
            # Try to find .env file in project root
            project_root = find_project_root()
            env_path = project_root / ".env"
        
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path))
            return True
        else:
            # Try loading from current directory or parent directories
            load_dotenv()
            return True
            
    except ImportError:
        print("⚠️ Warning: python-dotenv not available, environment variables may not be loaded")
        return False
    except Exception as e:
        print(f"⚠️ Warning: Could not load .env file: {e}")
        return False

def safe_import_backend_module(module_path: str, fallback_error_msg: str = None):
    """
    Safely import a backend module with proper error handling.
    
    Args:
        module_path: The module path to import (e.g., 'rag.advanced_rag_pipeline')
        fallback_error_msg: Custom error message if import fails
        
    Returns:
        The imported module or None if import failed
    """
    try:
        setup_backend_imports()
        
        # Dynamic import
        import importlib
        module = importlib.import_module(module_path)
        return module
        
    except ImportError as e:
        error_msg = fallback_error_msg or f"Could not import {module_path}: {e}"
        print(f"❌ Import Error: {error_msg}")
        print("💡 Make sure you're running from the project root and all dependencies are installed")
        return None
    except Exception as e:
        print(f"❌ Unexpected error importing {module_path}: {e}")
        return None

def get_benchmark_paths():
    """
    Get commonly used paths for benchmark scripts.
    
    Returns:
        Dictionary with common paths
    """
    project_root = find_project_root()
    
    return {
        'project_root': project_root,
        'benchmark_dir': project_root / 'benchmark',
        'benchmark_eval_dir': project_root / 'benchmark' / 'eval',
        'benchmark_data_dir': project_root / 'benchmark' / 'data',
        'benchmark_logs_dir': project_root / 'benchmark' / 'logs',
        'benchmark_results_dir': project_root / 'benchmark' / 'eval_results',
        'backend_src_dir': project_root / 'backend' / 'src',
        'testset_file': project_root / 'benchmark' / 'data' / 'testset.jsonl',
        'ground_truth_file': project_root / 'benchmark' / 'data' / 'ground_truth.json'
    }

# Auto-setup when module is imported
try:
    setup_backend_imports()
    setup_benchmark_imports()
    load_env_file()
except Exception as e:
    print(f"⚠️ Warning: Could not auto-setup imports: {e}")
