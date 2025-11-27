import os
from itertools import cycle
from typing import Dict, Optional

class APIKeyManager:
    def __init__(self):
        self._keys: Dict[str, cycle] = {}
        self._load_keys()

    def _load_keys(self):
        """
        Loads API keys from environment variables.
        Expects keys to be named like PROVIDER_NAME_API_KEY_1, PROVIDER_NAME_API_KEY_2, etc.
        """
        for key, value in os.environ.items():
            if key.endswith("_API_KEY") or "_API_KEY_" in key:
                parts = key.split("_API_KEY")
                provider_name = parts[0]
                if provider_name not in self._keys:
                    self._keys[provider_name] = []
                self._keys[provider_name].append(value)
        
        # Convert lists to cycles for rotation
        for provider_name, key_list in self._keys.items():
            self._keys[provider_name] = cycle(key_list)

    def get_key(self, provider_name: str) -> Optional[str]:
        """
        Retrieves an API key for a given provider.
        Rotates through available keys for the provider.
        """
        if provider_name in self._keys:
            return next(self._keys[provider_name])
        return None

# Initialize the APIKeyManager
api_key_manager = APIKeyManager()
