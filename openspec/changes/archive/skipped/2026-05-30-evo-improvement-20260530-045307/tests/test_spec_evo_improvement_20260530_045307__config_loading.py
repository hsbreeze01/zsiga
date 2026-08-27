"""Tests for load_config integration paths and runtime state management.

Spec: config-loading
Change: evo-improvement-20260530-045307
"""

from pathlib import Path
from unittest.mock import patch

from zsiga.config import (
    GithubConfig,
    IntakeConfig,
    LoggingConfig,
    SSHConfig,
    _runtime_state_path,
    load_config,
    load_runtime_state,
    save_runtime_state,
)


def _write_minimal_config(tmp_path, extra_yaml=""):
    """Write a minimal valid zsiga.yaml and return its path."""
    content = (
        """
agent:
  llm:
    provider: openai
    model: gpt-4
    api_key: sk-test
targets:
  default:
    path: /tmp/test
    transport: local
"""
        + extra_yaml
    )
    p = tmp_path / "zsiga.yaml"
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# load_config integration scenarios
# ---------------------------------------------------------------------------


class TestLoadConfigWithSSHTarget:
    """Scenario: SSH target with full configuration."""

    def test_ssh_target_parsing(self, tmp_path):
        p = tmp_path / "zsiga.yaml"
        p.write_text(
            """
agent:
  llm:
    provider: openai
    model: gpt-4
    api_key: sk-test
targets:
  ssh-target:
    path: /remote/proj
    transport: ssh
    ssh:
      host: myhost
      user: deploy
      port: 2222
      key_path: /keys/id_rsa
"""
        )
        config = load_config(path=str(p))
        assert "ssh-target" in config.targets
        tgt = config.targets["ssh-target"]
        assert tgt.transport == "ssh"
        assert isinstance(tgt.ssh, SSHConfig)
        assert tgt.ssh.host == "myhost"
        assert tgt.ssh.user == "deploy"
        assert tgt.ssh.port == 2222
        assert tgt.ssh.key_path == "/keys/id_rsa"


class TestLoadConfigWithPipelineOverrides:
    """Scenario: Pipeline override for max_changes_per_cycle and enrich_max_turns."""

    def test_pipeline_overrides(self, tmp_path):
        path = _write_minimal_config(
            tmp_path,
            extra_yaml="""
pipeline:
  max_changes_per_cycle: 5
  enrich_max_turns: 30
""",
        )
        config = load_config(path=path)
        assert config.pipeline.max_changes_per_cycle == 5
        assert config.pipeline.enrich_max_turns == 30


class TestLoadConfigWithCompactionOverrides:
    """Scenario: Compaction override for enabled and threshold_chars."""

    def test_compaction_overrides(self, tmp_path):
        path = _write_minimal_config(
            tmp_path,
            extra_yaml="""
pipeline:
  compaction:
    enabled: false
    threshold_chars: 50000
""",
        )
        config = load_config(path=path)
        assert config.pipeline.compaction.enabled is False
        assert config.pipeline.compaction.threshold_chars == 50000


class TestLoadConfigWithEnvVarSubstitution:
    """Scenario: API key from environment variable."""

    def test_env_var_in_api_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_API_KEY", "sk-from-env")
        p = tmp_path / "zsiga.yaml"
        p.write_text(
            """
agent:
  llm:
    provider: openai
    model: gpt-4
    api_key: "${MY_API_KEY}"
targets:
  default:
    path: /tmp/test
    transport: local
"""
        )
        config = load_config(path=str(p))
        assert config.llm.api_key == "sk-from-env"


class TestLoadConfigWithGithubSection:
    """Scenario: Github section with token, owner, issue_integration."""

    def test_github_parsing(self, tmp_path):
        path = _write_minimal_config(
            tmp_path,
            extra_yaml="""
github:
  token: ghp_xxx
  owner: myorg
  issue_integration: true
""",
        )
        config = load_config(path=path)
        assert isinstance(config.github, GithubConfig)
        assert config.github.token == "ghp_xxx"
        assert config.github.owner == "myorg"
        assert config.github.issue_integration is True


