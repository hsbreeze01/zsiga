# Spec: SRE Orchestrator Integration

## ADDED Requirements

### Requirement: SRE Pipeline Registration in Orchestrator

The orchestrator SHALL register the SRE pipeline as a distinct pipeline alongside the existing code pipeline. When the intent router returns `"sre"`, the orchestrator MUST dispatch to the SRE pipeline. When the intent router returns `"code"`, the orchestrator MUST dispatch to the existing code pipeline.

#### Scenario: Orchestrator dispatches SRE intent to SRE pipeline

- **testable**: true
- **target**: zsiga/orchestrator.py::Orchestrator.dispatch
- **Given** the orchestrator is initialized with the intent router and both pipelines registered
- **When** a task with SRE intent (e.g., "检查磁盘空间") is dispatched
- **Then** the orchestrator SHALL invoke the SRE pipeline's `run` method, not the code pipeline

#### Scenario: Orchestrator dispatches code intent to code pipeline

- **testable**: true
- **target**: zsiga/orchestrator.py::Orchestrator.dispatch
- **Given** the orchestrator is initialized with the intent router and both pipelines registered
- **When** a task with code intent (e.g., "修复这个函数") is dispatched
- **Then** the orchestrator SHALL invoke the code pipeline, not the SRE pipeline

### Requirement: Pipeline Dispatch Mutual Exclusivity

The SRE pipeline and code pipeline SHALL be mutually exclusive. The orchestrator MUST NOT invoke both pipelines for the same task.

#### Scenario: Single dispatch — never both pipelines for one task

- **testable**: true
- **target**: zsiga/orchestrator.py::Orchestrator.dispatch
- **Given** the orchestrator has both pipelines registered and tracks which pipelines are invoked
- **When** any task is dispatched
- **Then** exactly one pipeline SHALL be invoked — either the SRE pipeline or the code pipeline, never both

### Requirement: Existing Code Pipeline Unchanged

The integration of SRE pipeline into the orchestrator SHALL NOT alter the behavior of the existing code pipeline. When code intent is detected, the dispatch path and pipeline execution MUST remain identical to the pre-SRE-integration behavior.

#### Scenario: Code pipeline execution path preserved

- **testable**: true
- **target**: zsiga/orchestrator.py::Orchestrator.dispatch
- **Given** a code-intent task
- **When** the orchestrator dispatches it
- **Then** the dispatch result SHALL be structurally identical to the result produced before SRE integration (same keys, same pipeline name)

### Requirement: SRE Pipeline Registration Does Not Break Initialization

The orchestrator SHALL initialize successfully with both pipelines registered. If the SRE pipeline module is missing or fails to import, the orchestrator SHOULD still initialize with only the code pipeline and log a warning.

#### Scenario: Orchestrator initializes with both pipelines

- **testable**: true
- **target**: zsiga/orchestrator.py::Orchestrator.__init__
- **Given** both the code pipeline and SRE pipeline modules are available
- **When** the orchestrator is initialized
- **Then** it SHALL have both pipelines registered and no error SHALL be raised
