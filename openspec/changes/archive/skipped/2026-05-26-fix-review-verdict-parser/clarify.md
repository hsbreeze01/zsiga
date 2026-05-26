# clarify.md — fix-review-verdict-parser

## 需求拆解

### 原始需求
修复 review 阶段的 verdict/issue 解析器，使其能正确处理 critic 子代理实际产出的多种格式（带 XML 工具调用包裹、编号列表、项目符号列表、纯文本嵌入），从而让 review detail 字段不再为空、CRITICAL 问题能被正确检测并触发修复流程。

### 拆解后的子任务

- [ ] 1. **强化 `_extract_clean_review()` 的问题提取逻辑** (预估复杂度：中, 预估 token：~4000 / 无历史参考)
  - 文件：`zsiga/agent/reviewer.py`
  - 替换单一严格正则为多模式回退匹配：`N. [SEVERITY] ...` → `- [SEVERITY] ...` → `[SEVERITY] ...`
  - 剥离 XML 标签（`<tool_calling>`, `<tool_call:>` 及相关包裹）
  - 合并多行描述（遇下一个 issue marker 或空行停止）
  - 确保清理后内容能匹配至少一种模式

- [ ] 2. **将 XML 剥离/内容净化前移到 `parse_review_verdict()` 作为预处理步骤** (预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 文件：`zsiga/agent/reviewer.py`
  - 将 `run_review()` 中的净化逻辑下沉到 `parse_review_verdict()` 入口
  - 保证即使 `run_review()` 清理失败或被跳过，解析仍能工作
  - 保持 `run_review()` 中现有清理逻辑不变（避免双重清理的副作用，或移除冗余路径）

- [ ] 3. **添加诊断日志：verdict=ISSUES_FOUND 但 0 个 issue 时输出 WARNING** (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - 文件：`zsiga/agent/reviewer.py`
  - 在 `parse_review_verdict()` 返回前，当 verdict 为 ISSUES_FOUND 且 issues 列表为空时
  - `logger.warning(...)` 输出原始内容前 500 字符
  - 帮助未来诊断格式漂移

- [ ] 4. **测试覆盖** (预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 文件：`tests/test_reviewer.py`（如已有）或新建
  - 用例覆盖：编号格式、项目符号格式、纯 `[SEVERITY]` 格式、XML 包裹格式、多行描述、CLEAN verdict 不回归
  - 可用已归档的 review.md 文件作为 fixture 数据

## 边界

### IN scope
- `zsiga/agent/reviewer.py` 中的 `_extract_clean_review()` 函数改造
- `zsiga/agent/reviewer.py` 中的 `parse_review_verdict()` 函数改造（增加预处理 + 诊断日志）
- `run_review()` 中净化逻辑的协调调整（前移或去重）
- 对应测试文件中新增解析器测试用例

### OUT of scope
- Critic 子代理 prompt 的修改（不改生成端行为）
- 其他 pipeline 阶段（implement、reflect 等）的修改
- 数据库 schema 或已有 review 记录的回填修复
- `review` role 定义的修改

### 依赖的外部条件
- 已归档的 review.md 文件可用于验证（proposal 中列出了 3 个样本）
- `zsiga/agent/reviewer.py` 文件存在且包含 `_extract_clean_review` 和 `parse_review_verdict` 函数

## 目标

### 成功标准
1. `parse_review_verdict()` 能从编号列表 (`1. [CRITICAL] ...`) 中正确提取 issues
2. `parse_review_verdict()` 能从项目符号列表 (`- [CRITICAL] ...`) 中正确提取 issues
3. `parse_review_verdict()` 能从裸格式 (`[CRITICAL] ...`) 中正确提取 issues
4. XML `<tool_calling>` / `<tool_call:>` 包裹被正确剥离，不影响解析
5. 多行 issue 描述被正确合并为单条
6. verdict=ISSUES_FOUND 但 0 issues 解析成功时，输出 WARNING 日志含原始内容前 500 字符
7. 已有 CLEAN verdict 解析无回归（现有行为不变）
8. `ruff check zsiga/agent/reviewer.py` 通过
9. 无新增第三方依赖

### 验收方式
- 运行 `pytest tests/test_reviewer.py -v` 全部通过
- 手动用已归档 review.md 样本（cleanup-stale-test-files、validate-pipeline-fixes-20260520、add-health-check-endpoint）验证解析结果
- `ruff check zsiga/agent/reviewer.py` 无报错

## 约束

### 不能修改的文件
- `zsiga/agent/` 下除 `reviewer.py` 外的其他文件（不改子代理行为）
- `zsiga/pipeline/` 下的文件（不改 pipeline 流程控制）
- `zsiga/models.py` 或数据库相关文件（不改 schema）

### 项目部署分支
- 目标项目位于 `/home/zsiga/repo`，change 目录为 `openspec/changes/fix-review-verdict-parser`

### 已知风险
- **正则回溯风险**：多模式回退正则如果写法不当，可能在极端输入下产生灾难性回溯；应使用非贪婪匹配或锚定
- **清理逻辑双路径冲突**：`run_review()` 和 `parse_review_verdict()` 都做清理可能导致二次处理；需明确职责划分
- **现有测试回归**：`tests/test_reviewer.py` 已有测试用例，修改解析逻辑可能导致旧用例失败；需先理解现有断言

### 预估 token 消耗
- prompt: ~6000（读取 reviewer.py + 理解现有逻辑 + 实现变更）
- completion: ~3000（代码修改 + 测试编写）
- 数据来源: 无历史参考（基于 proposal 描述的复杂度估算）
