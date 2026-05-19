# Domain Glossary Cache

## ADDED Requirements

### REQ-GL-01: Glossary module SHALL extract project terminology

A new module `pipeline/glossary.py` SHALL scan a target project and extract
domain-specific terminology (class names, important function names, config keys,
database table names) into a structured glossary.

#### Scenario: First-time glossary extraction

- Given a project at `/path/to/stockshark` with no existing glossary cache
- When `extract_glossary(target_path, transport)` is called
- Then the module SHALL:
  1. Scan Python source files (excluding venv, __pycache__, .git)
  2. Extract: top-level class names, public function names (not `_` prefixed),
     route decorator paths, config key names
  3. Return a `Glossary` object containing categorized entries
  4. Cache the result to `memory/glossary/<project_name>.json`

#### Scenario: Glossary cache hit

- Given a glossary cache file `memory/glossary/stockshark.json` exists and is
  less than 24 hours old
- When `load_glossary(project_name)` is called
- Then it SHALL return the cached glossary without re-scanning the project

#### Scenario: Glossary cache expiry

- Given a glossary cache file is older than 24 hours
- When `load_glossary(project_name)` is called
- Then it SHALL re-extract the glossary and update the cache

### REQ-GL-02: Glossary SHALL integrate with project context

#### Scenario: Enricher uses glossary

- Given a glossary exists for the target project
- When `build_project_context()` is called in `pipeline/project_context.py`
- Then the glossary summary SHALL be appended as a "## Domain Glossary" section
- And the section SHALL list the top 30 most relevant terms grouped by category

### REQ-GL-03: Glossary SHALL persist to memory/glossary/

#### Scenario: Glossary persistence

- Given `extract_glossary()` completes successfully
- Then the glossary JSON SHALL be written to `memory/glossary/<project_name>.json`
- And the JSON format SHALL be: `{"project": "<name>", "extracted_at": "<iso>", "entries": [{"name": "...", "category": "class|function|route|config", "file": "..."}]}`
