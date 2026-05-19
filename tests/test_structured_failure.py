"""Tests for structured failure recording and success recording."""

import json
from pathlib import Path

from zsiga.memory.learn import _classify_failure, record_outcome, record_success


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_learnings(path: Path) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# _classify_failure two-layer classification
# ---------------------------------------------------------------------------

class TestClassifyFailure:

    def test_lint_e401(self):
        result = _classify_failure("E401 Multiple imports on one line")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "lint.e401"
        assert "import" in result["prevention"].lower()

    def test_lint_e701(self):
        result = _classify_failure("E701 Multiple statements on one line (colon)")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "lint.e701"

    def test_lint_e702(self):
        result = _classify_failure("E702 Multiple statements on one line (semicolon)")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "lint.e702"

    def test_lint_e722(self):
        result = _classify_failure("E722 Do not use bare except")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "lint.e722"

    def test_lint_e501(self):
        result = _classify_failure("E501 line too long")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "lint.e501"

    def test_lint_e741(self):
        result = _classify_failure("E741 ambiguous variable name 'l'")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "lint.e741"

    def test_test_assertion(self):
        result = _classify_failure("FAILED test_something - AssertionError: expected 1")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "test.assertion"

    def test_test_import(self):
        result = _classify_failure("ImportError: cannot import name 'foo'")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "test.import"

    def test_test_module_not_found(self):
        result = _classify_failure("ModuleNotFoundError: No module named 'bar'")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "test.import"

    def test_test_session(self):
        result = _classify_failure("1 failed, 3 passed in test session")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "test.assertion"

    def test_timeout(self):
        result = _classify_failure("timeout after 120s")
        assert result["error_domain"] == "infrastructure"
        assert result["root_cause_key"] == "timeout"

    def test_pipeline_decompose(self):
        result = _classify_failure("decompose returned false positive")
        assert result["error_domain"] == "pipeline"
        assert result["root_cause_key"] == "decompose.false_positive"

    def test_pipeline_proposal_empty(self):
        result = _classify_failure("proposal is empty")
        assert result["error_domain"] == "pipeline"
        assert result["root_cause_key"] == "proposal.empty"

    def test_infrastructure_ssh(self):
        result = _classify_failure("SSH connection timeout")
        assert result["error_domain"] == "infrastructure"
        assert result["root_cause_key"] == "ssh.timeout"

    def test_infrastructure_rate_limit(self):
        result = _classify_failure("rate_limit exceeded, 429 Too Many Requests")
        assert result["error_domain"] == "infrastructure"
        assert result["root_cause_key"] == "api.rate_limit"

    def test_unknown_error(self):
        result = _classify_failure("something unexpected happened")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "unknown"
        assert result["prevention"] == "review error and adjust approach"

    def test_empty_detail(self):
        result = _classify_failure("")
        assert result["error_domain"] == "code"
        assert result["root_cause_key"] == "unknown"


# ---------------------------------------------------------------------------
# record_outcome backward compatibility + new fields
# ---------------------------------------------------------------------------

class TestRecordOutcome:

    def test_backward_compatible_auto_infers(self, tmp_path):
        """Old-style call auto-infers error_domain and root_cause."""
        import zsiga.memory.learn as learn_mod
        original_dir = learn_mod._MEMORY_DIR
        learn_mod._MEMORY_DIR = tmp_path
        try:
            record_outcome("change-1", "proj", False, "implement",
                           detail="E401 Multiple imports")
            records = _read_learnings(tmp_path / "learnings.jsonl")
            assert len(records) == 1
            rec = records[0]
            assert rec["type"] == "lesson"
            assert rec["error_domain"] == "code"
            assert rec["root_cause"] == "lint.e401"
            assert rec["prevention"] != ""
            assert rec["what_happened"] != ""
            assert rec["pattern_key"] == "code.lint.e401"
        finally:
            learn_mod._MEMORY_DIR = original_dir

    def test_explicit_params_override(self, tmp_path):
        """Caller-provided params take precedence over auto-infer."""
        import zsiga.memory.learn as learn_mod
        original_dir = learn_mod._MEMORY_DIR
        learn_mod._MEMORY_DIR = tmp_path
        try:
            record_outcome(
                "change-2", "proj", False, "implement",
                detail="some detail",
                error_domain="pipeline",
                root_cause="decompose.false_positive",
                prevention="validate paths",
            )
            records = _read_learnings(tmp_path / "learnings.jsonl")
            rec = records[0]
            assert rec["error_domain"] == "pipeline"
            assert rec["root_cause"] == "decompose.false_positive"
            assert rec["prevention"] == "validate paths"
            assert rec["pattern_key"] == "pipeline.decompose.false_positive"
        finally:
            learn_mod._MEMORY_DIR = original_dir

    def test_success_does_not_record(self, tmp_path):
        """record_outcome with success=True should not write anything."""
        import zsiga.memory.learn as learn_mod
        original_dir = learn_mod._MEMORY_DIR
        learn_mod._MEMORY_DIR = tmp_path
        try:
            record_outcome("change-3", "proj", True, "deliver")
            assert not (tmp_path / "learnings.jsonl").exists()
        finally:
            learn_mod._MEMORY_DIR = original_dir

    def test_lesson_has_all_structured_fields(self, tmp_path):
        """Each lesson record must have error_domain, root_cause, prevention."""
        import zsiga.memory.learn as learn_mod
        original_dir = learn_mod._MEMORY_DIR
        learn_mod._MEMORY_DIR = tmp_path
        try:
            record_outcome("change-4", "proj", False, "verify",
                           detail="FAILED test session")
            records = _read_learnings(tmp_path / "learnings.jsonl")
            rec = records[0]
            for field in ("error_domain", "root_cause", "prevention", "what_happened"):
                assert field in rec
                assert rec[field]  # non-empty
        finally:
            learn_mod._MEMORY_DIR = original_dir


