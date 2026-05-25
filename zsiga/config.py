import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml


def _find_config() -> Path:
    candidates = [
        Path("zsiga.yaml"),
        Path.home() / ".zsiga" / "zsiga.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("zsiga.yaml not found in current dir or ~/.zsiga/")


def _resolve_env_vars(value):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.environ.get(env_var, "")
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0


class ConfigValidationError(Exception):
    def __init__(self, result: ValidationResult):
        self.result = result
        super().__init__("\n".join(result.errors))


class SSHConfig:
    def __init__(self, host: str, user: str = None, port: int = 22,
                 key_path: str = None):
        self.host = host
        self.user = user
        self.port = port
        self.key_path = key_path


class TargetConfig:
    def __init__(self, name: str, path: str, test_cmd: str = "pytest -x --tb=short",
                 lint_cmd: str = "ruff check .", transport: str = "local",
                 ssh: SSHConfig = None, venv_path: str = None,
                 deploy_branch: str = "main",
                 merge_to_branches: list = None):
        self.name = name
        self.path = path
        self.test_cmd = test_cmd
        self.lint_cmd = lint_cmd
        self.transport = transport
        self.ssh = ssh
        self.venv_path = venv_path
        self.deploy_branch = deploy_branch
        self.merge_to_branches = merge_to_branches or []


class LLMConfig:
    def __init__(self, provider: str, model: str, api_key: str,
                 base_url: str = None, proxy: str = None,
                 max_tokens: int = 4096, temperature: float = 0.3):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.proxy = proxy
        self.max_tokens = max_tokens
        self.temperature = temperature


class LLMFastConfig:
    def __init__(self, api_key: str, model: str = "glm-4-flash",
                 base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url


class CompactionConfig:
    def __init__(self, enabled: bool = True, threshold_chars: int = 60000,
                 keep_recent: int = 3, use_llm_summary: bool = True,
                 total_budget: int = 200000, per_turn_limit: int = 8192,
                 compaction_ratio: float = 0.8):
        self.enabled = enabled
        self.threshold_chars = threshold_chars
        self.keep_recent = keep_recent
        self.use_llm_summary = use_llm_summary
        self.total_budget = total_budget
        self.per_turn_limit = per_turn_limit
        self.compaction_ratio = compaction_ratio


DEFAULT_BUDGET_PROFILES: dict[str, int] = {
    "fix": 300000,
    "implementation": 600000,
    "cross_project": 200000,
    "self_modify": 800000,
}


class PipelineConfig:
    def __init__(self, max_changes_per_cycle: int = 3, impl_timeout_minutes: int = 20,
                 fix_attempts: int = 10, eval_fix_attempts: int = 3,
                 cycle_interval_hours: int = 8,
                 enrich_max_turns: int = 25, enrich_timeout: int = 600,
                 impl_max_turns: int = 50, impl_timeout: int = 1200,
                 verify_max_turns: int = 12, verify_timeout: int = 300,
                 fix_max_turns: int = 8,
                 compaction: CompactionConfig = None,
                 enrich_parallel_explore: bool = False,
                 explore_pool_max_concurrency: int = 3,
                 explore_pool_max_turns: int = 5,
                 explore_pool_timeout: int = 120,
                 review_max_turns: int = 10,
                 review_timeout: int = 180,
                 review_max_rounds: int = 2,
                 review_fix_max_turns: int = 6,
                 idle_poll_minutes: int = 5,
                 max_continuous_cycles: int = 20,
                 cooldown_minutes: int = 30,
                 budget_profiles: dict[str, int] = None,
        # Proposal Gate (Steward)
        proposal_gate_enabled: bool = False,
        proposal_gate_max_retries: int = 1,
        proposal_gate_steward_max_turns: int = 3,
        proposal_gate_steward_timeout: int = 90,
        proposal_gate_score_accept: int = 8,
        proposal_gate_score_pushback: int = 5,
        proposal_gate_learning_weight_days: int = 90,
        # Design Gate (Judge)
        design_gate_enabled: bool = False,
        design_gate_max_retries: int = 2,
        design_gate_max_turns: int = 4,
        design_gate_timeout: int = 120,
        # Role-specific timeouts
        analyst_max_turns: int = 8,
        analyst_timeout: int = 180,
        surveyor_max_turns: int = 3,
        surveyor_timeout: int = 60,
        fixer_max_turns: int = 8,
        fixer_timeout: int = 300,
        operator_max_turns: int = 10,
        operator_timeout: int = 600,
        # SRE safety
        operator_allowed_dirs: list = None,
        operator_blocked_commands: list = None):
        self.max_changes_per_cycle = max_changes_per_cycle
        self.impl_timeout_minutes = impl_timeout_minutes
        self.fix_attempts = fix_attempts
        self.eval_fix_attempts = eval_fix_attempts
        self.cycle_interval_hours = cycle_interval_hours
        self.enrich_max_turns = enrich_max_turns
        self.enrich_timeout = enrich_timeout
        self.impl_max_turns = impl_max_turns
        self.impl_timeout = impl_timeout
        self.verify_max_turns = verify_max_turns
        self.verify_timeout = verify_timeout
        self.fix_max_turns = fix_max_turns
        self.compaction = compaction or CompactionConfig()
        self.enrich_parallel_explore = enrich_parallel_explore
        self.explore_pool_max_concurrency = explore_pool_max_concurrency
        self.explore_pool_max_turns = explore_pool_max_turns
        self.explore_pool_timeout = explore_pool_timeout
        self.review_max_turns = review_max_turns
        self.review_timeout = review_timeout
        self.review_max_rounds = review_max_rounds
        self.review_fix_max_turns = review_fix_max_turns
        self.idle_poll_minutes = idle_poll_minutes
        self.max_continuous_cycles = max_continuous_cycles
        self.cooldown_minutes = cooldown_minutes
        # Proposal Gate
        self.proposal_gate_enabled = proposal_gate_enabled
        self.proposal_gate_max_retries = proposal_gate_max_retries
        self.proposal_gate_steward_max_turns = proposal_gate_steward_max_turns
        self.proposal_gate_steward_timeout = proposal_gate_steward_timeout
        self.proposal_gate_score_accept = proposal_gate_score_accept
        self.proposal_gate_score_pushback = proposal_gate_score_pushback
        self.proposal_gate_learning_weight_days = proposal_gate_learning_weight_days
        # Design Gate
        self.design_gate_enabled = design_gate_enabled
        self.design_gate_max_retries = design_gate_max_retries
        self.design_gate_max_turns = design_gate_max_turns
        self.design_gate_timeout = design_gate_timeout
        # Role-specific
        self.analyst_max_turns = analyst_max_turns
        self.analyst_timeout = analyst_timeout
        self.surveyor_max_turns = surveyor_max_turns
        self.surveyor_timeout = surveyor_timeout
        self.fixer_max_turns = fixer_max_turns
        self.fixer_timeout = fixer_timeout
        self.operator_max_turns = operator_max_turns
        self.operator_timeout = operator_timeout
        # SRE safety
        self.operator_allowed_dirs = operator_allowed_dirs or []
        self.operator_blocked_commands = operator_blocked_commands or [
            "rm -rf /", "shutdown", "reboot", "mkfs", "dd if=", "chmod 777", "> /etc/",
        ]
        self.budget_profiles = dict(DEFAULT_BUDGET_PROFILES)
        if budget_profiles:
            self.budget_profiles.update(budget_profiles)


class IntakeConfig:
    def __init__(self, mode: str = "dir_scan", scan_interval_seconds: int = 60,
                 api_url: str = None, poll_interval_seconds: int = 300,
                 api_headers: dict = None):
        self.mode = mode
        self.scan_interval_seconds = scan_interval_seconds
        self.api_url = api_url
        self.poll_interval_seconds = poll_interval_seconds
        self.api_headers = api_headers or {}


class SafetyConfig:
    def __init__(self, require_approval: bool = True, protected_paths: list = None,
                 max_files_per_task: int = 3, dry_run: bool = False):
        self.require_approval = require_approval
        self.protected_paths = protected_paths or []
        self.max_files_per_task = max_files_per_task
        self.dry_run = dry_run


class GithubConfig:
    def __init__(self, token: str = "", owner: str = "",
                 issue_integration: bool = False):
        self.token = token
        self.owner = owner
        self.issue_integration = issue_integration


class ZsigaConfig:
    def __init__(self, llm: LLMConfig, targets: dict[str, TargetConfig],
                 pipeline: PipelineConfig, intake: IntakeConfig,
                 safety: SafetyConfig, logging_config: 'LoggingConfig' = None,
                 llm_fast: 'LLMFastConfig' = None,
                 github: GithubConfig = None):
        self.llm = llm
        self.targets = targets
        self.pipeline = pipeline
        self.intake = intake
        self.safety = safety
        self.logging_config = logging_config
        self.llm_fast = llm_fast
        self.github = github


class LoggingConfig:
    """Logging configuration parsed from the ``logging`` section of zsiga.yaml."""

    def __init__(self, level: str = "INFO", fmt: str = "text",
                 file: str = None):
        self.level = level.upper()
        self.fmt = fmt
        self.file = file


def validate_config(config: ZsigaConfig) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    # LLM validation
    if not config.llm.provider:
        errors.append("llm.provider is required and must be a non-empty string")
    if not config.llm.model:
        errors.append("llm.model is required and must be a non-empty string")
    if not config.llm.api_key:
        errors.append("llm.api_key is required and must be a non-empty string")
    if not (0.0 <= config.llm.temperature <= 2.0):
        warnings.append(
            f"llm.temperature ({config.llm.temperature}) is outside the recommended range [0.0, 2.0]"
        )
    if config.llm.max_tokens <= 0:
        warnings.append("llm.max_tokens should be a positive integer")

    # Targets validation
    if not config.targets:
        errors.append("at least one target is required")
    else:
        for name, target in config.targets.items():
            if not target.path:
                errors.append(f"target '{name}': path must be a non-empty string")
            if target.transport not in ("local", "ssh"):
                errors.append(
                    f"target '{name}': transport must be 'local' or 'ssh', got '{target.transport}'"
                )
            if target.transport == "ssh":
                if target.ssh is None or not target.ssh.host:
                    errors.append(
                        f"target '{name}': SSH transport requires ssh config with a non-empty host"
                    )

    # Pipeline validation
    if not (1 <= config.pipeline.max_changes_per_cycle <= 10):
        warnings.append(
            f"pipeline.max_changes_per_cycle ({config.pipeline.max_changes_per_cycle}) is outside the recommended range [1, 10]"
        )
    if not (1 <= config.pipeline.fix_attempts <= 20):
        warnings.append(
            f"pipeline.fix_attempts ({config.pipeline.fix_attempts}) is outside the recommended range [1, 20]"
        )
    if config.pipeline.enrich_max_turns <= 0:
        warnings.append("pipeline.enrich_max_turns should be positive")
    if config.pipeline.impl_max_turns <= 0:
        warnings.append("pipeline.impl_max_turns should be positive")

    return ValidationResult(errors=errors, warnings=warnings)


def load_config(path: str = None) -> ZsigaConfig:
    config_path = Path(path) if path else _find_config()
    raw = yaml.safe_load(config_path.read_text())
    raw = _resolve_env_vars(raw)

    llm_raw = raw["agent"]["llm"]
    llm = LLMConfig(
        provider=llm_raw["provider"],
        model=llm_raw["model"],
        api_key=llm_raw["api_key"],
        base_url=llm_raw.get("base_url"),
        proxy=llm_raw.get("proxy"),
        max_tokens=llm_raw.get("max_tokens", 4096),
        temperature=llm_raw.get("temperature", 0.3),
    )

    llm_fast_raw = raw["agent"].get("llm_fast")
    llm_fast = None
    if llm_fast_raw:
        llm_fast = LLMFastConfig(
            api_key=llm_fast_raw.get("api_key", llm.api_key),
            model=llm_fast_raw.get("model", "glm-4-flash"),
            base_url=llm_fast_raw.get("base_url", "https://open.bigmodel.cn/api/paas/v4"),
        )

    targets = {}
    for name, tc in raw.get("targets", {}).items():
        ssh_raw = tc.get("ssh")
        ssh = None
        if ssh_raw:
            ssh = SSHConfig(
                host=ssh_raw["host"],
                user=ssh_raw.get("user"),
                port=ssh_raw.get("port", 22),
                key_path=ssh_raw.get("key_path"),
            )
        targets[name] = TargetConfig(
            name=name,
            path=tc["path"],
            test_cmd=tc.get("test_cmd", "pytest -x --tb=short"),
            lint_cmd=tc.get("lint_cmd", "ruff check ."),
            transport=tc.get("transport", "ssh" if ssh else "local"),
            ssh=ssh,
            venv_path=tc.get("venv_path"),
            deploy_branch=tc.get("deploy_branch", "main"),
            merge_to_branches=tc.get("merge_to_branches", []),
        )

    pipeline_raw = raw.get("pipeline", {})
    compaction_raw = pipeline_raw.get("compaction", {})
    compaction = CompactionConfig(
        enabled=compaction_raw.get("enabled", True),
        threshold_chars=compaction_raw.get("threshold_chars", 60000),
        keep_recent=compaction_raw.get("keep_recent", 3),
        use_llm_summary=compaction_raw.get("use_llm_summary", True),
        total_budget=compaction_raw.get("total_budget", 200000),
        per_turn_limit=compaction_raw.get("per_turn_limit", 8192),
        compaction_ratio=compaction_raw.get("compaction_ratio", 0.8),
    )
    pipeline = PipelineConfig(
        max_changes_per_cycle=pipeline_raw.get("max_changes_per_cycle", 3),
        impl_timeout_minutes=pipeline_raw.get("impl_timeout_minutes", 20),
        fix_attempts=pipeline_raw.get("fix_attempts", 10),
        eval_fix_attempts=pipeline_raw.get("eval_fix_attempts", 3),
        cycle_interval_hours=pipeline_raw.get("cycle_interval_hours", 8),
        enrich_max_turns=pipeline_raw.get("enrich_max_turns", 25),
        enrich_timeout=pipeline_raw.get("enrich_timeout", 600),
        impl_max_turns=pipeline_raw.get("impl_max_turns", 50),
        impl_timeout=pipeline_raw.get("impl_timeout", 1200),
        verify_max_turns=pipeline_raw.get("verify_max_turns", 12),
        verify_timeout=pipeline_raw.get("verify_timeout", 300),
        fix_max_turns=pipeline_raw.get("fix_max_turns", 8),
        compaction=compaction,
        enrich_parallel_explore=pipeline_raw.get("enrich_parallel_explore", False),
        explore_pool_max_concurrency=pipeline_raw.get("explore_pool", {}).get("max_concurrency", 3),
        explore_pool_max_turns=pipeline_raw.get("explore_pool", {}).get("max_turns_per_task", 5),
        explore_pool_timeout=pipeline_raw.get("explore_pool", {}).get("timeout_per_task", 120),
        review_max_turns=pipeline_raw.get("review_max_turns", 10),
        review_timeout=pipeline_raw.get("review_timeout", 180),
        review_max_rounds=pipeline_raw.get("review_max_rounds", 2),
        review_fix_max_turns=pipeline_raw.get("review_fix_max_turns", 6),
        idle_poll_minutes=pipeline_raw.get("idle_poll_minutes", 5),
        max_continuous_cycles=pipeline_raw.get("max_continuous_cycles", 20),
        cooldown_minutes=pipeline_raw.get("cooldown_minutes", 30),
        budget_profiles=pipeline_raw.get("budget_profiles"),
        # Proposal Gate
        proposal_gate_enabled=pipeline_raw.get("proposal_gate", {}).get("enabled", False),
        proposal_gate_max_retries=pipeline_raw.get("proposal_gate", {}).get("max_retries", 1),
        proposal_gate_steward_max_turns=pipeline_raw.get("proposal_gate", {}).get("steward_max_turns", 3),
        proposal_gate_steward_timeout=pipeline_raw.get("proposal_gate", {}).get("steward_timeout", 90),
        proposal_gate_score_accept=pipeline_raw.get("proposal_gate", {}).get("score_accept", 8),
        proposal_gate_score_pushback=pipeline_raw.get("proposal_gate", {}).get("score_pushback", 5),
        proposal_gate_learning_weight_days=pipeline_raw.get("proposal_gate", {}).get("learning_weight_days", 90),
        # Design Gate
        design_gate_enabled=pipeline_raw.get("design_gate", {}).get("enabled", False),
        design_gate_max_retries=pipeline_raw.get("design_gate", {}).get("max_retries", 2),
        design_gate_max_turns=pipeline_raw.get("design_gate", {}).get("max_turns", 4),
        design_gate_timeout=pipeline_raw.get("design_gate", {}).get("timeout", 120),
        # Role-specific
        analyst_max_turns=pipeline_raw.get("analyst_max_turns", 8),
        analyst_timeout=pipeline_raw.get("analyst_timeout", 180),
        surveyor_max_turns=pipeline_raw.get("surveyor_max_turns", 3),
        surveyor_timeout=pipeline_raw.get("surveyor_timeout", 60),
        fixer_max_turns=pipeline_raw.get("fixer_max_turns", 8),
        fixer_timeout=pipeline_raw.get("fixer_timeout", 300),
        operator_max_turns=pipeline_raw.get("operator_max_turns", 10),
        operator_timeout=pipeline_raw.get("operator_timeout", 600),
        # SRE safety
        operator_allowed_dirs=pipeline_raw.get("operator_allowed_dirs"),
        operator_blocked_commands=pipeline_raw.get("operator_blocked_commands"),
    )

    intake_raw = raw.get("intake", {})
    intake = IntakeConfig(
        mode=intake_raw.get("mode", "dir_scan"),
        scan_interval_seconds=intake_raw.get("dir_scan", {}).get("scan_interval_seconds", 60),
        api_url=intake_raw.get("api_poll", {}).get("url"),
        poll_interval_seconds=intake_raw.get("api_poll", {}).get("poll_interval_seconds", 300),
        api_headers=intake_raw.get("api_poll", {}).get("headers", {}),
    )

    safety_raw = raw.get("safety", {})
    safety = SafetyConfig(
        require_approval=safety_raw.get("require_approval", True),
        protected_paths=safety_raw.get("protected_paths", []),
        max_files_per_task=safety_raw.get("max_files_per_task", 3),
        dry_run=safety_raw.get("dry_run", False),
    )

    logging_raw = raw.get("logging", {})
    logging_config = LoggingConfig(
        level=logging_raw.get("level", "INFO"),
        fmt=logging_raw.get("format", "text"),
        file=logging_raw.get("file"),
    )

    github_raw = raw.get("github", {})
    github = GithubConfig(
        token=github_raw.get("token", ""),
        owner=github_raw.get("owner", ""),
        issue_integration=github_raw.get("issue_integration", False),
    )

    config = ZsigaConfig(llm=llm, targets=targets, pipeline=pipeline, intake=intake, safety=safety,
                         logging_config=logging_config, llm_fast=llm_fast,
                         github=github)

    result = validate_config(config)
    for w in result.warnings:
        print(f"[config warning] {w}", file=sys.stderr)
    if not result.valid:
        raise ConfigValidationError(result)

    return config
