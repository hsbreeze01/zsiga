# Spec: Phase Token Cap Configuration

## Requirement
Each pipeline phase SHALL have a configurable token cap that limits total token consumption for that phase.

### Scenario: Phase within cap
- Given: phase "enrich" with phase_cap=400000
- When: enrich phase completes having used 333K tokens
- Then: phase completes normally, no cap warning

### Scenario: Phase exceeds cap
- Given: phase "implement" with phase_cap=800000
- When: implement phase reaches 810K tokens at turn 15
- Then: phase terminates with CAP_EXCEEDED, warning logged, next phase (review) starts normally

### Scenario: Cap disabled
- Given: phase with phase_cap=0 (default)
- When: phase runs
- Then: no cap enforcement, only total_budget applies

### Scenario: Cap values from config
- Given: zsiga.yaml with `phase_token_caps: {enrich: 300000}`
- When: PipelineConfig loads
- Then: enrich phase uses 300000 cap instead of default 400000
