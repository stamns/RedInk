import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from backend.storage import get_storage


class HistoryService:
    def __init__(self):
        self.storage = get_storage()
        self._init_index()

    def _init_index(self):
        if not self.storage.get_json("index"):
            self.storage.save_json("index", {"records": []})

    def _load_index(self) -> Dict:
        index = self.storage.get_json("index")
        return index if index else {"records": []}

    def _save_index(self, index: Dict):
        self.storage.save_json("index", index)

    def create_record(
        self,
        topic: str,
        outline: Dict,
        task_id: Optional[str] = None
    ) -> str:
        record_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        record = {
            "id": record_id,
            "title": topic,
            "created_at": now,
            "updated_at": now,
            "outline": outline,
            "images": {
                "task_id": task_id,
                "generated": []
            },
            "status": "draft",  # draft/generating/completed/partial
            "thumbnail": None
        }

        self.storage.save_json(record_id, record)

        index = self._load_index()
        index["records"].insert(0, {
            "id": record_id,
            "title": topic,
            "created_at": now,
            "updated_at": now,
            "status": "draft",
            "thumbnail": None,
            "page_count": len(outline.get("pages", []))
        })
        self._save_index(index)

        return record_id

    def get_record(self, record_id: str) -> Optional[Dict]:
        return self.storage.get_json(record_id)

    def update_record(
        self,
        record_id: str,
        outline: Optional[Dict] = None,
        images: Optional[Dict] = None,
        status: Optional[str] = None,
        thumbnail: Optional[str] = None
    ) -> bool:
        record = self.get_record(record_id)
        if not record:
            return False

        now = datetime.now().isoformat()
        record["updated_at"] = now

        if outline is not None:
            record["outline"] = outline

        if images is not None:
            record["images"] = images

        if status is not None:
            record["status"] = status

        if thumbnail is not None:
            record["thumbnail"] = thumbnail

        self.storage.save_json(record_id, record)

        index = self._load_index()
        for idx_record in index["records"]:
            if idx_record["id"] == record_id:
                idx_record["updated_at"] = now
                if status:
                    idx_record["status"] = status
                if thumbnail:
                    idx_record["thumbnail"] = thumbnail
                if outline:
                    idx_record["page_count"] = len(outline.get("pages", []))
                break

        self._save_index(index)
        return True

    def delete_record(self, record_id: str) -> bool:
        record = self.get_record(record_id)
        if not record:
            return False

        if record.get("images") and record["images"].get("generated"):
            for img_file in record["images"]["generated"]:
                try:
                    self.storage.delete_file(img_file)
                except Exception as e:
                    print(f"删除图片失败: {img_file}, {e}")

        try:
            self.storage.delete_json(record_id)
        except Exception:
            return False

        index = self._load_index()
        index["records"] = [r for r in index["records"] if r["id"] != record_id]
        self._save_index(index)

        return True

    def list_records(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict:
        index = self._load_index()
        records = index.get("records", [])

        if status:
            records = [r for r in records if r.get("status") == status]

        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size
        page_records = records[start:end]

        return {
            "records": page_records,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    def search_records(self, keyword: str) -> List[Dict]:
        index = self._load_index()
        records = index.get("records", [])

        keyword_lower = keyword.lower()
        results = [
            r for r in records
            if keyword_lower in r.get("title", "").lower()
        ]

        return results

    def get_statistics(self) -> Dict:
        index = self._load_index()
        records = index.get("records", [])

        total = len(records)
        status_count = {}

        for record in records:
            status = record.get("status", "draft")
            status_count[status] = status_count.get(status, 0) + 1

        return {
            "total": total,
            "by_status": status_count
        }


_service_instance = None


def get_history_service() -> HistoryService:
    global _service_instance
    if _service_instance is None:
        _service_instance = HistoryService()
    return _service_instance
