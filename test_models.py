import json
import unittest
from datetime import date

from todo.models import Priority, Task


class PriorityTest(unittest.TestCase):
    def test_parse_is_case_and_space_insensitive(self):
        self.assertIs(Priority.parse("HIGH"), Priority.HIGH)
        self.assertIs(Priority.parse("  medium "), Priority.MEDIUM)

    def test_parse_rejects_unknown_value(self):
        with self.assertRaises(ValueError):
            Priority.parse("urgent")

    def test_rank_orders_low_medium_high(self):
        self.assertLess(Priority.LOW.rank, Priority.MEDIUM.rank)
        self.assertLess(Priority.MEDIUM.rank, Priority.HIGH.rank)


class TaskTest(unittest.TestCase):
    def test_defaults(self):
        task = Task("买菜")
        self.assertEqual(task.priority, Priority.MEDIUM)
        self.assertIsNone(task.due)
        self.assertFalse(task.done)
        self.assertEqual(len(task.id), 8)

    def test_title_is_stripped(self):
        self.assertEqual(Task("  写周报  ").title, "写周报")

    def test_empty_title_rejected(self):
        with self.assertRaises(ValueError):
            Task("   ")

    def test_priority_accepts_string(self):
        self.assertIs(Task("x", priority="high").priority, Priority.HIGH)

    def test_due_accepts_iso_string(self):
        self.assertEqual(Task("x", due="2025-01-31").due, date(2025, 1, 31))

    def test_invalid_due_rejected(self):
        with self.assertRaises(ValueError):
            Task("x", due="2025/01/31")

    def test_round_trip_through_dict(self):
        task = Task("写周报", priority=Priority.HIGH, due=date(2025, 1, 1))
        self.assertEqual(Task.from_dict(task.to_dict()), task)

    def test_from_dict_tolerates_missing_optional_fields(self):
        task = Task.from_dict({"id": "abc12345", "title": "旧数据"})
        self.assertEqual(task.priority, Priority.MEDIUM)
        self.assertIsNone(task.due)
        self.assertFalse(task.done)

    def test_to_dict_is_json_serializable(self):
        payload = json.dumps(Task("x", due=date(2025, 1, 1)).to_dict())
        self.assertIn('"due": "2025-01-01"', payload)

    def test_is_overdue(self):
        self.assertTrue(Task("x", due=date(2000, 1, 1)).is_overdue)
        self.assertFalse(Task("x", due=date(2000, 1, 1), done=True).is_overdue)
        self.assertFalse(Task("x", due=date(2999, 1, 1)).is_overdue)