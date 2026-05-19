# Delta Spec: Dashboard Auto-Refresh

## ADDED Requirements

### Requirement: Page Auto-Refresh

The dashboard HTML SHALL include a `<meta http-equiv="refresh" content="60">` tag in the `<head>` section to automatically reload the page every 60 seconds.

The dashboard SHALL display a visible "Auto-refresh: 60s" indicator in the header area, positioned near the page title.

#### Scenario: Auto-refresh meta tag present

- **Given** the dashboard HTML is generated
- **When** the page is opened in a browser
- **Then** the `<head>` SHALL contain `<meta http-equiv="refresh" content="60">`
- **And** the page SHALL display "Auto-refresh: 60s" text in the header area
