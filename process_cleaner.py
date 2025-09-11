#!/usr/bin/env python3
"""
FAQBuddy Process Cleaner

Checks for lingering Python, Node.js, or Uvicorn processes related to FAQBuddy and optionally kills them.
Run this after closing the app if you suspect some processes are still running.
"""
import subprocess
import sys
import os

# Define process keywords to look for
KEYWORDS = [
    'python',
    'uvicorn',
    'node',
    'next',
    'faqbuddy',
]

def find_processes():
    """Find all relevant processes."""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        matches = []
        for line in lines:
            if any(kw in line.lower() for kw in KEYWORDS) and 'process_cleaner' not in line:
                matches.append(line)
        return matches
    except Exception as e:
        print(f"Error finding processes: {e}")
        return []

def kill_processes(matches):
    """Kill all matched processes."""
    import signal
    import re
    pids = []
    for line in matches:
        parts = line.split()
        if len(parts) > 1 and parts[1].isdigit():
            pids.append(int(parts[1]))
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
            print(f"Killed process with PID {pid}")
        except Exception as e:
            print(f"Failed to kill PID {pid}: {e}")

if __name__ == "__main__":
    print("\n[FAQBuddy Process Cleaner]")
    matches = find_processes()
    if not matches:
        print("No lingering FAQBuddy-related processes found.")
        sys.exit(0)
    print("Found the following processes:")
    for line in matches:
        print(line)
    answer = input("\nDo you want to kill all these processes? [y/N]: ").strip().lower()
    if answer == 'y':
        kill_processes(matches)
        print("All matched processes killed.")
    else:
        print("No processes were killed.") 