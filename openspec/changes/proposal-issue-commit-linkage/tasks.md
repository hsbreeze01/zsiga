# Tasks: Proposal → GitHub Issue → Commit Linkage

## 1. Configuration Layer

- [ ] **1.1** Add `GithubConfig` class to `zsiga/config.py` and parse `github:` section in `load_config()`
  - Add `GithubConfig(token, owner, issue_integration)` class
  - Wire `GithubConfig` into `ZsigaConfig.__init__()` as optional `github` param
  - Parse `raw.get("github", {})` in `load_config()` with `_resolve_env_vars` for token
  - Default `issue_integration=False` when section absent
  - Files: `zsiga/config.py`, `zsiga.yaml`

## 2. GitHub Issue Module

- [ ] **2.1** Create `zsiga/pipeline/github_issue.py` with `create_issue()` and `extract_github_repo()`
  - `extract_github_repo(target_path, transport)` → runs `git remote get-url origin` via transport, parses SSH/HTTPS URLs, returns `"owner/repo"` or `None`
  - `create_issue(owner_repo, title, body, token)` → runs `curl -s -X POST` locally via `subprocess.run`, returns `issue_number` (int) or `None` on any failure
  - All errors caught and logged as `print()` warnings, never raise
  - 10-second curl timeout
  - File: `zsiga/pipeline/github_issue.py` (NEW)

## 3. Orchestrator DELIVER Phase Integration

- [ ] **3.1** Modify DELIVER phase in `zsiga/pipeline/orchestrator.py` to create GitHub Issue and include `closes #N` in commit message
  - Read `proposal_text` (already available in `_run_phases` scope) for Issue body
  - Before commit: if `config.github.issue_integration`, call `extract_github_repo()` then `create_issue()`
  - Build commit message: `feat({project_name}): {change_name} (closes #{N})` or plain without `(closes #N)`
  - On any failure: log warning, proceed with plain commit message
  - File: `zsiga/pipeline/orchestrator.py`

## 4. Tests

- [ ] **4.1** Add unit tests for `github_issue.py` and config parsing
  - Test `extract_github_repo()` with SSH URL, HTTPS URL, aliased SSH host, invalid URL, failed remote
  - Test `create_issue()` with mocked `subprocess.run`: success returns int, HTTP error returns None, timeout returns None, JSON parse error returns None
  - Test `GithubConfig` parsing: present+enabled, absent defaults to disabled, token env var resolution
  - Test orchestrator DELIVER message format: with issue_number and without
  - File: `tests/test_github_issue.py` (NEW)
