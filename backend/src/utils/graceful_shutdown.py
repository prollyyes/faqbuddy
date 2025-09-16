"""
Graceful shutdown utilities to prevent semaphore leaks and ensure proper cleanup.
"""

import signal
import sys
import atexit
import gc
import os
from typing import Callable, List

# List of cleanup functions to call on shutdown
_cleanup_functions: List[Callable] = []
_shutdown_initiated = False

def register_cleanup_function(func: Callable):
    """Register a function to be called during graceful shutdown."""
    _cleanup_functions.append(func)
    print(f"✅ Registered cleanup function: {func.__name__}")

def _cleanup_all():
    """Call all registered cleanup functions."""
    global _shutdown_initiated
    if _shutdown_initiated:
        return  # Prevent multiple cleanup calls
    
    _shutdown_initiated = True
    print("🛑 Graceful shutdown initiated...")
    
    for func in _cleanup_functions:
        try:
            func()
        except Exception as e:
            print(f"⚠️ Error during cleanup function {func.__name__}: {e}")
    
    # Force garbage collection
    gc.collect()
    print("✅ Graceful shutdown completed")

def _signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\n🛑 Received signal {signum}. Initiating graceful shutdown...")
    _cleanup_all()
    # Use os._exit() instead of sys.exit() to avoid asyncio cancellation issues
    os._exit(0)

def setup_graceful_shutdown():
    """Setup signal handlers for graceful shutdown."""
    # Register signal handlers
    signal.signal(signal.SIGINT, _signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, _signal_handler)  # Termination signal
    
    # Register cleanup with atexit as backup
    atexit.register(_cleanup_all)
    
    print("✅ Graceful shutdown handlers registered")

# Auto-setup graceful shutdown when module is imported
# setup_graceful_shutdown()  # DISABLED - causing startup issues
