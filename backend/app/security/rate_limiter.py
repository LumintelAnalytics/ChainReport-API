import time
import logging
from collections import defaultdict
from backend.app.cache.redis_client import redis_client
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RateLimiter, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.redis = redis_client.client
        self.limits = settings.RATE_LIMITS # This will be defined in config.py
        self.in_memory_counters = defaultdict(lambda: {'count': 0, 'last_reset': time.time()})
        if not self.redis:
            logger.warning("Redis client not available, using in-memory rate limiting. This is not recommended for production.")

    def check_rate_limit(self, service: str, count: int = 1) -> bool:
        """
        Checks if a request for a given service is within the allowed rate limit.
        :param service: The name of the external service (e.g., "onchain_agent", "price_agent").
        :param count: The number of requests to consume. Defaults to 1.
        :return: True if the request is allowed, False otherwise.
        """
        rate_limit = self.limits.get(service)
        if not rate_limit:
            logger.warning(f"No rate limit defined for service: {service}. Allowing request.")
            return True

        max_requests = rate_limit['max_requests']
        window_seconds = rate_limit['window_seconds']

        if self.redis:
            return self._check_rate_limit_redis(service, max_requests, window_seconds, count)
        else:
            return self._check_rate_limit_in_memory(service, max_requests, window_seconds, count)

    def _check_rate_limit_redis(self, service: str, max_requests: int, window_seconds: int, count: int) -> bool:
        key = f"rate_limit:{service}"
        current_time = int(time.time())

        # Use a Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, current_time - window_seconds) # Remove old entries
        pipe.zadd(key, {f"{current_time}:{time.time_ns()}": current_time}) # Add current request timestamp
        pipe.zcard(key) # Get current count
        pipe.expire(key, window_seconds) # Reset TTL

        try:
            _, _, current_count, _ = pipe.execute()
            if current_count + count -1 <= max_requests: # -1 because we already added the current request
                return True
            else:
                logger.warning(f"Rate limit exceeded for service: {service}. Current count: {current_count}, Max: {max_requests}")
                return False
        except Exception as e:
            logger.error(f"Redis rate limiting error for service {service}: {e}", exc_info=True)
            # Fallback to in-memory if Redis fails
            return self._check_rate_limit_in_memory(service, max_requests, window_seconds, count)

    def _check_rate_limit_in_memory(self, service: str, max_requests: int, window_seconds: int, count: int) -> bool:
        with self._lock:
            counter = self.in_memory_counters[service]
            current_time = time.time()

            if current_time - counter['last_reset'] > window_seconds:
                counter['count'] = 0
                counter['last_reset'] = current_time

            if counter['count'] + count <= max_requests:
                counter['count'] += count
                return True
            else:
                logger.warning(f"In-memory rate limit exceeded for service: {service}. Current count: {counter['count']}, Max: {max_requests}")
                return False

rate_limiter = RateLimiter()
