# Design: Dashboard Proposal Queue Panel

## Architecture Decision

**Reuse DirectoryScanner for proposal discovery** — The existing `zsiga/intake/scanner.py` `DirectoryScanner.scan()` already handles cross-target proposal enumeration with SSH/local transport abstraction, case-insensitive file detection, and directory filtering (skipping `archive`). Rather than duplicating this logic in the dashboard module, we reuse `DirectoryScanner` and extend the rendering to read proposal summaries.

## Data Flow

```
generate_dashboard()
  └── _render_proposal_queue()
        ├── load_config() → targets dict
        ├── DirectoryScanner(targets).scan() → list[proposal_dict]
        │     └── For each target: ls openspec/changes/ → filter archive → list dirs
        ├── For each proposal: read first line of proposal.md → summary
        ├── load data/daemon_state.json → current_change, current_phase
        └── Render HTML table with highlight for active proposal
```

## Key Design Points

1. **Proposal summary**: For each scanned proposal, read only the first line of `proposal.md` via transport (one `head -1` command per proposal, or `cat` + parse first line). Extract the `# Title` text. Fall back to "—" if unreadable.

2. **Transport reuse**: Create transports via `create_transport(target_config)` from `zsiga/transport.py`. For local targets, `LocalTransport` is used (subprocess). This ensures SSH targets are scanned correctly.

3. **Current change matching**: Read `data/daemon_state.json` to get `current_change` and `current_phase`. Match `current_change` against proposal `id` field. Highlight matching row with amber left border and phase badge.

4. **HTML structure**: Table-based rendering consistent with existing dashboard patterns (Phase Performance table). Uses existing CSS classes (`section`, `meta`).

5. **Placement**: Insert `{proposal_queue_section}` between `{daemon_section}` and the stats grid / Phase Performance section in the `_render()` template string.

6. **Error resilience**: Wrap `_render_proposal_queue()` in try/except (like existing `_render_daemon_status()`) so queue scanning failures don't break the entire dashboard.

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/metrics/dashboard.py` | Add `_render_proposal_queue()` function; call it in `_render()`; insert into HTML template |

## Files NOT Modified

- `zsiga/daemon.py` — no changes needed, daemon_state.json already provides current_change/current_phase
- `zsiga/intake/scanner.py` — reused as-is
- `zsiga/transport.py` — reused as-is
- `site/dashboard.html` — generated file, updated automatically by `generate_dashboard()`
