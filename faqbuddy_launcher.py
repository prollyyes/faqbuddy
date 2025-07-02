#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import signal
import re
import platform
from pathlib import Path

def cleanup_processes():
    """Clean up any existing FAQBuddy processes."""
    print("🧹 Cleaning up any existing FAQBuddy processes...")
    
    try:
        # Use platform-specific ps command
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(['ps', 'ax'], capture_output=True, text=True)
        else:  # Linux and others
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            
        lines = result.stdout.splitlines()
        killed_count = 0
        
        keywords = ['python', 'uvicorn', 'node', 'next', 'faqbuddy']
        
        for line in lines:
            if any(kw in line.lower() for kw in keywords) and 'process_cleaner' not in line and 'temp_launch' not in line:
                parts = line.split()
                if len(parts) > 1 and parts[1].isdigit():
                    try:
                        pid = int(parts[1])
                        os.kill(pid, signal.SIGKILL)
                        killed_count += 1
                        print(f"Killed process with PID {pid}")
                    except Exception as e:
                        print(f"Failed to kill PID {pid}: {e}")
        
        print(f"Cleaned up {killed_count} processes")
        return killed_count
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 0

def main():
    print("Starting FAQBuddy launch sequence...")
    
    # Clean up processes first
    cleanup_processes()
    
    # Wait a moment for cleanup
    time.sleep(2)
    
    print("🚀 Launching FAQBuddy...")
    
    # Launch the servers
    try:
        print(f"Executing: /opt/homebrew/Caskroom/miniconda/base/envs/thesis_env/bin/python launch_servers.py")
        subprocess.Popen([r"/opt/homebrew/Caskroom/miniconda/base/envs/thesis_env/bin/python", "launch_servers.py"])
        print("FAQBuddy launch initiated successfully!")
    except Exception as e:
        print(f"Failed to launch FAQBuddy: {e}")
    
    # Clean up this launcher script
    try:
        script_path = Path(__file__)
        if script_path.name == "faqbuddy_launcher.py":
            script_path.unlink()
    except Exception:
        pass

if __name__ == "__main__":
    main()
