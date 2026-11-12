"""Retry wrapper for agent tool calls and model calls.

Exponential backoff with full jitter, a total deadline, a retryable check,
and one idempotency key per logical operation so a retried write does not
run twice on a server that honours the key.
"""

import random
import time
import uuid
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


class TransientError(Exception):
    """Timeouts, 429s, 5xx. Safe to retry if the operation is idempotent."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class PermanentError(Exception):
    """Bad input, auth failure, policy refusal. Retrying will not help."""


@dataclass
class RetryPolicy:
    max_attempts: int = 4
    base_delay: float = 0.5
    max_delay: float = 8.0
    deadline: float = 30.0

    def delay(self, attempt: int, retry_after: float | None) -> float:
        if retry_after is not None:
            return min(retry_after, self.max_delay)
        cap = min(self.max_delay, self.base_delay * (2 ** attempt))
        return random.uniform(0, cap)


def call_with_retry(
    op: Callable[[str], T],
    policy: RetryPolicy = RetryPolicy(),
    is_retryable: Callable[[Exception], bool] = lambda e: isinstance(e, TransientError),
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    idempotency_key: str | None = None,
) -> T:
    """Run op(idempotency_key) until it succeeds, fails permanently, or runs out of budget.

    The same key goes to every attempt. That is the whole point: the server
    uses it to return the first result instead of performing the write again.
    """
    key = idempotency_key or str(uuid.uuid4())
    started = clock()
    last_error: Exception | None = None
    for attempt in range(policy.max_attempts):
        try:
            return op(key)
        except Exception as err:
            last_error = err
            if not is_retryable(err):
                raise
            if attempt == policy.max_attempts - 1:
                break
            wait = policy.delay(attempt, getattr(err, "retry_after", None))
            if clock() - started + wait > policy.deadline:
                break
            sleep(wait)
    raise TimeoutError(f"gave up after {attempt + 1} attempts: {last_error}") from last_error


if __name__ == "__main__":
    calls = {"n": 0}
    seen_keys = set()

    def flaky_charge(key: str) -> str:
        calls["n"] += 1
        seen_keys.add(key)
        if calls["n"] < 3:
            raise TransientError("upstream 503")
        return f"charged once under key {key[:8]}"

    print(call_with_retry(flaky_charge, sleep=lambda s: None))
    print(f"attempts={calls['n']} distinct_keys={len(seen_keys)}")
