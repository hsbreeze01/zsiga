"""Tests for config data class construction and defaults.

Spec: config-data-classes
Change: evo-improvement-20260530-045307
"""

from zsiga.config import (
    CompactionConfig,
    GithubConfig,
    IntakeConfig,
    LLMConfig,
    LLMFastConfig,
    LoggingConfig,
    PipelineConfig,
    SSHConfig,
    SafetyConfig,
    TargetConfig,
    ZsigaConfig,
)


class TestSSHConfigConstruction:
    """Scenario: Full construction with all parameters / Default values."""

    def test_full_construction(self):
        ssh = SSHConfig(host="myhost", user="deploy", port=2222, key_path="/keys/id_rsa")
        assert ssh.host == "myhost"
        assert ssh.user == "deploy"
        assert ssh.port == 2222
        assert ssh.key_path == "/keys/id_rsa"

    def test_defaults(self):
        ssh = SSHConfig(host="myhost")
        assert ssh.host == "myhost"
        assert ssh.user is None
        assert ssh.port == 22
        assert ssh.key_path is None


class TestTargetConfigDefaults:
    """Scenario: Minimal construction uses all defaults / Full construction overrides."""

    def test_minimal_construction_defaults(self):
        tc = TargetConfig(name="t1", path="/tmp/proj")
        assert tc.name == "t1"
        assert tc.path == "/tmp/proj"
        assert tc.test_cmd == "pytest -x --tb=short"
        assert tc.lint_cmd == "ruff check ."
        assert tc.transport == "local"
        assert tc.ssh is None
        assert tc.venv_path is None
        assert tc.deploy_branch == "main"
        assert tc.merge_to_branches == []
        assert tc.domain == ""
        assert tc.description == ""
        assert tc.tech_stack == []
        assert tc.key_dirs == []
        assert tc.conventions == ""

    def test_full_construction(self):
        ssh = SSHConfig(host="h")
        tc = TargetConfig(
            name="full",
            path="/p",
            test_cmd="pytest -v",
            lint_cmd="flake8 .",
            transport="ssh",
            ssh=ssh,
            venv_path="/venv",
            deploy_branch="deploy",
            merge_to_branches=["main", "staging"],
            domain="external",
            description="desc",
            tech_stack=["python"],
            key_dirs=["src"],
            conventions="PEP8",
        )
        assert tc.test_cmd == "pytest -v"
        assert tc.lint_cmd == "flake8 ."
        assert tc.transport == "ssh"
        assert tc.ssh is ssh
        assert tc.venv_path == "/venv"
        assert tc.deploy_branch == "deploy"
        assert tc.merge_to_branches == ["main", "staging"]
        assert tc.domain == "external"
        assert tc.description == "desc"
        assert tc.tech_stack == ["python"]
        assert tc.key_dirs == ["src"]
        assert tc.conventions == "PEP8"


class TestLLMConfigDefaults:
    """Scenario: Default values for optional parameters."""

    def test_defaults(self):
        llm = LLMConfig(provider="openai", model="gpt-4", api_key="sk-test")
        assert llm.provider == "openai"
        assert llm.model == "gpt-4"
        assert llm.api_key == "sk-test"
        assert llm.base_url is None
        assert llm.proxy is None
        assert llm.max_tokens == 4096
        assert llm.temperature == 0.3

    def test_full_construction(self):
        llm = LLMConfig(
            provider="custom",
            model="m1",
            api_key="k1",
            base_url="https://api.example.com",
            proxy="http://proxy:8080",
            max_tokens=8192,
            temperature=0.7,
        )
        assert llm.base_url == "https://api.example.com"
        assert llm.proxy == "http://proxy:8080"
        assert llm.max_tokens == 8192
        assert llm.temperature == 0.7


class TestLLMFastConfigConstruction:
    """Scenario: LLMFastConfig defaults and custom construction."""

    def test_defaults(self):
        cfg = LLMFastConfig(api_key="sk-fast")
        assert cfg.api_key == "sk-fast"
        assert cfg.model == "glm-4-flash"
        assert cfg.base_url == "https://open.bigmodel.cn/api/paas/v4"

    def test_custom(self):
        cfg = LLMFastConfig(api_key="k", model="m", base_url="http://b")
        assert cfg.model == "m"
        assert cfg.base_url == "http://b"


