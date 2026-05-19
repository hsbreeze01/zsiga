# Delta Spec: Learnings Search

## ADDED Requirements

### Requirement: Keyword Search over Learnings

The memory module SHALL provide a `search_learnings` function that performs keyword-based search over all entries in `learnings.jsonl`.

#### Scenario: Search with multiple keywords returns ranked results

- Given the `learnings.jsonl` file contains entries with titles and takeaways
- When `search_learnings` is called with a list of keywords `["pipeline", "implement"]`
- Then the function SHALL return all entries where at least one keyword appears in any of the searchable fields (`title`, `context`, `takeaway`)
- And results SHALL be ranked by relevance score, where entries matching more unique keywords score higher

#### Scenario: Search with no matching keywords returns empty list

- Given the `learnings.jsonl` file contains entries
- When `search_learnings` is called with keywords that match no entries
- Then the function SHALL return an empty list

#### Scenario: Search on missing learnings file returns empty list

- Given the `learnings.jsonl` file does not exist
- When `search_learnings` is called with any keywords
- Then the function SHALL return an empty list without raising an exception

### Requirement: Pattern Key Filtering

The `search_learnings` function SHALL accept an optional `pattern_key` parameter to filter results to entries matching a specific pattern key.

#### Scenario: Filter by exact pattern key

- Given the `learnings.jsonl` file contains entries with various `pattern_key` values
- When `search_learnings` is called with `pattern_key="pipeline.fail.implement"`
- Then the function SHALL return only entries whose `pattern_key` exactly matches the provided value

#### Scenario: Combined keyword search and pattern key filter

- Given the `learnings.jsonl` file contains entries
- When `search_learnings` is called with keywords and a `pattern_key`
- Then the function SHALL return only entries that both match the keywords AND have the specified `pattern_key`

### Requirement: Relevance Ranking

The search function SHALL rank results by the number of unique keyword matches across searchable fields, breaking ties by recency (most recent first).

#### Scenario: Entries with more keyword matches rank higher

- Given entry A matches 3 keywords and entry B matches 1 keyword
- When search results are returned
- Then entry A SHALL appear before entry B in the result list

### Requirement: Search Result Format

Each result returned by `search_learnings` SHALL be a dictionary containing the original entry fields plus a computed `_score` field indicating the number of matched keywords.

#### Scenario: Result includes score

- Given a matching entry exists in `learnings.jsonl`
- When `search_learnings` returns results
- Then each result dict SHALL contain all original JSON fields from the entry
- And each result SHALL include a `_score` field with an integer value >= 1

### Requirement: Keyword Matching is Case-Insensitive

The keyword search SHALL be case-insensitive, matching keywords against entry fields regardless of case.

#### Scenario: Case-insensitive match

- Given an entry has `takeaway` value `"Failed at implement: lint error"`
- When `search_learnings` is called with keywords `["LINT"]`
- Then the entry SHALL be included in the results
