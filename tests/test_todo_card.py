"""Tests for dashboard todo card rendering."""
import json
import os
from pathlib import Path

from zsiga.metrics.dashboard import _load_todos, _todo_section


def _write_todo_json(todos_dir: str, filename: str, items: list[dict]):
    p = Path(todos_dir) / filename
    p.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return p


class TestLoadTodos:
    def test_no_todos_dir(self, tmp_path):
        result = _load_todos(str(tmp_path))
        assert result == []

    def test_empty_todos_dir(self, tmp_path):
        (tmp_path / "data" / "todos").mkdir(parents=True)
        result = _load_todos(str(tmp_path))
        assert result == []

    def test_single_todo_file(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        items = [
            {"id": "t1", "content": "Task A", "status": "completed"},
            {"id": "t2", "content": "Task B", "status": "in_progress"},
            {"id": "t3", "content": "Task C", "status": "pending"},
        ]
        _write_todo_json(str(todos_dir), "change-xyz.json", items)
        result = _load_todos(str(tmp_path))
        assert len(result) == 1
        assert result[0]["name"] == "change-xyz"
        assert result[0]["summary"] == "1/3 completed (33%)"
        assert result[0]["pct"] == 33
        assert len(result[0]["items"]) == 3

    def test_multiple_todo_files_sorted_by_mtime(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        items_a = [{"id": "t1", "content": "A", "status": "completed"}]
        items_b = [{"id": "t1", "content": "B", "status": "pending"}]
        items_c = [{"id": "t1", "content": "C", "status": "in_progress"}]
        fa = _write_todo_json(str(todos_dir), "change-a.json", items_a)
        fb = _write_todo_json(str(todos_dir), "change-b.json", items_b)
        fc = _write_todo_json(str(todos_dir), "change-c.json", items_c)
        # Set mtimes so c is newest, a is oldest
        os.utime(str(fa), (1000, 1000))
        os.utime(str(fb), (2000, 2000))
        os.utime(str(fc), (3000, 3000))
        result = _load_todos(str(tmp_path))
        assert len(result) == 3
        assert result[0]["name"] == "change-c"
        assert result[1]["name"] == "change-b"
        assert result[2]["name"] == "change-a"

    def test_max_5_todos(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        items = [{"id": "t1", "content": "X", "status": "pending"}]
        for i in range(7):
            f = _write_todo_json(str(todos_dir), f"change-{i}.json", items)
            os.utime(str(f), (1000 + i, 1000 + i))
        result = _load_todos(str(tmp_path))
        assert len(result) == 5

    def test_invalid_json_skipped(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        (todos_dir / "bad.json").write_text("not json{{{", encoding="utf-8")
        items = [{"id": "t1", "content": "Good", "status": "completed"}]
        _write_todo_json(str(todos_dir), "good.json", items)
        result = _load_todos(str(tmp_path))
        assert len(result) == 1
        assert result[0]["name"] == "good"

    def test_empty_json_skipped(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        (todos_dir / "empty.json").write_text("", encoding="utf-8")
        result = _load_todos(str(tmp_path))
        assert result == []


class TestTodoSection:
    def test_no_todos_returns_empty(self, tmp_path):
        result = _todo_section(str(tmp_path))
        assert result == ""

    def test_renders_todo_section(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        items = [
            {"id": "t1", "content": "Done task", "status": "completed"},
            {"id": "t2", "content": "WIP task", "status": "in_progress"},
            {"id": "t3", "content": "Todo task", "status": "pending"},
        ]
        _write_todo_json(str(todos_dir), "change-xyz.json", items)
        result = _todo_section(str(tmp_path))
        assert "📋 Todo Progress" in result
        assert "change-xyz" in result
        assert "1/3 completed (33%)" in result
        assert "✅" in result
        assert "🔄" in result
        assert "⬜" in result
        assert "progress" in result

    def test_uses_existing_css_classes(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        items = [{"id": "t1", "content": "Task", "status": "completed"}]
        _write_todo_json(str(todos_dir), "test-change.json", items)
        result = _todo_section(str(tmp_path))
        assert 'class="milestone"' in result
        assert 'class="criterion"' in result
        assert 'class="progress"' in result
        assert 'class="fill"' in result

    def test_100_percent_uses_green(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        items = [
            {"id": "t1", "content": "A", "status": "completed"},
            {"id": "t2", "content": "B", "status": "completed"},
        ]
        _write_todo_json(str(todos_dir), "done.json", items)
        result = _todo_section(str(tmp_path))
        assert "#22c55e" in result

    def test_cancelled_and_blocked_icons(self, tmp_path):
        todos_dir = tmp_path / "data" / "todos"
        todos_dir.mkdir(parents=True)
        items = [
            {"id": "t1", "content": "Cancelled", "status": "cancelled"},
            {"id": "t2", "content": "Blocked", "status": "blocked"},
        ]
        _write_todo_json(str(todos_dir), "issues.json", items)
        result = _todo_section(str(tmp_path))
        assert "🚫" in result
        assert "🔒" in result
