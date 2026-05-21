# Clarify: fix-learnings-noise-and-inject

## 需求拆解

### 原始需求
清理 learnings.jsonl 中的噪声记录（空文本、daemon.cycle_error、code.unknown），在写入路径增加校验防止未来噪声，并将有效 learnings 注入到 IMPLEMENT 和 ENRICH 阶段的 system prompt 中，闭合"反思→学习→应用"反馈环。

### 拆解后的子任务

- [ ] 1. **Learnings 写入校验层** — 修改 reflector.py 中 record_lesson / learnings 写入路径，增加文本空值/过短校验（<10字符跳过）、pattern_key 黑名单校验（daemon.cycle_error 开头的跳过），跳过时 DEBUG 日志计数。同步在 DB 写入路径做相同校验。（预估复杂度：低, 预估 token：~3000）
- [ ] 2. **一次性噪声清理** — 新增清理函数，扫描 memory/learnings.jsonl 删除 text 为空 / pattern_key 为 daemon.cycle_error 或 code.unknown 的记录，写回文件；同时清理 DB lessons 表对应记录（按 pattern_key 匹配）。提供 CLI 入口或脚本可执行。（预估复杂度：低, 预估 token：~2500）
- [ ] 3. **Learnings 检索与注入通用模块** — 新增 learnings 注入工具函数（可放 reflector.py 或独立模块）：从 learnings.jsonl 读取记录，按 pattern_key 与当前 change_name 关键词匹配 + pipeline.fail.*/pipeline.pass.* 通用类别过滤，返回最近 N 条格式化文本。含单元测试覆盖匹配逻辑。（预估复杂度：中, 预估 token：~4000）
- [ ] 4. **IMPLEMENT prompt 注入集成** — 修改 implementer.py 的 system prompt 构建函数，调用注入模块获取最近 5 条相关 learnings，以 `## Previous Learnings (avoid repeating mistakes)` section header 注入；无相关 learnings 时不注入。含集成测试验证 prompt 包含 section。（预估复杂度：中, 预估 token：~3500）
- [ ] 5. **ENRICH prompt 注入集成** — 修改 enricher.py 的 system prompt 构建函数，调用注入模块获取最近 3 条相关 learnings，以 `## Relevant Past Experience` section header 注入；无相关 learnings 时不注入。含集成测试验证 prompt 包含 section。（预估复杂度：中, 预估 token：~3500）

## 边界

### IN scope
- reflector.py 写入校验逻辑（text 长度、pattern_key 黑名单）
- memory/learnings.jsonl 现有噪声清理
- DB lessons 表对应记录清理
- learnings 检索/匹配/格式化工具函数
- implementer.py system prompt 中注入 learnings section
- enricher.py system prompt 中注入 learnings section
- 对应单元测试和集成测试

### OUT of scope
- 修改 learnings.jsonl 的存储格式或 schema
- 修改 daemon 循环逻辑本身（daemon.cycle_error 的根因修复）
- 修改其他 agent（reviewer/verifier/planner）的 prompt
- 新建 API 端点或 dashboard 变更
- pattern_miner.py 的模式挖掘逻辑

### 依赖的外部条件
- reflector.py 中 record_lesson / 写入 learnings.jsonl 的函数位置可定位
- implementer.py 和 enricher.py 的 system prompt 构建函数可定位并可扩展
- memory/learnings.jsonl 文件可读写
- DB lessons 表 schema 已知且可按 pattern_key 查询删除

## 目标

### 成功标准
1. `daemon.cycle_error` 开头的 pattern_key 不再被写入 learnings.jsonl 和 DB lessons 表
2. 现有 learnings.jsonl 中 text 为空 / pattern_key 为 daemon.cycle_error 或 code.unknown 的记录被清除
3. IMPLEMENT 阶段 system prompt 在有相关 learnings 时包含 `## Previous Learnings (avoid repeating mistakes)` section，最多 5 条
4. ENRICH 阶段 system prompt 在有相关 learnings 时包含 `## Relevant Past Experience` section，最多 3 条
5. 无相关 learnings 时不注入任何内容（不浪费 context window）
6. 全套 pytest 通过，无新增失败

### 验收方式
- 运行 `pytest` 全量通过
- 手动检查 learnings.jsonl 不含空文本和 daemon.cycle_error 记录
- 单元测试覆盖：校验跳过逻辑、清理逻辑、检索匹配逻辑、prompt 注入逻辑
- 集成测试验证 implementer/enricher 在有 learnings 时 prompt 包含对应 section header

## 约束

### 不能修改的文件
- site/dashboard.html
- skills/skill_evolver.py
- tests/conftest_zsiga.py（可新增测试文件，不修改现有 conftest）
- venv2/ 下所有文件
- pyproject.toml / requirements.txt

### 项目部署分支
- main

### 已知风险
- reflector.py 的 learnings 写入路径可能被多处调用，需确认所有入口都经过校验
- DB lessons 表清理需要确保不误删有效记录（清理范围严格限定为 text 为空 + pattern_key 黑名单）
- learnings 注入增加 system prompt 长度，需控制最大条数避免超出 context window
- enricher.py 的 system prompt 构建函数结构可能与 implementer.py 不同，需分别适配

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考
