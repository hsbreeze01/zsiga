# Tasks: Session Timeline Renderer

## 1. Core Rendering Logic

- [x] **1.1** Create `zsiga/metrics/timeline.py` with `render_timeline(session: dict) -> str` and all helpers (`_format_duration`, `_outcome_icon`, `_render_bar`, `_format_timestamp`, `_render_header`, `_render_footer`)
- [x] **1.2** Create `tests/test_timeline.py` with full test coverage: multi-phase rendering, single phase, zero phases, proportional bar math, outcome icons, time formatting, no-ANSI guarantee, edge cases (zero runtime, empty phases list)

## 2. Integration (optional, deferred)

> These tasks are **not in scope** for this change. They are listed for future reference only.

- [ ] ~~2.1 Add timeline output to dashboard HTML as a `<pre>` section~~ (scope: frontend)
- [ ] ~~2.2 Add CLI command to render a session file timeline~~ (future scope)
