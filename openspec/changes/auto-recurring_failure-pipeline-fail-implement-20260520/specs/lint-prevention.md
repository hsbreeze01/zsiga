# Spec: Implementer Lint Prevention

## ADDED Requirements

### Requirement: Implementer SHALL include lint-prevention rules in system prompt

The implementer system prompt SHALL contain an explicit section listing common lint violations
that MUST be avoided during code generation. This acts as a proactive guard rather than relying
solely on post-hoc mechanical verification.

#### Scenario: Agent generates code without E701/E702/E401 violations

- **Given** the implementer phase is active
- **When** the agent writes Python code as part of a task
- **Then** the generated code SHALL NOT contain any of the following patterns:
  - `if condition: action` on a single line (E701)
  - Multiple statements joined by semicolons (E702)
  - Multiple imports on a single `import` line (E401)
  - Single-letter ambiguous variable names like `l`, `O`, `I` (E741)
  - Trailing whitespace or missing final newline (W292/W291)

#### Scenario: Lint-prevention section is appended to IMPLEMENTER_SYSTEM

- **Given** the implementer module is loaded
- **When** the `IMPLEMENTER_SYSTEM` constant is constructed
- **Then** it SHALL include a "## Lint Prevention Rules" section with explicit examples
  of forbidden patterns and their correct alternatives

### Requirement: Implementer SHALL inject active pattern warnings

The implementer phase SHALL receive recurring-failure pattern warnings from the pattern miner
as part of its context, so the agent can proactively avoid known failure modes.

#### Scenario: Pattern warnings are included in implementer user prompt

- **Given** the pipeline has pattern warnings mined from learnings
- **And** at least one warning has severity "high"
- **When** the implementer phase starts for a change
- **Then** the user prompt SHALL include the top-3 high-severity pattern warnings
  as a "## Known Failure Patterns (AVOID)" section

#### Scenario: No high-severity warnings exist

- **Given** no pattern warnings exist or none have severity "high"
- **When** the implementer phase starts
- **Then** the implementer prompt SHALL NOT include any pattern-warning section
  (no noise injection)
