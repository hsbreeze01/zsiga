# Spec: SRE Pipeline

## ADDED Requirements

### Requirement: SRE Pipeline Module

A new module `zsiga/pipeline/sre_pipeline.py` SHALL implement a function `run_sre_pipeline(intent, target_path, transport)` that executes the SRE operational pipeline. The pipeline SHALL consist of five sequential phases: DIAGNOSE, PLAN, EXECUTE, VERIFY, REPORT.

The function SHALL accept the following parameters:
- `intent`: an `Intent` object from intent classification
- `target_path`: string path to the target project
- `transport`: a `Transport` instance for command execution

The function SHALL return an `SREResult` dataclass containing: `success: bool`, `report_path: str`, `phases_completed: list[str]`, `commands_executed: list[str]`.

#### Scenario: SRE pipeline returns SREResult dataclass

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::run_sre_pipeline
- **Given** a valid SRE intent and localhost transport
- **When** `run_sre_pipeline(intent, target_path, transport)` completes
- **Then** the return type SHALL be `SREResult`
- **And** `phases_completed` SHALL contain exactly `["DIAGNOSE", "PLAN", "EXECUTE", "VERIFY", "REPORT"]`

#### Scenario: SRE pipeline produces no git commit

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::run_sre_pipeline
- **Given** a completed SRE pipeline run
- **When** the pipeline finishes
- **Then** no git commit SHALL have been created (no tag, no branch created)

### Requirement: DIAGNOSE Phase

The DIAGNOSE phase SHALL collect current system state: service statuses (via `systemctl status`), resource usage (via `df`, `free`), recent logs (via `journalctl`), and running processes (via `ps`). The collected state SHALL be stored as a structured snapshot for later comparison.

#### Scenario: DIAGNOSE phase collects system state

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::diagnose
- **Given** a DIAGNOSE phase execution
- **When** `diagnose(transport)` is called
- **Then** the return value SHALL be a dict with keys including at least `"services"`, `"disk"`, `"memory"`, `"processes"`

### Requirement: PLAN Phase

The PLAN phase SHALL generate a sequence of shell commands that address the SRE intent. Every generated command MUST pass command whitelist validation. If any planned command matches the blacklist, the PLAN phase SHALL fail and return an error.

#### Scenario: PLAN rejects blacklisted commands

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::plan
- **Given** a plan that includes a blacklisted command (e.g., `rm -rf /tmp/log`)
- **When** `plan()` validates the command list
- **Then** it SHALL raise `CommandValidationError` or return with `success=False`
- **And** no command SHALL be executed

#### Scenario: PLAN accepts whitelisted commands

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::plan
- **Given** a plan that includes only whitelisted commands (e.g., `systemctl restart nginx`, `df -h`)
- **When** `plan()` validates the command list
- **Then** all commands SHALL pass validation

### Requirement: EXECUTE Phase

The EXECUTE phase SHALL execute planned commands sequentially. Before each command execution, a snapshot of the current state SHALL be captured. If a command fails (non-zero exit code), the EXECUTE phase SHALL stop and return the failure information. Each executed command and its result SHALL be recorded.

#### Scenario: EXECUTE records each command result

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::execute
- **Given** a list of 3 planned commands
- **When** `execute(commands, transport)` completes successfully
- **Then** the return value SHALL contain exactly 3 command records, each with `command`, `exit_code`, and `stdout` fields

#### Scenario: EXECUTE stops on command failure

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::execute
- **Given** a list of 3 planned commands where the 2nd command fails
- **When** `execute(commands, transport)` is called
- **Then** only 2 command records SHALL be returned (the 2nd being the failure)
- **And** `success` SHALL be `False`

### Requirement: VERIFY Phase

The VERIFY phase SHALL re-collect system state (same data sources as DIAGNOSE) and compare with the pre-execution snapshot. It SHALL confirm whether the target state described in the intent has been achieved.

#### Scenario: VERIFY compares pre and post state

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::verify
- **Given** pre-execution snapshot and post-execution state
- **When** `verify(pre_snapshot, post_snapshot, intent)` is called
- **Then** the return value SHALL be a dict with key `"passed"` (bool) and `"differences"` (list)

### Requirement: REPORT Phase

The REPORT phase SHALL generate an `execution_report.md` file at `{change_dir}/execution_report.md`. The report SHALL contain: intent description, all phases executed with results, commands run with outputs, verification result, and a summary. The report SHALL NOT trigger any git operations.

#### Scenario: REPORT generates execution_report.md

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::report
- **Given** completed DIAGNOSE, PLAN, EXECUTE, and VERIFY results
- **When** `report(results, change_dir, transport)` is called
- **Then** a file `execution_report.md` SHALL exist in `change_dir`
- **And** its content SHALL contain headings for "Intent", "Phases", "Commands", and "Verification"

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
