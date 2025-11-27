import hashlib
import json
from typing import Any, Dict, Optional

from backend.app.cache.redis_client import redis_client

CACHE_TTL = 3600  # Cache time-to-live in seconds (1 hour)

def _generate_cache_key(url: str, params: Optional[Dict[str, Any]]) -> str:
    """Generates a unique cache key based on the URL and parameters."""
    sorted_params = json.dumps(sorted(params.items())) if params else ""
    hash_input = f"{url}-{sorted_params}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

async def cache_request(url: str, params: Optional[Dict[str, Any]] = None, external_api_call: callable = None) -> Any:
    """
    Checks Redis cache before making an external API call.
    Stores hashed request keys and responses with TTL values.
    """
    cache_key = _generate_cache_key(url, params)
    cached_response = await redis_client.get(cache_key)

    if cached_response:
        return json.loads(cached_response)

    if external_api_call:
        response = await external_api_call()
        await redis_client.setex(cache_key, CACHE_TTL, json.dumps(response))
        return response
    return None
