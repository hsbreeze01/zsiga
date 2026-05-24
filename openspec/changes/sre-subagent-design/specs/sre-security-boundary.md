# Spec: SRE Security Boundary

## ADDED Requirements

### Requirement: Command Validation Passes Whitelisted Commands

The `validate_command()` function SHALL return `True` when a command starts with a whitelisted prefix and does not match any blacklist pattern.

#### Scenario: Whitelisted command passes validation

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a whitelist `["systemctl restart", "df"]` and blacklist `["rm -rf"]`
- **When** `validate_command("systemctl restart nginx", whitelist, blacklist)` is called
- **Then** the result SHALL be `True`

---

### Requirement: Command Validation Rejects Non-Whitelisted Commands

The `validate_command()` function SHALL return `False` when a command does not start with any whitelisted prefix.

#### Scenario: Non-whitelisted command fails validation

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a whitelist `["systemctl"]` and an empty blacklist
- **When** `validate_command("apt-get install something", whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

---

### Requirement: Blacklist Overrides Whitelist

The `validate_command()` function SHALL return `False` when a command matches a blacklist entry, even if it also matches a whitelist entry. Blacklist takes priority over whitelist.

#### Scenario: Blacklisted command fails even if whitelisted

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a whitelist `["systemctl"]` and a blacklist `["eval"]`
- **When** `validate_command("systemctl eval malicious", whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

---

### Requirement: Empty Command Rejected

The `validate_command()` function SHALL return `False` for an empty string command.

#### Scenario: Empty command fails validation

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** any whitelist and blacklist
- **When** `validate_command("", whitelist, blacklist)` is called
- **Then** the result SHALL be `False`

---

### Requirement: Pre-Execution State Snapshot

The SRE pipeline SHALL expose a `take_snapshot(transport)` function that captures the current system state as a dict with keys `"services"`, `"disk"`, and `"memory"`. Each value SHALL be a non-empty string.

#### Scenario: Snapshot captures service and resource state

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::take_snapshot
- **Given** a `LocalTransport` instance
- **When** `take_snapshot(transport)` is called
- **Then** the result SHALL be a dict containing keys `"services"`, `"disk"`, and `"memory"`

#### Scenario: Snapshot contains non-empty string values

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::take_snapshot
- **Given** a `LocalTransport` instance
- **When** `take_snapshot(transport)` is called
- **Then** each of `snapshot["services"]`, `snapshot["disk"]`, and `snapshot["memory"]` SHALL be a non-empty string

---

### Requirement: Dangerous Command Detection

The SRE pipeline SHALL expose an `is_dangerous_command(cmd)` function that returns `True` for commands that perform state mutations on services (e.g., `systemctl stop`, `systemctl restart`) and `False` for read-only commands (e.g., `systemctl status`, `df -h`).

#### Scenario: Service stop commands are flagged as dangerous

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::is_dangerous_command
- **Given** a command `"systemctl stop nginx"`
- **When** `is_dangerous_command("systemctl stop nginx")` is called
- **Then** the result SHALL be `True`

#### Scenario: Status query is not flagged as dangerous

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::is_dangerous_command
- **Given** a command `"systemctl status nginx"`
- **When** `is_dangerous_command("systemctl status nginx")` is called
- **Then** the result SHALL be `False`

#### Scenario: Disk usage query is not flagged as dangerous

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::is_dangerous_command
- **Given** a command `"df -h"`
- **When** `is_dangerous_command("df -h")` is called
- **Then** the result SHALL be `False`
