# clarify.md — fix-learnings-noise-and-inject

## 需求拆解

### 原始需求
清理 learnings 噪声（空文本记录与 daemon 崩溃信号），在写入时加校验防止未来噪声，并将有效 learnings 注入到 IMPLEMENT 和 ENRICH 阶段的 prompt 中，接通"学习→反馈"闭环。

### 拆解后的子任务

- [ ] 1. **Learnings 写入校验 gate** — 在 `reflector.py`（或 `record_lesson()` / learnings 写入函数）中添加写入前过滤逻辑：text 为空或 < 10 字符时跳过；`pattern_key` 以 `daemon.cycle_error` 开头时跳过；被跳过条目以 DEBUG 级别记录日志。(预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - 涉及文件：`reflector.py`（或 learnings 写入模块）、对应测试文件
  - 验证方式：写单元测试验证空文本 / 短文本 / `daemon.cycle_error` 前缀的 pattern_key 均不被记录

- [ ] 2. **一次性清理现有 learnings 噪声** — 新增清理函数，扫描 `memory/learnings.jsonl`：删除 text 为空的记录；删除 `pattern_key` 为 `daemon.cycle_error` 或 `code.unknown` 的记录；保留其余记录并写回；同时清理 DB lessons 表中对应记录（按 pattern_key 匹配）。(预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 涉及文件：新增清理函数（可放在 reflector.py 或独立模块）、`memory/learnings.jsonl`、DB lessons 表
  - 验证方式：写单元测试用临时 jsonl 文件验证过滤逻辑正确；确认清理后文件中不再含目标噪声

- [ ] 3. **Learnings 搜索与匹配工具函数** — 实现一个可复用的 learnings 查询函数，接受 `change_name` / 关键词，返回最近 N 条相关 learnings。"相关"定义：pattern_key 包含当前 change_name 的关键词，或属于通用的 `pipeline.fail.*` / `pipeline.pass.*` 类别。(预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 涉及文件：可放在 reflector.py 或独立的 learnings 模块
  - 验证方式：写单元测试验证不同 query 场景下的匹配与排序逻辑

- [ ] 4. **Learnings 注入 IMPLEMENT prompt** — 修改 `implementer.py` 的 system prompt 构建函数：调用任务 3 的查询函数获取最近 5 条相关 learnings；以 `## Previous Learnings (avoid repeating mistakes)` 为 section header 注入；每条格式 `- [{pattern_key}] {text}`；无相关 learnings 时不注入。(预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 涉及文件：`implementer.py`、对应测试文件
  - 验证方式：写单元测试验证 prompt 构建时正确包含 / 不包含 learnings section

- [ ] 5. **Learnings 注入 ENRICH prompt** — 修改 `enricher.py` 的 system prompt 构建函数：与 IMPLEMENT 相同逻辑，section header 为 `## Relevant Past Experience`，最多注入 3 条。(预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - 涉及文件：`enricher.py`、对应测试文件
  - 验证方式：写单元测试验证 ENRICH prompt 中 learnings section 的正确性与数量上限

## 边界

### IN scope
- learnings 写入时的噪声过滤 gate
- 现有 learnings.jsonl 中空文本 / `daemon.cycle_error` / `code.unknown` 记录的一次性清理
- DB lessons 表中对应噪声记录的清理
- IMPLEMENT 阶段 system prompt 中注入最近 5 条相关 learnings
- ENRICH 阶段 system prompt 中注入最近 3 条相关 learnings
- 相关 learnings 的搜索匹配工具函数
- 以上所有功能的单元测试

### OUT of scope
- 改变 learnings.jsonl 的存储格式或路径
- 修改 dashboard 页面展示 learnings
- 修改 daemon 循环逻辑或 cycle_error 本身的产生原因
- 修改 reflector 的反思逻辑（只改写入 gate）
- 其他 agent 阶段（CLARIFY / SPEC / VERIFY / REVIEW 等）的 prompt 注入
- learnings 的去重 / 合并 / 摘要等高级功能

### 依赖的外部条件
- `reflector.py` 中存在可定位的 learnings 写入函数（如 `record_lesson()`）
- `implementer.py` 中存在可定位的 system prompt 构建函数
- `enricher.py` 中存在可定位的 system prompt 构建函数
- `memory/learnings.jsonl` 文件存在且为 JSONL 格式
- DB lessons 表存在且可通过 pattern_key 查询

## 目标

### 成功标准
1. `daemon.cycle_error` 类型的 learnings 不再被记录到 learnings.jsonl
2. 现有 learnings.jsonl 中 text 为空 / `daemon.cycle_error` / `code.unknown` 的记录被清除
3. DB lessons 表中对应噪声记录被清除
4. IMPLEMENT 阶段的 system prompt 中出现 `## Previous Learnings (avoid repeating mistakes)` section（当有相关 learnings 时）
5. ENRICH 阶段的 system prompt 中出现 `## Relevant Past Experience` section（当有相关 learnings 时）
6. 无相关 learnings 时，IMPLEMENT / ENRICH 的 prompt 中不注入任何额外 section
7. 全套 pytest 通过（无新增失败）

### 验收方式
- 运行 `pytest tests/test_learnings_search.py tests/test_reflector.py` 及相关测试全部通过
- 手动检查 `memory/learnings.jsonl` 不含空文本 / `daemon.cycle_error` / `code.unknown` 记录
- `ruff check` 无新增 lint 错误
- 构造含 learnings 的 fixture，验证 IMPLEMENT/ENRICH prompt 输出包含正确 section

## 约束

### 不能修改的文件
- `pyproject.toml`
- `requirements.txt`
- `site/dashboard.html`
- `venv2/` 目录下任何文件
- `tests/conftest_zsiga.py`（除非必要且不破坏现有 fixture）

### 项目部署分支
- main

### 已知风险
- `reflector.py` / `implementer.py` / `enricher.py` 的具体函数签名和结构需在实施时确认，proposal 中描述可能与实际代码有偏差
- DB lessons 表的访问方式（ORM / 原始 SQL）需确认，清理操作需确保不锁表或丢失有效数据
- learnings 搜索匹配的相关性定义（`pipeline.fail.*` / `pipeline.pass.*` 通配）可能需要调优才能避免过多/过少匹配
- 一次性清理为破坏性操作，应在测试环境验证后再执行

### 预估 token 消耗
- prompt: ~6000
- completion: ~5000
- 数据来源: 无历史参考
