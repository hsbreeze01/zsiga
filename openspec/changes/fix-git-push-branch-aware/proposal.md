# Proposal: Fix Git Push — Branch-Aware + Error Handling

## Summary

DELIVER 阶段的 git push 存在两个问题：
1. **旧版 branch 硬编码 `main`**：虽然新版已改为 feature → deploy branch 流程，但 `git_ops.push()` 和 `git_ops.pull()` 的默认参数仍是 `"main"`，容易被误用
2. **push 失败静默吞掉**：`git_ops.push()` 不检查 `exit_code`，不打印任何日志。push 失败后代码继续执行，DELIVER 显示成功但远端没收到代码

## Evidence

1. 当前 `git_ops.push` 实现：
   ```python
   def push(target_path, remote="origin", branch="main", ...):
       transport.run_shell(f"git push {remote} {branch}", cwd=target_path)
       # ❌ 不检查 exit_code，不打印日志
   ```
2. 所有 DELIVER 日志中从未出现 "Merged ... and pushed" 消息
3. 49 上 zsiga 曾 `ahead 72` 未推送；47 上 data-agent `ahead 6`、factory `ahead 13`

## Root Cause

`git_ops` 所有函数（push、pull、checkout、merge 等）都不检查 `run_shell` 的 `exit_code`，失败静默继续。

## Requirements

### 1. `git_ops.py` — 所有写操作检查 exit_code 并日志
- `push()`：检查 exit_code，非零时 `print(f"  ❌ git push failed: {stderr}")` 并 raise 或返回 False
- `pull()`、`merge_branch()`、`checkout()`、`delete_branch()`：同理
- `commit()`、`add_all()`：同理
- 所有函数加上日志输出：`print(f"  git push {remote} {branch} ...")` 在执行前，`print(f"  ✅ pushed")` 在成功后

### 2. `git_ops.push()` — 移除 `branch="main"` 默认值
- 改为 `branch: str = None`，如果未传则用 `current_branch()` 获取当前分支
- **绝对不能硬编码任何分支名**，必须动态获取当前实际分支

### 3. `orchestrator.py` DELIVER 阶段 — 加错误处理
- push/merge 失败时记录日志，不静默继续
- 如果 push 失败，DELIVER outcome 应该是 FAIL 而非 SUCCESS
- 保持 feature branch → merge → deploy branch 的流程不变

### 4. 远端项目（47 上 SSH transport）的 push 也要生效
- 确保 SSH transport 的 `run_shell` 返回的 exit_code 被正确检查
- SSH key 和 remote 配置可能不同（如 `github-agent` vs `origin`），不要假设 remote 名是 `origin`

## Constraints
- Scope: project=zsiga
- 关键文件：`zsiga/git_ops.py`、`zsiga/pipeline/orchestrator.py`
- 不要改动 transport 层的核心逻辑
- 运行 pytest 确认不破坏现有测试
