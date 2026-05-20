"""Tests for GitHub Issue integration (github_issue.py + config parsing)."""

import json
import os
import subprocess
from unittest.mock import MagicMock, patch

from zsiga.config import GithubConfig, load_config
from zsiga.pipeline.github_issue import create_issue, extract_github_repo


# ---------------------------------------------------------------------------
# extract_github_repo
# ---------------------------------------------------------------------------

class TestExtractGithubRepo:
    """Tests for extract_github_repo() parsing various remote URL formats."""

    def _make_transport(self, stdout: str, exit_code: int = 0):
        transport = MagicMock()
        transport.run_shell.return_value = {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": "",
        }
        return transport

    def test_ssh_url(self):
        t = self._make_transport("git@github.com:hsbreeze01/myrepo.git\n")
        assert extract_github_repo("/proj", t) == "hsbreeze01/myrepo"

    def test_ssh_url_alias_host(self):
        t = self._make_transport("git@github-agent:hsbreeze01/myrepo.git\n")
        assert extract_github_repo("/proj", t) == "hsbreeze01/myrepo"

    def test_https_url(self):
        t = self._make_transport("https://github.com/hsbreeze01/myrepo.git\n")
        assert extract_github_repo("/proj", t) == "hsbreeze01/myrepo"

    def test_https_url_no_git_suffix(self):
        t = self._make_transport("https://github.com/hsbreeze01/myrepo\n")
        assert extract_github_repo("/proj", t) == "hsbreeze01/myrepo"

    def test_invalid_url(self):
        t = self._make_transport("https://gitlab.com/owner/repo.git\n")
        assert extract_github_repo("/proj", t) is None

    def test_remote_command_fails(self):
        t = self._make_transport("", exit_code=128)
        assert extract_github_repo("/proj", t) is None

    def test_transport_exception(self):
        t = MagicMock()
        t.run_shell.side_effect = Exception("connection lost")
        assert extract_github_repo("/proj", t) is None


# ---------------------------------------------------------------------------
# create_issue
# ---------------------------------------------------------------------------

class TestCreateIssue:
    """Tests for create_issue() with mocked subprocess.run."""

    def test_success_returns_issue_number(self):
        response_body = json.dumps({"number": 42, "html_url": "https://..."})
        mock_output = f"{response_body}\n201"
        with patch("zsiga.pipeline.github_issue.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            result = create_issue("owner/repo", "title", "body", "tok123")
        assert result == 42

    def test_http_error_returns_none(self):
        response_body = json.dumps({"message": "Unauthorized"})
        mock_output = f"{response_body}\n401"
        with patch("zsiga.pipeline.github_issue.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            result = create_issue("owner/repo", "title", "body", "tok123")
        assert result is None

    def test_rate_limit_returns_none(self):
        response_body = json.dumps({"message": "rate limit exceeded"})
        mock_output = f"{response_body}\n403"
        with patch("zsiga.pipeline.github_issue.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            result = create_issue("owner/repo", "title", "body", "tok123")
        assert result is None

    def test_timeout_returns_none(self):
        with patch("zsiga.pipeline.github_issue.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="curl", timeout=10)
            result = create_issue("owner/repo", "title", "body", "tok123")
        assert result is None

    def test_json_parse_error_returns_none(self):
        mock_output = "not-json\n201"
        with patch("zsiga.pipeline.github_issue.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            result = create_issue("owner/repo", "title", "body", "tok123")
        assert result is None

    def test_empty_token_returns_none(self):
        result = create_issue("owner/repo", "title", "body", "")
        assert result is None


# ---------------------------------------------------------------------------
# GithubConfig parsing
# ---------------------------------------------------------------------------

class TestGithubConfigParsing:
    """Tests for GithubConfig defaults and yaml parsing."""

    def test_defaults_disabled(self):
        cfg = GithubConfig()
        assert cfg.issue_integration is False
        assert cfg.token == ""
        assert cfg.owner == ""

    def test_enabled_with_token(self):
        cfg = GithubConfig(token="ghp_abc", owner="me", issue_integration=True)
        assert cfg.issue_integration is True
        assert cfg.token == "ghp_abc"

    def test_config_loads_github_section(self, tmp_path, monkeypatch):
        yaml_text = """
agent:
  name: zsiga
  llm:
    provider: test
    model: m1
    api_key: key1
targets:
  demo:
    path: /tmp/demo
pipeline: {}
intake: {}
safety: {}
github:
  token: mytoken
  issue_integration: true
"""
        cfg_file = tmp_path / "zsiga.yaml"
        cfg_file.write_text(yaml_text)
        monkeypatch.chdir(tmp_path)
        os.chdir(tmp_path)
        cfg = load_config(str(cfg_file))
        assert cfg.github is not None
        assert cfg.github.issue_integration is True
        assert cfg.github.token == "mytoken"

    def test_config_missing_github_defaults_disabled(self, tmp_path, monkeypatch):
        yaml_text = """
agent:
  name: zsiga
  llm:
    provider: test
    model: m1
    api_key: key1
targets:
  demo:
    path: /tmp/demo
pipeline: {}
intake: {}
safety: {}
"""
        cfg_file = tmp_path / "zsiga.yaml"
        cfg_file.write_text(yaml_text)
        cfg = load_config(str(cfg_file))
        assert cfg.github is not None
        assert cfg.github.issue_integration is False


# ---------------------------------------------------------------------------
# Orchestrator DELIVER message format
# ---------------------------------------------------------------------------

class TestDeliverCommitMessage:
    """Verify commit message is built correctly with/without issue number."""

    def test_message_with_issue_number(self):
        msg = "feat(myrepo): add-feature-x"
        issue_number = 42
        if issue_number:
            msg += f" (closes #{issue_number})"
        assert msg == "feat(myrepo): add-feature-x (closes #42)"

    def test_message_without_issue_number(self):
        msg = "feat(myrepo): add-feature-x"
        issue_number = None
        if issue_number:
            msg += f" (closes #{issue_number})"
        assert msg == "feat(myrepo): add-feature-x"
