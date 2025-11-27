import hashlib
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from redis.exceptions import RedisError

from backend.app.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # Cache time-to-live in seconds (1 hour)


def _generate_cache_key(url: str, params: Optional[Dict[str, Any]]) -> str:
    """Generates a unique cache key based on the URL and parameters."""
    sorted_params = json.dumps(params, sort_keys=True, default=str) if params else ""
    hash_input = f"{url}-{sorted_params}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


async def cache_request(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    external_api_call: Optional[Callable[[], Awaitable[Any]]] = None,
    serializer: Callable[[Any], str] = json.dumps,
    deserializer: Callable[[str], Any] = json.loads,
) -> Any:
    """
    Checks Redis cache before making an external API call.
    Stores hashed request keys and responses with TTL values.
    Accepts optional `serializer` and `deserializer` callables (defaulting to `json.dumps`/`json.loads`)
    to handle complex object types consistently.
    If serialization fails, logs the error and skips caching, returning the original response.
    """
    cache_key = _generate_cache_key(url, params)
    try:
        cached_response = redis_client.get_cache(cache_key)
        if cached_response:
            try:
                return deserializer(cached_response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to deserialize cached response for key {cache_key}: {e}")
                # If deserialization fails, treat as a cache miss
                pass
    except RedisError as e:
        logger.warning(f"Redis GET error for key {cache_key}: {e}")

    if external_api_call:
        response = await external_api_call()
        try:
            # Attempt to serialize the response before caching
            serialized_response = serializer(response)
            redis_client.set_cache(cache_key, serialized_response, CACHE_TTL)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize response for caching (key: {cache_key}): {e}. Skipping cache."
            )
        except RedisError as e:
            logger.warning(f"Redis SETEX error for key {cache_key}: {e}")
        return response
    return None
