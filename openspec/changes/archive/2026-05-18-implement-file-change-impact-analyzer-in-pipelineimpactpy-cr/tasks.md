# Tasks: File Change Impact Analyzer

## 1. Core Module Implementation

- [ ] **1.1** Create `zsiga/pipeline/impact.py` — data models (`ImpactReport`), import graph builder (`_build_import_graph`), downstream resolver (`_find_downstream`), test scope matcher (`_find_test_scope`), risk classifier (`_classify_risk`), and `analyze_impact` entry point

## 2. Test Suite

- [ ] **2.1** Create `tests/test_impact.py` — test import graph construction, downstream dependency discovery (direct + transitive), test scope estimation (import match + naming convention), risk level classification (low/medium/high), edge cases (empty input, non-existent files, missing test coverage)
