# Spec: SRE Role Definition

## ADDED Requirements

### Requirement: SRE Role Enum Member

The `Role` enum in `roles.py` SHALL include an `SRE` member with value `"sre"`.

#### Scenario: SRE role enum value exists

- **testable**: true
- **target**: zsiga/agent/roles.py::Role
- **Given** the `Role` enum is loaded
- **When** accessing `Role("sre")` and `Role.SRE.value`
- **Then** `Role("sre")` SHALL be `Role.SRE` and `.value` SHALL equal `"sre"`

---

### Requirement: SRE Role Configuration Attributes

The `get_role_config(Role.SRE)` function SHALL return a role config object with the following attributes: `name == "sre"`, `max_turns == 15`, `read_only == False`, and `allowed_tools` being the set `{"bash", "read_file", "search", "list_files"}`.

#### Scenario: SRE role config has correct attributes

- **testable**: true
- **target**: zsiga/agent/roles.py::get_role_config
- **Given** the roles module is loaded
- **When** `get_role_config(Role.SRE)` is called
- **Then** the returned config SHALL have `name == "sre"`, `max_turns == 15`, `read_only is False`, and `allowed_tools == {"bash", "read_file", "search", "list_files"}`

---

### Requirement: SRE System Prompt Content

The `get_role_system_prompt(Role.SRE)` function SHALL return a non-empty string of at least 50 characters that mentions idempotency (幂等/idempotent) and rollback/revert (回滚/rollback/revert) operational constraints.

#### Scenario: SRE system prompt is non-empty

- **testable**: true
- **target**: zsiga/agent/roles.py::get_role_system_prompt
- **Given** the roles module is loaded
- **When** `get_role_system_prompt(Role.SRE)` is called
- **Then** the result SHALL be a string with length greater than 50

#### Scenario: SRE system prompt mentions idempotency

- **testable**: true
- **target**: zsiga/agent/roles.py::get_role_system_prompt
- **Given** the SRE system prompt is retrieved
- **When** checking its content
- **Then** it SHALL contain either "幂等" or "idempotent" (case-insensitive)

#### Scenario: SRE system prompt mentions rollback

- **testable**: true
- **target**: zsiga/agent/roles.py::get_role_system_prompt
- **Given** the SRE system prompt is retrieved
- **When** checking its content
- **Then** it SHALL contain at least one of: "回滚", "rollback", or "revert" (case-insensitive)

---

### Requirement: Existing Roles Preserved

Adding the SRE role SHALL NOT modify any existing role configurations. `get_all_roles()` SHALL return all original roles (EXPLORE, IMPLEMENT, REVIEW, DIAGNOSER) with their original attributes unchanged.

#### Scenario: Existing roles remain unchanged

- **testable**: true
- **target**: zsiga/agent/roles.py::get_all_roles
- **Given** the SRE role has been added
- **When** `get_all_roles()` is called
- **Then** all original roles (EXPLORE, IMPLEMENT, REVIEW, DIAGNOSER) SHALL be present with their original `name`, `read_only`, and `max_turns` values preserved

---

### Requirement: SRE Command Whitelist

The SRE role config SHALL include a `command_whitelist` attribute containing entries for `systemctl start`, `systemctl stop`, `systemctl restart`, `systemctl status`, and diagnostic commands: `df`, `free`, `du`, `journalctl`, `dmesg`.

#### Scenario: Command whitelist contains systemctl variants

- **testable**: true
- **target**: zsiga/agent/roles.py::get_role_config
- **Given** the SRE role config is retrieved
- **When** inspecting `config.command_whitelist`
- **Then** it SHALL contain entries matching "systemctl start", "systemctl stop", "systemctl restart", and "systemctl status"

#### Scenario: Command whitelist contains diagnostic commands

- **testable**: true
- **target**: zsiga/agent/roles.py::get_role_config
- **Given** the SRE role config is retrieved
- **When** inspecting `config.command_whitelist`
- **Then** it SHALL contain exactly "df", "free", "du", "journalctl", and "dmesg"

---

### Requirement: SRE Command Blacklist

The SRE role config SHALL include a `command_blacklist` attribute containing at minimum: `"rm -rf"`, `"iptables"`, and `"sysctl"`.

#### Scenario: Blacklist blocks rm -rf

- **testable**: true
- **target**: zsiga/agent/roles.py::get_role_config
- **Given** the SRE role config is retrieved
- **When** inspecting `config.command_blacklist`
- **Then** it SHALL contain `"rm -rf"`

#### Scenario: Blacklist blocks iptables and sysctl

- **testable**: true
- **target**: zsiga/agent/roles.py::get_role_config
- **Given** the SRE role config is retrieved
- **When** inspecting `config.command_blacklist`
- **Then** it SHALL contain both `"iptables"` and `"sysctl"`
