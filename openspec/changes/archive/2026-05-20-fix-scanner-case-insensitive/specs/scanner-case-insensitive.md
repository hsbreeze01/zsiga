# Delta Spec: Scanner 文件名大小写不敏感检测

## MODIFIED Requirements

### REQ-SCI-001: Artifact 文件检测改为大小写不敏感

Scanner 在扫描 change 目录时，对 `proposal.md`、`design.md`、`tasks.md` 的检测 SHALL 使用大小写不敏感匹配，而非严格的硬编码小写文件名。

Scanner SHALL 使用 `find -iname` 或等效机制定位实际文件，并将实际文件名记录到返回的 change dict 中。

#### Scenario: 目录中存在 PROPOSAL.md（全大写）

- **Given** 一个 change 目录中包含名为 `PROPOSAL.md` 的文件（无小写 `proposal.md`）
- **When** Scanner 扫描该目录
- **Then** Scanner SHALL 成功检测到该文件并将其作为 proposal artifact 识别
- **And** 返回的 dict 中 SHALL 包含 `"proposal_filename": "PROPOSAL.md"` 字段

#### Scenario: 目录中存在 Proposal.md（混合大小写）

- **Given** 一个 change 目录中包含名为 `Proposal.md` 的文件
- **When** Scanner 扫描该目录
- **Then** Scanner SHALL 成功检测到该文件
- **And** 返回的 dict 中 SHALL 包含 `"proposal_filename": "Proposal.md"` 字段

#### Scenario: 目录中仅存在小写 proposal.md（向后兼容）

- **Given** 一个 change 目录中包含名为 `proposal.md` 的文件（标准小写）
- **When** Scanner 扫描该目录
- **Then** Scanner SHALL 正常检测该文件，行为与修改前一致
- **And** 返回的 dict 中 SHALL 包含 `"proposal_filename": "proposal.md"` 字段

#### Scenario: design.md 和 tasks.md 同样大小写不敏感

- **Given** 一个 change 目录中包含 `DESIGN.md` 和 `TASKS.md`
- **When** Scanner 扫描该目录
- **Then** Scanner SHALL 成功检测两个文件
- **And** 返回的 dict 中 SHALL 包含 `"design_filename"` 和 `"tasks_filename"` 字段记录实际文件名

### REQ-SCI-002: 跳过目录时输出告警日志

当 change 目录存在但通过大小写不敏感搜索仍无法找到 proposal 文件时，Scanner SHALL 输出 warn 级别日志。

#### Scenario: 目录存在但无任何 proposal 文件

- **Given** 一个 change 目录中包含其他文件，但没有 `proposal.md` 的任何大小写变体
- **When** Scanner 扫描该目录
- **Then** Scanner SHALL 输出 warn 日志：`⚠ Scanner: directory {change_dir} exists but no proposal.md found (case-insensitive search)`
- **And** 该目录 SHALL 被跳过，不进入后续 pipeline

### REQ-SCI-003: Pipeline 使用实际文件名读取 artifact

Orchestrator 及后续 pipeline 组件在读取 proposal / design / tasks 内容时，SHALL 使用 Scanner 记录的实际文件名（`proposal_filename` / `design_filename` / `tasks_filename`），而非硬编码的小写文件名。

#### Scenario: Orchestrator 读取大写 PROPOSAL.md 的内容

- **Given** Scanner 返回一个 change dict，其中 `"proposal_filename": "PROPOSAL.md"`
- **When** Orchestrator 读取 proposal 内容
- **Then** Orchestrator SHALL 使用 `PROPOSAL.md` 构建文件路径
- **And** SHALL NOT 使用硬编码的 `proposal.md`
