"""
NEXUS Rate Limiting Utilities
In-memory sliding window rate limiter per user.
Returns 429 Too Many Requests with Retry-After header.
"""
import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, status

_USER_TIMESTAMPS: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))


def check_rate_limit(user_id: str, action: str, limit: int, window_seconds: int) -> None:
    """
    Checks if a user has exceeded the limit for a given action within window_seconds.
    Raises HTTPException(429) if exceeded.
    """
    now = time.time()
    user_records = _USER_TIMESTAMPS[user_id][action]

    # Prune old timestamps
    cutoff = now - window_seconds
    _USER_TIMESTAMPS[user_id][action] = [t for t in user_records if t > cutoff]
    current_count = len(_USER_TIMESTAMPS[user_id][action])

    if current_count >= limit:
        oldest = _USER_TIMESTAMPS[user_id][action][0]
        retry_after = max(1, int(window_seconds - (now - oldest)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for action '{action}'. Limit: {limit} per {window_seconds}s. Try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    _USER_TIMESTAMPS[user_id][action].append(now)


def reset_rate_limits() -> None:
    """Helper for testing to reset limits."""
    _USER_TIMESTAMPS.clear()
