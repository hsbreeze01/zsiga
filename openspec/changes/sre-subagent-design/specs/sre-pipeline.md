# Spec: SRE Pipeline

## ADDED Requirements

### Requirement: Command Validation Function

The SRE pipeline SHALL expose a `validate_command(cmd, whitelist, blacklist)` function that returns `True` only when `cmd` is non-empty, matches at least one whitelist entry prefix, and does not match any blacklist entry. A command matching both whitelist and blacklist SHALL be rejected (blacklist takes priority).

#### Scenario: Command Validation — whitelisted command passes

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a whitelist containing `"systemctl restart"` and `"df"`, and a blacklist containing `"rm -rf"` and `"eval"`
- **When** `validate_command("systemctl restart nginx", whitelist, blacklist)` is called
- **Then** the result SHALL be `True`

#### Scenario: Command Validation — non-whitelisted command fails

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a whitelist containing `"systemctl"` and `"df"` and `"free"`, and an empty blacklist
- **When** `validate_command("apt-get install something", whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

#### Scenario: Command Validation — blacklisted command fails even with whitelist match

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a whitelist containing `"systemctl"` and a blacklist containing `"eval"`
- **When** `validate_command("systemctl eval malicious", whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

#### Scenario: Command Validation — empty command fails

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a whitelist containing `"systemctl"` and a blacklist containing `"rm -rf"`
- **When** `validate_command("", whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

---

### Requirement: DIAGNOSE Phase

The SRE pipeline SHALL expose a `diagnose(transport)` function that collects system state and returns a dict with keys `"services"`, `"disk"`, `"memory"`, and `"processes"`.

#### Scenario: DIAGNOSE phase collects system state

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::diagnose
- **Given** a `LocalTransport` instance
- **When** `diagnose(transport)` is called
- **Then** the result SHALL be a dict containing keys `"services"`, `"disk"`, `"memory"`, and `"processes"`

---

### Requirement: PLAN Phase

The SRE pipeline SHALL expose a `plan(intent_description, proposed_commands, whitelist, blacklist)` function that validates all proposed commands against the whitelist and blacklist. If any command fails validation, `result["success"]` SHALL be `False`. If all pass, `result["success"]` SHALL be `True`.

#### Scenario: PLAN rejects blacklisted commands

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::plan
- **Given** proposed commands containing `"rm -rf /var/log"` and `"df -h"`, with whitelist `["systemctl", "df"]` and blacklist `["rm -rf"]`
- **When** `plan(...)` is called
- **Then** `result["success"]` SHALL be `False`

#### Scenario: PLAN accepts whitelisted commands

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::plan
- **Given** proposed commands containing `"systemctl restart nginx"` and `"df -h"`, with whitelist `["systemctl restart", "df"]` and blacklist `["rm -rf"]`
- **When** `plan(...)` is called
- **Then** `result["success"]` SHALL be `True`

---

### Requirement: EXECUTE Phase

The SRE pipeline SHALL expose an `execute(commands, transport)` function that runs commands sequentially via the transport. It SHALL record each command's `command`, `exit_code`, and `stdout`. If a command fails (non-zero exit code), execution SHALL stop immediately and `result["success"]` SHALL be `False` with only completed commands recorded.

#### Scenario: EXECUTE records each command result

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::execute
- **Given** a `LocalTransport` instance and commands `["echo hello", "echo world", "echo done"]`
- **When** `execute(commands, transport)` is called
- **Then** `result["success"]` SHALL be `True` and `result["commands"]` SHALL contain 3 entries, each with keys `"command"`, `"exit_code"`, and `"stdout"`

#### Scenario: EXECUTE stops on command failure

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::execute
- **Given** a `LocalTransport` instance and commands `["echo ok", "false", "echo should_not_run"]`
- **When** `execute(commands, transport)` is called
- **Then** `result["success"]` SHALL be `False` and only 2 command records SHALL be present (the successful first command and the failed second command)

---

### Requirement: VERIFY Phase

The SRE pipeline SHALL expose a `verify(pre, post, intent)` function that compares pre-execution and post-execution system state dicts and returns a dict with keys `"passed"` and `"differences"`.

#### Scenario: VERIFY compares pre and post state

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::verify
- **Given** pre-state and post-state dicts with `"services"`, `"disk"`, and `"memory"` keys, and an intent description
- **When** `verify(pre, post, "free up disk space")` is called
- **Then** the result SHALL contain keys `"passed"` and `"differences"`

---

### Requirement: REPORT Phase

The SRE pipeline SHALL expose a `report(results, output_dir, transport)` function that writes an `execution_report.md` file to `output_dir`. The report SHALL contain sections: `## Intent`, `## Timeline` (or `## Phases`), `## Commands`, and `## Verification`.

#### Scenario: REPORT generates execution_report.md

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::report
- **Given** execution results with phases, commands, and verification data, and a temporary output directory
- **When** `report(results, tmpdir, transport)` is called
- **Then** a file named `execution_report.md` SHALL exist in `tmpdir` containing sections `## Intent`, `## Timeline` or `## Phases`, `## Commands`, and `## Verification`

---

### Requirement: Report Content Generation

The SRE pipeline SHALL expose a `generate_report_content(results)` function that returns a markdown string starting with `# SRE Execution Report` and containing sections `## Intent`, `## Timeline`, `## Commands`, `## Verification`, and `## Summary`. All executed commands SHALL appear in the Commands section.

#### Scenario: Report contains all required sections

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::generate_report_content
- **Given** execution results with intent, phases, commands, and verification data
- **When** `generate_report_content(results)` is called
- **Then** the returned string SHALL contain `# SRE Execution Report`, `## Intent`, `## Timeline`, `## Commands`, `## Verification`, and `## Summary`

#### Scenario: Report commands table includes all executed commands

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::generate_report_content
- **Given** execution results with 2 commands: `"systemctl status nginx"` and `"df -h"`
- **When** `generate_report_content(results)` is called
- **Then** the returned string SHALL contain both `"systemctl status nginx"` and `"df -h"`
