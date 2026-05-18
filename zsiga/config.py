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
                 ssh: SSHConfig = None, venv_path: str = None):
        self.name = name
        self.path = path
        self.test_cmd = test_cmd
        self.lint_cmd = lint_cmd
        self.transport = transport
        self.ssh = ssh
        self.venv_path = venv_path


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
                 review_fix_max_turns: int = 6):
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


class ZsigaConfig:
    def __init__(self, llm: LLMConfig, targets: dict[str, TargetConfig],
                 pipeline: PipelineConfig, intake: IntakeConfig,
                 safety: SafetyConfig, logging_config: 'LoggingConfig' = None):
        self.llm = llm
        self.targets = targets
        self.pipeline = pipeline
        self.intake = intake
        self.safety = safety
        self.logging_config = logging_config


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

    config = ZsigaConfig(llm=llm, targets=targets, pipeline=pipeline, intake=intake, safety=safety,
                         logging_config=logging_config)

    result = validate_config(config)
    for w in result.warnings:
        print(f"[config warning] {w}", file=sys.stderr)
    if not result.valid:
        raise ConfigValidationError(result)

    return config
