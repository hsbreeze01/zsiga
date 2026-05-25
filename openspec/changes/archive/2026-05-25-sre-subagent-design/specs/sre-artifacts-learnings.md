# Spec: SRE Artifacts and Learnings

## ADDED Requirements

### Requirement: Execution Report Generation

The SRE pipeline SHALL produce an `execution_report.md` file in the change directory upon completion. The report MUST contain:
1. A header with the task description and timestamp
2. A list of executed steps with their results (success/failure)
3. A verification summary
4. An overall status (success/failure)

#### Scenario: execution_report.md is generated after pipeline run

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._report
- **Given** the SRE pipeline has completed all phases (DIAGNOSE through VERIFY)
- **When** the REPORT phase runs
- **Then** an `execution_report.md` file SHALL exist in the output directory

#### Scenario: execution_report.md contains required sections

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._report
- **Given** the REPORT phase has completed
- **When** the `execution_report.md` content is read
- **Then** it SHALL contain a header line starting with `"# "`, at least one step result, and a status indicator (success or failure)

#### Scenario: execution_report.md includes timestamp

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._report
- **Given** the REPORT phase has completed
- **When** the `execution_report.md` content is read
- **Then** it SHALL contain an ISO-format timestamp (pattern: `YYYY-MM-DD`)

### Requirement: Learnings Append

The SRE pipeline SHALL append operational experience records to `learnings.jsonl`. Each record MUST be a valid JSON line with at minimum:
- `"category": "sre"`
- `"task"`: the original task description
- `"lessons"`: list of lessons learned
- `"timestamp"`: ISO-format timestamp

#### Scenario: learnings.jsonl receives SRE category entry

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._report
- **Given** the SRE pipeline has completed a task
- **When** the REPORT phase writes learnings
- **Then** a new line SHALL be appended to `learnings.jsonl` that is valid JSON with `"category": "sre"`

#### Scenario: Learnings entry has required fields

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._report
- **Given** a learnings entry is written
- **When** the JSON line is parsed
- **Then** it SHALL contain keys `"category"`, `"task"`, `"lessons"`, and `"timestamp"`

#### Scenario: Learnings append is additive

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline._report
- **Given** an existing `learnings.jsonl` with N lines
- **When** the REPORT phase appends a new learning entry
- **Then** the file SHALL have N+1 lines, and all previous lines SHALL be unchanged

### Requirement: No Git Commit From SRE Pipeline

The SRE pipeline MUST NOT create any git commits. The REPORT phase and all other phases SHALL NOT invoke `git add`, `git commit`, or `git push`.

#### Scenario: No git commit in pipeline command history

- **testable**: true
- **target**: zsiga/pipeline/sre_pipeline.py::SREPipeline.run
- **Given** a full SRE pipeline run (all 5 phases)
- **When** all commands issued during the run are collected
- **Then** none SHALL match the pattern `git commit` or `git add`
