# Delta Spec: clarify.md Output Contract

## ADDED Requirements

### REQ-CO-001: clarify.md SHALL contain four mandatory sections

The `clarify.md` file SHALL contain exactly four top-level sections in this order:

1. **需求拆解** (Requirement Decomposition) — Original requirement summary and decomposed subtasks
2. **边界** (Boundary) — IN scope, OUT of scope, and external dependencies
3. **目标** (Goal) — Success criteria and acceptance methods
4. **约束** (Constraint) — Protected files, deploy branch, known risks, token estimation

Each section SHALL use the `##` heading level. The file SHALL be valid Markdown.

#### Scenario: clarify.md has all four sections
- **Given** the CLARIFY phase generates `clarify.md`
- **When** the file is read and parsed
- **Then** it SHALL contain exactly the headings `## 需求拆解`, `## 边界`, `## 目标`, `## 约束`
- **And** each section SHALL contain at least one non-empty line of content

#### Scenario: Missing section triggers retry
- **Given** the CLARIFY phase generates `clarify.md` without the `## 边界` section
- **When** the enricher validates the output
- **Then** the system SHALL log a warning and retry the generation

### REQ-CO-002: 需求拆解 section SHALL decompose into independently verifiable subtasks

The `## 需求拆解` section SHALL contain:
- An `原始需求` subsection quoting the core requirement from `proposal.md`
- A numbered list of subtasks, each independently verifiable
- Each subtask SHALL include an estimated complexity (`低`/`中`/`高`)
- Each subtask SHALL include an estimated token consumption (or "无历史参考" if no data)

#### Scenario: Subtask with complexity and token estimate
- **Given** the CLARIFY phase generates `clarify.md`
- **When** a subtask entry is read
- **Then** it SHALL contain text like `1. <description> (预估复杂度：中, 预估 token：~5000)`
- **Or** it SHALL contain `1. <description> (预估复杂度：低, 预估 token：无历史参考)`

#### Scenario: Subtasks map to current tasks.md format for IMPLEMENT consumption
- **Given** the CLARIFY phase produces `clarify.md` with subtasks
- **When** the IMPLEMENT phase reads `clarify.md`
- **Then** the subtask list SHALL be parseable as a checklist with `- [ ]` markers
- **And** each subtask SHALL be completable independently (bounded file scope)

### REQ-CO-003: 边界 section SHALL define explicit IN/OUT scope

The `## 边界` section SHALL contain three mandatory subsections:
- `IN scope` — bulleted list of features, files, or behaviors explicitly in scope
- `OUT of scope` — bulleted list of what is explicitly excluded
- `依赖的外部条件` — bulleted list of external dependencies (databases, APIs, manual steps)

#### Scenario: IN scope lists specific targets
- **Given** the CLARIFY phase generates `clarify.md`
- **When** the `## 边界` section is read
- **Then** `IN scope` SHALL list at least one specific file, module, or feature
- **And** `OUT of scope` SHALL list at least one exclusion or state "无"

#### Scenario: IMPLEMENT respects OUT of scope
- **Given** `clarify.md` lists a file or feature in `OUT of scope`
- **When** the IMPLEMENT phase processes tasks
- **Then** the implementer SHALL NOT modify any file or feature listed in `OUT of scope`

### REQ-CO-004: 目标 section SHALL define verifiable success criteria

The `## 目标` section SHALL contain:
- `成功标准` — a numbered list of conditions that MUST all be true for the change to be considered successful
- `验收方式` — how each criterion is verified (pytest, manual, service health check, etc.)

#### Scenario: VERIFY phase checks success criteria
- **Given** `clarify.md` defines success criteria under `## 目标`
- **When** the VERIFY phase evaluates the implementation
- **Then** the verifier SHALL check each success criterion against the actual implementation
- **And** the verdict SHALL be PASS only if ALL criteria are met

#### Scenario: Success criteria reference measurable outcomes
- **Given** the CLARIFY phase generates success criteria
- **When** a criterion is written
- **Then** it SHALL be a falsifiable statement (e.g., "pytest passes", "new function returns X for input Y")
- **And** it SHALL NOT be vague (e.g., "code quality improves")

### REQ-CO-005: 约束 section SHALL include protected files, deploy branch, and risks

The `## 约束` section SHALL contain:
- `不能修改的文件` — list of files that MUST NOT be modified
- `项目部署分支` — the deploy branch name (read from target config)
- `已知风险` — risks derived from historical lessons (pattern_miner data)
- `预估 token 消耗` — total estimated token consumption for all subtasks

#### Scenario: Deploy branch is read from config
- **Given** the target config has `deploy_branch: "main"`
- **When** the CLARIFY phase generates `clarify.md`
- **Then** `## 约束 > 项目部署分支` SHALL be `main`

#### Scenario: Known risks reference pattern_miner data
- **Given** the pattern miner has recorded `pipeline.fail.implement` with severity "high"
- **When** the CLARIFY phase generates `clarify.md`
- **Then** `## 约束 > 已知风险` SHALL reference relevant failure patterns

#### Scenario: Token estimation uses historical data
- **Given** `zsiga.db` contains historical token consumption for similar changes
- **When** the CLARIFY phase estimates token consumption
- **Then** the estimate SHALL be based on the average of historical values for similar changes
- **Or** if no history exists, it SHALL state "无历史参考"