class TestCompactionConfigDefaults:
    """Scenario: All defaults match specification."""

    def test_defaults(self):
        c = CompactionConfig()
        assert c.enabled is True
        assert c.threshold_chars == 30000
        assert c.keep_recent == 3
        assert c.use_llm_summary is True
        assert c.total_budget == 200000
        assert c.per_turn_limit == 8192
        assert c.compaction_ratio == 0.8


class TestPipelineConfigDefaults:
    """Scenario: Default values for key fields / Custom budget_profiles merge."""

    def test_defaults(self):
        p = PipelineConfig()
        assert p.max_changes_per_cycle == 3
        assert p.fix_attempts == 10
        assert p.impl_timeout_minutes == 20
        assert isinstance(p.compaction, CompactionConfig)
        assert "rm -rf /" in p.operator_blocked_commands
        assert p.budget_profiles["fix"] == 300000
        assert p.budget_profiles["implementation"] == 600000

    def test_budget_profiles_merge(self):
        p = PipelineConfig(budget_profiles={"fix": 500000, "custom": 100000})
        assert p.budget_profiles["fix"] == 500000
        assert p.budget_profiles["custom"] == 100000
        assert p.budget_profiles["implementation"] == 600000
        assert p.budget_profiles["cross_project"] == 200000
        assert p.budget_profiles["self_modify"] == 800000


class TestIntakeConfigDefaults:
    """Scenario: IntakeConfig defaults."""

    def test_defaults(self):
        i = IntakeConfig()
        assert i.mode == "dir_scan"
        assert i.scan_interval_seconds == 60
        assert i.api_url is None
        assert i.poll_interval_seconds == 300
        assert i.api_headers == {}


class TestSafetyConfigDefaults:
    """Scenario: SafetyConfig defaults."""

    def test_defaults(self):
        s = SafetyConfig()
        assert s.require_approval is True
        assert s.protected_paths == []
        assert s.max_files_per_task == 3
        assert s.dry_run is False


class TestGithubConfigDefaults:
    """Scenario: GithubConfig defaults."""

    def test_defaults(self):
        g = GithubConfig()
        assert g.token == ""
        assert g.owner == ""
        assert g.issue_integration is False

    def test_custom(self):
        g = GithubConfig(token="ghp_x", owner="org", issue_integration=True)
        assert g.token == "ghp_x"
        assert g.owner == "org"
        assert g.issue_integration is True


class TestLoggingConfig:
    """Scenario: LoggingConfig level normalization and defaults."""

    def test_level_uppercased(self):
        lg = LoggingConfig(level="debug")
        assert lg.level == "DEBUG"

    def test_defaults(self):
        lg = LoggingConfig()
        assert lg.level == "INFO"
        assert lg.fmt == "text"
        assert lg.file is None


class TestZsigaConfigConstruction:
    """Scenario: Minimal construction with None optionals."""

    def test_required_and_optional_args(self):
        llm = LLMConfig(provider="p", model="m", api_key="k")
        targets = {"t": TargetConfig(name="t", path="/p")}
        cfg = ZsigaConfig(
            llm=llm,
            targets=targets,
            pipeline=PipelineConfig(),
            intake=IntakeConfig(),
            safety=SafetyConfig(),
        )
        assert cfg.llm is llm
        assert cfg.targets is targets
        assert cfg.logging_config is None
        assert cfg.llm_fast is None
        assert cfg.github is None
        assert cfg.active_target == "zsiga"

    def test_all_optional_args(self):
        llm = LLMConfig(provider="p", model="m", api_key="k")
        targets = {"t": TargetConfig(name="t", path="/p")}
        logging_config = LoggingConfig(level="warn")
        github = GithubConfig(token="tok")
        llm_fast = LLMFastConfig(api_key="fast-k")

        cfg = ZsigaConfig(
            llm=llm,
            targets=targets,
            pipeline=PipelineConfig(),
            intake=IntakeConfig(),
            safety=SafetyConfig(),
            logging_config=logging_config,
            llm_fast=llm_fast,
            github=github,
            active_target="custom",
        )
        assert cfg.logging_config is logging_config
        assert cfg.llm_fast is llm_fast
        assert cfg.github is github
        assert cfg.active_target == "custom"
