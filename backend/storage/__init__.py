import os
from typing import Optional
from .base import StorageBackend
from .local import LocalStorage

_storage_instance: Optional[StorageBackend] = None

def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is None:
        backend_type = os.environ.get("STORAGE_BACKEND", "local")
        
        if backend_type == "vercel_blob":
            from .vercel import VercelStorage
            _storage_instance = VercelStorage()
        else:
            _storage_instance = LocalStorage()
            
    return _storage_instance
