"""Tests for the Change Conflict Detector (dependency module)."""

import os
import tempfile

from zsiga.pipeline.dependency import (
    ChangeConflictDetector,
    ChangeInfo,
    _extract_target_files,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_changes_dir(tree: dict, base: str = None) -> str:
    """Create a temporary changes directory from a dict spec.

    ``tree`` maps change-id → {filename: content}.
    A special key ``None`` creates files at the changes-dir root.
    """
    tmpdir = base or tempfile.mkdtemp()
    for change_id, files in tree.items():
        if change_id is None:
            # Files at changes-dir root (e.g. archive)
            continue
        change_path = os.path.join(tmpdir, change_id)
        os.makedirs(change_path, exist_ok=True)
        if isinstance(files, dict):
            for fname, content in files.items():
                with open(os.path.join(change_path, fname), "w") as f:
                    f.write(content)
    # Handle archive dir if specified
    if None in tree and isinstance(tree[None], dict):
        archive_path = os.path.join(tmpdir, "archive")
        os.makedirs(archive_path, exist_ok=True)
    return tmpdir


# ---------------------------------------------------------------------------
# CCD-04: Target Files Extraction
# ---------------------------------------------------------------------------

class TestExtractTargetFiles:
    """CCD-04 scenarios."""

    def test_design_with_explicit_file_list(self):
        content = (
            "## Files to Add/Modify\n"
            "- `zsiga/pipeline/dependency.py` — New module\n"
            "- `tests/test_dependency.py` — New test file\n"
        )
        result = _extract_target_files(content)
        assert result == {"zsiga/pipeline/dependency.py", "tests/test_dependency.py"}

    def test_design_with_no_file_references(self):
        content = "## Overview\nThis change adds a new feature.\n"
        result = _extract_target_files(content)
        assert result == set()

    def test_deduplicated_paths(self):
        content = (
            "Modify `zsiga/pipeline/utils.py` and also `zsiga/pipeline/utils.py` again.\n"
        )
        result = _extract_target_files(content)
        assert result == {"zsiga/pipeline/utils.py"}

    def test_extracts_md_files_too(self):
        content = "See `docs/changelog.md` for details.\n"
        result = _extract_target_files(content)
        assert result == {"docs/changelog.md"}

    def test_ignores_non_py_md_extensions(self):
        content = "Check `config.yaml` and `Makefile`.\n"
        result = _extract_target_files(content)
        assert result == set()


# ---------------------------------------------------------------------------
# CCD-01: Scan Pending Changes
# ---------------------------------------------------------------------------

class TestScanChanges:
    """CCD-01 scenarios."""

    def test_multiple_pending_changes_found(self):
        tmpdir = _make_changes_dir({
            "change-a": {
                "proposal.md": "# A",
                "design.md": "Files: `zsiga/pipeline/a.py`, `tests/test_a.py`",
                "tasks.md": "# Tasks A",
            },
            "change-b": {
                "proposal.md": "# B",
                "design.md": "Files: `zsiga/pipeline/b.py`",
                "tasks.md": "# Tasks B",
            },
            "change-c": {
                "proposal.md": "# C",
                "design.md": "Files: `zsiga/pipeline/c.py`",
                "tasks.md": "# Tasks C",
            },
        })
        detector = ChangeConflictDetector()
        result = detector.scan_changes(tmpdir)
        assert len(result) == 3
        ids = {r.id for r in result}
        assert ids == {"change-a", "change-b", "change-c"}
        # Each should have target_files parsed
        a_info = next(r for r in result if r.id == "change-a")
        assert "zsiga/pipeline/a.py" in a_info.target_files
        assert "tests/test_a.py" in a_info.target_files

    def test_empty_changes_directory(self):
        tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmpdir, "archive"), exist_ok=True)
        detector = ChangeConflictDetector()
        result = detector.scan_changes(tmpdir)
        assert result == []

    def test_change_missing_design_md(self):
        tmpdir = _make_changes_dir({
            "change-no-design": {
                "proposal.md": "# No design",
            },
        })
        detector = ChangeConflictDetector()
        result = detector.scan_changes(tmpdir)
        assert len(result) == 1
        assert result[0].id == "change-no-design"
        assert result[0].target_files == set()

    def test_archive_directory_skipped(self):
        tmpdir = _make_changes_dir({
            "change-a": {
                "design.md": "`foo.py`",
            },
            None: {},
        })
        # Create an archive subdirectory with a design.md to ensure it's skipped
        archive_dir = os.path.join(tmpdir, "archive")
        os.makedirs(archive_dir, exist_ok=True)
        with open(os.path.join(archive_dir, "design.md"), "w") as f:
            f.write("`archive.py`")
        detector = ChangeConflictDetector()
        result = detector.scan_changes(tmpdir)
        ids = {r.id for r in result}
        assert "archive" not in ids
        assert "change-a" in ids


