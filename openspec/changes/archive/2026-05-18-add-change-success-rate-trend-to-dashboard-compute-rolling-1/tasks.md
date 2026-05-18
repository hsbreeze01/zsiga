# Tasks: Change Success Rate Trend

## 1. Rolling Rate Computation

- [ ] **1.1** Add `compute_rolling_rates(changes, window=10)` to `zsiga/metrics/collector.py`
  - For each change index, compute success rate of the preceding `window` changes (or growing window if fewer than `window` total so far)
  - Return `list[float]` of percentages rounded to 1 decimal
  - Handle edge case: empty list returns `[]`

## 2. Sparkline Rendering

- [ ] **2.1** Add `_sparkline_html(rates)` to `zsiga/metrics/dashboard.py`
  - Take last 20 data points
  - Linearly map to Unicode block chars `▁▂▃▄▅▆▇█`
  - Wrap each char in `<span>` with `class="trend-down"` if rate[i] < rate[i-1]
  - Handle edge cases: empty list → return "—", all equal → use `▄`
  - Add `.trend-down { color: #ef4444; }` to the `<style>` block in `_render()`

- [ ] **2.2** Add sparkline card to the grid in `_render()` in `zsiga/metrics/dashboard.py`
  - Place after the "✅ Verify Rate" card
  - Label: `📈 Success Trend`
  - Value: rendered sparkline HTML from `_sparkline_html()`
  - Meta line: `latest: {last_rate}%`

## 3. Tests

- [ ] **3.1** Create `tests/test_success_rate_trend.py` with unit tests
  - Test `compute_rolling_rates` with full window, growing window, empty input, single change
  - Test `_sparkline_html` with normal data, all-equal data, empty data, downward trend detection
  - Verify sparkline card appears in rendered dashboard HTML