# ---------------------------------------------------------------------------
# record_success
# ---------------------------------------------------------------------------

class TestRecordSuccess:

    def test_first_pass_no_fix_attempts(self, tmp_path):
        """All phases with no fix_attempts → first_pass=True."""
        import zsiga.memory.learn as learn_mod
        original_dir = learn_mod._MEMORY_DIR
        learn_mod._MEMORY_DIR = tmp_path
        try:
            record_success("change-ok", "proj",
                           phase_records=[
                               {"phase": "implement", "fix_attempts": 0},
                               {"phase": "verify", "fix_attempts": 0},
                           ],
                           total_turns=4, total_seconds=120.5)
            records = _read_learnings(tmp_path / "learnings.jsonl")
            assert len(records) == 1
            rec = records[0]
            assert rec["type"] == "success_pattern"
            assert rec["first_pass"] is True
            assert rec["fix_attempts"] == 0
            assert rec["total_turns"] == 4
            assert rec["total_seconds"] == 120.5
            assert rec["pattern_key"] == "pipeline.pass.deliver"
            assert rec["error_domain"] == "success"
            assert rec["severity"] == "low"
        finally:
            learn_mod._MEMORY_DIR = original_dir

    def test_fix_loop_first_pass_false(self, tmp_path):
        """Phase with fix_attempts > 0 → first_pass=False."""
        import zsiga.memory.learn as learn_mod
        original_dir = learn_mod._MEMORY_DIR
        learn_mod._MEMORY_DIR = tmp_path
        try:
            record_success("change-fix", "proj",
                           phase_records=[
                               {"phase": "implement", "fix_attempts": 2},
                           ],
                           total_turns=6, total_seconds=300.0)
            records = _read_learnings(tmp_path / "learnings.jsonl")
            rec = records[0]
            assert rec["first_pass"] is False
            assert rec["fix_attempts"] == 2
        finally:
            learn_mod._MEMORY_DIR = original_dir

    def test_no_phase_records_first_pass(self, tmp_path):
        """No phase_records → first_pass=True, fix_attempts=0."""
        import zsiga.memory.learn as learn_mod
        original_dir = learn_mod._MEMORY_DIR
        learn_mod._MEMORY_DIR = tmp_path
        try:
            record_success("change-simple", "proj")
            records = _read_learnings(tmp_path / "learnings.jsonl")
            rec = records[0]
            assert rec["first_pass"] is True
            assert rec["fix_attempts"] == 0
        finally:
            learn_mod._MEMORY_DIR = original_dir

    def test_record_has_ts_and_change_name(self, tmp_path):
        """Record includes ts and change_name."""
        import zsiga.memory.learn as learn_mod
        original_dir = learn_mod._MEMORY_DIR
        learn_mod._MEMORY_DIR = tmp_path
        try:
            record_success("my-change", "proj", total_turns=2, total_seconds=60.0)
            records = _read_learnings(tmp_path / "learnings.jsonl")
            rec = records[0]
            assert rec["change_name"] == "my-change"
            assert "ts" in rec
            assert rec["ts"] != ""
        finally:
            learn_mod._MEMORY_DIR = original_dir
