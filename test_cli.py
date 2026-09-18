import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from todo.cli import main


class CliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "todo.json"

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["--file", str(self.db), *args])
        return code, out.getvalue(), err.getvalue()

    def read_db(self):
        return json.loads(self.db.read_text(encoding="utf-8"))

    def test_full_workflow(self):
        code, out, _ = self.run_cli("add", "写周报", "-p", "high", "-d", "2025-01-01")
        self.assertEqual(code, 0)
        self.assertIn("已创建任务", out)

        task_id = self.read_db()["tasks"][0]["id"]

        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("写周报", out)

        code, out, _ = self.run_cli("done", task_id)
        self.assertEqual(code, 0)

        # 默认隐藏已完成
        _, out, _ = self.run_cli("list")
        self.assertNotIn("写周报", out)
        _, out, _ = self.run_cli("list", "--all")
        self.assertIn("写周报", out)

        code, _, _ = self.run_cli("rm", task_id)
        self.assertEqual(code, 0)
        self.assertEqual(self.read_db()["tasks"], [])

    def test_list_filters_by_priority(self):
        self.run_cli("add", "高", "-p", "high")
        self.run_cli("add", "低", "-p", "low")
        _, out, _ = self.run_cli("list", "-p", "high")
        self.assertIn("高", out)
        self.assertNotIn("低", out)

    def test_unknown_id_returns_error_code(self):
        code, _, err = self.run_cli("done", "deadbeef")
        self.assertEqual(code, 1)
        self.assertIn("找不到任务", err)

    def test_invalid_date_returns_error_code(self):
        code, _, err = self.run_cli("add", "x", "-d", "2025/01/01")
        self.assertEqual(code, 1)
        self.assertIn("日期格式无效", err)

    def test_corrupt_db_returns_error_code(self):
        self.db.write_text("{ broken", encoding="utf-8")
        code, _, err = self.run_cli("list")
        self.assertEqual(code, 2)
        self.assertIn("错误", err)

    def test_empty_list_prints_friendly_message(self):
        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("没有匹配的任务", out)