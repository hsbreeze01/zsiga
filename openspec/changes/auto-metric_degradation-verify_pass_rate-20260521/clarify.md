# Clarify: Investigate Metric Degradation — verify_pass_rate

## 需求拆解

### 原始需求
`verify_pass_rate` 指标当前为 49.2%，低于可接受阈值。需要定位 verify 阶段失败的根因并修复，使通过率恢复到健康水平。

### 拆解后的子任务
- [ ] 1. **诊断 verify 失败根因**：分析 `metrics/changes.jsonl` 和 `data/daemon.log`，统计 verify 阶段失败的分类（lint / test / checkout冲突 / review拒绝），识别高频失败模式（预估复杂度：中，预估 token：~4000 / 无历史参考）
- [ ] 2. **修复 daemon cycle 中的 checkout 冲突**：verify 阶段最常见的失败是 `git checkout` 时因未提交文件被阻塞，需在 checkout 前自动 stash 或 commit 临时文件（涉及文件范围：daemon 主循环逻辑）（预估复杂度：高，预估 token：~6000 / 无历史参考）
- [ ] 3. **修复 implement 阶段 lint 错误导致 verify 失败的链路**：verify 前置的 implement 阶段生成的代码常含 lint 违规（如 E701 多语句同行），需在 verify 前增加自动 lint-fix 步骤（预估复杂度：中，预估 token：~4000 / 无历史参考）
- [ ] 4. **修复 review-critical 误判导致 verify 失败**：review 阶段误报 "No implementation changes exist"，需优化 review 判定逻辑以正确识别已实现文件（预估复杂度：中，预估 token：~5000 / 无历史参考）

## 边界

### IN scope
- 定位 verify_pass_rate 低于阈值的根因
- 修复 daemon pipeline 中导致 verify 失败的代码缺陷
- 确保 verify 阶段的 lint、test、review 检查流程健壮
- 新增/修改的测试用例

### OUT of scope
- 不修改 dashboard 前端 UI（`site/dashboard.html`）
- 不修改 `venv2/` 下的任何文件
- 不涉及 `skills/` 模块的演化逻辑
- 不改变 openspec 流程定义本身（只修实现）

### 依赖的外部条件
- 需要有可用的 `metrics/changes.jsonl` 历史数据用于根因分析
- 需要能执行 `pytest` 和 `ruff` 验证修复效果
- 需要能操作 git（stash / commit）以解决 checkout 冲突

## 目标

### 成功标准
1. `verify_pass_rate` 指标从当前 49.2% 提升至 ≥ 80%
2. 所有新增/修改代码通过 `ruff check` 无 lint 错误
3. 所有新增/修改代码通过 `pytest` 全部用例通过
4. daemon cycle 中不再因未提交文件导致 checkout 冲突
5. implement → verify 链路中 lint 违规在 verify 前被自动修复

### 验收方式
- 运行 `pytest` 全部通过
- 运行 `ruff check .` 无错误
- 手动构造失败场景（未提交文件、lint 违规代码），验证 daemon 能自动恢复
- 检查 metrics 数据确认 verify_pass_rate 提升趋势

## 约束

### 不能修改的文件
- `site/dashboard.html`
- `venv2/` 下所有文件
- `pyproject.toml`
- `requirements.txt`

### 项目部署分支
main

### 已知风险
- 根因可能涉及多个模块的交互，修复一处可能引发另一处回归
- `git stash` 策略可能丢失 daemon 运行时中间状态数据（如 `data/zsiga.db`、`data/daemon_state.json`）
- 自动 lint-fix 可能改变 implement 阶段生成代码的语义，需确保 fix 后仍通过测试
- 历史数据不足可能导致根因分析不够精确

### 预估 token 消耗
- prompt: ~15000
- completion: ~8000
- 数据来源: 无历史参考
