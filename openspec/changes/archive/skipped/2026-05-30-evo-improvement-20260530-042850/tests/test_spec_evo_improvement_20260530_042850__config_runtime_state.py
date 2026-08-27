"""Tests for runtime state management: _runtime_state_path, load_runtime_state, save_runtime_state.

Spec: config-runtime-state
Change: evo-improvement-20260530-042850
"""

from pathlib import Path
from unittest.mock import patch

from zsiga.config import (
    _runtime_state_path,
    load_runtime_state,
    save_runtime_state,
)


class TestRuntimeStatePathWithZsigaHome:
    """Spec: config-runtime-state — Path with ZSIGA_HOME set."""

    def test_uses_zsiga_home(self, monkeypatch):
        monkeypatch.setenv("ZSIGA_HOME", "/opt/zsiga")
        result = _runtime_state_path()
        assert result == Path("/opt/zsiga/data/runtime_state.yaml")


class TestRuntimeStatePathWithoutZsigaHome:
    """Spec: config-runtime-state — Path without ZSIGA_HOME falls back to config dir."""

    def test_falls_back_to_config_dir(self, monkeypatch):
        monkeypatch.delenv("ZSIGA_HOME", raising=False)
        fake_config_path = Path("/project/zsiga.yaml")
        with patch("zsiga.config._find_config", return_value=fake_config_path):
            result = _runtime_state_path()
        assert result == Path("/project/data/runtime_state.yaml")


class TestLoadRuntimeStateNonExistent:
    """Spec: config-runtime-state — Load from non-existent file returns empty dict."""

    def test_returns_empty_dict(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path / "nonexistent"))
        result = load_runtime_state()
        assert result == {}


class TestLoadRuntimeStateValidFile:
    """Spec: config-runtime-state — Load from valid file returns parsed dict."""

    def test_loads_valid_yaml(self, monkeypatch, tmp_path):
        state_dir = tmp_path / "data"
        state_dir.mkdir()
        state_file = state_dir / "runtime_state.yaml"
        state_file.write_text("active_target: my-project\n")
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        result = load_runtime_state()
        assert result == {"active_target": "my-project"}


class TestLoadRuntimeStateCorruptFile:
    """Spec: config-runtime-state — Load from corrupt file returns empty dict."""

    def test_corrupt_yaml_returns_empty(self, monkeypatch, tmp_path):
        state_dir = tmp_path / "data"
        state_dir.mkdir()
        state_file = state_dir / "runtime_state.yaml"
        state_file.write_text(": {broken\n")
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        result = load_runtime_state()
        assert result == {}


class TestSaveRuntimeStateCreatesParentDirs:
    """Spec: config-runtime-state — Save creates parent directories."""

    def test_creates_dirs_and_writes(self, monkeypatch, tmp_path):
        # Point state to a non-existent subdirectory
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path / "deep" / "nested"))
        save_runtime_state({"active_target": "proj-a"})
        state_file = tmp_path / "deep" / "nested" / "data" / "runtime_state.yaml"
        assert state_file.exists()
        content = state_file.read_text()
        assert "proj-a" in content


class TestSaveAndLoadRoundTrip:
    """Spec: config-runtime-state — Save and load round-trip."""

    def test_round_trip(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        original = {"active_target": "round-trip", "count": 42}
        save_runtime_state(original)
        loaded = load_runtime_state()
        assert loaded == original
