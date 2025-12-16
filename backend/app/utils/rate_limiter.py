import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, limit: int, period: int):
        self.limit = limit
        self.period = period
        self.requests = defaultdict(list)

    def is_limited(self, key: str) -> bool:
        current_time = time.time()
        # Remove timestamps outside the current period
        self.requests[key] = [
            t for t in self.requests[key] if t > current_time - self.period
        ]

        if len(self.requests[key]) >= self.limit:
            return True
        
        self.requests[key].append(current_time)
        return False
