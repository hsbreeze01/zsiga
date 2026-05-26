Verdict: PASS
Layer 1: vacuous — all scenarios demoted to testable=false; no mechanical pytest run
Completeness: ✓ All 14 scenarios across 4 requirements in phase-cap-budget.md are implemented in code and covered by the test file. The phase-cap-config.md higher-level integration scenarios are outside the scope of Group 1 tasks (TokenBudget-level only).
Correctness: ✓ phase_cap attribute is a plain public attribute (default 0, readable/writable). cap_exceeded logic correctly guards with `phase_cap > 0`. reset_phase() resets only `_used`, preserving `_extended`, `_consecutive_stale`, and `phase_cap`. Backward compatibility maintained — session_exceeded logic unchanged, new key added harmlessly.
Coherence: ✓ Implementation follows existing TokenBudget patterns (attribute style, method structure, return-dict construction). Tests map 1:1 to spec scenarios.
