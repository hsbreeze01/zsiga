"""Unit tests for must-modify-files extraction in implementer."""
from zsiga.pipeline.implementer import (
    _build_must_modify_section,
    _extract_must_modify_files,
)


def test_extracts_inline_backticked_paths():
    text = (
        "Modify `zsiga/pipeline/diagnoser.py` to add tests in "
        "`tests/test_diagnoser.py`."
    )
    assert _extract_must_modify_files(text) == [
        "zsiga/pipeline/diagnoser.py",
        "tests/test_diagnoser.py",
    ]


def test_extracts_unquoted_paths():
    text = "Add unit tests in tests/test_diagnoser.py for the new behavior."
    assert _extract_must_modify_files(text) == ["tests/test_diagnoser.py"]


def test_strips_line_number_suffix():
    text = "See src/bar.py:42 — split the multi-statement line."
    assert _extract_must_modify_files(text) == ["src/bar.py"]


def test_dedupes_across_inputs_preserves_first_seen_order():
    a = "tasks reference zsiga/pipeline/orchestrator.py"
    b = "specs reference zsiga/pipeline/diagnoser.py"
    c = "design reiterates zsiga/pipeline/orchestrator.py"
    assert _extract_must_modify_files(a, b, c) == [
        "zsiga/pipeline/orchestrator.py",
        "zsiga/pipeline/diagnoser.py",
    ]


def test_skips_placeholders_and_examples():
    text = (
        "follow the pattern path/to/your_module.py — for example "
        "your/project/utils.py — only the real one zsiga/foo.py counts"
    )
    assert _extract_must_modify_files(text) == ["zsiga/foo.py"]


def test_ignores_bare_filenames_without_directory():
    # README.md has no '/', should not be treated as a must-modify file.
    text = "update README.md and CHANGELOG.md"
    assert _extract_must_modify_files(text) == []


def test_supports_multiple_extensions():
    text = (
        "edit `site/dashboard.html`, `site/styles.css`, "
        "`config/app.yaml`, `scripts/deploy.sh`"
    )
    assert _extract_must_modify_files(text) == [
        "site/dashboard.html",
        "site/styles.css",
        "config/app.yaml",
        "scripts/deploy.sh",
    ]


def test_build_section_returns_empty_when_no_files():
    assert _build_must_modify_section("nothing", "", "") == ""


def test_build_section_emits_bullets_and_warning():
    tasks = "- [ ] modify `zsiga/agent/loop.py`"
    section = _build_must_modify_section("", "", tasks)
    assert "## MUST-MODIFY Files" in section
    assert "- `zsiga/agent/loop.py`" in section
    assert "spec violation" in section.lower()
