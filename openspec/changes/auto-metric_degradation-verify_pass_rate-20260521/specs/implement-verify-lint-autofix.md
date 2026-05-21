# Spec: Implement-Verify Lint Auto-Fix Chain

## ADDED Requirements

### Requirement: Automatic lint-fix before verify

Before the verify phase executes, the pipeline SHALL run an automatic lint-fix step (`ruff check --fix`) on all files that were modified during the implement phase. This ensures that common lint violations introduced during code generation do not propagate into the verify stage and cause false verify failures.

#### Scenario: E701 multiple-statements-on-one-line auto-fix

- **Given** the implement phase produced a Python file containing `E701 Multiple statements on one line (colon)`
- **And** the file is listed as a target file of the current change
- **When** the pipeline transitions from implement to verify
- **Then** the pipeline SHALL run `ruff check --fix` on all implement-modified files
- **And** the E701 violation SHALL be automatically corrected
- **And** the verify phase SHALL proceed on the fixed files

#### Scenario: Auto-fix introduces no new violations

- **Given** the automatic lint-fix step has corrected violations in implement-modified files
- **When** the verify phase runs `ruff check`
- **Then** all previously fixable violations SHALL be resolved
- **And** no new violations SHALL be introduced by the fix

### Requirement: Lint-fix safety gate

The automatic lint-fix step SHALL NOT apply fixes that change runtime behavior. If `ruff check --fix` cannot safely fix a violation, the pipeline SHALL fall back to reporting the violation as an implement-stage failure (not verify-stage), giving the implement phase a chance to correct it.

#### Scenario: Unsafe lint violation falls back to implement

- **Given** the implement phase produced code with a lint violation that `ruff --fix` cannot safely auto-correct
- **When** the pre-verify lint-fix step runs
- **Then** the pipeline SHALL report this as an implement-stage failure
- **And** the verify phase SHALL NOT be reached for this cycle attempt

### Requirement: Lint-fix logging

Every automatic lint-fix action SHALL be logged with sufficient detail for post-hoc analysis, including which files were fixed and which violations were corrected.

#### Scenario: Audit trail for auto-fix actions

- **Given** the pre-verify lint-fix step corrected violations in `src/module.py`
- **When** the daemon writes to `data/daemon.log`
- **Then** the log entry SHALL include the file path, the violation codes fixed (e.g., `E701`), and a timestamp
- **And** the log SHALL be queryable for auto-fix frequency analysis
