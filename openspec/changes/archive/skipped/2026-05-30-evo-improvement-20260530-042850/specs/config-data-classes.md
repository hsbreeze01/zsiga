# config-data-classes

## ADDED Requirements

### Requirement: Config data class construction

All configuration data classes in `zsiga/config.py` SHALL be constructable with their documented
parameters and SHALL expose those values as instance attributes. Default values MUST be applied
when optional parameters are omitted.

#### Scenario: SSHConfig full construction

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SSHConfig.__init__
- **Given** SSHConfig is constructed with host="myhost", user="deploy", port=2222, key_path="/keys/id_rsa"
- **When** the instance attributes are inspected
- **Then** host == "myhost", user == "deploy", port == 2222, key_path == "/keys/id_rsa"

#### Scenario: SSHConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SSHConfig.__init__
- **Given** SSHConfig is constructed with host="myhost" only
- **When** the instance attributes are inspected
- **Then** user is None, port == 22, key_path is None

#### Scenario: TargetConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** TargetConfig is constructed with name="t1", path="/tmp/proj"
- **When** the instance attributes are inspected
- **Then** test_cmd == "pytest -x --tb=short", lint_cmd == "ruff check .", transport == "local",
  ssh is None, venv_path is None, deploy_branch == "main", merge_to_branches == [],
  domain == "", description == "", tech_stack == [], key_dirs == [], conventions == ""

#### Scenario: TargetConfig full construction

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** TargetConfig is constructed with all parameters specified
- **When** the instance attributes are inspected
- **Then** all attributes match the provided values exactly

#### Scenario: LLMConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LLMConfig.__init__
- **Given** LLMConfig is constructed with provider="openai", model="gpt-4", api_key="sk-test"
- **When** the instance attributes are inspected
- **Then** base_url is None, proxy is None, max_tokens == 4096, temperature == 0.3

#### Scenario: LLMConfig full construction

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LLMConfig.__init__
- **Given** LLMConfig is constructed with all parameters specified
- **When** the instance attributes are inspected
- **Then** all attributes match the provided values exactly

#### Scenario: CompactionConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::CompactionConfig.__init__
- **Given** CompactionConfig is constructed with no arguments
- **When** the instance attributes are inspected
- **Then** enabled is True, threshold_chars == 30000, keep_recent == 3,
  use_llm_summary is True, total_budget == 200000, per_turn_limit == 8192,
  compaction_ratio == 0.8

#### Scenario: PipelineConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** PipelineConfig is constructed with no arguments
- **When** key attributes are inspected
- **Then** max_changes_per_cycle == 3, fix_attempts == 10, compaction is a CompactionConfig,
  operator_blocked_commands contains "rm -rf /", budget_profiles contains "fix" == 300000

#### Scenario: PipelineConfig budget_profiles merge

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** PipelineConfig is constructed with budget_profiles={"fix": 500000, "custom": 100000}
- **When** budget_profiles is inspected
- **Then** it contains "fix" == 500000 (overridden), "custom" == 100000 (added),
  and all other DEFAULT_BUDGET_PROFILES keys remain unchanged

#### Scenario: IntakeConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::IntakeConfig.__init__
- **Given** IntakeConfig is constructed with no arguments
- **When** the instance attributes are inspected
- **Then** mode == "dir_scan", scan_interval_seconds == 60, api_url is None,
  poll_interval_seconds == 300, api_headers == {}

#### Scenario: SafetyConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SafetyConfig.__init__
- **Given** SafetyConfig is constructed with no arguments
- **When** the instance attributes are inspected
- **Then** require_approval is True, protected_paths == [], max_files_per_task == 3, dry_run is False

#### Scenario: GithubConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::GithubConfig.__init__
- **Given** GithubConfig is constructed with no arguments
- **When** the instance attributes are inspected
- **Then** token == "", owner == "", issue_integration is False

#### Scenario: LoggingConfig level normalization

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** LoggingConfig is constructed with level="debug"
- **When** the level attribute is inspected
- **Then** level == "DEBUG" (uppercased)

#### Scenario: LoggingConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** LoggingConfig is constructed with no arguments
- **When** the instance attributes are inspected
- **Then** level == "INFO", fmt == "text", file is None

#### Scenario: ZsigaConfig construction

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::ZsigaConfig.__init__
- **Given** ZsigaConfig is constructed with required args (llm, targets, pipeline, intake, safety)
  and optional args (logging_config, llm_fast, github, active_target)
- **When** the instance attributes are inspected
- **Then** all attributes match the provided values

