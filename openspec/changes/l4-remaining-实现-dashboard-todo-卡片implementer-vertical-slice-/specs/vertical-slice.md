# Implementer Vertical Slice

## MODIFIED Requirements

### REQ-VS-01: Implementer system prompt SHALL enforce vertical slice execution

The implementer's system prompt (`IMPLEMENTER_SYSTEM` in `pipeline/implementer.py`)
SHALL instruct the agent to execute tasks one at a time in a strict
read → edit 1-2 files → verify → commit → next cycle.

#### Scenario: Multi-task change execution

- Given a `tasks.md` with 4 unchecked tasks (1.1, 1.2, 1.3, 2.1)
- When the implementer agent begins execution
- Then the agent SHALL:
  1. Pick the first unchecked task only
  2. Read relevant code (≤ 3 file reads)
  3. Edit at most 2 files for this single task
  4. Run lint on changed files only
  5. Run pytest on related test files only
  6. Check-mark the task as `- [x]`
  7. Commit if all tasks in the current group are done
  8. Move to the next task
- And the agent SHALL NOT attempt to edit 3+ files in a single cycle

#### Scenario: Single task requires more than 2 files

- Given a task legitimately requires changes to 3 files (e.g., model + service + route)
- When the agent executes this task
- Then the agent MAY edit up to 3 files but MUST run lint/test after every 2 files
- And the agent MUST document why 3 files are needed in a brief comment

### REQ-VS-02: Implementer SHALL run incremental lint after each task

#### Scenario: Lint isolation per task

- Given task 1.1 modifies `zsiga/pipeline/foo.py`
- When the agent finishes task 1.1
- Then it SHALL run `ruff check` only on `zsiga/pipeline/foo.py`
- And it SHALL NOT run project-wide lint until all tasks are complete
