from collections import defaultdict, deque
from time import monotonic


class LoginRateLimiter:
    _attempts = defaultdict(deque)

    @classmethod
    def hit(cls, key, max_attempts, window_seconds):
        now = monotonic()
        attempts = cls._attempts[key]

        while attempts and now - attempts[0] > window_seconds:
            attempts.popleft()

        if len(attempts) >= max_attempts:
            retry_after = max(int(window_seconds - (now - attempts[0])), 1)
            return False, retry_after

        attempts.append(now)
        return True, 0

    @classmethod
    def clear(cls, key):
        cls._attempts.pop(key, None)
