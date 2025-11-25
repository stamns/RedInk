import os
import requests
import json
from typing import Optional, Dict, List, Any
from .base import StorageBackend

class VercelStorage(StorageBackend):
    def __init__(self):
        self.blob_token = os.environ.get("VERCEL_BLOB_READ_WRITE_TOKEN")
        # VERCEL_BLOB_URL should be the public base URL of the store, e.g. https://store-id.public.blob.vercel-storage.com
        self.blob_url_base = os.environ.get("VERCEL_BLOB_URL")
        
        self.kv_url = os.environ.get("VERCEL_KV_REST_API_URL")
        self.kv_token = os.environ.get("VERCEL_KV_REST_API_TOKEN")

        if not self.blob_token:
            raise ValueError("VERCEL_BLOB_READ_WRITE_TOKEN is not set")
        if not self.kv_url or not self.kv_token:
            raise ValueError("VERCEL_KV_REST_API_URL or VERCEL_KV_REST_API_TOKEN is not set")

    def save_file(self, filename: str, data: bytes, content_type: str = "image/png") -> str:
        # Using Vercel Blob REST API
        # Since there is no official Python SDK documentation that guarantees exact path without random suffix,
        # we try to use the 'x-add-random-suffix: false' header if supported, or rely on the returned URL.
        # However, to keep compatibility with the current system which relies on filenames,
        # we ideally want the filename to be the identifier.
        
        # NOTE: The public API endpoint for upload is typically https://blob.vercel-storage.com
        # We append the filename to the path.
        api_url = f"https://blob.vercel-storage.com/{filename}"
        
        headers = {
            "Authorization": f"Bearer {self.blob_token}",
            "x-api-version": "1",
            "x-add-random-suffix": "false", # Attempt to disable random suffix
            "x-content-type": content_type
        }
        
        response = requests.put(api_url, data=data, headers=headers)
        response.raise_for_status()
        
        # The response JSON usually contains 'url'
        result = response.json()
        return result.get("url", f"{self.blob_url_base}/{filename}")

    def get_file(self, filename: str) -> Optional[bytes]:
        # Fetch from Blob URL
        # We assume the URL can be constructed from base + filename if we don't have the full URL stored.
        # But if save_file returned a full URL and we only kept filename, we rely on VERCEL_BLOB_URL
        
        url = self.get_file_url(filename)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None

    def delete_file(self, filename: str) -> bool:
        # Vercel Blob delete API
        # POST /delete with body { urls: [url] }
        url = self.get_file_url(filename)
        api_url = "https://blob.vercel-storage.com/delete"
        headers = {
            "Authorization": f"Bearer {self.blob_token}",
            "x-api-version": "1",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(api_url, json={"urls": [url]}, headers=headers)
            return response.status_code == 200
        except Exception:
            return False

    def get_file_url(self, filename: str) -> str:
        # If filename is already a URL, return it
        if filename.startswith("http"):
            return filename
        
        # Otherwise construct it
        if self.blob_url_base:
            # remove trailing slash
            base = self.blob_url_base.rstrip("/")
            return f"{base}/{filename}"
        return filename

    def save_json(self, key: str, data: Dict[str, Any]) -> bool:
        # Use Vercel KV (Upstash Redis)
        url = f"{self.kv_url}/set/{key}"
        headers = {"Authorization": f"Bearer {self.kv_token}"}
        
        try:
            # Store as stringified JSON
            payload = json.dumps(data)
            response = requests.post(url, data=payload, headers=headers)
            return response.status_code == 200 and response.json().get("result") == "OK"
        except Exception:
            return False

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        url = f"{self.kv_url}/get/{key}"
        headers = {"Authorization": f"Bearer {self.kv_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json().get("result")
                if result:
                    return json.loads(result)
        except Exception:
            pass
        return None

    def delete_json(self, key: str) -> bool:
        url = f"{self.kv_url}/del/{key}"
        headers = {"Authorization": f"Bearer {self.kv_token}"}
        
        try:
            response = requests.post(url, headers=headers)
            return response.status_code == 200
        except Exception:
            return False

    def list_json(self, prefix: str = "") -> List[str]:
        # SCAN or KEYS. Keys is simpler but slower. Upstash supports KEYS.
        # Provide a pattern.
        pattern = f"{prefix}*" if prefix else "*"
        url = f"{self.kv_url}/keys/{pattern}"
        headers = {"Authorization": f"Bearer {self.kv_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("result", [])
        except Exception:
            pass
        return []
