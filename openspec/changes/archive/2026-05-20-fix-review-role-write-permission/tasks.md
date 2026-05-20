# Tasks: Fix Review Role Write Permission

## Group 1: Core Fix

- [x] 1.1 Add `"write_file"` to `Role.REVIEW.allowed_tools` in `zsiga/agent/roles.py` and update `tests/test_roles.py` to assert `write_file` is present in the REVIEW role's allowed tools (and `edit_file` is absent)
