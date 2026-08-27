# config-load-error-paths.md

## ADDED Requirements

### Requirement: `load_config` path resolution SHALL accept an explicit path or discover one

When called with `path` argument, `load_config` SHALL use that path directly.
When called without `path`, it SHALL delegate to `_find_config()`.

#### Scenario: uses explicit path when provided

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config file at an arbitrary temporary path
- **When** `load_config(path=str(that_path))` is called
- **Then** it SHALL successfully parse and return a `ZsigaConfig`

#### Scenario: raises FileNotFoundError when no path and no config found

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** no `zsiga.yaml` in the current directory or `~/.zsiga/`
- **When** `load_config()` is called without a path argument
- **Then** it SHALL raise `FileNotFoundError`

---

### Requirement: `load_config` SHALL raise on malformed YAML

When the YAML content cannot be parsed, `load_config` SHALL propagate the parse error.

#### Scenario: raises on invalid YAML syntax

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a file containing invalid YAML (`": broken [`)
- **When** `load_config(path=str(that_file))` is called
- **Then** it SHALL raise an exception (YAML parse error)

#### Scenario: raises ConfigValidationError for invalid config values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML file with valid syntax but missing required fields (e.g. `llm.api_key` is empty)
- **When** `load_config(path=str(that_file))` is called
- **Then** it SHALL raise `ConfigValidationError`

---

### Requirement: `load_config` SHALL resolve environment variables in loaded config

After loading the raw YAML, `load_config` SHALL pass it through `_resolve_env_vars`
before constructing config objects.

#### Scenario: resolves env vars in api_key field

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** environment variable `TEST_API_KEY` is set to `"resolved-key"` and a YAML config file with `api_key: "${TEST_API_KEY}"`
- **When** `load_config(path=str(config_file))` is called
- **Then** the returned `ZsigaConfig.llm.api_key` SHALL equal `"resolved-key"`

