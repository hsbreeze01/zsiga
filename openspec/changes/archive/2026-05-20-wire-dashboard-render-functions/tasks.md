# Tasks: Dashboard Render Function Wiring

## Group 1: Wire functions into _render()

1.1 - [x] Read `_render()` function in `dashboard.py` to map exact insertion points (hero div end, grid start, Phase Performance end, Resource Usage start, `<head>` section, `<body>` start) — 1 round

1.2 - [x] Wire all 4 integrations into `_render()`: (a) add `daemon_section = _daemon_status_section()` before grid + insert `{daemon_section}`, (b) add `failure_section = _failure_diagnosis_section()` between Phase Performance and Resource Usage + insert `{failure_section}`, (c) add `compute_rolling_rates` import + call + `_sparkline_html()` and insert sparkline card, (d) add `<meta http-equiv="refresh" content="60">` in head and auto-refresh indicator at body start — 2 rounds

1.3 - [x] Run `ruff check` + `pytest` to validate; fix any lint or test failures — 1 round

1.4 - [x] Verify `site/dashboard.html` is regenerated with all 4 new sections by running `generate_dashboard()` and inspecting output — 1 round
