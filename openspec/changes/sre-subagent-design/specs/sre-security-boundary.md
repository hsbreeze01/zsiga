# Spec: SRE Security Boundary

## ADDED Requirements

### Requirement: Command Validation Function

A function `validate_command(command: str, whitelist: list[str], blacklist: list[str]) -> bool` SHALL be provided in `zsiga/pipeline/sre_pipeline.py`. It SHALL return `True` only if the command starts with at least one whitelist entry AND does not match any blacklist pattern. Matching SHALL be prefix-based for both whitelist and blacklist.

#### Scenario: Whitelisted command passes validation

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::validate_command
- **Given** `command="systemctl restart nginx"`, whitelist containing `"systemctl restart"`, blacklist containing `"rm -rf"`
- **When** `validate_command(command, whitelist, blacklist)` is called
- **Then** the result SHALL be `True`

#### Scenario: Non-whitelisted command fails validation

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::validate_command
- **Given** `command="apt-get install something"`, whitelist containing `"systemctl"`, blacklist empty
- **When** `validate_command(command, whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

#### Scenario: Blacklisted command fails even if whitelisted prefix matches

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::validate_command
- **Given** `command="systemctl eval malicious"`, whitelist containing `"systemctl"`, blacklist containing `"eval"`
- **When** `validate_command(command, whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

#### Scenario: Empty command fails validation

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::validate_command
- **Given** `command=""`, non-empty whitelist and blacklist
- **When** `validate_command(command, whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

### Requirement: Pre-execution State Snapshot

Before executing each command in the EXECUTE phase, the pipeline SHALL capture a snapshot of relevant system state. The snapshot SHALL include: list of running services (`systemctl list-units --type=service --state=running`), disk usage (`df -h`), and memory usage (`free -h`).

#### Scenario: Snapshot captures service and resource state

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::take_snapshot
- **Given** a transport for command execution
- **When** `take_snapshot(transport)` is called
- **Then** the return value SHALL be a dict with keys `"services"`, `"disk"`, `"memory"`

#### Scenario: Snapshot contains non-empty string values

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::take_snapshot
- **Given** a working transport
- **When** `take_snapshot(transport)` is called
- **Then** each value in the returned dict SHALL be a non-empty string

### Requirement: Approval Gate for Dangerous Operations

Commands that involve service stop or restart operations SHALL be flagged with `require_approval=True`. The pipeline SHALL check this flag before execution and skip the command if approval is not granted. In automated (non-interactive) mode, dangerous operations SHALL be logged and skipped.

#### Scenario: Service stop commands are flagged as dangerous

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::is_dangerous_command
- **Given** a command `"systemctl stop nginx"`
- **When** `is_dangerous_command(command)` is called
- **Then** the result SHALL be `True`

#### Scenario: Status query is not flagged as dangerous

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::is_dangerous_command
- **Given** a command `"systemctl status nginx"`
- **When** `is_dangerous_command(command)` is called
- **Then** the result SHALL be `False`

#### Scenario: Disk usage query is not flagged as dangerous

- **testable**: true
- **target**: zsiga.pipeline.sre_pipeline::is_dangerous_command
- **Given** a command `"df -h"`
- **When** `is_dangerous_command(command)` is called
- **Then** the result SHALL be `False`

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
