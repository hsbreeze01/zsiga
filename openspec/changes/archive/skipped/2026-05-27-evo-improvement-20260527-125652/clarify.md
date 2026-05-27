# clarify.md — evo-improvement-20260527-125652

## 需求拆解

### 原始需求
探索模块 `zsiga/transport.py` 的代码质量，识别可优化项并实施改进。当前该模块缺少测试覆盖，可能存在代码异味（过长函数、重复代码、缺失错误处理）。需要阅读源码、识别问题、实施针对性改进并添加基本测试覆盖。

### 拆解后的子任务
- [ ] 1. 阅读 `zsiga/transport.py` 源码，梳理 `create_transport`、`Transport`、`LocalTransport`、`SSHTransport` 的职责、API 和依赖关系，输出分析结论（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 2. 识别并实施至少 1 项实质性代码改进（非格式化），如补充缺失的 `shutil` 导入、修复 `scp -i None` 参数问题、增加错误处理等（预估复杂度：中, 预估 token：~3000 / 无历史参考）
- [ ] 3. 新建 `tests/test_transport.py`，为 `create_transport`、`LocalTransport`、`SSHTransport` 编写基本测试覆盖（预估复杂度：中, 预估 token：~3000 / 无历史参考）

## 边界

### IN scope
- 分析 `zsiga/transport.py` 的代码质量（96 行）
- 实施小范围针对性改进（至少 1 项实质性改进）
- 新建 `tests/test_transport.py` 添加基本测试覆盖
- 确保所有变更通过 pytest 和 ruff 检查

### OUT of scope
- 大范围重构 transport 模块的类层次结构
- 修改 transport.py 的公共 API 签名
- 修改依赖 `transport.py` 的其他模块（daemon.py、config.py、runner.py）
- 添加集成测试或端到端测试

### 依赖的外部条件
- `zsiga/transport.py` 文件存在且可读（已确认 96 行）
- 项目 pytest 和 ruff 配置正常工作
- SSHTransport 的测试可能需要 mock SSH 相关依赖

## 目标

### 成功标准
1. `zsiga/transport.py` 中实施了至少 1 项非格式化的实质性代码改进（如修复 bug、补充错误处理、修复缺失导入等）
2. `tests/test_transport.py` 文件存在且包含至少 1 个可执行的测试用例
3. 所有变更通过 `pytest` 和 `ruff check`

### 验收方式
- `tests/test_transport.py` 文件存在且包含 testable 符号
- `pytest tests/test_transport.py` 通过（exit code 0）
- `ruff check zsiga/transport.py tests/test_transport.py` 无错误
- 对比 git diff，`zsiga/transport.py` 的变更非纯格式化

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（transport 消费者）
- `zsiga/config.py`（transport 配置来源）
- `zsiga/harness/runner.py`（transport 消费者）
- 任何 `tests/test_*.py` 中已存在的测试文件（仅新建 `tests/test_transport.py`）

### 项目部署分支
- main（默认分支）

### 已知风险
- `tests/test_transport.py` 不存在，属零基线新建，需确保 import 路径正确
- `LocalTransport.copy()` 可能使用了未导入的 `shutil`（Scout 发现），需验证
- `SSHTransport` 可能存在 `scp -i None` 参数问题（Scout 发现），需验证
- 此 proposal 由自演进引擎自动生成，历史上 explore-and-improve 类 proposal 在 verify 阶段有失败记录
- transport 模块被 daemon.py、runner.py 等核心模块依赖，修改需确保行为不变

### 预估 token 消耗
- prompt: ~6000
- completion: ~3000
- 数据来源: 无历史参考
