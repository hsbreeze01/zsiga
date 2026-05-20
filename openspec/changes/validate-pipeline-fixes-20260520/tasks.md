# Tasks: validate-pipeline-fixes-20260520

## Group 1: Dashboard Phase Table & Flow Indicator

- [x] 1.1 **Phase table completeness** — Modify `_phase_table` in `zsiga/metrics/dashboard.py` to iterate over all Phase enum values, showing count=0 for phases with no recorded data
- [x] 1.2 **Pipeline flow indicator** — Add a static line below `<h1>` in `site/dashboard.html` showing `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
