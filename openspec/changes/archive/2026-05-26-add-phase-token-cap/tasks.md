# Tasks: Phase Token Cap

## Group 1: TokenBudget phase_cap support
- [x] 1.1 Add `phase_cap` attribute to `TokenBudget.__init__` (default 0, publicly readable/writable)
- [x] 1.2 Add `cap_exceeded` boolean to `record()` return dict
- [x] 1.3 Add `reset_phase()` method that resets only `_used`
- [x] 1.4 Write tests for all phase_cap scenarios
