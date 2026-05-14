"""Todo 驱动编排 — 动态 todo list 替代固定 pipeline"""
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class TodoItem:
    id: str
    content: str
    status: TodoStatus = TodoStatus.PENDING
    priority: int = 0
    assigned_to: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    result: str = ""


class TodoList:
    """动态 todo list，支持创建/更新/完成/取消，持久化到 JSON 文件。"""

    def __init__(self, persist_path: str = None):
        self._items: list[TodoItem] = []
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path and self._persist_path.exists():
            self._load()

    def add(self, id: str, content: str, priority: int = 0) -> TodoItem:
        item = TodoItem(id=id, content=content, priority=priority)
        self._items.append(item)
        self._persist()
        return item

    def get(self, id: str) -> TodoItem | None:
        for item in self._items:
            if item.id == id:
                return item
        return None

    def start(self, id: str) -> bool:
        item = self.get(id)
        if not item or item.status != TodoStatus.PENDING:
            return False
        item.status = TodoStatus.IN_PROGRESS
        item.started_at = time.time()
        self._persist()
        return True

    def complete(self, id: str, result: str = "") -> bool:
        item = self.get(id)
        if not item or item.status != TodoStatus.IN_PROGRESS:
            return False
        item.status = TodoStatus.COMPLETED
        item.completed_at = time.time()
        item.result = result
        self._persist()
        return True

    def cancel(self, id: str) -> bool:
        item = self.get(id)
        if not item or item.status in (TodoStatus.COMPLETED, TodoStatus.CANCELLED):
            return False
        item.status = TodoStatus.CANCELLED
        self._persist()
        return True

    def block(self, id: str, reason: str = "") -> bool:
        item = self.get(id)
        if not item:
            return False
        item.status = TodoStatus.BLOCKED
        item.result = reason
        self._persist()
        return True

    @property
    def items(self) -> list[TodoItem]:
        return list(self._items)

    @property
    def pending(self) -> list[TodoItem]:
        return [i for i in self._items if i.status == TodoStatus.PENDING]

    @property
    def in_progress(self) -> list[TodoItem]:
        return [i for i in self._items if i.status == TodoStatus.IN_PROGRESS]

    @property
    def completed(self) -> list[TodoItem]:
        return [i for i in self._items if i.status == TodoStatus.COMPLETED]

    def summary(self) -> dict:
        total = len(self._items)
        by_status = {}
        for status in TodoStatus:
            by_status[status.value] = sum(1 for i in self._items if i.status == status)
        return {
            "total": total,
            "by_status": by_status,
            "progress_pct": round(by_status.get("completed", 0) / total * 100, 1) if total else 0,
        }

    def _persist(self):
        if not self._persist_path:
            return
        data = [asdict(item) for item in self._items]
        for d in data:
            d["status"] = d["status"].value if isinstance(d["status"], TodoStatus) else d["status"]
        self._persist_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load(self):
        raw = self._persist_path.read_text().strip()
        if not raw:
            return
        data = json.loads(raw)
        self._items = []
        for d in data:
            d["status"] = TodoStatus(d["status"])
            self._items.append(TodoItem(**d))
