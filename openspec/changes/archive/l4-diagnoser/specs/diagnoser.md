# Spec: Structured Diagnosis Loop

## ADDED Requirements

### Requirement: Diagnoser Module
The system SHALL provide a `Diagnoser` class in `zsiga/pipeline/diagnoser.py` that implements a structured diagnosis loop triggered after verify-phase failure.

#### Scenario: Diagnoser is importable
- Given the `zsiga.pipeline.diagnoser` module exists
- When `from zsiga.pipeline.diagnoser import Diagnoser` is executed
- Then the import succeeds without error

#### Scenario: Diagnoser exposes required methods
- Given a `Diagnoser` instance
- Then it SHALL have methods `hypothesize()`, `instrument()`, and `targeted_fix()`

---

### Requirement: Hypothesis Generation
After verify failure, the Diagnoser SHALL generate 3–5 ordered root-cause hypotheses based on failure information (error output, verify.md feedback, git diff).

#### Scenario: Generate hypotheses from verify failure
- Given a verify failure with error detail "tests:\nAssertionError at line 42" and verify.md feedback
- When `hypothesize(failure_info)` is called
- Then the result SHALL contain between 3 and 5 `Hypothesis` objects
- And each hypothesis SHALL have `rank` (int, 1-based), `description` (str), `confidence` (float 0–1), and `evidence` (str)
- And hypotheses SHALL be sorted by confidence descending

#### Scenario: Hypotheses reference error clues
- Given failure detail containing "ImportError: No module named 'foo'"
- When `hypothesize(failure_info)` is called
- Then at least one hypothesis SHALL mention "import" or "module" or "dependency" in its description

---

### Requirement: Read-Only Instrumentation
The Diagnoser SHALL perform read-only probes (file reads, command runs) to test each hypothesis without modifying any project files.

#### Scenario: Instrument probes hypotheses without side effects
- Given 3 hypotheses about a test failure
- When `instrument(hypotheses, target_path, transport)` is called
- Then for each hypothesis, exactly one probe result SHALL be recorded in the hypothesis's `probe_result` field
- And no file in `target_path` SHALL be modified during instrumentation
- And at most 3 hypotheses SHALL be probed (to conserve turns)

#### Scenario: Probe collects diagnostic evidence
- Given a hypothesis "missing import" about file `src/main.py`
- When `instrument()` runs the probe for this hypothesis
- Then the probe SHALL read the relevant file or run a diagnostic command
- And the `probe_result` SHALL contain either `confirmed: bool` and `evidence: str`

---

### Requirement: Targeted Fix Generation
Based on instrumented probe results, the Diagnoser SHALL select the most likely root cause and produce a `FixPlan` for the IMPLEMENT phase.

#### Scenario: Generate fix plan from confirmed hypothesis
- Given 3 hypotheses where hypothesis #2 is confirmed by probe
- When `targeted_fix(hypotheses)` is called
- Then the result SHALL be a `FixPlan` with `root_cause` (str), `fix_description` (str), and `affected_files` (list[str])
- And the `root_cause` SHALL reference the confirmed hypothesis's description

#### Scenario: No confirmed hypothesis falls back to best guess
- Given 3 hypotheses where none are confirmed by probe
- When `targeted_fix(hypotheses)` is called
- Then the result SHALL still be a `FixPlan`
- And `root_cause` SHALL reference the highest-confidence hypothesis's description
- And `fix_description` SHALL note "unconfirmed hypothesis"

---

### Requirement: Diagnosis Report Recording
Each diagnosis run SHALL produce a `DiagnosisReport` that is persisted for metrics and future learning.

#### Scenario: Diagnosis report is generated
- Given a complete diagnose cycle (hypothesize → instrument → targeted_fix)
- When the cycle completes
- Then a `DiagnosisReport` SHALL be created with fields: `change_name`, `hypotheses` (list), `confirmed_hypothesis` (optional), `fix_plan` (FixPlan), `timestamp`
- And the report SHALL be writeable to the change directory

#### Scenario: Report written to change directory
- Given a `DiagnosisReport` for change "l4-diagnoser"
- When `report.save(change_dir, transport)` is called
- Then the file `{change_dir}/diagnosis.md` SHALL exist
- And it SHALL contain a markdown-formatted report

---

### Requirement: Orchestrator Integration
The orchestrator SHALL invoke the Diagnoser when the eval-fix loop fails (verify FAIL after all eval-fix attempts exhausted).

#### Scenario: Diagnose triggered on verify failure
- Given the verify phase returns FAIL
- And all eval-fix attempts are exhausted without success
- When the orchestrator processes the failure
- Then the Diagnoser SHALL be invoked before the final revert
- And the `DiagnosisReport` SHALL be saved to the change directory

#### Scenario: Diagnose not triggered on success
- Given the verify phase returns PASS
- When the orchestrator processes the result
- Then the Diagnoser SHALL NOT be invoked

---

### Requirement: Diagnoser Role in Agent Roles
The system SHALL register a `DIAGNOSER` role in `zsiga/agent/roles.py` for the structured diagnosis sub-agent.

#### Scenario: DIAGNOSER role exists
- Given the `zsiga.agent.roles` module
- When `get_role_config(Role.DIAGNOSER)` is called
- Then it SHALL return a `RoleConfig` with `name="diagnose"`, `read_only=True`, and `max_turns` between 3 and 8
- And `allowed_tools` SHALL include only read-only tools: `bash`, `read_file`, `search`, `list_files`, `ast_search`, `goto_definition`, `find_references`, `diagnostics`
