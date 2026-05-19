# Dashboard TODO Card

## ADDED Requirements

### REQ-DC-01: Dashboard SHALL render active todo progress section

The dashboard generator SHALL include a "Todo Progress" section that displays
all persisted todo lists found under the project's `data/todos/` directory.

#### Scenario: No active todos

- Given no todo JSON files exist in `data/todos/`
- When `generate_dashboard()` is called
- Then the dashboard HTML SHALL NOT render the Todo Progress section
  (it is omitted entirely, not shown empty)

#### Scenario: Active todos exist

- Given a todo JSON file `data/todos/change-xyz.json` exists containing 5 items
  (2 completed, 1 in_progress, 2 pending)
- When `generate_dashboard()` is called
- Then the dashboard SHALL render a "📋 Todo Progress" section showing:
  - The change name derived from the filename
  - A summary: "2/5 completed (40%)"
  - Each todo item with status icon (✅ completed, 🔄 in_progress, ⬜ pending, 🚫 cancelled, 🔒 blocked)
  - A progress bar reflecting completion percentage

### REQ-DC-02: Todo data aggregation SHALL scan data/todos/

#### Scenario: Multiple todo lists

- Given three todo files exist: `data/todos/change-a.json`, `data/todos/change-b.json`, `data/todos/change-c.json`
- When dashboard generation reads todo data
- Then it SHALL aggregate all lists and display the most recent 5 lists
  sorted by file modification time (newest first)

### REQ-DC-03: Todo card styling SHALL match existing dashboard theme

#### Scenario: Visual consistency

- Given the todo section is rendered
- Then the card SHALL use the existing `.milestone`, `.criterion`, `.progress`
  CSS classes from the dashboard stylesheet
- And no new CSS classes or external stylesheets SHALL be introduced
