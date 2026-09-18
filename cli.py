"""命令行入口：解析参数 → 调用 TaskService → 打印结果。"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from .models import Priority, Task
from .service import SORT_KEYS, TaskNotFound, TaskService
from .storage import JsonStorage, StorageError

DEFAULT_DB = os.environ.get("TODO_FILE", str(Path.home() / ".todo.json"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo", description="待办事项 CLI（JSON 存储）"
    )
    parser.add_argument(
        "--file", default=DEFAULT_DB,
        help=f"数据文件路径（默认 {DEFAULT_DB}，可用环境变量 TODO_FILE 覆盖）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="创建任务")
    p_add.add_argument("title", help="任务标题")
    p_add.add_argument(
        "-p", "--priority", default=Priority.MEDIUM.value,
        choices=[p.value for p in Priority], help="优先级（默认 medium）",
    )
    p_add.add_argument("-d", "--due", metavar="YYYY-MM-DD", help="截止日期")

    p_list = sub.add_parser("list", help="列出 / 筛选任务")
    p_list.add_argument("-p", "--priority", choices=[p.value for p in Priority])
    p_list.add_argument("--due-before", metavar="YYYY-MM-DD", help="截止日期早于等于该日")
    p_list.add_argument("--due-after", metavar="YYYY-MM-DD", help="截止日期晚于等于该日")
    p_list.add_argument("-a", "--all", action="store_true", help="包含已完成任务")
    p_list.add_argument("-k", "--keyword", help="按标题关键词筛选")
    p_list.add_argument("--sort", choices=list(SORT_KEYS), default="created",
                        help="排序方式（默认 created）")

    p_done = sub.add_parser("done", help="标记任务为已完成")
    p_done.add_argument("ids", nargs="+", metavar="ID")

    p_rm = sub.add_parser("rm", help="删除任务")
    p_rm.add_argument("ids", nargs="+", metavar="ID")

    return parser


# ---------- 辅助 ----------
def parse_date_arg(value: str | None, option: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{option} 日期格式无效: {value!r}（应为 YYYY-MM-DD）") from None


def format_task(task: Task) -> str:
    box = "x" if task.done else " "
    due = task.due.isoformat() if task.due else "-"
    line = f"[{box}] {task.id}  {task.priority.value:<6} {due:<10} {task.title}"
    if task.is_overdue:
        line += "  (已过期)"
    return line


# ---------- 各子命令 ----------
def cmd_add(service: TaskService, args: argparse.Namespace) -> int:
    task = service.add(
        args.title,
        priority=Priority.parse(args.priority),
        due=parse_date_arg(args.due, "--due"),
    )
    print(f"已创建任务 {task.id}: {task.title}")
    return 0


def cmd_list(service: TaskService, args: argparse.Namespace) -> int:
    tasks = service.list_tasks(
        priority=Priority.parse(args.priority) if args.priority else None,
        due_before=parse_date_arg(args.due_before, "--due-before"),
        due_after=parse_date_arg(args.due_after, "--due-after"),
        include_done=args.all,
        keyword=args.keyword,
        sort=args.sort,
    )
    if not tasks:
        print("没有匹配的任务。")
        return 0
    for task in tasks:
        print(format_task(task))
    print(f"\n共 {len(tasks)} 项")
    return 0


def cmd_done(service: TaskService, args: argparse.Namespace) -> int:
    for task_id in args.ids:
        task = service.complete(task_id)
        print(f"已完成 {task.id}: {task.title}")
    return 0


def cmd_rm(service: TaskService, args: argparse.Namespace) -> int:
    for task_id in args.ids:
        task = service.delete(task_id)
        print(f"已删除 {task.id}: {task.title}")
    return 0


HANDLERS = {"add": cmd_add, "list": cmd_list, "done": cmd_done, "rm": cmd_rm}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        service = TaskService(JsonStorage(args.file))
    except StorageError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2

    try:
        return HANDLERS[args.command](service, args)
    except (ValueError, TaskNotFound, StorageError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())