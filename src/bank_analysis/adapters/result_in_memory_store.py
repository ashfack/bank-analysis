
# src/bank_analysis/adapters/result_store.py
from typing import Dict, Any
from threading import Lock

class InMemoryResultStore:
    def __init__(self):
        self._lock = Lock()
        self._store: Dict[str, Any] = {}

    def put(self, session_id: str, payload: Any):
        with self._lock:
            self._store[session_id] = payload

    def get(self, session_id: str) -> Any | None:
        with self._lock:
            return self._store.get(session_id)

    def remove(self, session_id: str):
        with self._lock:
            self._store.pop(session_id, None)
