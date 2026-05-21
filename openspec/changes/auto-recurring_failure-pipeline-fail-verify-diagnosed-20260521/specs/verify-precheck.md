# Spec: Verify Pre-Validation Check

## ADDED Requirements

### Requirement: Verify Phase SHALL Run Import and Lint Pre-Checks

Before the LLM-based verifier agent runs, the orchestrator SHALL execute lightweight mechanical pre-checks (import validation and lint) against changed files. If a pre-check fails with a known error pattern, the orchestrator MUST skip the LLM verify call and proceed directly to the eval-fix loop or diagnosis, saving LLM turns and avoiding the "Unconfirmed hypothesis" diagnosis path.

#### Scenario: Import error detected during pre-check

- **Given** the IMPLEMENT phase has completed and changed files are known
- **And** a Python file in the changed set contains `import nonexistent_module`
- **When** the verify pre-check runs
- **Then** the pre-check SHALL detect the import error
- **And** the orchestrator SHALL record the error as a structured pre-check failure with:
  - the specific file path
  - the module name that could not be imported
  - the error type (`import_error`)
- **And** the orchestrator SHALL skip the LLM-based verify and enter the eval-fix loop directly with this specific error message

#### Scenario: Lint error detected during pre-check

- **Given** the IMPLEMENT phase has completed and changed files are known
- **And** a Python file in the changed set has a lint violation (e.g., `E701`)
- **When** the verify pre-check runs
- **Then** the pre-check SHALL detect the lint error
- **And** the orchestrator SHALL record the error as a structured pre-check failure with:
  - the specific file path
  - the lint rule code and message
  - the error type (`lint_error`)
- **And** the orchestrator SHALL skip the LLM-based verify and enter the eval-fix loop directly

#### Scenario: Pre-check passes — normal verify proceeds

- **Given** the IMPLEMENT phase has completed and changed files are known
- **And** all changed Python files pass import validation and lint
- **When** the verify pre-check runs
- **Then** the pre-check SHALL return a pass result
- **And** the orchestrator SHALL proceed with the normal LLM-based verify phase unchanged

### Requirement: Pre-Check MUST Be Lightweight

The pre-check SHALL complete within 30 seconds for any change. It MUST only inspect changed files (those in the git diff since `pre_sha`), not the entire project.

#### Scenario: Pre-check scoped to changed files only

- **Given** `pre_sha` is the git commit before IMPLEMENT
- **And** only 3 files were changed
- **When** the pre-check runs
- **Then** it SHALL run import checks and lint ONLY on those 3 files
- **And** it SHALL NOT scan unrelated files

### Requirement: Pre-Check Results SHALL Be Passed to Diagnosis

If the eval-fix loop also fails after a pre-check failure, the structured pre-check error information SHALL be available to the diagnoser so it can produce a specific root cause instead of the generic "Unconfirmed hypothesis".

#### Scenario: Pre-check failure flows into diagnosis

- **Given** a pre-check detected an import error in `src/foo.py` for module `bar`
- **And** the eval-fix loop failed to resolve the error
- **When** `_run_diagnosis()` is called
- **Then** the `failure_info` dict SHALL include the pre-check error details (file, module, error type)
- **And** the diagnoser SHALL produce a `FixPlan` referencing the specific import error (not "Unconfirmed hypothesis")
