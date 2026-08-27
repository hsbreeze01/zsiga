现在我已经独立验证了所有关键事实。让我做出判断。

## Verdict: PUSHBACK

## 我的判断

这个 proposal 是一个典型的 **zombie proposal**——我验证了 `openspec/changes/` 中存在 **52 份** 包含 "add-tests-config" 的 proposal 文件，全部 archived/skipped，无一成功。更关键的是，它的核心前提是**虚假的**：`zsiga/config.py` 确实没有一个叫 `tests/test_config.py` 的文件，但它已经有 **39 个测试**（`test_config_validation.py`）+ **8 个测试**（`config_unit_coverage.py`）+ **5 个测试**（`config_load_robustness.py`）+ **30+ 个测试**在 `test_active_target_filter.py` 中通过实际调用覆盖了 `load_runtime_state`/`save_runtime_state`。创建一个名为 `tests/test_config.py` 的文件来放冗余测试，只满足了一个错误的发现逻辑（引擎用 `basename` 匹配），不产生任何实际价值。真正需要修复的是 `zsiga/intake/evolution.py` 的测试发现机制，但这不在本 proposal scope 内。

## 评分详情
- 可行性: 2/2 — `zsiga/config.py` 存在（548行），所有目标函数已验证存在；`tests/test_config.py` 确实不存在。确定性事实支持。
- 可执行性: 2/2 — 有明确的 target files（新建 `tests/test_config.py`），有具体的函数名（`test__find_config` 等），有设计路径（mock 隔离）。
- 能力匹配: 0/2 — 52 次同题 proposal，0 次成功实现。这是教科书级的 zombie loop。
- 历史风险: -1/2 (0 base - 1 auto-generated penalty) — 标题 `add-tests-config` 为自演进引擎自动生成，且完全相同的 proposal 已循环 52 次以上。
- 范围合理性: 1/2 — scope 定义清晰（新建文件、不改源码），但核心前提为假：模块已被测试覆盖，创建冗余测试文件只服务于引擎的发现缺陷。
- 验收可测性: 2/2 — 4 条 BAC 格式规范，覆盖文件存在、符号存在、数量要求、pytest 退出码，可自动验证。
- 总分: 6/12

## 疑虑
1. **虚假前提**：proposal 称"模块缺少测试文件"，但 `tests/test_config_validation.py` 已有 39 个测试全面覆盖 `validate_config`、`load_config`、所有 dataclass；`config_unit_coverage.py` 已覆盖 `_find_config` 和 `_resolve_env_vars`。所谓"缺测试"仅因为文件名不叫 `test_config.py`。
2. **Zombie loop 根因未解**：52 次循环的根因是 `evolution.py` 用 `os.path.basename()` 匹配测试文件名（Scout #1 已定位），本 proposal 不修复此问题，下次仍会生成同名 proposal。
3. **冗余代码危害**：创建 `tests/test_config.py` 会新增与已有 52+ 测试重复的代码，增加维护负担但不增加任何覆盖价值。`_runtime_state_path`/`load_runtime_state`/`save_runtime_state` 在 `test_active_target_filter.py` 中已通过实际调用被充分测试。
4. **BAC-02 设计缺陷**：要求 `test__find_config` 等函数存在于新文件中，但这些测试逻辑已在 `config_unit_coverage.py` 中实现。BAC 衡量的是文件名而非覆盖增量。

## 建议
1. **重构为修复引擎发现逻辑**：将 proposal 改为修复 `zsiga/intake/evolution.py` 中测试文件的发现机制（使用模块级符号搜索而非文件名 basename 匹配），从根本上消除 zombie loop。这是唯一有价值的行动。
2. **如果坚持添加测试**：scope 应缩小到仅覆盖真正缺测试的 3 个函数（`_runtime_state_path`, `load_runtime_state`, `save_runtime_state`），并明确承认已有覆盖（在 proposal 中引用已有测试文件），避免冗余。
3. **补充覆盖率数据**：在 proposal 中加入 `pytest --cov zsiga.config` 的实际覆盖率数字和未覆盖行号，而非依赖文件名存在性推断覆盖状态。

## 历史参考
- FAIL: add-tests-config × 52 次循环 — 全部 archived/skipped (2026-05-27 ~ 2026-05-30)，根因为引擎测试发现逻辑缺陷导致的 false negative
- FAIL: verify-layer0-with-tests at verify (2026-05-27) — 教训: review error and adjust approach
