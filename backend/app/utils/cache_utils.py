import hashlib
import json
import logging
from typing import Any, Callable, Dict, Awaitable, Optional

from backend.app.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # Cache time-to-live in seconds (1 hour)


def _generate_cache_key(url: str, params: Optional[Dict[str, Any]]) -> str:
    """Generates a unique cache key based on the URL and parameters."""
    sorted_params = json.dumps(params, sort_keys=True, default=str) if params else ""
    hash_input = f"{url}-{sorted_params}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


async def cache_request(url: str, params: Optional[Dict[str, Any]] = None, external_api_call: Optional[Callable[[], Awaitable[Any]]] = None) -> Any:
    """
    Checks Redis cache before making an external API call.
    Stores hashed request keys and responses with TTL values.
    """
    cache_key = _generate_cache_key(url, params)
    try:
        cached_response = await redis_client.get(cache_key)
        if cached_response:
            return json.loads(cached_response)
    except Exception as e:
        logger.warning(f"Redis GET error for key {cache_key}: {e}")

    if external_api_call:
        response = await external_api_call()
        try:
            # Attempt to serialize the response before caching
            serialized_response = json.dumps(response)
            await redis_client.setex(cache_key, CACHE_TTL, serialized_response)
        except TypeError as e:
            logger.warning(f"Failed to serialize response for caching (key: {cache_key}): {e}")
        except Exception as e:
            logger.warning(f"Redis SETEX error for key {cache_key}: {e}")
        return response
    return None
