# Proposal: P2 Intent Accuracy Tracking + Confidence Gate

## Summary

Track intent classification accuracy: record each intent decision + actual outcome, add confidence threshold gate, enable Reflector to detect systematic misclassification.

## Implementation

### 1. intent_accuracy DB table
### 2. Record intent decision in orchestrator after classify()
### 3. Update with actual outcome after _run_phases()
### 4. Confidence gate: < 0.6 → explore first, then re-classify
### 5. Reflector checks intent accuracy in _scan_metric_degradation()

## Constraints
- Scope: project=zsiga
