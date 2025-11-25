import redis
import threading
import logging
from redis.exceptions import RedisError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RedisClient, cls).__new__(cls)
                    cls._instance.client = cls._instance._initialize_redis_client()
        return cls._instance

    def _initialize_redis_client(self):
        try:
            client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            client.ping()
        except RedisError:
            logger.warning("Redis unavailable, caching disabled", exc_info=True)
            return None
        else:
            return client

    def set_cache(self, key: str, value: str, ttl: int = 3600):
        """
        Sets a key-value pair in Redis cache with an optional time-to-live (TTL).
        :param key: The key to store the value under.
        :param value: The value to store.
        :param ttl: Time-to-live in seconds. Defaults to 1 hour.
        """
        if not self.client:
            return
        try:
            self.client.setex(key, ttl, value)
        except RedisError:
            logger.warning("Error setting cache for key %s", key, exc_info=True)

    def get_cache(self, key: str):
        """
        Retrieves a value from Redis cache.
        :param key: The key to retrieve the value for.
        :return: The value associated with the key, or None if not found or an error occurs.
        """
        if not self.client:
            return None
        try:
            return self.client.get(key)
        except RedisError:
            logger.warning("Error getting cache for key %s", key, exc_info=True)
        return None

    def delete_cache(self, key: str):
        """
        Deletes a key-value pair from Redis cache.
        :param key: The key to delete.
        """
        if not self.client:
            return
        try:
            self.client.delete(key)
        except RedisError:
            logger.warning("Error deleting cache for key %s", key, exc_info=True)

redis_client = RedisClient()
