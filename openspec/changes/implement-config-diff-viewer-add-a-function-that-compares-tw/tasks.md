# Tasks: Config Diff Viewer

## 1. Core Implementation

- [x] **1.1** Create `zsiga/config_diff.py` with `WATCHED_SECTIONS` constant, `_flatten_section` helper, and `compare_configs(old_config, new_config) -> dict` function. The function flattens watched sections from both configs, diffs leaf keys, and returns `{"changed": [...sorted...], "details": {...}}`.

## 2. Tests

- [x] **2.1** Create `tests/test_config_diff.py` with tests covering: identical configs (empty diff), model change, budget change, transport change, key removed, key added, unrelated section ignored, dot-notation flattening, alphabetical sorting of changed list, missing section in one config, empty input dicts.
