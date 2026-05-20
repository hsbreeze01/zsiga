# Design: Scanner 文件名大小写不敏感

## 架构决策

### ADR-1: 使用 `os.listdir` + `str.lower()` 过滤代替 `find` 命令

**决策**：在 Python 层面用 `os.listdir()` 列出目录内容，再通过 `.lower()` 比对匹配文件名，而非调用 shell `find -iname`。

**理由**：
- `scanner.py` 已是 Python 代码，避免混合 shell 调用增加复杂度
- `os.listdir` 是纯 Python 操作，跨平台且无需 subprocess 开销
- 与现有代码风格一致（当前 scanner 虽用 subprocess 调 shell，但文件名匹配逻辑可以纯 Python 化）
- 更容易做单元测试（mock `os.listdir` 即可）

### ADR-2: 使用辅助函数 `_find_file_ci(directory, target_name)` 复用逻辑

**决策**：提取一个大小写不敏感文件查找辅助函数，proposal / design / tasks 三种文件统一调用。

**理由**：
- 消除三处重复的查找逻辑
- 便于单元测试独立验证

### ADR-3: 在 change dict 中记录实际文件名

**决策**：在 scanner 返回的每个 change dict 中增加 `proposal_filename`、`design_filename`、`tasks_filename` 三个字段。

**理由**：
- 后续 pipeline 组件（orchestrator）需要知道实际文件名才能正确读取
- 不修改现有字段语义，向后兼容

## 数据流

```
1. Scanner 扫描 change 目录
   ├─ os.listdir(change_dir) 获取所有文件名
   ├─ _find_file_ci(change_dir, "proposal.md") → "PROPOSAL.md" 或 None
   ├─ _find_file_ci(change_dir, "design.md")   → "Design.md"   或 None
   ├─ _find_file_ci(change_dir, "tasks.md")    → "TASKS.md"     或 None
   │
   ├─ 如果 proposal 未找到 → 输出 warn 日志 → 跳过该目录
   └─ 如果 proposal 找到 → 构造 change dict，包含 *_filename 字段

2. Orchestrator 读取 artifact
   ├─ 从 change dict 读取 proposal_filename
   ├─ 用 proposal_filename 构建完整路径读取内容
   └─ design_filename / tasks_filename 同理
```

## 修改文件列表

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `intake/scanner.py` | MODIFIED | 新增 `_find_file_ci()` 辅助函数；将硬编码文件名检测替换为大小写不敏感查找；新增跳过日志；change dict 新增 `*_filename` 字段 |
| `orchestrator.py` | MODIFIED | `_process_change()` 中读取 proposal/design/tasks 时使用 `*_filename` 字段替代硬编码文件名 |

## 不修改的部分

- change 目录的命名规范不变（仍是小写 kebab-case）
- artifact 内容格式不变（仍是 Markdown）
- 现有小写文件名的工作流完全兼容
