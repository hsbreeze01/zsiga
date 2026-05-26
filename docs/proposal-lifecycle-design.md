# Proposal Lifecycle Design

## 1. 现状问题

### 1.1 git clean -fd 摧毁 proposal 文件

**位置**: `zsiga/git_ops.py:23` — `reset_hard()` 内部执行 `git clean -fd`

**影响**: Pipeline 处理完 proposal 后，cleanup 调用 `reset_hard()` 清除工作区。`git clean -fd` 删除所有 untracked 文件，包括：
- `openspec/changes/{name}/proposal.md`（用户手动创建的）
- `openspec/changes/{name}/steward-review.md`（steward gate 生成）
- `openspec/changes/{name}/clarify.md`、`specs/`（pipeline 中间产物）

但目录可能残留（因为有 `.phase_state` 等 hidden file），导致 scanner 每次发现空目录打 warning。

**后果**: Proposal 被处理后，如果 outcome=skipped，目录残留但 proposal.md 已被删除，scanner 反复 warning 但无法处理。

### 1.2 Skipped proposal 无限重试

**位置**: `zsiga/pipeline/orchestrator.py:143-174` — `run_cycle()` 过滤逻辑

**现状**:
- `consecutive_fails >= 3` → paused（仅统计 fail/reverted）
- `last_outcome == "success"` → completed → archive
- **skipped 不计入 consecutive_fails**，也没有 skip 次数上限

**DB 证据**:
| Proposal | Skip 次数 | 最终结果 |
|---|---|---|
| auto-metric_degradation | 1 | 永远 skip（目录已不存在） |
| auto-recurring_failure | 1 | 永远 skip（目录已不存在） |
| fix-self-assessment | 1 | 永远 skip（目录已不存在） |
| optimize-pipeline | 2 | 永远 skip（proposal.md 被删除） |
| sre-subagent | 1 | 永远 skip（目录已不存在） |

5 个 proposal 被 skip 后**永远不会再成功**。但 scanner 在有 proposal.md 的情况下会无限重试。

### 1.3 archive_change 仅在 success 时调用

**位置**: `orchestrator.py:166-172`

只在 `last_outcome == "success"` 时 archive。Skipped/failed 的 proposal 永远不会被归档，也不会被清理。

### 1.4 Scanner 对空目录只 warning 不处理

**位置**: `scanner.py:60-64`

发现目录无 proposal.md 时打印 warning 然后 `continue`，不清理也不记录。

---

## 2. 生命周期定义

### 2.1 状态机

```
                    ┌──────────────────────────────────────┐
                    │            DISCOVERED                │
                    │  (scanner 发现 proposal.md)           │
                    └───────┬──────────┬───────────────────┘
                            │          │
                    [steward │          │ [steward REJECT
                     ACCEPT] │          │  或 exception]
                            │          │
                            ▼          ▼
                    ┌───────────┐  ┌──────────┐
                    │ PROCESSING │  │ SKIPPED  │
                    │ (pipeline  │  │          │
                    │  执行中)   │  └────┬─────┘
                    └──┬─────┬──┘       │
                       │     │          │ [skip_count >= 2
               [success]    │ [fail/   │  或 steward REJECT × 2]
                            │ revert]  │
                       │    │          ▼
                       ▼    ▼    ┌──────────┐
               ┌──────────┐     │ ABANDONED │ ──→ 归档到 archive/skipped/
               │ SUCCESS  │     └──────────┘
               └────┬─────┘
                    │
                    ▼
              归档到 archive/
```

### 2.2 状态定义

| 状态 | 含义 | proposal.md | 目录 |
|---|---|---|---|
| **DISCOVERED** | Scanner 找到 proposal.md | 存在 | 存在于 openspec/changes/ |
| **PROCESSING** | Pipeline 正在执行 | 存在 | 存在，中间产物在写入 |
| **SUCCESS** | Pipeline 全部 phase 通过 | 不重要 | 移动到 archive/ |
| **SKIPPED** | Steward REJECT/PUSHBACK 或 pipeline 异常 | 应存在 | 应存在于 openspec/changes/ |
| **ABANDONED** | 连续 skip 超限，放弃重试 | 不重要 | 移动到 archive/skipped/ |

---

## 3. 各阶段产物定义

### 3.1 产出文件

| Phase | 写入文件 | Git tracked? |
|---|---|---|
| Steward Gate | `steward-review.md`, `steward-review-{ts}.md` | 否 |
| CLARIFY | `clarify.md` | 否 |
| ENRICH | `specs/*.md`, `design.md`, `tasks.md` | 否 |
| Design Gate | `judge-feedback.md` | 否 |
| IMPLEMENT | 代码变更（git tracked）, `review.md`（由 reviewer 写入） | 代码是，review.md 否 |
| VERIFY | `verify.md`, `verify_layer1.json` | 否 |
| REFLECT | `reflect.md` | 否 |
| DELIVER | git commit + tag + push | 是 |

