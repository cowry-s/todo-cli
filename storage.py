"""持久化层：只管读写 JSON 文件，不含任何业务逻辑。"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import Task

SCHEMA_VERSION = 1


class StorageError(Exception):
    """数据文件损坏 / 无法读写。"""


class JsonStorage:
    def __init__(self, path: str | os.PathLike) -> None:
        self.path = Path(path)

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StorageError(f"数据文件不是合法 JSON: {self.path} ({exc})") from exc

        if not isinstance(raw, dict):
            raise StorageError(f"数据文件格式错误（顶层应为对象）: {self.path}")

        try:
            return [Task.from_dict(item) for item in raw.get("tasks", [])]
        except (KeyError, TypeError, ValueError) as exc:
            raise StorageError(f"数据文件内容无法解析: {exc}") from exc

    def save(self, tasks: list[Task]) -> None:
        payload = {
            "version": SCHEMA_VERSION,
            "tasks": [t.to_dict() for t in tasks],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # 先写临时文件再 os.replace：即使中途崩溃也不会留下半个损坏的文件
        fd, tmp_path = tempfile.mkstemp(
            dir=self.path.parent, prefix=".todo-", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, self.path)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise