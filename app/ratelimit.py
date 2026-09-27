"""Egyszerű, memóriában tartott csúszóablakos korlátozás.

Egy példányban futó szerverhez elég (Render). Több példánynál közös tároló (pl. Redis) kellene.
"""
import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)
_last_sweep = time.monotonic()


def allow(key: str, limit: int, window_s: int) -> bool:
    """True, ha a kulcs még belefér: legfeljebb `limit` esemény `window_s` másodpercenként."""
    global _last_sweep
    now = time.monotonic()
    with _lock:
        if now - _last_sweep > 600:
            # régi kulcsok takarítása, hogy a szótár ne nőjön a végtelenségig
            for k in [k for k, q in _hits.items() if not q or now - q[-1] > 3600]:
                del _hits[k]
            _last_sweep = now
        q = _hits[key]
        while q and now - q[0] > window_s:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


def reset():
    with _lock:
        _hits.clear()
