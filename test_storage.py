import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from todo.models import Priority, Task
from todo.storage import JsonStorage, StorageError


class JsonStorageTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "todo.json"
        self.storage = JsonStorage(self.path)

    def test_load_missing_file_returns_empty_list(self):
        self.assertEqual(self.storage.load(), [])

    def test_save_then_load_round_trip(self):
        tasks = [
            Task("写周报", priority=Priority.HIGH, due=date(2025, 1, 1)),
            Task("买菜"),
        ]
        self.storage.save(tasks)
        self.assertEqual(self.storage.load(), tasks)

    def test_saved_file_has_version_and_utf8_titles(self):
        self.storage.save([Task("写周报")])
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(raw["version"], 1)
        self.assertEqual(raw["tasks"][0]["title"], "写周报")

    def test_save_creates_missing_parent_directories(self):
        nested = Path(self._tmp.name) / "a" / "b" / "todo.json"
        JsonStorage(nested).save([Task("x")])
        self.assertTrue(nested.exists())

    def test_corrupt_json_raises_storage_error(self):
        self.path.write_text("{ not json", encoding="utf-8")
        with self.assertRaises(StorageError):
            self.storage.load()

    def test_wrong_shape_raises_storage_error(self):
        self.path.write_text('["a", "b"]', encoding="utf-8")
        with self.assertRaises(StorageError):
            self.storage.load()

    def test_bad_task_payload_raises_storage_error(self):
        self.path.write_text('{"tasks": [{"id": "x"}]}', encoding="utf-8")
        with self.assertRaises(StorageError):
            self.storage.load()