Write the review to the file directly.

<write_file>
<path>/home/zsiga/repo/openspec/changes/dashboard-add-feedback-loop-metrics/review.md</path>
<content>Verdict: ISSUES_FOUND

Issues:
1. [CRITICAL] Missing "No data yet" fallback in rendering — The spec requires that when no injection data is available, the card SHALL show "No injection data yet". The test `test_no_crash_on_empty_data` mocks all metric functions to return zeros, but the actual rendering function `_render_feedback_loop` is not shown in the diff, and the test only checks "does not crash" — it does NOT assert that the string "No injection data yet" appears. Similarly for the "No auto-proposals yet", "No self-assessments recorded", and "No learnings yet" fallback strings. The spec explicitly requires "No learnings yet", "No injection data yet", "No auto-proposals yet", and "No self-assessments recorded" as distinct fallback messages, but the test only checks for generic card titles (e.g., "Injection Rate" appears) — not the empty-state fallback text. This means the empty-state requirements are not verifiably covered.

2. [SUGGESTION] Malformed JSON in learnings file silently skipped — The `compute_learnings_health` function (not shown in diff, but tested) silently skips lines that are not valid JSON. This is fine, but the test `test_malformed_json_skipped` writes a line "not json\n" without checking if the function logs or warns. Consider adding a warning log for malformed entries to aid debugging. (Found in tests/test_feedback_loop_metrics.py line ~137-149)</content>
</write_file>