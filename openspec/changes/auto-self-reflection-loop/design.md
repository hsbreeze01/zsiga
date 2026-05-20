# Design: Self-Reflection Loop

## Architecture Decision

Add a **Reflector** module as a new component in `zsiga/intake/`. The Reflector is a **read-only consumer** of existing data sources (learnings, metrics, diagnosis files) and a **producer** of proposals into `openspec/changes/`. It does not modify any existing module.

### Why a separate module, not extend pattern_miner?

- **Single Responsibility**: pattern_miner mines patterns; Reflector decides *what to do about them*. Mixing these concerns would make both harder to test and evolve independently.
- **No risk to existing flows**: pattern_miner, collector, learn.py continue working unchanged. Reflector is additive.

### Why pure-rule, no LLM?

- **Determinism**: self-reflection should produce consistent results for the same inputs. LLM calls introduce non-determinism and cost.
- **Speed**: scanning signals + generating a proposal should complete in < 1 second, which is only possible with string templating.
- **Reliability**: no network dependency means the Reflector cannot fail due to LLM API issues.

## Data Flow

```
                    ┌─────────────────────────┐
                    │   daemon.py run_cycle()  │
                    └────────────┬────────────┘
                                 │
                    idle_cycles >= 3 && processed_count == 0 ?
                                 │
                         Yes ────┴──── No → skip
                                 │
                    ┌────────────▼────────────┐
                    │  Reflector.run(base_path)│
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
    memory/learnings.jsonl  data/stats_       metrics/changes.jsonl
    (pattern_miner output)   snapshot.json    (diagnosis.md files)
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    scan_signals()        │
                    │  → list[Signal]          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  should_propose() filter │
                    │  ↕ data/reflector_       │
                    │    history.jsonl         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  generate_proposal()     │
                    │  → mkdir + proposal.md   │
                    │    under openspec/changes/│
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  daemon continues cycle  │
                    │  → picks up new proposals│
                    └─────────────────────────┘
```

## Signal Data Model

```python
@dataclass
class Signal:
    type: str           # "recurring_failure" | "metric_degradation" | "recurring_root_cause"
    priority: str       # "high" | "medium"
    pattern_key: str    # unique identifier for dedup
    title: str          # human-readable title
    data: dict          # type-specific payload
```

## File Layout

### New Files

| File | Purpose |
|------|---------|
| `zsiga/intake/reflector.py` | Reflector class with scan_signals, should_propose, generate_proposal, run |
| `tests/test_reflector.py` | Unit tests for all Reflector methods |
| `data/reflector_history.jsonl` | Append-only log of generated proposals (created at runtime) |

### Modified Files

| File | Change |
|------|--------|
| `zsiga/daemon.py` | Add ~15 lines: import Reflector, call `reflector.run()` in the idle-cycle branch of the daemon loop, after `run_cycle()` and before `generate_dashboard()` |

### Unchanged Files

- `zsiga/pattern_miner.py` — read only
- `zsiga/learn.py` — read only
- `zsiga/metrics/collector.py` — read only (if exists; stats read from JSON)
- `memory/learnings.jsonl` — read only
- `metrics/changes.jsonl` — read only

## Proposal Naming Convention

```
openspec/changes/auto-{signal_type}-{sanitized_key}-{YYYYMMDD}/proposal.md
```

- `auto-` prefix distinguishes self-generated from external proposals
- `sanitized_key` = `re.sub(r'[^a-zA-Z0-9_-]', '-', pattern_key).lower()`
- Date uses `datetime.now().strftime("%Y%m%d")`
- If a directory with the same name already exists, append `-2`, `-3`, etc.

## Proposal Template

Each `proposal.md` is assembled from string constants mapped to `signal.type`:

- **recurring_failure**: "Fix recurring pipeline failure pattern `{pattern_key}` (seen {count} times)"
- **metric_degradation**: "Investigate and improve `{metric}` (currently at {value}%)"
- **recurring_root_cause**: "Address recurring root cause `{root_cause}` (seen {occurrences} times)"

## Dedup / Rate-Limit Storage

`data/reflector_history.jsonl` — one JSON object per line:

```json
{"timestamp": "2025-01-20T14:30:00", "signal_type": "recurring_failure", "pattern_key": "pipeline-fail-implement", "directory": "auto-recurring_failure-pipeline-fail-implement-20250120"}
```

Query logic:
- Count entries where `timestamp > now - 24h` → enforce rate limit (≤ 3)
- Check `(signal_type, pattern_key)` existence in same window → enforce dedup

## Error Handling

- `reflector.run()` is called inside `try/except` in daemon.py — errors are logged as warnings, never crash the daemon
- Missing data files (e.g., no learnings.jsonl yet) → `scan_signals()` returns empty list
- Corrupted JSON lines → individual line parse failures are skipped with a warning
- Filesystem errors writing proposal → caught and logged
