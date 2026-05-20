# Tasks: P3 Dynamic Budget Allocation

## 1. Configuration Layer

- [ ] **1.1** Add `BudgetProfileConfig` and parse `pipeline.budget_profiles` in `config.py`
  - Add a `BudgetProfileConfig` dataclass (or simple dict mapping) holding profile name → `total_budget`
  - In `PipelineConfig.__init__`, accept `budget_profiles: dict[str, int]` parameter
  - In `load_config()`, parse `pipeline_raw.get("budget_profiles", {})` into the config
  - Provide `DEFAULT_BUDGET_PROFILES` constant with the 4 default profiles
  - Merge user overrides onto defaults

## 2. Profile Selection Logic

- [ ] **2.1** Implement `select_budget_profile()` in `token_budget.py`
  - Function signature: `select_budget_profile(intent_type: IntentType, project: str, is_cross_project: bool, profiles: dict[str, int]) -> tuple[str, int]`
  - Rules in order: cross_project → self_modify → fix → implementation
  - Returns `(profile_name, total_budget)`
  - Add unit tests for all 4 selection paths + fallback

## 3. Orchestrator Integration

- [ ] **3.1** Wire budget profile selection into `orchestrator._process_change()`
  - After intent classification, call `select_budget_profile()`
  - Set `self.agent.budget.total_budget = selected_budget` before `_run_phases()`
  - Store `budget_profile` on the `ChangeRecord`
  - Log the selected profile name and budget value

## 4. Metrics & Statistics

- [ ] **4.1** Add `budget_profile` field to `ChangeRecord` and compute per-profile stats
  - Add `budget_profile: str = ""` to `ChangeRecord` dataclass
  - Include `budget_profile` in `to_dict()` serialization
  - In `compute_stats()`, add `budget_profile_stats` dict mapping profile names to `{count, avg_tokens}`
  - Handle old records where `budget_profile` is absent (default to `"unknown"`)

## 5. Configuration Update

- [ ] **5.1** Add `budget_profiles` section to `zsiga.yaml`
  - Add the 4 default profiles under `pipeline.budget_profiles`
  - This is a documentation/example change — defaults already work without it
