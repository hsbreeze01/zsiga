# Spec: SRE Role Definition

## ADDED Requirements

### Requirement: SRE Role Configuration

The roles module SHALL register an SRE role with the following configuration attributes:
- `name`: `"sre"`
- `max_turns`: 15
- `read_only`: `False`
- `allowed_tools`: `["bash", "read_file", "search", "list_files"]`

#### Scenario: SRE role is registered and retrievable

- **testable**: true
- **target**: zsiga/roles.py::get_role
- **Given** the roles module is loaded
- **When** `get_role("sre")` is called
- **Then** it SHALL return a role object with `name == "sre"`, `max_turns == 15`, `read_only == False`

#### Scenario: SRE role has correct allowed tools

- **testable**: true
- **target**: zsiga/roles.py::get_role
- **Given** the roles module is loaded
- **When** the `allowed_tools` attribute of the SRE role is inspected
- **Then** it SHALL contain exactly `["bash", "read_file", "search", "list_files"]`

### Requirement: SRE System Prompt with Operational Guidelines

The SRE role SHALL include a system_prompt that encodes the following operational principles:
1. **Idempotency**: All operations MUST be idempotent — running the same command twice produces the same result.
2. **Rollback strategy**: Each plan step SHOULD include a rollback command.
3. **Whitelist-only commands**: Only whitelisted commands SHALL be executed.
4. **No code commits**: SRE pipeline MUST NOT produce git commits.

#### Scenario: SRE system prompt mentions idempotency

- **testable**: true
- **target**: zsiga/roles.py::get_role
- **Given** the SRE role is retrieved
- **When** the `system_prompt` attribute is inspected
- **Then** it SHALL contain the word "幂等" or "idempotent" (case-insensitive)

#### Scenario: SRE system prompt mentions rollback

- **testable**: true
- **target**: zsiga/roles.py::get_role
- **Given** the SRE role is retrieved
- **When** the `system_prompt` attribute is inspected
- **Then** it SHALL contain "回滚" or "rollback" (case-insensitive)

#### Scenario: SRE system prompt mentions whitelist constraint

- **testable**: true
- **target**: zsiga/roles.py::get_role
- **Given** the SRE role is retrieved
- **When** the `system_prompt` attribute is inspected
- **Then** it SHALL contain "白名单" or "whitelist" (case-insensitive)

#### Scenario: SRE system prompt prohibits git commits

- **testable**: true
- **target**: zsiga/roles.py::get_role
- **Given** the SRE role is retrieved
- **When** the `system_prompt` attribute is inspected
- **Then** it SHALL contain "git commit" (case-insensitive) with a prohibition context (e.g., "禁止", "不得", "MUST NOT", "no git")