class TestLoadConfigWithLoggingSection:
    """Scenario: Logging section with lowercase level."""

    def test_logging_parsing(self, tmp_path):
        path = _write_minimal_config(
            tmp_path,
            extra_yaml="""
logging:
  level: debug
  format: json
  file: /tmp/zsiga.log
""",
        )
        config = load_config(path=path)
        assert isinstance(config.logging_config, LoggingConfig)
        assert config.logging_config.level == "DEBUG"
        assert config.logging_config.fmt == "json"
        assert config.logging_config.file == "/tmp/zsiga.log"


class TestLoadConfigWithSafetyOverrides:
    """Scenario: Safety overrides for require_approval and max_files_per_task."""

    def test_safety_overrides(self, tmp_path):
        path = _write_minimal_config(
            tmp_path,
            extra_yaml="""
safety:
  require_approval: false
  max_files_per_task: 10
""",
        )
        config = load_config(path=path)
        assert config.safety.require_approval is False
        assert config.safety.max_files_per_task == 10


class TestLoadConfigWithIntakeApiPoll:
    """Scenario: Intake API poll configuration."""

    def test_intake_api_poll_parsing(self, tmp_path):
        path = _write_minimal_config(
            tmp_path,
            extra_yaml="""
intake:
  mode: api_poll
  api_poll:
    url: https://example.com/api
    poll_interval_seconds: 60
""",
        )
        config = load_config(path=path)
        assert isinstance(config.intake, IntakeConfig)
        assert config.intake.mode == "api_poll"
        assert config.intake.api_url == "https://example.com/api"
        assert config.intake.poll_interval_seconds == 60


# ---------------------------------------------------------------------------
# Runtime state scenarios
# ---------------------------------------------------------------------------


class TestRuntimeStatePathWithZsigaHome:
    """Scenario: Path with ZSIGA_HOME set."""

    def test_uses_zsiga_home(self, monkeypatch):
        monkeypatch.setenv("ZSIGA_HOME", "/opt/zsiga")
        result = _runtime_state_path()
        assert result == Path("/opt/zsiga/data/runtime_state.yaml")


class TestRuntimeStatePathFallback:
    """Scenario: Path falls back to config parent dir when ZSIGA_HOME unset."""

    def test_falls_back_to_config_dir(self, monkeypatch):
        monkeypatch.delenv("ZSIGA_HOME", raising=False)
        fake_config_path = Path("/project/zsiga.yaml")
        with patch("zsiga.config._find_config", return_value=fake_config_path):
            result = _runtime_state_path()
        assert result == Path("/project/data/runtime_state.yaml")


class TestLoadRuntimeStateNonExistent:
    """Scenario: Non-existent file returns empty dict."""

    def test_returns_empty_dict(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path / "nonexistent"))
        result = load_runtime_state()
        assert result == {}


class TestLoadRuntimeStateValidFile:
    """Scenario: Valid YAML file returns parsed dict."""

    def test_loads_valid_yaml(self, monkeypatch, tmp_path):
        state_dir = tmp_path / "data"
        state_dir.mkdir()
        state_file = state_dir / "runtime_state.yaml"
        state_file.write_text("active_target: my-project\n")
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        result = load_runtime_state()
        assert result == {"active_target": "my-project"}


class TestLoadRuntimeStateCorruptFile:
    """Scenario: Corrupt YAML file returns empty dict."""

    def test_corrupt_yaml_returns_empty(self, monkeypatch, tmp_path):
        state_dir = tmp_path / "data"
        state_dir.mkdir()
        state_file = state_dir / "runtime_state.yaml"
        state_file.write_text(": {broken\n")
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        result = load_runtime_state()
        assert result == {}


class TestSaveRuntimeStateCreatesParentDirs:
    """Scenario: Save creates parent directories."""

    def test_creates_dirs_and_writes(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path / "deep" / "nested"))
        save_runtime_state({"active_target": "proj-a"})
        state_file = tmp_path / "deep" / "nested" / "data" / "runtime_state.yaml"
        assert state_file.exists()
        content = state_file.read_text()
        assert "proj-a" in content


class TestSaveAndLoadRoundTrip:
    """Scenario: Round-trip preserves all keys and values."""

    def test_round_trip(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ZSIGA_HOME", str(tmp_path))
        original = {"active_target": "round-trip", "count": 42}
        save_runtime_state(original)
        loaded = load_runtime_state()
        assert loaded == original
