# Design: Proposal → GitHub Issue → Commit Linkage

## Architecture Decision

This change introduces a **non-blocking GitHub Issue integration** into the DELIVER phase. The key design principle is **graceful degradation**: GitHub API failures MUST NEVER block code delivery.

The integration uses the **GitHub REST API via curl** (no `gh` CLI dependency), consistent with the project's approach of using subprocess calls through the existing `Transport` layer. However, the GitHub API calls themselves run **locally** (where zsiga runs), not on the remote target — because they are HTTP API calls, not git operations on the target filesystem.

## Data Flow

```
DELIVER phase (orchestrator._run_phases):
  │
  ├─ 1. Read proposal.md content from change_dir (via transport)
  │
  ├─ 2. IF github.issue_integration is enabled:
  │     ├─ 2a. Extract owner/repo from git remote URL (via transport)
  │     ├─ 2b. Call create_issue() locally (curl to GitHub API)
  │     │     ├─ Success → get issue_number
  │     │     └─ Failure → log warning, issue_number = None
  │     └─ 2c. Build commit message with/without (closes #N)
  │     ELSE: build commit message without issue reference
  │
  ├─ 3. git add + git commit (via transport, message includes #N if available)
  ├─ 4. git tag (unchanged)
  ├─ 5. git push (unchanged)
  └─ 6. archive_change (unchanged)
```

## New Module: `zsiga/pipeline/github_issue.py`

A thin module with two public functions:

- **`create_issue(owner_repo, title, body, token)`** → `int | None`
  - Runs `curl -s -X POST` locally via `subprocess.run`
  - Returns `issue_number` on success, `None` on any failure
  - All errors caught internally, logged as warnings

- **`extract_github_repo(target_path, transport)`** → `str | None`
  - Runs `git remote get-url origin` on the target via transport
  - Parses SSH and HTTPS URL formats using regex
  - Returns `"owner/repo"` or `None`

Both functions are pure (no side effects beyond subprocess calls) and independently testable.

## Config Changes

### `zsiga/config.py`

Add a `GithubConfig` class:

```python
class GithubConfig:
    def __init__(self, token: str = "", owner: str = "", issue_integration: bool = False):
        self.token = token        # resolved from ${GITHUB_TOKEN}
        self.owner = owner        # default owner (optional, auto-detected per target)
        self.issue_integration = issue_integration
```

Add `github` field to `ZsigaConfig` and parse it in `load_config()`.

### `zsiga.yaml`

Add optional `github:` section:

```yaml
github:
  token: ${GITHUB_TOKEN}
  issue_integration: true
```

The section is optional. If absent, `GithubConfig` defaults to `issue_integration=False`.

## Orchestrator Changes

In `_run_phases()`, the DELIVER phase section is modified:

**Before:**
```python
git_ops.commit(target_path, f"feat({project_name}): {change_name}", transport=transport)
```

**After:**
```python
issue_number = None
if self.config.github and self.config.github.issue_integration:
    issue_number = _try_create_issue(
        self.config.github, target_path, transport,
        change_name, proposal_text,
    )
msg = f"feat({project_name}): {change_name}"
if issue_number:
    msg += f" (closes #{issue_number})"
git_ops.commit(target_path, msg, transport=transport)
```

A helper `_try_create_issue()` wraps the extraction + creation + error handling.

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `zsiga/pipeline/github_issue.py` | **NEW** | `create_issue()`, `extract_github_repo()` |
| `zsiga/config.py` | MODIFY | Add `GithubConfig` class, parse `github:` section in `load_config()` |
| `zsiga/pipeline/orchestrator.py` | MODIFY | DELIVER phase: create Issue, build commit message with `closes #N` |
| `zsiga.yaml` | MODIFY | Add `github:` section (opt-in) |

## Error Handling Strategy

| Error Condition | Behavior |
|----------------|----------|
| `github` section missing in config | Skip Issue creation entirely |
| `issue_integration: false` | Skip Issue creation entirely |
| `GITHUB_TOKEN` env var not set / empty | Log warning, skip |
| `git remote get-url origin` fails | Log warning, skip |
| Remote URL is not a GitHub URL | Log warning, skip |
| curl returns non-200 HTTP status | Log warning with status + body, skip |
| curl times out (10s) | Log warning, skip |
| JSON parse error on response | Log warning, skip |

In ALL failure cases, the DELIVER phase continues with a plain commit message.

## Verification Strategy

1. Unit tests for `create_issue()` — mock `subprocess.run` to simulate success/failure
2. Unit tests for `extract_github_repo()` — test SSH, HTTPS, alias, and invalid URLs
3. Unit tests for `GithubConfig` parsing — test with/without `github:` section
4. Integration test: verify DELIVER phase builds correct commit message with/without Issue
5. `ruff check zsiga/` — zero errors
6. `pytest tests/` — all pass
