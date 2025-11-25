import redis
import os
from backend.app.core.config import settings

class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.client = cls._instance._initialize_redis_client()
        return cls._instance

    def _initialize_redis_client(self):
        try:
            return redis.StrictRedis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
        except Exception as e:
            print(f"Error initializing Redis client: {e}")
            return None

    def set_cache(self, key: str, value: str, ttl: int = 3600):
        """
        Sets a key-value pair in Redis cache with an optional time-to-live (TTL).
        :param key: The key to store the value under.
        :param value: The value to store.
        :param ttl: Time-to-live in seconds. Defaults to 1 hour.
        """
        if self.client:
            try:
                self.client.setex(key, ttl, value)
            except Exception as e:
                print(f"Error setting cache for key {key}: {e}")

    def get_cache(self, key: str):
        """
        Retrieves a value from Redis cache.
        :param key: The key to retrieve the value for.
        :return: The value associated with the key, or None if not found or an error occurs.
        """
        if self.client:
            try:
                return self.client.get(key)
            except Exception as e:
                print(f"Error getting cache for key {key}: {e}")
        return None

    def delete_cache(self, key: str):
        """
        Deletes a key-value pair from Redis cache.
        :param key: The key to delete.
        """
        if self.client:
            try:
                self.client.delete(key)
            except Exception as e:
                print(f"Error deleting cache for key {key}: {e}")

redis_client = RedisClient()
