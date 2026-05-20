# Proposal: Proposal → GitHub Issue → Commit 关联

## Summary

在 DELIVER 阶段集成 GitHub Issue 创建：每个 proposal 被处理时自动创建对应 GitHub Issue，commit message 关联 `#issue_id`，push 后 Issue 自动关闭。

## Motivation (铁律)

用户要求：
1. 所有代码部署必须走 git，对应好分支（已实施 git-based-deployment）
2. 工程管理好习惯：proposal 与 issue 关联，commit 同时关联 issue id
3. 目前所有仓库 0 个 issues，无法追踪变更历史

## Design

### 流程

```
ENRICH → IMPLEMENT → VERIFY → DELIVER:
                                  ↓
                          1. 读取 proposal.md 内容
                          2. GitHub API: POST /repos/{owner}/{repo}/issues
                             title = proposal 标题
                             body = proposal 全文
                             labels = ["zsiga"]
                          3. 获取 issue_number
                          4. git commit -m "feat: {change_name} (closes #{issue_number})"
                          5. git tag zsiga-{change_name}
                          6. git push
                          7. GitHub 自动关闭 Issue（closes #N 语法）
                          8. archive change
```

### GitHub API 调用

使用 curl + GitHub REST API（不依赖 gh CLI）：

```bash
curl -s -X POST \
  -H "Authorization: token {GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/{owner}/{repo}/issues \
  -d '{"title":"...","body":"...","labels":["zsiga"]}'
```

返回 `{"number": 42, "html_url": "..."}`

### 配置

在 `zsiga.yaml` 中增加：

```yaml
github:
  token: ${GITHUB_TOKEN}    # 从环境变量读取
  owner: hsbreeze01
  issue_integration: true   # 开关
```

### 仓库映射

从 target 的 git remote URL 自动解析 `{owner}/{repo}`：

```python
def _extract_github_repo(target_path, transport):
    r = transport.run_shell("git remote get-url origin", cwd=target_path)
    url = r["stdout"].strip()
    # git@github.com:hsbreeze01/repo.git → hsbreeze01/repo
    # git@github-alias:hsbreeze01/repo.git → hsbreeze01/repo
    match = re.search(r':([^/]+/[^.]+)(?:\.git)?$', url)
    return match.group(1) if match else None
```

注意：47 上 SSH config 使用了 alias（github-agent, github-factory 等），但 URL 中 owner/repo 部分不变。

### Commit Message 格式变更

当前：`feat({project_name}): {change_name}`
改为：`feat({project_name}): {change_name} (closes #{issue_number})`

REVERT 时：`revert: {change_name} (ref #{issue_number})`

### 失败处理

- GitHub API 不可用 → 跳过 issue 创建，commit 仍继续（降级模式）
- Issue 创建失败 → 记录 warning，commit 不含 issue id
- 不可因为 issue 创建失败而阻断 DELIVER

## Files Changed

| File | Change |
|------|--------|
| `config.py` | Add GithubConfig dataclass (token, owner, enabled) |
| `zsiga.yaml` | Add `github:` section |
| `pipeline/github_issue.py` | NEW: create_issue(), close_issue() via curl |
| `pipeline/orchestrator.py` | DELIVER phase: create issue before commit, include #N in message |
| `git_ops.py` | No change (message format handled in orchestrator) |

## Expected Behavior

1. 每个 proposal 处理成功后自动创建 GitHub Issue
2. Commit message 包含 `closes #N`
3. Push 后 Issue 自动关闭
4. 降级模式：GitHub API 不可用时不阻断
5. 所有 6 个仓库的 Issue 面板开始有记录

## Constraints

- Scope: project=zsiga
- GITHUB_TOKEN 从环境变量读取，不硬编码
- 降级模式是必须的（GitHub API 可能超时/限流）
- All changes must pass `pytest` and `ruff`
- Reference: `/home/zsiga/CMDB.md`
