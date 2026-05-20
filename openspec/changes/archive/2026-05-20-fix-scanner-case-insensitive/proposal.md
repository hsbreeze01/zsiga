# Proposal: Scanner 文件名大小写不敏感 — 消除 proposal.md vs PROPOSAL.md 的盲区

## Summary
将 `intake/scanner.py` 中对 `proposal.md` / `design.md` / `tasks.md` 的文件检测从严格大小写改为不区分大小写，使用 `find` 或 `ls` 匹配。

## Motivation
当前 `scanner.py` 第 35 行使用 `test -f '{change_dir}/proposal.md'` 严格检测小写文件名。Linux 区分大小写，如果用户或工具创建了 `PROPOSAL.md`（大写），scanner 永远不会拾取这个 change。

**实际影响**：47 上 `database-resource-management` 目录原本是 `PROPOSAL.md`（大写），导致 daemon 连续多个 cycle 都跳过了这个 change，直到手动修复文件名为小写。

### 为何 zsiga 自己没有发现这个问题？

这是一个**静默失败盲区**：

1. **Scanner 不记录跳过原因** — 当 `test -f proposal.md` 返回 false 时，scanner 静默跳过，不输出任何日志。没有人知道"有 change 目录但被跳过了"
2. **无"可见但未处理"告警** — scanner 只报告"找到了什么"，不报告"存在但跳过了什么"。如果有目录但没有 proposal.md，这本身就是异常信号，但被忽略了
3. **大小写假设** — scanner 假设文件名一定是小写，这个假设没有被验证或文档化

本质：**缺乏"发现了异常但未处理"的自省能力** — agent 知道自己做了什么，不知道自己跳过了什么。

## Expected Behavior

### 改造点（scanner.py）

1. **proposal.md 检测改为大小写不敏感**（第 35 行）：
   - 替换 `test -f '{change_dir}/proposal.md'` 为 `find '{change_dir}' -maxdepth 1 -iname 'proposal.md' | head -1`
   - 如果找到，记录实际文件名到 proposal dict 中

2. **design.md / tasks.md 同样改为不敏感**（第 42-50 行区域）

3. **新增"跳过日志"**：当目录存在但找不到 proposal 文件时，输出 warn 日志：
   ```
   ⚠ Scanner: directory {change_dir} exists but no proposal.md found (case-insensitive search)
   ```

4. **proposal dict 新增字段**：`"proposal_filename": actual_filename`（记录实际文件名，供后续 pipeline 使用）

### 联动修改

- `orchestrator.py` 的 `_process_change()` 中读取 proposal 时，使用 `proposal_filename` 而非硬编码 `proposal.md`
- `design.md` / `tasks.md` 的读取同理

## Acceptance Criteria

1. `PROPOSAL.md`（大写）能被 scanner 正确拾取
2. `Proposal.md` / `proPosal.md` 等混合大小写也能正确拾取
3. 跳过的目录有 warn 级别日志输出
4. 后续 pipeline 读取 proposal 内容时使用实际文件名，不硬编码
5. 现有小写文件名的 change 不受影响（向后兼容）
