from datetime import datetime, timedelta
from collections import defaultdict


_failed_attempts: dict[str, list[datetime]] = defaultdict(list)

MAX_ATTEMPTS = 5
WINDOW = timedelta(minutes=15)

def _clean(key: str):
    now = datetime.utcnow()
    _failed_attempts[key] = [t for t in _failed_attempts[key] if now - t < WINDOW]

def is_blocked(key: str) -> bool:
    _clean(key)
    return len(_failed_attempts[key]) >= MAX_ATTEMPTS

def register_failure(key: str):
    _failed_attempts[key].append(datetime.utcnow())

def clear_failures(key: str):
    _failed_attempts.pop(key, None)
