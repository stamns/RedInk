from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any

class StorageBackend(ABC):
    @abstractmethod
    def save_file(self, filename: str, data: bytes, content_type: str = "image/png") -> str:
        """
        Save a file and return its identifier (path or URL).
        """
        pass

    @abstractmethod
    def get_file(self, filename: str) -> Optional[bytes]:
        """
        Get file content as bytes.
        """
        pass

    @abstractmethod
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file.
        """
        pass
    
    @abstractmethod
    def get_file_url(self, filename: str) -> str:
        """
        Get access URL for the file.
        """
        pass

    @abstractmethod
    def save_json(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Save JSON data.
        """
        pass

    @abstractmethod
    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON data.
        """
        pass

    @abstractmethod
    def delete_json(self, key: str) -> bool:
        """
        Delete JSON data.
        """
        pass
        
    @abstractmethod
    def list_json(self, prefix: str = "") -> List[str]:
        """
        List JSON keys.
        """
        pass
