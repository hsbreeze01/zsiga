# Design: Config Diff Viewer

## Architecture Decision

Add a pure-function utility `compare_configs` in a new module `zsiga/config_diff.py`. This function operates on already-parsed Python dicts (no file I/O), keeping it testable and composable. YAML loading is the caller's responsibility.

## Data Flow

```
zsiga.yaml (file) ──yaml.safe_load──> dict
zsiga.yaml (file) ──yaml.safe_load──> dict
                                      ↘            ↙
                               compare_configs(old, new)
                                        ↓
                              {"changed": [...], "details": {...}}
```

## Key Design Choices

1. **Pure function on dicts** — No file paths, no YAML parsing inside. The function receives two dicts and returns a dict. This makes it trivially testable and reusable from CLI, API, or tests.

2. **Flattened dot-notation keys** — Recursive walk of the `model`, `budget`, and `transport` subtrees. Each leaf value is addressed as `section.subkey.leaf` (e.g. `model.name`, `transport.http.port`).

3. **Watched sections only** — Only the three sections specified in the proposal are compared. A constant `WATCHED_SECTIONS = ("model", "budget", "transport")` defines the scope.

4. **None sentinel for missing keys** — If a key exists in one config but not the other, the missing side is represented as `None`.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `zsiga/config_diff.py` | **CREATE** | New module with `compare_configs` and helper `_flatten_section` |
| `tests/test_config_diff.py` | **CREATE** | Unit tests covering all spec scenarios |

## Function Signatures

```python
WATCHED_SECTIONS = ("model", "budget", "transport")

def _flatten_section(data: dict, prefix: str) -> dict[str, Any]:
    """Recursively flatten a nested dict into {dot.path: value} pairs."""

def compare_configs(old_config: dict, new_config: dict) -> dict:
    """Compare two parsed configs, return {"changed": [...], "details": {...}}."""
```

## Edge Cases

- Empty dicts → empty diff
- Section missing entirely from one config → all leaf keys from the other side reported with `None` on the missing side
- Non-dict leaf values (int, str, float, bool, None) → compared directly
- Lists under watched sections → compared by equality (no element-level diff)
