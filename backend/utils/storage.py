import os
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict

try:
    import redis
except ImportError:
    redis = None

class StorageProvider(ABC):
    @abstractmethod
    def save(self, path: str, data: Union[bytes, str, Dict]) -> str:
        """Save data to the specified path."""
        pass

    @abstractmethod
    def load(self, path: str, as_json: bool = False) -> Union[bytes, str, Dict, None]:
        """Load data from the specified path."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete file at path."""
        pass
    
    @abstractmethod
    def get_url(self, path: str) -> str:
        """Get public URL for the file (if applicable)."""
        pass

class LocalStorage(StorageProvider):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_path(self, path: str) -> str:
        # Simple path joining, assuming path is relative
        if os.path.isabs(path):
             if path.startswith(self.base_dir):
                 return path
        return os.path.join(self.base_dir, path)

    def save(self, path: str, data: Union[bytes, str, Dict]) -> str:
        full_path = self._get_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        mode = "w" if isinstance(data, (str, dict)) else "wb"
        encoding = "utf-8" if mode == "w" else None
        
        with open(full_path, mode, encoding=encoding) as f:
            if isinstance(data, dict):
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                f.write(data)
        return path

    def load(self, path: str, as_json: bool = False) -> Union[bytes, str, Dict, None]:
        full_path = self._get_path(path)
        if not os.path.exists(full_path):
            return None
            
        try:
            if as_json:
                with open(full_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            
            with open(full_path, "rb") as f:
                return f.read()
        except Exception:
            return None

    def exists(self, path: str) -> bool:
        return os.path.exists(self._get_path(path))

    def delete(self, path: str) -> bool:
        full_path = self._get_path(path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
        
    def get_url(self, path: str) -> str:
        # Local storage URL handling needs to be done by the app routes
        # This just returns the filename/path relative to storage root
        return path

class RedisStorage(StorageProvider):
    def __init__(self, url: str):
        if not redis:
            raise ImportError("redis package is required for RedisStorage")
        self.client = redis.Redis.from_url(url, decode_responses=False)
        self.prefix = "redink:"

    def _get_key(self, path: str) -> str:
        path = path.strip("/")
        return f"{self.prefix}{path}"

    def save(self, path: str, data: Union[bytes, str, Dict]) -> str:
        key = self._get_key(path)
        if isinstance(data, dict):
            payload = json.dumps(data, ensure_ascii=False)
            self.client.set(key, payload.encode('utf-8'))
        elif isinstance(data, str):
            self.client.set(key, data.encode('utf-8'))
        else:
            self.client.set(key, data)
        return path

    def load(self, path: str, as_json: bool = False) -> Union[bytes, str, Dict, None]:
        key = self._get_key(path)
        data = self.client.get(key)
        if data is None:
            return None
        
        if as_json:
            return json.loads(data.decode('utf-8'))
        return data

    def exists(self, path: str) -> bool:
        key = self._get_key(path)
        return bool(self.client.exists(key))

    def delete(self, path: str) -> bool:
        key = self._get_key(path)
        return bool(self.client.delete(key))
        
    def get_url(self, path: str) -> str:
        # Redis doesn't expose public URLs directly.
        # The app should serve it via an endpoint that reads from storage.
        return path

_storage_instance = None

def get_storage() -> StorageProvider:
    global _storage_instance
    if _storage_instance is None:
        from backend.config import Config
        backend = Config.STORAGE_BACKEND
        if backend == 'vercel-kv':
            url = os.getenv("KV_URL") or os.getenv("REDIS_URL")
            if not url:
                raise ValueError("KV_URL or REDIS_URL environment variable is required for vercel-kv storage")
            _storage_instance = RedisStorage(url)
        else:
            # Default to local storage relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            _storage_instance = LocalStorage(base_dir)
            
    return _storage_instance
