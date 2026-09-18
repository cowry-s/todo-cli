"""数据模型：Task 与 Priority，负责 dict / JSON 之间的转换。"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class Priority(str, Enum):
    """继承 str 让 json.dump 可以直接序列化。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def parse(cls, value: str) -> "Priority":
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            valid = ", ".join(p.value for p in cls)
            raise ValueError(f"无效优先级 {value!r}，可选: {valid}") from None

    @property
    def rank(self) -> int:
        """数值越大优先级越高，用于排序。"""
        return {"low": 1, "medium": 2, "high": 3}[self.value]


def parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise ValueError(f"日期格式无效: {value!r}，应为 YYYY-MM-DD") from None


@dataclass
class Task:
    title: str
    priority: Priority = Priority.MEDIUM
    due: date | None = None
    done: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("任务标题不能为空")
        if not isinstance(self.priority, Priority):
            self.priority = Priority.parse(self.priority)
        self.due = parse_date(self.due)

    # ---------- 序列化 ----------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority.value,
            "due": self.due.isoformat() if self.due else None,
            "done": self.done,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            priority=data.get("priority", Priority.MEDIUM.value),
            due=data.get("due"),
            done=bool(data.get("done", False)),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
        )

    @property
    def is_overdue(self) -> bool:
        return bool(self.due and not self.done and self.due < date.today())