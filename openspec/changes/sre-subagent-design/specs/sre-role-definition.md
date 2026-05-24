# Spec: SRE Agent Role Definition

## ADDED Requirements

### Requirement: SRE Role in Role Enum

The `Role` enum in `roles.py` SHALL include a new value `SRE = "sre"`. The `_ROLES` dictionary SHALL contain a corresponding `RoleConfig` entry with the following attributes:

- `name`: `"sre"`
- `max_turns`: `15`
- `read_only`: `False`
- `allowed_tools`: `["bash", "read_file", "search", "list_files"]`
- `system_prompt`: a non-empty string containing SRE operational guidelines

#### Scenario: SRE role enum value exists

- **testable**: true
- **target**: zsiga.agent.roles::Role
- **Given** the `Role` enum
- **When** `Role("sre")` is called
- **Then** it SHALL return `Role.SRE`

#### Scenario: SRE role config has correct attributes

- **testable**: true
- **target**: zsiga.agent.roles::get_role_config
- **Given** the SRE role configuration
- **When** `get_role_config(Role.SRE)` is called
- **Then** the returned `RoleConfig` SHALL have `name="sre"`, `max_turns=15`, `read_only=False`
- **And** `allowed_tools` SHALL be `["bash", "read_file", "search", "list_files"]`

#### Scenario: SRE system prompt is non-empty

- **testable**: true
- **target**: zsiga.agent.roles::get_role_system_prompt
- **Given** the SRE role
- **When** `get_role_system_prompt(Role.SRE)` is called
- **Then** the returned string SHALL have length greater than 50 characters

#### Scenario: SRE system prompt mentions idempotency

- **testable**: true
- **target**: zsiga.agent.roles::get_role_system_prompt
- **Given** the SRE role system prompt
- **When** the prompt text is inspected
- **Then** it SHALL contain the substring "幂等" or "idempotent"

#### Scenario: SRE system prompt mentions rollback

- **testable**: true
- **target**: zsiga.agent.roles::get_role_system_prompt
- **Given** the SRE role system prompt
- **When** the prompt text is inspected
- **Then** it SHALL contain the substring "回滚" or "rollback" or "revert"

#### Scenario: Existing roles remain unchanged

- **testable**: true
- **target**: zsiga.agent.roles::get_all_roles
- **Given** the full role registry
- **When** `get_all_roles()` is called
- **Then** the result SHALL contain keys for `Role.EXPLORE`, `Role.IMPLEMENT`, `Role.REVIEW`, `Role.DIAGNOSER`
- **And** each of those SHALL have the same `name`, `max_turns`, and `read_only` values as before

### Requirement: SRE Command Whitelist

The SRE `RoleConfig` SHALL expose a `command_whitelist` attribute containing a list of allowed command prefixes. The whitelist SHALL include at minimum: `systemctl start`, `systemctl stop`, `systemctl restart`, `systemctl status`, `curl`, `df`, `free`, `du`, `journalctl`, `dmesg`, `crontab`, `ps`, `top`, `ls`, `cat`, `grep`, `find`, `wc`, `uptime`.

#### Scenario: Command whitelist contains systemctl variants

- **testable**: true
- **target**: zsiga.agent.roles::get_role_config
- **Given** the SRE role configuration
- **When** `get_role_config(Role.SRE).command_whitelist` is accessed
- **Then** it SHALL contain entries starting with `"systemctl start"`, `"systemctl stop"`, `"systemctl restart"`, `"systemctl status"`

#### Scenario: Command whitelist contains diagnostic commands

- **testable**: true
- **target**: zsiga.agent.roles::get_role_config
- **Given** the SRE role configuration
- **When** `get_role_config(Role.SRE).command_whitelist` is accessed
- **Then** it SHALL contain `"df"`, `"free"`, `"du"`, `"journalctl"`, `"dmesg"`

### Requirement: SRE Command Blacklist

The SRE `RoleConfig` SHALL expose a `command_blacklist` attribute containing a list of forbidden command patterns. The blacklist SHALL include at minimum: `rm -rf`, `rm -r /`, `iptables`, `sysctl`, `mkfs`, `dd if=`, `chmod 777`, `chown`, `passwd`, `ssh-keygen`, `eval`, `exec`.

#### Scenario: Blacklist blocks rm -rf

- **testable**: true
- **target**: zsiga.agent.roles::get_role_config
- **Given** the SRE role configuration
- **When** `get_role_config(Role.SRE).command_blacklist` is accessed
- **Then** it SHALL contain `"rm -rf"`

#### Scenario: Blacklist blocks iptables and sysctl

- **testable**: true
- **target**: zsiga.agent.roles::get_role_config
- **Given** the SRE role configuration
- **When** `get_role_config(Role.SRE).command_blacklist` is accessed
- **Then** it SHALL contain `"iptables"` and `"sysctl"`

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
