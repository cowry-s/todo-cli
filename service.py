"""业务逻辑层：增删改查 + 筛选。

只依赖 storage 的 load/save 两个方法（鸭子类型），
测试时可以注入内存实现，完全不碰文件系统。
"""
from __future__ import annotations

from datetime import date
from typing import Protocol, Sequence

from .models import Priority, Task

#: 排序策略表，key 即命令行 --sort 的可选值
SORT_KEYS = {
    "created": lambda t: t.created_at,
    "priority": lambda t: (-t.priority.rank, t.due is None, t.due or date.max),
    "due": lambda t: (t.due is None, t.due or date.max),
    "title": lambda t: t.title.lower(),
}


class Storage(Protocol):
    def load(self) -> list[Task]: ...
    def save(self, tasks: list[Task]) -> None: ...


class TaskNotFound(LookupError):
    """按 ID（或 ID 前缀）找不到唯一任务。"""


class TaskService:
    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._tasks: list[Task] = list(storage.load())

    # ---------- 读 ----------
    @property
    def tasks(self) -> tuple[Task, ...]:
        return tuple(self._tasks)

    def get(self, task_id: str) -> Task:
        """支持完整 ID 或唯一前缀，方便命令行输入。"""
        if not task_id:
            raise TaskNotFound("任务 ID 不能为空")

        exact = [t for t in self._tasks if t.id == task_id]
        if exact:
            return exact[0]

        matches = [t for t in self._tasks if t.id.startswith(task_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise TaskNotFound(f"ID 前缀 {task_id!r} 不唯一（匹配 {len(matches)} 条）")
        raise TaskNotFound(f"找不到任务: {task_id}")

    def list_tasks(
        self,
        *,
        priority: Priority | None = None,
        due_before: date | None = None,
        due_after: date | None = None,
        include_done: bool = False,
        keyword: str | None = None,
        sort: str = "created",
    ) -> list[Task]:
        result = list(self._tasks)

        if not include_done:
            result = [t for t in result if not t.done]
        if priority is not None:
            result = [t for t in result if t.priority == priority]
        if due_before is not None:
            result = [t for t in result if t.due and t.due <= due_before]
        if due_after is not None:
            result = [t for t in result if t.due and t.due >= due_after]
        if keyword:
            kw = keyword.strip().lower()
            result = [t for t in result if kw in t.title.lower()]

        try:
            key = SORT_KEYS[sort]
        except KeyError:
            raise ValueError(
                f"未知排序方式 {sort!r}，可选: {', '.join(SORT_KEYS)}"
            ) from None
        return sorted(result, key=key)

    # ---------- 写 ----------
    def add(
        self,
        title: str,
        priority: Priority | str = Priority.MEDIUM,
        due: date | str | None = None,
    ) -> Task:
        task = Task(title=title, priority=priority, due=due)
        self._tasks.append(task)
        self._flush()
        return task

    def complete(self, task_id: str) -> Task:
        task = self.get(task_id)
        task.done = True
        self._flush()
        return task

    def delete(self, task_id: str) -> Task:
        task = self.get(task_id)
        self._tasks.remove(task)
        self._flush()
        return task

    # ---------- 内部 ----------
    def _flush(self) -> None:
        self._storage.save(self._tasks)