# ---------------------------------------------------------------------------
# CCD-02: Find File Overlaps
# ---------------------------------------------------------------------------

class TestFindOverlaps:
    """CCD-02 scenarios."""

    def test_two_changes_share_one_file(self):
        changes = [
            ChangeInfo(id="A", target_files={"zsiga/pipeline/utils.py", "zsiga/pipeline/diagnoser.py"}, change_dir="/tmp/a"),
            ChangeInfo(id="B", target_files={"zsiga/pipeline/utils.py", "tests/test_foo.py"}, change_dir="/tmp/b"),
        ]
        detector = ChangeConflictDetector()
        result = detector.find_overlaps(changes)
        assert len(result) == 1
        assert result[0].change_ids == ("A", "B")
        assert result[0].shared_files == ["zsiga/pipeline/utils.py"]

    def test_no_overlapping_files(self):
        changes = [
            ChangeInfo(id="A", target_files={"a.py"}, change_dir="/tmp/a"),
            ChangeInfo(id="B", target_files={"b.py"}, change_dir="/tmp/b"),
            ChangeInfo(id="C", target_files={"c.py"}, change_dir="/tmp/c"),
        ]
        detector = ChangeConflictDetector()
        result = detector.find_overlaps(changes)
        assert result == []

    def test_three_changes_all_share_one_file(self):
        changes = [
            ChangeInfo(id="A", target_files={"zsiga/pipeline/utils.py"}, change_dir="/tmp/a"),
            ChangeInfo(id="B", target_files={"zsiga/pipeline/utils.py"}, change_dir="/tmp/b"),
            ChangeInfo(id="C", target_files={"zsiga/pipeline/utils.py"}, change_dir="/tmp/c"),
        ]
        detector = ChangeConflictDetector()
        result = detector.find_overlaps(changes)
        assert len(result) == 3
        pairs = {cp.change_ids for cp in result}
        assert pairs == {("A", "B"), ("A", "C"), ("B", "C")}
        for cp in result:
            assert "zsiga/pipeline/utils.py" in cp.shared_files

    def test_changes_with_empty_target_files_ignored(self):
        changes = [
            ChangeInfo(id="A", target_files=set(), change_dir="/tmp/a"),
            ChangeInfo(id="B", target_files={"b.py"}, change_dir="/tmp/b"),
        ]
        detector = ChangeConflictDetector()
        result = detector.find_overlaps(changes)
        assert result == []


# ---------------------------------------------------------------------------
# CCD-03: Suggest Execution Order
# ---------------------------------------------------------------------------

class TestSuggestOrder:
    """CCD-03 scenarios."""

    def test_fewer_dependencies_first(self):
        changes = [
            ChangeInfo(id="A", target_files={"f1.py", "f2.py", "f3.py"}, change_dir="/tmp/a"),
            ChangeInfo(id="B", target_files={"f1.py"}, change_dir="/tmp/b"),
        ]
        detector = ChangeConflictDetector()
        result = detector.suggest_order(changes)
        # No overlaps, so sort by overlap count (both 0), then lexicographic
        assert result == ["A", "B"]

    def test_overlapping_changes_after_non_overlapping(self):
        changes = [
            ChangeInfo(id="A", target_files={"unique.py"}, change_dir="/tmp/a"),
            ChangeInfo(id="B", target_files={"shared.py"}, change_dir="/tmp/b"),
            ChangeInfo(id="C", target_files={"shared.py"}, change_dir="/tmp/c"),
        ]
        detector = ChangeConflictDetector()
        result = detector.suggest_order(changes)
        # A has 0 overlaps, B and C each have 1
        assert result.index("A") < result.index("B")
        assert result.index("A") < result.index("C")

    def test_all_changes_overlap_deterministic(self):
        changes = [
            ChangeInfo(id="delta", target_files={"shared.py"}, change_dir="/tmp/d"),
            ChangeInfo(id="alpha", target_files={"shared.py"}, change_dir="/tmp/a"),
            ChangeInfo(id="charlie", target_files={"shared.py"}, change_dir="/tmp/c"),
            ChangeInfo(id="bravo", target_files={"shared.py"}, change_dir="/tmp/b"),
        ]
        detector = ChangeConflictDetector()
        result = detector.suggest_order(changes)
        # All have 3 overlap edges, so tiebreak by id
        assert result == ["alpha", "bravo", "charlie", "delta"]

    def test_single_change(self):
        changes = [
            ChangeInfo(id="only-one", target_files={"f.py"}, change_dir="/tmp/o"),
        ]
        detector = ChangeConflictDetector()
        result = detector.suggest_order(changes)
        assert result == ["only-one"]
