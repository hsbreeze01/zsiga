"""Disk-aware filter tests for _extract_must_modify_files."""
import os
from pathlib import Path

from zsiga.pipeline.implementer import (
    _build_must_modify_section,
    _extract_must_modify_files,
)


def test_disk_filter_drops_nonexistent_paths(tmp_path: Path):
    # Create one real file, leave two as scenario examples.
    (tmp_path / "zsiga").mkdir()
    (tmp_path / "zsiga" / "real.py").write_text("# real\n")
    text = (
        "edit `zsiga/real.py` and reference `src/foo.py:42` plus `src/bar.py`"
    )
    assert _extract_must_modify_files(
        text, target_path=str(tmp_path),
    ) == ["zsiga/real.py"]


def test_disk_filter_keeps_new_test_file_pattern(tmp_path: Path):
    # tests/test_thing.py doesn't exist yet, but is a sensible new-file
    # target the spec is asking us to create.
    text = "create `tests/test_thing.py` and modify `pipeline/foo.py`"
    assert _extract_must_modify_files(
        text, target_path=str(tmp_path),
    ) == ["tests/test_thing.py"]


def test_disk_filter_drops_non_test_new_files(tmp_path: Path):
    # Brand-new non-test file that doesn't exist yet should NOT survive
    # the disk filter (false-positive class — example paths in scenarios).
    text = "with a file path like `src/foo.py:42` — only example, not a target"
    assert _extract_must_modify_files(text, target_path=str(tmp_path)) == []


def test_no_target_path_preserves_old_behavior():
    # When target_path is None we must not break the existing extractor
    # contract; tests/test_implementer_must_files.py covers this in detail.
    text = "edit `pipeline/foo.py`"
    assert _extract_must_modify_files(text) == ["pipeline/foo.py"]


def test_build_section_uses_disk_filter(tmp_path: Path):
    (tmp_path / "real").mkdir()
    (tmp_path / "real" / "f.py").write_text("# real\n")
    tasks = "modify `real/f.py` and `nope/missing.py`"
    section = _build_must_modify_section(
        "", "", tasks, target_path=str(tmp_path),
    )
    assert "`real/f.py`" in section
    assert "nope/missing.py" not in section


def test_build_section_returns_empty_when_all_filtered_out(tmp_path: Path):
    tasks = "all examples: `nope/a.py` and `nope/b.py` and `path/to/foo.py`"
    assert _build_must_modify_section(
        "", "", tasks, target_path=str(tmp_path),
    ) == ""
