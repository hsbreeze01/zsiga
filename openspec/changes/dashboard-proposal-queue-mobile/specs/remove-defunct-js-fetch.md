# Spec: remove-defunct-js-fetch

## REMOVED Requirements

### Requirement: No client-side fetch to /api/status.json

The dashboard HTML SHALL NOT contain any JavaScript `fetch()` call targeting `/api/status.json`. This endpoint does not exist on the server, so such calls always fail.

#### Scenario: Fetch call removed from script block
- **Given** the dashboard HTML source (template or Python-generated)
- **When** searched for the string `/api/status.json`
- **Then** no matches SHALL be found

---

### Requirement: No updateQueueSection function

The dashboard HTML SHALL NOT contain a JavaScript function named `updateQueueSection` (or similar) that attempts to dynamically populate a queue section from a non-existent API.

#### Scenario: updateQueueSection function removed
- **Given** the dashboard HTML source (template or Python-generated)
- **When** searched for the string `updateQueueSection`
- **Then** no matches SHALL be found

---

### Requirement: No empty queue-section placeholder div

The dashboard HTML SHALL NOT contain an empty `<div id="queue-section">` (or similar empty placeholder) element. The Proposal Queue panel is now rendered server-side by Python.

#### Scenario: Empty queue div removed
- **Given** the dashboard HTML source (template or Python-generated)
- **When** searched for `id="queue-section"`
- **Then** no matches SHALL be found

---

### Requirement: No static proposal_queue_section placeholder

The dashboard rendering logic SHALL NOT use a `{proposal_queue_section}` placeholder variable that is substituted into the template. Instead, the full queue panel HTML SHALL be rendered directly by Python.

#### Scenario: Placeholder variable removed from rendering
- **Given** the Python dashboard rendering code
- **When** searched for the string `proposal_queue_section`
- **Then** no matches SHALL be found
