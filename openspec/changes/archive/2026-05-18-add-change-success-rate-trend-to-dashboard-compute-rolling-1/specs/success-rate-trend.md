# Delta Spec: Change Success Rate Trend

## ADDED Requirements

### Requirement: Rolling Success Rate Computation

The system SHALL compute a rolling-window success rate from the ordered change history.

- The window size MUST be 10 changes.
- For each position *i* ≥ window_size in the change list (ordered by `id ASC`), the system SHALL calculate the success rate as `(number of successes in changes[i-10..i]) / 10 * 100`, rounded to one decimal place.
- If fewer than 10 changes exist in total, the system SHALL still produce data points for every position where at least 1 change exists, using a growing window from change index 0 to the current position.
- The computation result SHALL be a list of floats representing success rates over time, one data point per change.

#### Scenario: Enough changes for full window

- **Given** the changes table contains 25 change records ordered chronologically
- **When** the rolling success rate is computed with window size 10
- **Then** the result SHALL contain 25 data points
- **And** data points 0–9 SHALL use a growing window (1 through 10 changes)
- **And** data points 10–24 SHALL each use exactly the preceding 10 changes

#### Scenario: Fewer changes than window size

- **Given** the changes table contains 5 change records
- **When** the rolling success rate is computed
- **Then** the result SHALL contain 5 data points
- **And** each point uses the growing window from change 0 to that index

---

### Requirement: ASCII Sparkline Rendering

The system SHALL render the rolling success rate as an ASCII sparkline string embedded in the dashboard HTML.

- The sparkline MUST use the Unicode block characters `▁▂▃▄▅▆▇█` (U+2581 through U+2588) to represent values from lowest to highest.
- Values MUST be linearly mapped to the 8 sparkline levels based on the min/max of the data set.
- If all values are equal, every character SHALL be `▄` (the midpoint character).
- The sparkline SHALL display at most the last 20 data points to keep the visual compact.

#### Scenario: Normal data spread

- **Given** rolling rates are `[60.0, 70.0, 80.0, 90.0, 100.0]`
- **When** the sparkline is rendered
- **Then** each rate SHALL map to a distinct sparkline character proportional to its position between min (60.0) and max (100.0)

#### Scenario: All values identical

- **Given** all rolling rates are `[80.0, 80.0, 80.0]`
- **When** the sparkline is rendered
- **Then** every sparkline character SHALL be `▄`

---

### Requirement: Downward Trend Highlighting

The dashboard SHALL visually highlight downward trends in the sparkline.

- Any sparkline character whose corresponding rate is lower than the immediately preceding rate SHALL be rendered with the CSS class `trend-down`.
- Characters that are not part of a downward trend SHALL have no special class.
- The `trend-down` style MUST use the color `#ef4444` (the dashboard's existing "bad" red).

#### Scenario: Mixed trend

- **Given** rolling rates for the last 5 positions are `[80.0, 90.0, 70.0, 75.0, 60.0]`
- **When** the sparkline is rendered
- **Then** positions 2 and 4 (values 70.0 and 60.0, both lower than their predecessor) SHALL have class `trend-down`
- **And** positions 0, 1, 3 SHALL have no trend class

#### Scenario: Monotonically increasing

- **Given** rolling rates are `[50.0, 60.0, 70.0, 80.0, 90.0]`
- **When** the sparkline is rendered
- **Then** no characters SHALL have the `trend-down` class

---

### Requirement: Dashboard Sparkline Card

The dashboard SHALL display a new card in the top grid area showing the success rate trend.

- The card label SHALL read "📈 Success Trend".
- The card value area SHALL display the rendered sparkline with per-character trend coloring.
- The card SHALL include a meta line showing the latest rolling rate as a percentage (e.g., "latest: 89.0%").
- The card SHALL be placed after the existing "✅ Verify Rate" card in the grid layout.

#### Scenario: Dashboard generation with sparkline data

- **Given** the system generates the dashboard HTML
- **When** at least one change record exists
- **Then** the rendered HTML SHALL contain a `<div class="card">` element whose label contains "📈 Success Trend"
- **And** the card body SHALL contain a `<span>` element with the sparkline characters
- **And** characters at downward-trend positions SHALL be wrapped in `<span class="trend-down">` elements styled with color `#ef4444`

#### Scenario: No change records

- **Given** the changes table is empty
- **When** the dashboard is generated
- **Then** the sparkline card SHALL still appear with placeholder text "—" and no sparkline characters