### 3.2 元数据文件

| 文件 | 写入者 | 作用 |
|---|---|---|
| `.paused` | run_cycle | 标记 proposal 暂停处理 |
| `.phase_state` | PhaseWAL | 记录当前 phase 进度（crash recovery） |
| `steward-review.md` | proposal_gate | Steward 评审结果（被覆盖） |
| `steward-review-{ts}.md` | proposal_gate | Steward 评审结果（带时间戳，不覆盖） |

---

## 4. 设计方案

### 4.1 git clean 排除 openspec 目录

**目标**: `git clean -fd` 不删除 openspec/ 下的任何文件。

**方案**: `reset_hard()` 改用 `git clean -fd --exclude=openspec/`

```python
# git_ops.py
def reset_hard(target_path: str, sha: str, transport: Transport = None):
    transport = transport or LocalTransport()
    r = transport.run_shell(f"git reset --hard {sha}", cwd=target_path)
    _check_result(r, "git reset")
    r2 = transport.run_shell("git clean -fd --exclude=openspec/", cwd=target_path)
    _check_result(r2, "git clean")
```

**验证**: 创建 untracked 文件 `openspec/changes/test/proposal.md`，执行 `reset_hard`，确认文件仍存在。

### 4.2 Skipped proposal 重试上限

**目标**: Proposal 被 skip 2 次后自动放弃。

**方案**: 在 `run_cycle()` 的过滤逻辑中增加 skip 计数：

```python
# 统计连续 skip 次数（从最近一条记录往前数）
consecutive_skips = 0
for c in reversed(mine):
    if c.get("outcome") == "skipped":
        consecutive_skips += 1
    else:
        break

MAX_SKIP_RETRIES = 2

if consecutive_skips >= MAX_SKIP_RETRIES:
    abandoned_names.append(name)
    # 移动到 archive/skipped/
elif paused_file.exists() or consecutive_fails >= 3:
    paused_names.append(name)
elif last_outcome == "success":
    completed_names.append(name)
else:
    active_proposals.append(prop)
```

**验证**: DB 中已有 skip 2 次的 proposal，重启 daemon 后确认它不再出现在 active proposals 中。

### 4.3 Abandoned proposal 归档

**目标**: Abandoned proposal 移动到 `archive/skipped/{date}-{name}/`，不留在 openspec/changes/ 中。

**方案**: 复用 `archive_change()` 但指定子目录：

```python
# 在 run_cycle 中
if consecutive_skips >= MAX_SKIP_RETRIES:
    try:
        archive_change(target_path, name, transport=transport, sub_dir="skipped")
    except Exception:
        pass
```

`archive_change` 新增 `sub_dir` 参数，默认为 `archive/`，可指定 `archive/skipped/`。

### 4.4 Scanner 空目录自动清理

**目标**: Scanner 发现目录无 proposal.md 时，如果目录只有 hidden files（`.phase_state` 等），自动删除整个目录。

**方案**: 在 scanner 的 warning 后，检查目录是否为空（仅 hidden files），如果是则 `rmdir`：

```python
if proposal_filename is None:
    # 检查是否只有 hidden files
    non_hidden = [f for f in dir_listing if not f.startswith(".")]
    if not non_hidden:
        transport.run_shell(f"rmdir '{change_dir}'", timeout=5)
    else:
        logger.warning(...)
    continue
```

---

## 5. 验证计划

| 验证项 | 方法 | 预期结果 |
|---|---|---|
| git clean 不删除 openspec | 创建 untracked proposal.md → 跑 pipeline → 检查文件存在 | proposal.md 保留 |
| skip 2 次后 abandon | 提交会被 skip 的 proposal → 等 2 个 cycle | 第 3 个 cycle 不再处理 |
| abandoned 归档 | 触发 abandon → 检查 archive/skipped/ | 目录出现在 archive/skipped/ |
| 空目录清理 | pipeline skip 后残留空目录 → 下次 scanner | 空目录被自动删除 |
| 正常 proposal 不受影响 | 提交正常 proposal → 全 pipeline 通过 | SUCCESS + archive |

---

## 6. 不在范围内

- Pipeline phase 内部逻辑（clarify/enrich/implement 等）不变
- Steward gate 评分逻辑不变
- DB schema 不变（skip_reason 已覆盖需求）
- 归档目录结构保持 `archive/{date}-{name}/` 的命名约定
