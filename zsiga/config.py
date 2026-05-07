import os
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


class TargetConfig:
    def __init__(self, name: str, path: str, test_cmd: str = "pytest -x --tb=short",
                 lint_cmd: str = "ruff check ."):
        self.name = name
        self.path = path
        self.test_cmd = test_cmd
        self.lint_cmd = lint_cmd


class LLMConfig:
    def __init__(self, provider: str, model: str, api_key: str,
                 max_tokens: int = 4096, temperature: float = 0.3):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature


class PipelineConfig:
    def __init__(self, max_changes_per_cycle: int = 3, impl_timeout_minutes: int = 20,
                 fix_attempts: int = 10, eval_fix_attempts: int = 9,
                 cycle_interval_hours: int = 8):
        self.max_changes_per_cycle = max_changes_per_cycle
        self.impl_timeout_minutes = impl_timeout_minutes
        self.fix_attempts = fix_attempts
        self.eval_fix_attempts = eval_fix_attempts
        self.cycle_interval_hours = cycle_interval_hours


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
                 max_files_per_task: int = 3):
        self.require_approval = require_approval
        self.protected_paths = protected_paths or []
        self.max_files_per_task = max_files_per_task


class ZsigaConfig:
    def __init__(self, llm: LLMConfig, targets: dict[str, TargetConfig],
                 pipeline: PipelineConfig, intake: IntakeConfig,
                 safety: SafetyConfig):
        self.llm = llm
        self.targets = targets
        self.pipeline = pipeline
        self.intake = intake
        self.safety = safety


def load_config(path: str = None) -> ZsigaConfig:
    config_path = Path(path) if path else _find_config()
    raw = yaml.safe_load(config_path.read_text())
    raw = _resolve_env_vars(raw)

    llm_raw = raw["agent"]["llm"]
    llm = LLMConfig(
        provider=llm_raw["provider"],
        model=llm_raw["model"],
        api_key=llm_raw["api_key"],
        max_tokens=llm_raw.get("max_tokens", 4096),
        temperature=llm_raw.get("temperature", 0.3),
    )

    targets = {}
    for name, tc in raw.get("targets", {}).items():
        targets[name] = TargetConfig(
            name=name,
            path=tc["path"],
            test_cmd=tc.get("test_cmd", "pytest -x --tb=short"),
            lint_cmd=tc.get("lint_cmd", "ruff check ."),
        )

    pipeline_raw = raw.get("pipeline", {})
    pipeline = PipelineConfig(
        max_changes_per_cycle=pipeline_raw.get("max_changes_per_cycle", 3),
        impl_timeout_minutes=pipeline_raw.get("impl_timeout_minutes", 20),
        fix_attempts=pipeline_raw.get("fix_attempts", 10),
        eval_fix_attempts=pipeline_raw.get("eval_fix_attempts", 9),
        cycle_interval_hours=pipeline_raw.get("cycle_interval_hours", 8),
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
    )

    return ZsigaConfig(llm=llm, targets=targets, pipeline=pipeline, intake=intake, safety=safety)
