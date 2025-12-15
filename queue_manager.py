import threading
import uuid
import time
from collections import deque

class RequestQueue:
    """
    Manages a thread-safe queue for LLM requests to ensure serial processing.
    """
    def __init__(self):
        self._queue = deque()
        self._current_processing = None
        self._lock = threading.Lock()

    def join(self) -> str:
        """Add a request to the queue and return its ID."""
        req_id = str(uuid.uuid4())
        with self._lock:
            self._queue.append(req_id)
        return req_id

    def leave(self, req_id: str):
        """Remove a request from the queue or finish processing."""
        with self._lock:
            if self._current_processing == req_id:
                self._current_processing = None
            elif req_id in self._queue:
                self._queue.remove(req_id)

    def get_position(self, req_id: str) -> int:
        """
        Get the 1-based position in the queue.
        Returns 0 if currently processing.
        Returns -1 if not found in queue or processing.
        """
        with self._lock:
            if self._current_processing == req_id:
                return 0
            try:
                # index is 0-based, so position is index + 1
                return self._queue.index(req_id) + 1
            except ValueError:
                return -1

    def is_turn(self, req_id: str) -> bool:
        """
        Check if it's this request's turn to process.
        If it is, it promotes the request to 'processing' state.
        """
        with self._lock:
            # If no one is processing and this ID is at the front
            if self._current_processing is None:
                if self._queue and self._queue[0] == req_id:
                    self._current_processing = req_id
                    self._queue.popleft()
                    return True
            return False

    def wait_for_turn_blocking(self, req_id: str, check_interval: float = 0.1):
        """
        Block until it is this request's turn.
        Useful for non-streaming endpoints.
        """
        while True:
            if self.is_turn(req_id):
                return
            time.sleep(check_interval)
