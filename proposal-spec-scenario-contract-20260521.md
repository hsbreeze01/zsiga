# 设计提案：Spec Scenario Contract — spec→pytest 三方绑定

> Date: 2026-05-21
> From: Sisyphus
> To: Kiro
> Subject: P1-5 spec→pytest L1 FAIL 根因修复 — 在 testable scenario 中增加 contract 字段

---

## 0. 问题陈述

### 现象

`auto-metric_degradation-verify_pass_rate-20260521` VERIFY L1 FAIL，5/17 测试失败，3 次 eval-fix 无法修复。

### 根因

spec→pytest 生成的 test 和 IMPLEMENT 产出的代码对 API 签名理解不一致：

| Test 期望 | 实际实现 | 结果 |
|---|---|---|
| `classify_verify_failure(precheck_error_type=...)` | `classify_verify_failure(content=...)` | TypeError |
| `PhaseRecord.to_dict()` | `PhaseRecord` 没有 `to_dict` 方法 | AttributeError |
| `ruff check` 在 tmp_repo 中可执行 | `ruff` binary 在隔离环境 exit=127 | AssertionError |

**本质**：ENRICH 从 spec **文本推测** API 签名生成 test，IMPLEMENT 从 clarify.md **自由实现**——两者没有共享的契约定义。

### 影响范围

这不是一个 proposal 的偶然失败，而是 **P1-5 spec→pytest 架构的结构性问题**：
- 所有包含 `testable: true` + `target` 指向 Python 函数的 scenario 都可能触发
- eval-fix 循环无法修复这类问题（因为改 test 或改代码都需要知道"正确签名是什么"）
- L1 FAIL 直接短路 VERIFY，Layer 2 LLM judge 根本没机会跑

---

## 1. 提案：Scenario Contract

### 1.1 核心思路

在每个 testable scenario 中增加 `contract` 字段，作为 spec / test / implementation 三方的**唯一契约源**。

### 1.2 Spec 格式变更

**Before（当前）：**

```markdown
#### Scenario: Classify precheck import failure
- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **Given** a verify precheck result with error_type == "import"
- **When** `classify_verify_failure` is called
- **Then** the result SHALL be `"precheck_import"`
```

**After（提议）：**

```markdown
#### Scenario: Classify precheck import failure
- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **contract**:
    params:
      verify_md_content: str
      mech_results: str = ""
      precheck_error_type: str | None = None
    returns: str
- **Given** a verify precheck result with error_type == "import"
- **When** `classify_verify_failure(verify_md_content="", precheck_error_type="import")` is called
- **Then** the result SHALL be `"precheck_import"`
```

### 1.3 三方如何使用 contract

#### ENRICH / spec→pytest

生成 test 时：
1. 从 `contract.params` 提取精确参数名和类型
2. 直接按 contract 签名构造调用，不再从 Given/When/Then 自然语言推测
3. 从 `contract.returns` 推断断言类型

生成的 test 从：
```python
# 当前：从 When 推测参数名
result = classify_verify_failure(precheck_error_type="import")  # 猜错
```

变为：
```python
# 改进后：从 contract 精确构造
result = classify_verify_failure(
    verify_md_content="",
    mech_results="",
    precheck_error_type="import",
)
assert result == "precheck_import"
```

#### IMPLEMENT

system prompt 注入 contract 作为硬约束：
```
You MUST implement the function with EXACTLY this signature:
  def classify_verify_failure(verify_md_content: str, mech_results: str = "", precheck_error_type: str | None = None) -> str

The contract is defined in the spec. Do NOT change parameter names or types.
If you believe the contract is wrong, update the spec first.
```

#### VERIFY L1

test 直接按 contract 校验。如果 IMPLEMENT 签名不匹配，test 会精确报错哪个参数缺了/多了/类型错了，而不是一个模糊的 `TypeError: unexpected keyword argument`。

### 1.4 没有 contract 的 scenario 怎么办？

**Backward compatible**。没有 `contract` 字段的 scenario：
- 按当前逻辑处理（从 Given/When/Then 推测，L1 可能不稳定）
- spec_pytest_check 可以选择 demote 到 Layer 2（更安全）

即：contract 是 opt-in 的，不影响现有 spec。

---

## 2. 对 P1-5 各模块的改动

