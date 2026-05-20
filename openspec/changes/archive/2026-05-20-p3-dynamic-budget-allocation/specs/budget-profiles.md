# Spec: Budget Profiles by Task Type

## ADDED Requirements

### Requirement: Budget Profile Definition

The system SHALL support named budget profiles, each specifying a `total_budget` token limit.
The default profiles SHALL be:

| Profile        | total_budget | Rationale                                    |
|----------------|-------------|----------------------------------------------|
| `fix`          | 300 000     | Targeted fix is small scope                  |
| `implementation` | 600 000  | Default scope for new feature work           |
| `cross_project` | 200 000    | Sub-task on a non-originating project        |
| `self_modify`  | 800 000     | Modifying zsiga itself needs extra room      |

Operators MAY override profile values or add new profiles via the
`pipeline.budget_profiles` section of `zsiga.yaml`.

#### Scenario: default profile values used when config absent

- **Given** the `pipeline.budget_profiles` section is missing or empty in `zsiga.yaml`
- **When** the system loads configuration
- **Then** the four default profiles (`fix`, `implementation`, `cross_project`, `self_modify`) SHALL be available with the default token limits listed above

#### Scenario: custom profile overrides default

- **Given** `zsiga.yaml` contains:
  ```yaml
  pipeline:
    budget_profiles:
      fix:
        total_budget: 150000
  ```
- **When** the system loads configuration
- **Then** the `fix` profile SHALL have `total_budget = 150000`
- **And** the other default profiles SHALL retain their default values

#### Scenario: new profile added via config

- **Given** `zsiga.yaml` contains:
  ```yaml
  pipeline:
    budget_profiles:
      research:
        total_budget: 100000
  ```
- **When** the system loads configuration
- **Then** a `research` profile with `total_budget = 100000` SHALL be available alongside the defaults

---

### Requirement: Budget Profile Selection

The system SHALL select a budget profile based on the resolved intent type,
the originating project name, and whether the change is a cross-project sub-task.

Selection logic (evaluated in order):

1. If the change is a cross-project sub-task → `cross_project` profile.
2. If the target project equals `"zsiga"` → `self_modify` profile.
3. If the intent type is `FIX` → `fix` profile.
4. Otherwise → `implementation` profile.

The selected profile name and `total_budget` SHALL be logged at the start of
`_process_change`.

#### Scenario: cross-project sub-task selects cross_project profile

- **Given** a change whose originating project differs from the target project
- **When** the system selects a budget profile
- **Then** the `cross_project` profile (default 200 000) SHALL be selected

#### Scenario: zsiga self-modification selects self_modify profile

- **Given** a change targeting the `"zsiga"` project
- **And** the change is not a cross-project sub-task
- **When** the system selects a budget profile
- **Then** the `self_modify` profile (default 800 000) SHALL be selected

#### Scenario: fix intent selects fix profile

- **Given** a change with `IntentType.FIX`
- **And** the target project is not `"zsiga"`
- **When** the system selects a budget profile
- **Then** the `fix` profile (default 300 000) SHALL be selected

#### Scenario: implementation intent selects implementation profile

- **Given** a change with `IntentType.IMPLEMENTATION`
- **And** the target project is not `"zsiga"`
- **When** the system selects a budget profile
- **Then** the `implementation` profile (default 600 000) SHALL be selected

---

### Requirement: Dynamic Budget Application

When a budget profile is selected, the system SHALL create a `TokenBudget`
instance with the profile's `total_budget` before the agent loop begins
execution for that change.

The `AgentLoop.set_phase()` method already resets `_used` and `_extended`;
the orchestrator SHALL additionally update `budget.total_budget` to the
selected profile's value before the first phase starts.

#### Scenario: budget applied for fix intent

- **Given** a change resolved to the `fix` profile (total_budget = 300 000)
- **When** the orchestrator begins the IMPLEMENT phase
- **Then** the `AgentLoop.budget.total_budget` SHALL equal 300 000

#### Scenario: budget applied for self_modify

- **Given** a change targeting the `zsiga` project with `self_modify` profile (total_budget = 800 000)
- **When** the orchestrator begins the ENRICH phase
- **Then** the `AgentLoop.budget.total_budget` SHALL equal 800 000

---

### Requirement: Per-Profile Budget Statistics

The `compute_stats()` function SHALL include a `budget_profile_stats` key
in its output. Each change record SHALL store the `budget_profile` name used.

`budget_profile_stats` SHALL be a dict mapping profile names to:
- `count`: number of changes that used this profile
- `avg_tokens`: average total tokens (prompt + completion) consumed per change

#### Scenario: stats include per-profile breakdown

- **Given** the change history contains 3 changes with profile `fix` and 2 changes with profile `implementation`
- **When** `compute_stats()` is called
- **Then** `stats["budget_profile_stats"]["fix"]["count"]` SHALL equal 3
- **And** `stats["budget_profile_stats"]["implementation"]["count"]` SHALL equal 2

#### Scenario: budget_profile recorded in ChangeRecord

- **Given** a change processed with profile `cross_project`
- **When** the change is recorded to metrics
- **Then** the change dict SHALL contain `"budget_profile": "cross_project"`
