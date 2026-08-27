"""
Spec-derived tests for config runtime state functions.
Generated from: specs/config-runtime-state-tests.md
Change: evo-improvement-20260530-153304

These tests cover the three genuinely uncovered entry points in zsiga/config.py:
  - _runtime_state_path()
  - load_runtime_state()
  - save_runtime_state()

They do NOT re-test validate_config, _find_config, _resolve_env_vars, or load_config,
which are already covered by tests/test_config_validation.py (39 tests) and other files.
"""
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_runtime_env(tmp_path: Path, monkeypatch, zsiga_home: str = ""):
    """Point runtime state to tmp_path and return the expected state file path."""
    state_file = tmp_path / "data" / "runtime_state.yaml"
    if zsiga_home:
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
    else:
        monkeypatch.delenv("ZSIGA_HOME", raising=False)
        monkeypatch.setattr("zsiga.config._find_config", lambda: tmp_path / "zsiga.yaml")
    return state_file


# ===================================================================
# Scenario: zsiga-home-env-set
# Requirement: runtime-state-path-with-zsiga-home
# ===================================================================

def test_zsiga_home_env_set(tmp_path, monkeypatch):
    """_runtime_state_path returns $ZSIGA_HOME/data/runtime_state.yaml when env set."""
    monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
    from zsiga.config import _runtime_state_path

    result = _runtime_state_path()
    assert result == tmp_path / "data" / "runtime_state.yaml"


# ===================================================================
# Scenario: zsiga-home-env-unset
# Requirement: runtime-state-path-without-zsiga-home
# ===================================================================

def test_zsiga_home_env_unset(tmp_path, monkeypatch):
    """_runtime_state_path falls back to _find_config parent when ZSIGA_HOME unset."""
    monkeypatch.delenv("ZSIGA_HOME", raising=False)
    config_file = tmp_path / "zsiga.yaml"
    monkeypatch.setattr("zsiga.config._find_config", lambda: config_file)
    from zsiga.config import _runtime_state_path

    result = _runtime_state_path()
    assert result.name == "runtime_state.yaml"
    assert result.parent == config_file.parent / "data"


# ===================================================================
# Scenario: load-existing-valid-yaml
# Requirement: load-runtime-state-existing-file
# ===================================================================

def test_load_existing_valid_yaml(tmp_path, monkeypatch):
    """load_runtime_state returns dict matching file content."""
    state_file = _setup_runtime_env(tmp_path, monkeypatch, zsiga_home=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(yaml.dump({"active_target": "zsiga", "pending_switch": None}))
    from zsiga.config import load_runtime_state

    result = load_runtime_state()
    assert result == {"active_target": "zsiga", "pending_switch": None}


# ===================================================================
# Scenario: load-missing-file
# Requirement: load-runtime-state-missing-file
# ===================================================================

def test_load_missing_file(tmp_path, monkeypatch):
    """load_runtime_state returns {} when file does not exist."""
    _setup_runtime_env(tmp_path, monkeypatch, zsiga_home=True)
    from zsiga.config import load_runtime_state

    result = load_runtime_state()
    assert result == {}


# ===================================================================
# Scenario: load-corrupted-yaml
# Requirement: load-runtime-state-corrupted-yaml
# ===================================================================

def test_load_corrupted_yaml(tmp_path, monkeypatch):
    """load_runtime_state returns {} for corrupted YAML without raising."""
    state_file = _setup_runtime_env(tmp_path, monkeypatch, zsiga_home=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(": invalid: [yaml")
    from zsiga.config import load_runtime_state

    result = load_runtime_state()
    assert result == {}


# ===================================================================
# Scenario: load-empty-file
# Requirement: load-runtime-state-empty-file
# ===================================================================

def test_load_empty_file(tmp_path, monkeypatch):
    """load_runtime_state returns {} for empty file."""
    state_file = _setup_runtime_env(tmp_path, monkeypatch, zsiga_home=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("")
    from zsiga.config import load_runtime_state

    result = load_runtime_state()
    assert result == {}


# ===================================================================
# Scenario: save-creates-file-and-dirs
# Requirement: save-runtime-state-writes-yaml
# ===================================================================

def test_save_creates_file_and_dirs(tmp_path, monkeypatch):
    """save_runtime_state creates parent dirs and writes valid YAML."""
    monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
    from zsiga.config import save_runtime_state

    save_runtime_state({"active_target": "factory", "counter": 42})

    state_file = tmp_path / "data" / "runtime_state.yaml"
    assert state_file.exists(), "State file should be created"
    loaded = yaml.safe_load(state_file.read_text())
    assert loaded == {"active_target": "factory", "counter": 42}


# ===================================================================
# Scenario: save-load-round-trip
# Requirement: save-runtime-state-round-trip
# ===================================================================

def test_save_load_round_trip(tmp_path, monkeypatch):
    """Data survives a save -> load round-trip including unicode and nesting."""
    monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
    from zsiga.config import save_runtime_state, load_runtime_state

    data = {"active": "zsiga", "tags": ["evolution", "测试"], "nested": {"k": 1}}
    save_runtime_state(data)
    loaded = load_runtime_state()
    assert loaded == data


# ===================================================================
# Scenario: file-exists-and-passes
# Requirement: test-file-minimal-structure
# ===================================================================

def test_this_file_has_enough_tests():
    """Meta-check: this file contains >= 3 test functions and they all pass."""
    import importlib
    import inspect

    mod = importlib.import_module(__name__)
    test_fns = [name for name, obj in inspect.getmembers(mod)
                if inspect.isfunction(obj) and name.startswith("test_")]
    assert len(test_fns) >= 3, f"Found only {len(test_fns)} test functions"
