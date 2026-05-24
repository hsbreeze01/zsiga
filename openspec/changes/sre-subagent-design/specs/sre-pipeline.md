# Spec: SRE Pipeline

## ADDED Requirements

### Requirement: Five-Phase Pipeline Execution

The SRE pipeline SHALL execute exactly 5 phases in order: DIAGNOSE → PLAN → EXECUTE → VERIFY → REPORT. Each phase MUST complete before the next begins. The pipeline SHALL be implemented in `zsiga/pipeline/sre_pipeline.py`.

#### Scenario: Pipeline defines all five phases in order

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline
- **Given** the `SREPipeline` class is imported
- **When** its phase names or phase order is inspected
- **Then** it SHALL contain exactly the phases `["DIAGNOSE", "PLAN", "EXECUTE", "VERIFY", "REPORT"]` in that order

#### Scenario: Pipeline run produces phase completion record for each phase

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline.run
- **Given** a valid SRE task input (e.g., "检查磁盘使用情况")
- **When** `SREPipeline.run` is called with the task and mocked transport (no real bash execution)
- **Then** the result SHALL contain records for all 5 phases, each with a `"phase"` key and a `"status"` key

### Requirement: DIAGNOSE Phase — State Collection

The DIAGNOSE phase SHALL collect current system state information: service status, recent logs, and resource usage. It MUST NOT execute any state-changing commands.

#### Scenario: DIAGNOSE phase collects read-only information

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._diagnose
- **Given** a mock transport that records all commands sent
- **When** the DIAGNOSE phase runs with input "检查 nginx 服务状态"
- **Then** all commands issued during DIAGNOSE SHALL be read-only commands (e.g., `systemctl status`, `df`, `free`, `journalctl`, `ps`) — no `start`, `stop`, `restart` commands

### Requirement: PLAN Phase — Whitelist-Constrained Command Generation

The PLAN phase SHALL generate a sequence of shell commands that are all within the command whitelist. Any command not in the whitelist MUST be rejected before execution.

#### Scenario: PLAN phase only generates whitelisted commands

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._plan
- **Given** the DIAGNOSE phase has completed with collected state
- **When** the PLAN phase generates a command plan
- **Then** every command in the plan SHALL pass the whitelist validation function

### Requirement: EXECUTE Phase — Step-by-Step Execution with Assertion

The EXECUTE phase SHALL execute planned commands one at a time. After each command, it MUST check the result. If any step fails, execution SHALL halt and the pipeline SHALL proceed to REPORT with a failure status.

#### Scenario: EXECUTE stops on first failure

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._execute
- **Given** a plan with 3 commands where the 2nd command returns a non-zero exit code
- **When** the EXECUTE phase runs
- **Then** only 2 commands SHALL be executed (the first and the failing second), and the execute result SHALL have `"status" == "failed"`

#### Scenario: EXECUTE succeeds when all commands pass

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._execute
- **Given** a plan with 2 commands where both return exit code 0
- **When** the EXECUTE phase runs
- **Then** all 2 commands SHALL be executed, and the execute result SHALL have `"status" == "success"`

### Requirement: VERIFY Phase — Target State Validation

The VERIFY phase SHALL run verification commands to confirm the target state is achieved. If verification fails, the phase SHALL return a `"status" == "failed"` result with diagnostic details.

#### Scenario: VERIFY returns success when target state matches

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._verify
- **Given** the EXECUTE phase completed successfully and verification commands return expected output
- **When** the VERIFY phase runs
- **Then** the result SHALL have `"status" == "success"`

#### Scenario: VERIFY returns failure when target state not achieved

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._verify
- **Given** the EXECUTE phase completed but verification commands show the issue persists
- **When** the VERIFY phase runs
- **Then** the result SHALL have `"status" == "failed"` with diagnostic information

### Requirement: REPORT Phase — Output Without Git Commit

The REPORT phase SHALL produce an execution report. The pipeline MUST NOT create any git commit during its entire lifecycle.

#### Scenario: Pipeline does not invoke git commit

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline.run
- **Given** a mock transport that records all commands
- **When** the full pipeline runs to completion
- **Then** no `git commit` command SHALL appear in the recorded commands

#### Scenario: REPORT phase produces execution report data

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._report
- **Given** all previous phases have completed
- **When** the REPORT phase runs
- **Then** it SHALL return a dict containing at minimum keys: `"phases"`, `"status"`, `"steps"` (or equivalent summary of what was done)
