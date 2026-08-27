# test-file-discovery

EvolutionEngine 的 `_scan_code_structure()` 方法 SHALL 通过 import 分析（而非仅文件名前缀匹配）判断源模块是否已有测试文件，消除对 `harness/runner.py`、`config.py` 等模块的误报。

## MODIFIED Requirements

### Requirement: import-aware test file discovery

`_scan_code_structure()` 在判断源模块是否有对应测试文件时，SHALL 不仅检查 `test_{basename}.py` 的精确文件名匹配，还 SHALL 检查 `tests/test_*.py` 文件中是否存在对目标模块的 import 语句。

- 对于 `tests/` 下每个 `test_*.py` 文件，使用 AST 提取所有 `from zsiga.xxx import` 和 `import zsiga.xxx` 语句中的模块路径
- 将提取到的模块路径（如 `zsiga/harness/runner`）与源模块的相对路径（如 `zsiga/harness/runner.py`）进行匹配
- 只要任一测试文件 import 了目标模块，该模块 SHALL NOT 出现在 `modules_without_tests` 列表中
- 旧的 basename 短路径匹配 MAY 保留为快速回退，但 SHALL 被基于 import 的检查补充

#### Scenario: module with differently-named test file is not flagged as untested

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/harness/runner.py` and a test file at `tests/test_harness_runner.py` that contains `from zsiga.harness.runner import HarnessRunner`
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/harness/runner.py` SHALL NOT appear in the returned `modules_without_tests` list

#### Scenario: module with basename-matching test file still works (backward compatibility)

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/alpha.py` and a test file at `tests/test_alpha.py` that contains `from zsiga.alpha import fn`
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/alpha.py` SHALL NOT appear in the returned `modules_without_tests` list

#### Scenario: config module detected via differently-named test file

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/config.py` and a test file at `tests/test_config_validation.py` that contains `from zsiga.config import load_config`
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/config.py` SHALL NOT appear in the returned `modules_without_tests` list

#### Scenario: truly untested module is still reported

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/orphan.py` and NO test file under `tests/` that imports from `zsiga.orphan`
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/orphan.py` SHALL appear in the returned `modules_without_tests` list

#### Scenario: test file with multiple imports covers all imported modules

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a test file `tests/test_harness_runner.py` containing both `from zsiga.harness.runner import HarnessRunner` and `from zsiga.harness.discover import discover_tests`, and source files at `zsiga/harness/runner.py` and `zsiga/harness/discover.py`
- **When** `_scan_code_structure()` is called
- **Then** neither `zsiga/harness/runner.py` nor `zsiga/harness/discover.py` SHALL appear in `modules_without_tests`

#### Scenario: import-based detection handles syntax errors in test files gracefully

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/deep/broken.py`, and a test file `tests/test_deep_broken.py` that contains `from zsiga.deep.broken import broken_fn` but has invalid Python syntax, with no other test importing `zsiga.deep.broken`
- **When** `_scan_code_structure()` is called
- **Then** the method SHALL NOT raise an exception, and `zsiga/deep/broken.py` SHALL appear in `modules_without_tests`

#### Scenario: test file with no matching source module does not cause errors

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a test file `tests/test_some_integration.py` that imports `from zsiga.pipeline.orchestrator import run` (no `zsiga/some_integration.py` exists)
- **When** `_scan_code_structure()` is called
- **Then** the function SHALL complete without error

### Requirement: import extraction helper

EvolutionEngine 模块 SHALL 暴露一个辅助函数 `extract_zsiga_imports(file_path)`，给定一个 Python 源文件路径，返回文件中引用的所有 `zsiga.*` 模块路径的集合。

- 该函数 SHALL 使用 `ast`（而非正则表达式）解析文件以保证可靠性
- 对于 `import zsiga.foo.bar`，提取的模块路径 SHALL 为 `zsiga/foo/bar`
- 对于 `from zsiga.foo.bar import Baz`，提取的模块路径 SHALL 为 `zsiga/foo/bar`
- 非 `zsiga` 的 import SHALL 被忽略
- 文件不存在时 SHALL 返回空集合，不抛出异常
- 文件有语法错误时 SHALL 返回空集合，不抛出异常

#### Scenario: extract single import from test file

- **testable**: true
- **target**: zsiga/intake/evolution.py::extract_zsiga_imports
- **Given** a Python file with content `from zsiga.harness.runner import HarnessRunner`
- **When** `extract_zsiga_imports(file_path)` is called
- **Then** the result SHALL contain `"zsiga/harness/runner"`

#### Scenario: extract multiple imports from test file

- **testable**: true
- **target**: zsiga/intake/evolution.py::extract_zsiga_imports
- **Given** a Python file with content:
  ```
  from zsiga.config import load_config
  from zsiga.harness.runner import HarnessRunner
  import zsiga.logging
  ```
- **When** `extract_zsiga_imports(file_path)` is called
- **Then** the result SHALL contain `"zsiga/config"`, `"zsiga/harness/runner"`, and `"zsiga/logging"`

#### Scenario: syntax error in test file returns empty set

- **testable**: true
- **target**: zsiga/intake/evolution.py::extract_zsiga_imports
- **Given** a Python file with invalid syntax (e.g., `def foo(:`)
- **When** `extract_zsiga_imports(file_path)` is called
- **Then** the result SHALL be an empty set and no exception SHALL be raised

#### Scenario: nonexistent file returns empty set

- **testable**: true
- **target**: zsiga/intake/evolution.py::extract_zsiga_imports
- **Given** a file path that does not exist on disk
- **When** `extract_zsiga_imports(file_path)` is called
- **Then** the result SHALL be an empty set and no exception SHALL be raised
