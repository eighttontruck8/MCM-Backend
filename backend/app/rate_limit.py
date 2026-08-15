from __future__ import annotations

import hashlib
import math
import time
from collections import defaultdict, deque
from threading import Lock

from app.errors import DomainError


class InMemoryRateLimiter:
    """단일 프로세스용 sliding-window limiter. 운영에서는 공유 저장소 구현으로 교체한다."""

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def enforce(self, key: str, *, limit: int, window_seconds: int) -> None:
        if limit <= 0:
            return
        window_seconds = max(1, window_seconds)
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            requests = self._requests[key]
            while requests and requests[0] <= cutoff:
                requests.popleft()
            if len(requests) >= limit:
                retry_after = max(1, math.ceil(window_seconds - (now - requests[0])))
                raise DomainError(
                    429,
                    "RATE_LIMIT_EXCEEDED",
                    "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
                    {"retry_after_seconds": retry_after},
                )
            requests.append(now)


def rate_limit_key(scope: str, client_host: str | None, identity: str) -> str:
    identity_hash = hashlib.sha256(identity.strip().lower().encode()).hexdigest()
    return f"{scope}:{client_host or 'unknown'}:{identity_hash}"
