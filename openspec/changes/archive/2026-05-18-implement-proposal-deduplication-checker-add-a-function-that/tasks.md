# Tasks: Proposal Deduplication Checker

## Group 1: Core Module

- [x] 1.1 Create `zsiga/pipeline/dedup.py` with `ArchivedProposal` and `DuplicateMatch` dataclasses, plus pure functions: `normalize` (lowercase, collapse whitespace, strip `# Proposal:` prefix), `compute_similarity` (Jaccard on word sets), `load_archived_proposals` (scan archive dir, read each proposal.md), and `check_duplicates` (orchestrate all of the above, filter by threshold, sort by score descending)

## Group 2: Tests

- [x] 2.1 Create `tests/test_dedup.py` with tests covering all PDC-01 through PDC-05 scenarios: load archived proposals (multiple/empty/missing-proposal), compute similarity (identical/different/partially-similar), check duplicates (exact-duplicate/multiple-above-threshold/no-duplicates/empty-archive/custom-threshold), normalize (whitespace/case/header-prefix), and determinism (consistent-results-across-runs)