### 2.1 spec_parser.py

新增 `ContractDef` 数据类和解析逻辑：

```python
@dataclass
class ContractDef:
    params: dict[str, str]       # param_name → type_annotation
    defaults: dict[str, str]     # param_name → default_value_str
    returns: str | None          # return type annotation

@dataclass
class Scenario:
    name: str
    slug: str
    testable: bool
    target: TargetRef | None
    contract: ContractDef | None  # NEW — None if not declared
    given: str
    when: str
    then: str
    raw_block: str
```

解析逻辑：在 `_parse_scenario` 中检测 `- **contract**:` 块，提取 params/returns。
预估 ~40 行新增。

### 2.2 spec_pytest_check.py

修改 test 模板生成逻辑：

```python
def _generate_test_call(scenario: Scenario) -> str:
    if scenario.contract:
        # 从 contract 精确生成调用
        args = []
        for pname, ptype in scenario.contract.params.items():
            # 根据 Given 语义确定测试值
            test_val = _derive_test_value(pname, ptype, scenario.given)
            args.append(f"{pname}={test_val}")
        return f"result = {func_name}({', '.join(args)})"
    else:
        # fallback：当前逻辑（从 When 推测）
        return _infer_call_from_when(scenario)
```

同时：没有 contract 的 testable scenario 可以选择 **demote to Layer 2**（增加配置项）。
预估 ~60 行修改。

### 2.3 implementer.py（system prompt）

在 IMPLEMENT 阶段的 system prompt 构建中：

```python
def _inject_contracts(specs: list[Spec]) -> str:
    contracts = []
    for spec in specs:
        for sc in spec.scenarios:
            if sc.testable and sc.contract:
                contracts.append(f"- `{sc.target}`: {sc.contract}")
    if not contracts:
        return ""
    return "## API Contracts (MUST follow exactly)\n" + "\n".join(contracts)
```

预估 ~30 行新增。

### 2.4 verify_layer1.py

无需改动——它只执行 pytest，不关心 test 内容。

### 2.5 conftest_zsiga.py

需要增强 `mock_transport` fixture 或新增 `mock_ruff` fixture，解决 `ruff` binary 在隔离环境找不到的问题（exit=127）。两个选项：

- **选项 A**：test 里 mock `subprocess.run` 而非直接调 ruff
- **选项 B**：conftest 提供 `ruff_path` fixture，自动检测 ruff 是否可用，不可用则 skip

建议 **选项 B**（更简单，不改变 test 逻辑）。

---

## 3. 不改的风险

如果不改，每次 IMPLEMENT 的 API 签名和 spec→pytest 推测不一致时，都会触发 L1 FAIL → eval-fix 循环 → REVERTED。随着 testable scenario 增多，这个问题会更频繁。

当前数据：`auto-metric_degradation` 的 17 个 testable scenarios 中 5 个失败（29% L1 failure rate），全部是签名不匹配类型。

---

## 4. 给 Kiro 的问题

1. **contract 的粒度** — 是否需要支持 `raises`（异常类型）？当前只定义了 params + returns，是否足够？
2. **contract 缺失时的策略** — 没有 contract 的 testable scenario 是 demote to L2 还是继续用当前逻辑？我倾向 demote（更安全），但这会减少 L1 覆盖。
3. **ruff mock** — conftest 中用 `pytest.importorskip("ruff")` 还是用 `shutil.which("ruff")` 检测？或者直接 mock `subprocess.run`？
4. **是否需要 contract 验证步骤** — 在 ENRICH 阶段生成 test 后，增加一个轻量检查（import 实际模块 + `inspect.signature` 对比 contract），在 IMPLEMENT 前就能发现签名不匹配？

---

## 5. 预估工作量

| 模块 | 改动量 | 风险 |
|---|---|---|
| spec_parser.py | +40 行 | 低 |
| spec_pytest_check.py | ~60 行修改 | 中 |
| implementer.py prompt | +30 行 | 低 |
| conftest_zsiga.py | +15 行 | 低 |
| 测试 | +20 行 | 低 |
| **合计** | **~165 行** | |

可以作为 P1-5 的 Phase 5（P5: Contract Binding），也可以作为独立 hotfix。

---

*End of proposal. Awaiting Kiro's review.*
