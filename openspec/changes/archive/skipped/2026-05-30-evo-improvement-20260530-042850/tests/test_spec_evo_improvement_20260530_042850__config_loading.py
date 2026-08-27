"""Tests for _find_config and load_config pipeline.

Spec: config-loading
Change: evo-improvement-20260530-042850
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from zsiga.config import (
    GithubConfig,
    IntakeConfig,
    LoggingConfig,
    SSHConfig,
    _find_config,
    load_config,
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


class TestFindConfigInCurrentDir:
    """Spec: config-loading — Find config in current directory."""

    def test_finds_in_current_dir(self, tmp_path, monkeypatch):
        config_file = tmp_path / "zsiga.yaml"
        config_file.write_text("dummy: true")
        monkeypatch.chdir(tmp_path)
        # Mock home dir to not have config
        with patch.object(Path, "home", return_value=tmp_path / "nonexistent_home"):
            result = _find_config()
        # _find_config returns Path("zsiga.yaml") (relative) when found in cwd
        assert result == Path("zsiga.yaml")
        assert result.exists()


class TestFindConfigInHomeDir:
    """Spec: config-loading — Find config in home directory fallback."""

    def test_falls_back_to_home(self, tmp_path, monkeypatch):
        # No config in current dir
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)
        # Config in home
        home_dir = tmp_path / "home"
        zsiga_dir = home_dir / ".zsiga"
        zsiga_dir.mkdir(parents=True)
        (zsiga_dir / "zsiga.yaml").write_text("dummy: true")
        with patch.object(Path, "home", return_value=home_dir):
            result = _find_config()
        assert result == zsiga_dir / "zsiga.yaml"


class TestFindConfigRaisesFileNotFound:
    """Spec: config-loading — Raise FileNotFoundError when no config."""

    def test_raises_when_no_config(self, tmp_path, monkeypatch):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)
        with patch.object(Path, "home", return_value=tmp_path / "no_home"):
            with pytest.raises(FileNotFoundError, match="zsiga.yaml not found"):
                _find_config()


class TestLoadConfigWithSSHTarget:
    """Spec: config-loading — Load config with SSH target."""

    def test_ssh_target_parsing(self, tmp_path):
        path = _write_minimal_config(
            tmp_path,
            extra_yaml="""
targets:
  ssh-target:
    path: /remote/proj
    transport: ssh
    ssh:
      host: myhost
      user: deploy
      port: 2222
      key_path: /keys/id_rsa
""",
        )
        # Replace the default target with this one
        content = Path(path).read_text()
        content = content.replace(
            """targets:
  default:
    path: /tmp/test
    transport: local""",
            """targets:
  ssh-target:
    path: /remote/proj
    transport: ssh
    ssh:
      host: myhost
      user: deploy
      port: 2222
      key_path: /keys/id_rsa""",
        )
        Path(path).write_text(content)
        config = load_config(path=path)
        assert "ssh-target" in config.targets
        tgt = config.targets["ssh-target"]
        assert tgt.transport == "ssh"
        assert isinstance(tgt.ssh, SSHConfig)
        assert tgt.ssh.host == "myhost"
        assert tgt.ssh.user == "deploy"
        assert tgt.ssh.port == 2222
        assert tgt.ssh.key_path == "/keys/id_rsa"


class TestLoadConfigWithPipelineOverrides:
    """Spec: config-loading — Load config with pipeline overrides."""

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
    """Spec: config-loading — Load config with compaction overrides."""

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
    """Spec: config-loading — Load config with env var in api_key."""

    def test_env_var_in_api_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_API_KEY", "sk-from-env")
        p = tmp_path / "zsiga.yaml"
        p.write_text("""
agent:
  llm:
    provider: openai
    model: gpt-4
    api_key: "${MY_API_KEY}"
targets:
  default:
    path: /tmp/test
    transport: local
""")
        config = load_config(path=str(p))
        assert config.llm.api_key == "sk-from-env"


class TestLoadConfigWithGithubSection:
    """Spec: config-loading — Load config with github section."""

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
    """Spec: config-loading — Load config with logging section."""

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
    """Spec: config-loading — Load config with safety overrides."""

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
    """Spec: config-loading — Load config with intake api_poll."""

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
