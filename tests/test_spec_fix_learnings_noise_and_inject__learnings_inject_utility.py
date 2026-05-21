"""Tests for spec: learnings-inject-utility.

Covers fetch_relevant_learnings: relevance filtering, max_count, empty results.
"""
import json
from pathlib import Path
from unittest.mock import patch


def _write_jsonl(fpath: Path, records: list[dict]):
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


class TestFetchRelevantLearnings:
    """Verify fetch_relevant_learnings returns correct results."""

    def _call(self, change_name, max_count=5, tmp_dir=None):
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_dir):
            from zsiga.memory.learn import fetch_relevant_learnings
            return fetch_relevant_learnings(change_name, max_count=max_count)

    def test_returns_matching_pipeline_lessons(self, tmp_path):
        _write_jsonl(tmp_path / "learnings.jsonl", [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "avoid lint errors", "ts": "2026-05-09T00:00:00"},
            {"pattern_key": "pipeline.pass.deliver", "takeaway": "Success", "ts": "2026-05-08T00:00:00"},
        ])
        result = self._call("fix-foo-bar", max_count=5, tmp_dir=tmp_path)
        assert "pipeline.fail.implement" in result
        assert "pipeline.pass.deliver" in result

    def test_returns_direct_name_match_lessons(self, tmp_path):
        _write_jsonl(tmp_path / "learnings.jsonl", [
            {"pattern_key": "code.unknown", "takeaway": "fix the unknown", "ts": "2026-05-09T00:00:00"},
        ])
        result = self._call("code-unknown-fix", max_count=5, tmp_dir=tmp_path)
        assert "fix the unknown" in result

    def test_respects_max_count_limit(self, tmp_path):
        records = [
            {"pattern_key": "pipeline.fail.implement", "takeaway": f"lesson {i}", "ts": f"2026-05-{10-i:02d}T00:00:00"}
            for i in range(10)
        ]
        _write_jsonl(tmp_path / "learnings.jsonl", records)
        result = self._call("any-change", max_count=3, tmp_dir=tmp_path)
        bullet_lines = [line for line in result.split("\n") if line.strip().startswith("- [")]
        assert len(bullet_lines) == 3

    def test_returns_empty_string_when_no_matches(self, tmp_path):
        _write_jsonl(tmp_path / "learnings.jsonl", [
            {"pattern_key": "ops.service_management", "takeaway": "use systemctl", "ts": "2026-05-09T00:00:00"},
        ])
        result = self._call("fix-xyz", max_count=5, tmp_dir=tmp_path)
        assert result == ""

    def test_skips_entries_with_missing_takeaway(self, tmp_path):
        _write_jsonl(tmp_path / "learnings.jsonl", [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "", "ts": "2026-05-09T00:00:00"},
            {"pattern_key": "pipeline.fail.implement", "takeaway": "valid takeaway", "ts": "2026-05-08T00:00:00"},
        ])
        result = self._call("any-change", max_count=5, tmp_dir=tmp_path)
        bullet_lines = [line for line in result.split("\n") if line.strip().startswith("- [")]
        assert len(bullet_lines) == 1
        assert "valid takeaway" in result
