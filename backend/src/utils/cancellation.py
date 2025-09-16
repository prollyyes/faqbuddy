"""
Cancellation utility for managing request cancellation across the application.
This avoids circular imports between Chat.py and LLM files.
"""

import threading
from typing import Dict

# Global cancellation tracking
_active_requests: Dict[str, bool] = {}
_cancellation_lock = threading.Lock()

def register_request(request_id: str) -> None:
    """Register an active request for potential cancellation."""
    with _cancellation_lock:
        _active_requests[request_id] = True

def cancel_request(request_id: str) -> bool:
    """Cancel a specific request by ID."""
    with _cancellation_lock:
        if request_id in _active_requests:
            _active_requests[request_id] = False
            return True
        return False

def is_request_cancelled(request_id: str) -> bool:
    """Check if a request has been cancelled."""
    with _cancellation_lock:
        return not _active_requests.get(request_id, False)

def cleanup_request(request_id: str) -> None:
    """Clean up a request from the active requests tracking."""
    with _cancellation_lock:
        _active_requests.pop(request_id, None)

def has_active_requests() -> bool:
    """Check if there are any active requests."""
    with _cancellation_lock:
        return len(_active_requests) > 0

def cleanup_all_requests() -> None:
    """Emergency cleanup of all active requests."""
    with _cancellation_lock:
        request_count = len(_active_requests)
        _active_requests.clear()
        print(f"🧹 Cleared {request_count} active requests")
