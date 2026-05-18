# Proposal Deduplication Checker

## ADDED Requirements

### Requirement: PDC-01 — Load Archived Proposals

The system SHALL provide a function that loads all proposal texts from
archived openspec changes in a given `archive/` directory.

#### Scenario: Multiple archived proposals found

- **Given** an openspec `changes/archive/` directory containing 5 archived
  change subdirectories, each with a `proposal.md`
- **When** the load function is called with the archive directory path
- **Then** it SHALL return a list of entries, each containing at minimum the
  change `id` (directory name) and the `proposal_text` content

#### Scenario: Empty archive directory

- **Given** an openspec `changes/archive/` directory that is empty or does
  not exist
- **When** the load function is called
- **Then** it SHALL return an empty list without error

#### Scenario: Archived change missing proposal.md

- **Given** an archived change subdirectory that contains only `design.md`
  but no `proposal.md`
- **When** the load function is called
- **Then** that subdirectory SHALL be skipped (not included in the result)

### Requirement: PDC-02 — Compute Similarity Score

The system SHALL provide a function that computes a text similarity score
between a new proposal text and an archived proposal text, returning a
float between 0.0 (completely dissimilar) and 1.0 (identical).

#### Scenario: Identical proposals

- **Given** a new proposal text that is identical to an archived proposal text
- **When** the similarity function is called
- **Then** it SHALL return a score of 1.0

#### Scenario: Completely different proposals

- **Given** a new proposal about "implement retry backoff" and an archived
  proposal about "add dashboard widget"
- **When** the similarity function is called
- **Then** it SHALL return a score below 0.3

#### Scenario: Partially similar proposals

- **Given** a new proposal about "implement change conflict detector" and an
  archived proposal about "implement change conflict resolver"
- **When** the similarity function is called
- **Then** it SHALL return a score between 0.3 and 0.9

### Requirement: PDC-03 — Find Potential Duplicates

The system SHALL provide a `check_duplicates` function that compares a new
proposal text against all archived proposals and returns a list of potential
duplicates with their similarity scores, filtered by a configurable threshold.

#### Scenario: Exact duplicate found in archive

- **Given** a new proposal text and an archive containing a proposal with
  identical content (score ≥ threshold)
- **When** `check_duplicates(new_text, archive_dir)` is called
- **Then** it SHALL return a list containing one `DuplicateMatch` entry with
  `score = 1.0` and the matching change `id`

#### Scenario: Multiple similar proposals found

- **Given** a new proposal text and an archive containing 3 proposals with
  scores 0.85, 0.45, and 0.12 (threshold default 0.5)
- **When** `check_duplicates(new_text, archive_dir)` is called
- **Then** it SHALL return only the proposal with score 0.85 (above threshold),
  sorted by score descending

#### Scenario: No duplicates found

- **Given** a new proposal text and an archive where all proposals score below
  the threshold
- **When** `check_duplicates(new_text, archive_dir)` is called
- **Then** it SHALL return an empty list

#### Scenario: Empty archive

- **Given** a new proposal text and an empty archive directory
- **When** `check_duplicates(new_text, archive_dir)` is called
- **Then** it SHALL return an empty list without error

#### Scenario: Custom threshold

- **Given** a new proposal text and an archive containing proposals with
  scores 0.85 and 0.45
- **When** `check_duplicates(new_text, archive_dir, threshold=0.9)` is called
- **Then** only the proposal with score ≥ 0.9 SHALL be returned

### Requirement: PDC-04 — Text Normalization

The system SHALL normalize proposal texts before comparison to ensure
robust similarity measurement.

#### Scenario: Whitespace normalization

- **Given** two proposal texts that differ only in extra whitespace, newlines,
  or indentation
- **When** similarity is computed
- **Then** the score SHALL be 1.0

#### Scenario: Case normalization

- **Given** two proposal texts that differ only in letter casing
- **When** similarity is computed
- **Then** the score SHALL be 1.0

#### Scenario: Header prefix stripped

- **Given** two proposals where one starts with "# Proposal: " prefix and the
  other does not, but the body is otherwise identical
- **When** similarity is computed
- **Then** the score SHALL be ≥ 0.9

### Requirement: PDC-05 — Deterministic and No External Dependencies

The deduplication checker SHALL be a pure Python module with no external
ML/NLP dependencies (no scikit-learn, no transformers, no numpy).

#### Scenario: Word-overlap based similarity

- **Given** the similarity function implementation
- **When** it is invoked
- **Then** it SHALL use token/word-overlap based text comparison (e.g.,
  Jaccard similarity on word sets) without requiring any dependency beyond
  the Python standard library

#### Scenario: Consistent results across runs

- **Given** the same new proposal text and the same archive
- **When** `check_duplicates` is called twice
- **Then** both calls SHALL return identical scores and duplicate lists
