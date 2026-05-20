# Tasks: Self-Reflection Loop

## 1. Reflector Core

- [x] **Implement `zsiga/intake/reflector.py`** — Signal dataclass, Reflector class with `scan_signals(base_path)`, `should_propose(signal, base_path)`, `generate_proposal(signal, base_path)`, and `run(base_path)` entry point. Includes all three signal type scanners (recurring_failure from learnings.jsonl, metric_degradation from stats/snapshot, recurring_root_cause from reverted changes + diagnosis.md), dedup logic against `data/reflector_history.jsonl`, rate limiting (≤3/24h), non-interference check for external proposals, and proposal directory + `proposal.md` creation with string templating.

## 2. Daemon Integration

- [x] **Modify `zsiga/daemon.py`** — Import Reflector, add self-reflection block in the daemon loop after `run_cycle()` and before `generate_dashboard()`. Trigger condition: `idle_cycles >= 3 and processed_count == 0`. Wrap in try/except, log warning on error. If proposals generated, `continue` to next cycle for immediate pickup.

## 3. Tests

- [x] **Implement `tests/test_reflector.py`** — Test suite covering: (a) scan_signals for each of the 3 signal types with fixture data, (b) should_propose dedup within 24h, (c) should_propose rate limit at 3/24h, (d) should_propose respects external proposal priority, (e) generate_proposal writes correct directory name and proposal.md content, (f) run orchestrates scan→filter→generate correctly, (g) error resilience (missing files, corrupted JSONL). Use tmp_path fixtures for all filesystem operations.
