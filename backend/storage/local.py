import os
import json
import shutil
from typing import Optional, Dict, List, Any
from .base import StorageBackend

class LocalStorage(StorageBackend):
    def __init__(self):
        # Determine project root relative to this file: backend/storage/local.py -> .../project
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = os.path.join(self.project_root, "output")
        self.history_dir = os.path.join(self.project_root, "history")
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)

    def save_file(self, filename: str, data: bytes, content_type: str = "image/png") -> str:
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(data)
        return filename

    def get_file(self, filename: str) -> Optional[bytes]:
        filepath = os.path.join(self.output_dir, filename)
        if not os.path.exists(filepath):
            return None
        with open(filepath, "rb") as f:
            return f.read()

    def delete_file(self, filename: str) -> bool:
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except OSError:
                return False
        return False
    
    def get_file_url(self, filename: str) -> str:
        # Local URL structure
        return f"/api/images/{filename}"

    def save_json(self, key: str, data: Dict[str, Any]) -> bool:
        filepath = os.path.join(self.history_dir, f"{key}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except OSError:
            return False

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        filepath = os.path.join(self.history_dir, f"{key}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def delete_json(self, key: str) -> bool:
        filepath = os.path.join(self.history_dir, f"{key}.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except OSError:
                return False
        return False

    def list_json(self, prefix: str = "") -> List[str]:
        # Lists keys (filenames without .json extension)
        files = []
        if os.path.exists(self.history_dir):
            for f in os.listdir(self.history_dir):
                if f.endswith(".json"):
                    key = f[:-5]
                    if key.startswith(prefix):
                        files.append(key)
        return files
