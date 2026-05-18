# Delta Spec: Task Decomposition in Orchestrator

## ADDED Requirements

### REQ-TD-01: Multi-project Decomposition Support

The orchestrator SHALL support decomposing high-level instructions into multi-project subtask lists.

#### Scenario: Cross-project instruction triggers decomposition

- **Given** a proposal whose content references multiple configured target projects
- **When** the orchestrator processes the change
- **Then** it SHALL call `task_decomposer.decompose()` with the proposal content and available project names
- **And** it SHALL return a `Decomposition` containing subtasks grouped by project

### REQ-TD-02: Parallel Dispatch of Decomposed Tasks

The orchestrator SHALL dispatch subtasks within the same parallel group sequentially (to conserve agent resources) but process each project independently.

#### Scenario: Multiple projects in parallel group

- **Given** a `Decomposition` with 3 subtasks in a single parallel group
- **When** the orchestrator dispatches the group
- **Then** it SHALL process each subtask by calling `_process_change()` with a synthetic proposal for each project
- **And** each subtask result SHALL be recorded

### REQ-TD-03: Result Aggregation

The orchestrator SHALL aggregate results from all dispatched subtasks into a unified summary report.

#### Scenario: Aggregation after parallel dispatch

- **Given** all subtasks in a decomposition have completed (pass or fail)
- **When** the orchestrator finishes dispatching
- **Then** it SHALL call `task_decomposer.aggregate_results()` to produce a summary
- **And** the summary SHALL be printed to stdout
- **And** the summary SHALL be recorded as a lesson

### REQ-TD-04: Single-project Proposals Bypass Decomposition

The orchestrator SHALL NOT invoke task decomposition for single-project proposals, preserving existing behavior.

#### Scenario: Single-project proposal goes through standard pipeline

- **Given** a proposal that targets exactly one project
- **When** the orchestrator processes the change
- **Then** it SHALL skip the decomposition step
- **And** proceed with the standard ENRICH → IMPLEMENT → VERIFY → DELIVER phases
