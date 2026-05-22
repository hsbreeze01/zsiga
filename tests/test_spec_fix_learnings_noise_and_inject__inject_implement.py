"""Tests for spec: filter-and-inject.md — Learnings Injection into IMPLEMENT Prompt.

Covers:
- Learnings section injected when relevant entries exist
- No learnings section when no relevant entries
- Maximum 5 learnings injected
"""

import json
from pathlib import Path

import pytest


def _write_jsonl(path: Path, entries: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


@pytest.fixture
def memory_dir(tmp_path, monkeypatch):
    import zsiga.memory.learn as learn_mod
    monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
    return tmp_path


LEARNINGS_3 = [
    {
        "type": "lesson",
        "pattern_key": "pipeline.fail.verify.diagnosed",
        "takeaway": "Diagnosed root cause: missing import",
        "ts": "2025-01-10T10:00:00",
    },
    {
        "type": "lesson",
        "pattern_key": "pipeline.fail.implement",
        "takeaway": "E701 lint error caused test failure",
        "ts": "2025-01-11T10:00:00",
    },
    {
        "type": "lesson",
        "pattern_key": "pipeline.pass.deliver",
        "takeaway": "Small focused changes work well",
        "ts": "2025-01-12T10:00:00",
    },
]


# ---------------------------------------------------------------
# Scenario: Learnings section injected when relevant entries exist
# ---------------------------------------------------------------


class TestLearningsSectionInjected:
    def test_section_header_present(self, memory_dir):
        from zsiga.pipeline.implementer import _build_learnings_section
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, LEARNINGS_3)

        section = _build_learnings_section("test-change", max_results=5)
        assert "## Previous Learnings (avoid repeating mistakes)" in section

    def test_section_contains_formatted_lines(self, memory_dir):
        from zsiga.pipeline.implementer import _build_learnings_section
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, LEARNINGS_3)

        section = _build_learnings_section("test-change", max_results=5)
        assert "- [pipeline.fail.verify.diagnosed]" in section
        assert "- [pipeline.fail.implement]" in section
        assert "Diagnosed root cause: missing import" in section

    def test_exact_count_of_lines(self, memory_dir):
        from zsiga.pipeline.implementer import _build_learnings_section
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, LEARNINGS_3)

        section = _build_learnings_section("test-change", max_results=5)
        learning_lines = [line for line in section.strip().split("\n") if line.startswith("- [")]
        assert len(learning_lines) == 3


# ---------------------------------------------------------------
# Scenario: No learnings section when no relevant entries
# ---------------------------------------------------------------


class TestNoLearningsSectionWhenEmpty:
    def test_empty_string_when_no_learnings(self, memory_dir):
        from zsiga.pipeline.implementer import _build_learnings_section
        # No learnings.jsonl
        section = _build_learnings_section("test-change", max_results=5)
        assert section == ""

    def test_no_section_when_only_noise(self, memory_dir):
        from zsiga.pipeline.implementer import _build_learnings_section
        lf = memory_dir / "learnings.jsonl"
        noise = [
            {"type": "lesson", "pattern_key": "daemon.cycle_error", "takeaway": "noise", "ts": "2025-01-01T00:00:00"},
            {"type": "lesson", "pattern_key": "code.unknown", "takeaway": "review error", "ts": "2025-01-02T00:00:00"},
        ]
        _write_jsonl(lf, noise)

        section = _build_learnings_section("test-change", max_results=5)
        assert "## Previous Learnings" not in section
        assert section == ""


# ---------------------------------------------------------------
# Scenario: Maximum 5 learnings injected
# ---------------------------------------------------------------


class TestMax5Learnings:
    def test_at_most_5_lines(self, memory_dir):
        from zsiga.pipeline.implementer import _build_learnings_section
        lf = memory_dir / "learnings.jsonl"
        entries = []
        for i in range(8):
            entries.append({
                "type": "lesson",
                "pattern_key": f"pipeline.fail.type{i}",
                "takeaway": f"Failure lesson {i} with enough characters to pass",
                "ts": f"2025-01-{10+i:02d}T10:00:00",
            })
        _write_jsonl(lf, entries)

        section = _build_learnings_section("test-change", max_results=5)
        learning_lines = [line for line in section.strip().split("\n") if line.startswith("- [")]
        assert len(learning_lines) <= 5
