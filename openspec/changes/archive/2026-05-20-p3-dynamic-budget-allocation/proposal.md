# Proposal: P3 Dynamic Budget Allocation by Task Type

## Summary

Allocate different token budgets based on task type instead of flat 600K.

## Implementation

### 1. Budget profiles in zsiga.yaml
- fix: 300K, implementation: 600K, cross_project: 200K, self_modify: 800K
### 2. Profile selection by intent_type + project + cross_project flag
### 3. Per-profile stats in compute_budget_stats()

## Constraints
- Scope: project=zsiga
- Depends on P1 (value-based budget + statistics)
