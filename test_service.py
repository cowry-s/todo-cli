import unittest
from datetime import date

from todo.models import Priority, Task
from todo.service import TaskNotFound, TaskService


class InMemoryStorage:
    """测试替身：接口与 JsonStorage 一致，但走内存 + 序列化往返。"""

    def __init__(self, tasks=()):
        self.saved: list[Task] = [Task.from_dict(t.to_dict()) for t in tasks]

    def load(self):
        return [Task.from_dict(t.to_dict()) for t in self.saved]

    def save(self, tasks):
        self.saved = [Task.from_dict(t.to_dict()) for t in tasks]


class ServiceTestBase(unittest.TestCase):
    def make_service(self, *tasks) -> TaskService:
        self.storage = InMemoryStorage(tasks)
        return TaskService(self.storage)


class AddTest(ServiceTestBase):
    def test_add_persists_and_is_reloadable(self):
        service = self.make_service()
        task = service.add("写周报", priority=Priority.HIGH, due=date(2025, 1, 1))

        reloaded = TaskService(self.storage)
        self.assertEqual(reloaded.tasks, (task,))

    def test_add_rejects_empty_title(self):
        service = self.make_service()
        with self.assertRaises(ValueError):
            service.add("   ")


class CompleteTest(ServiceTestBase):
    def test_complete_marks_done_and_persists(self):
        service = self.make_service()
        task = service.add("写周报")
        service.complete(task.id)

        self.assertTrue(TaskService(self.storage).tasks[0].done)

    def test_complete_unknown_id_raises(self):
        service = self.make_service()
        with self.assertRaises(TaskNotFound):
            service.complete("nope")


class DeleteTest(ServiceTestBase):
    def test_delete_removes_and_persists(self):
        service = self.make_service()
        task = service.add("写周报")
        service.delete(task.id)

        self.assertEqual(TaskService(self.storage).tasks, ())

    def test_delete_unknown_id_raises(self):
        service = self.make_service()
        with self.assertRaises(TaskNotFound):
            service.delete("nope")


class LookupTest(ServiceTestBase):
    def test_unique_prefix_is_accepted(self):
        service = self.make_service(Task("a", id="abcd1111"), Task("b", id="wxyz9999"))
        self.assertEqual(service.get("abcd").title, "a")

    def test_ambiguous_prefix_raises(self):
        service = self.make_service(Task("a", id="abcd1111"), Task("b", id="abcd2222"))
        with self.assertRaises(TaskNotFound):
            service.get("abcd")


class ListTest(ServiceTestBase):
    def setUp(self):
        self.service = self.make_service(
            Task("高优先-近截止", priority=Priority.HIGH, due=date(2025, 1, 10)),
            Task("低优先-远截止", priority=Priority.LOW, due=date(2025, 6, 30)),
            Task("中优先-无截止", priority=Priority.MEDIUM),
        )

    def titles(self, tasks):
        return [t.title for t in tasks]

    def test_hides_done_by_default(self):
        done = self.service.add("已完成任务")
        self.service.complete(done.id)
        self.assertNotIn("已完成任务", self.titles(self.service.list_tasks()))
        self.assertIn("已完成任务", self.titles(self.service.list_tasks(include_done=True)))

    def test_filter_by_priority(self):
        result = self.service.list_tasks(priority=Priority.HIGH)
        self.assertEqual(self.titles(result), ["高优先-近截止"])

    def test_filter_due_before(self):
        result = self.service.list_tasks(due_before=date(2025, 3, 1))
        self.assertEqual(self.titles(result), ["高优先-近截止"])

    def test_filter_due_after(self):
        result = self.service.list_tasks(due_after=date(2025, 3, 1))
        self.assertEqual(self.titles(result), ["低优先-远截止"])

    def test_tasks_without_due_are_excluded_by_date_filters(self):
        self.assertEqual(self.service.list_tasks(due_before=date(2999, 1, 1)).__len__(), 2)

    def test_filter_by_keyword_is_case_insensitive(self):
        service = self.make_service(Task("Write Report"), Task("买菜"))
        self.assertEqual(
            [t.title for t in service.list_tasks(keyword="report")], ["Write Report"]
        )

    def test_sort_by_priority_puts_high_first(self):
        result = self.service.list_tasks(sort="priority")
        self.assertEqual(result[0].priority, Priority.HIGH)

    def test_sort_by_due_puts_soonest_first_and_undated_last(self):
        result = self.service.list_tasks(sort="due")
        self.assertEqual(
            self.titles(result), ["高优先-近截止", "低优先-远截止", "中优先-无截止"]
        )

    def test_unknown_sort_key_raises(self):
        with self.assertRaises(ValueError):
            self.service.list_tasks(sort="magic")

    def test_filters_combine(self):
        result = self.service.list_tasks(
            priority=Priority.HIGH, due_before=date(2024, 1, 1)
        )
        self.assertEqual(result, [])