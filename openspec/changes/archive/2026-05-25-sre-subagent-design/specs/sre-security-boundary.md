# Spec: SRE Security Boundary

## ADDED Requirements

### Requirement: Command Whitelist Enforcement

The SRE pipeline SHALL maintain a hardcoded command whitelist. Only commands whose base executable matches the whitelist SHALL be allowed for execution. The whitelist MUST include at minimum:

- `systemctl` (subcommands: start, stop, restart, status)
- `curl`
- `df`
- `free`
- `du`
- `journalctl`
- `dmesg`
- `crontab`
- `ps`
- `cat`
- `ls`
- `grep`

#### Scenario: Whitelisted command passes validation

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"systemctl status nginx"`
- **When** `validate_command` is called with that string
- **Then** it SHALL return `True`

#### Scenario: Whitelisted command with sudo passes validation

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"sudo systemctl restart nginx"`
- **When** `validate_command` is called with that string
- **Then** it SHALL return `True` (sudo prefix is transparent)

#### Scenario: Non-whitelisted command is rejected

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"apt-get install something"`
- **When** `validate_command` is called with that string
- **Then** it SHALL return `False`

### Requirement: Blacklisted Command Rejection

The following commands and patterns MUST be unconditionally rejected regardless of whitelist status:

- `rm -rf` or `rm -r` (recursive delete)
- `iptables` (firewall rules)
- `sysctl` (kernel parameters)
- `ssh-keygen`, `ssh-copy-id` (key operations)
- `chmod 777`, `chown` (permission changes)
- `dd` (raw disk operations)
- `mkfs` (filesystem format)
- `shutdown`, `reboot`, `poweroff` (system power)
- `passwd` (password changes)

#### Scenario: Blacklisted rm -rf is rejected

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"rm -rf /var/log/old"`
- **When** `validate_command` is called
- **Then** it SHALL return `False`

#### Scenario: Blacklisted iptables is rejected

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"iptables -A INPUT -j DROP"`
- **When** `validate_command` is called
- **Then** it SHALL return `False`

#### Scenario: Blacklisted reboot is rejected

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"reboot"`
- **When** `validate_command` is called
- **Then** it SHALL return `False`

#### Scenario: Blacklisted command hidden behind sudo is still rejected

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"sudo reboot"`
- **When** `validate_command` is called
- **Then** it SHALL return `False`

#### Scenario: Blacklisted sysctl is rejected

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"sysctl -w vm.swappiness=10"`
- **When** `validate_command` is called
- **Then** it SHALL return `False`

### Requirement: Blacklist Takes Precedence Over Whitelist

If a command matches both whitelist and blacklist patterns, the blacklist MUST take precedence and the command SHALL be rejected.

#### Scenario: systemctl is whitelisted but shutdown subcommand is not

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::validate_command
- **Given** a command string `"systemctl shutdown"` (shutdown is blacklisted)
- **When** `validate_command` is called
- **Then** it SHALL return `False`

### Requirement: Pre-Execution Snapshot for Revert

Before executing each command in the EXECUTE phase, the pipeline SHOULD capture a lightweight snapshot of relevant state. If execution fails, the pipeline SHOULD attempt to revert to the pre-execution state using rollback commands from the PLAN phase.

#### Scenario: Execution failure triggers rollback attempt

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._execute
- **Given** a plan with a step that fails, and the plan includes a rollback command for that step
- **When** the EXECUTE phase encounters the failure
- **Then** the rollback command for the failed step SHALL be invoked before proceeding to REPORT

### Requirement: Dangerous Operation Approval Gate

Operations classified as dangerous (e.g., `systemctl stop`, `systemctl restart`) SHALL be flagged with `require_approval: true`. When running in a context without approval, these operations MUST be skipped with a warning.

#### Scenario: Dangerous command flagged in plan

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::classify_command_risk
- **Given** a command `"systemctl stop nginx"`
- **When** `classify_command_risk` is called
- **Then** it SHALL return a dict with `"require_approval" == True`

#### Scenario: Safe command not flagged

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::classify_command_risk
- **Given** a command `"systemctl status nginx"`
- **When** `classify_command_risk` is called
- **Then** it SHALL return a dict with `"require_approval" == False`
