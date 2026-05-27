# config-load-robustness

Describes behavioral changes to `zsiga/config.py::load_config` so that
edge-case inputs (empty file, malformed YAML, missing required keys)
produce **descriptive `ValueError`** instead of raw `TypeError`,
`KeyError`, or `yaml.YAMLError`.

These are concrete, observable defects in the current code:
- Line 338: `yaml.safe_load(config_path.read_text())` returns `None` for
  empty files; the subsequent `raw["agent"]` on line 341 raises an opaque
  `TypeError`.
- Line 338: `yaml.safe_load` raises `yaml.YAMLError` on malformed YAML,
  which propagates uncaught.
- Line 341: `raw["agent"]["llm"]` raises bare `KeyError` with no context
  when the required key path is absent.

---

## MODIFIED Requirements

### Requirement: load_config rejects empty or whitespace-only YAML files

`load_config` SHALL raise `ValueError` with a message containing the
substring `"empty"` when the YAML file parses to `None` (i.e. the file
is empty or contains only whitespace).

This replaces the current behavior where `raw["agent"]` raises
`TypeError: 'NoneType' object is not subscriptable`.

#### Scenario: Empty file raises ValueError

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a zero-byte YAML file at a known path
- **When** `load_config(path=<that_path>)` is called
- **Then** it SHALL raise `ValueError` whose message contains `"empty"`

#### Scenario: Whitespace-only file raises ValueError

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML file containing only whitespace (`"   \n\n  "`)
- **When** `load_config(path=<that_file>)` is called
- **Then** it SHALL raise `ValueError` whose message contains `"empty"`

---

### Requirement: load_config wraps malformed YAML errors as ValueError

`load_config` SHALL catch `yaml.YAMLError` raised during parsing and
re-raise it as `ValueError` with a message that contains `"yaml"` or
`"parse"` or `"malformed"`.  The original exception MUST be chained via
`raise ValueError(...) from e`.

This replaces the current behavior where `yaml.YAMLError` propagates
uncaught.

#### Scenario: Malformed YAML raises ValueError not YAMLError

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML file with invalid syntax (e.g. `"{unclosed bracket"`)
- **When** `load_config(path=<that_file>)` is called
- **Then** it SHALL raise `ValueError` (not `yaml.YAMLError`) whose
  message contains `"yaml"` or `"parse"` or `"malformed"`

---

### Requirement: load_config reports missing required keys by name

`load_config` SHALL raise `ValueError` with a descriptive message when
the YAML parses successfully but is missing a required key path.  The
message SHALL contain the name of the missing key (e.g. `"agent"`,
`"llm"`).

This replaces the current behavior where `raw["agent"]` raises bare
`KeyError('agent')`.

#### Scenario: Missing agent key raises ValueError mentioning agent

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML file that parses to
  `{"targets": {"default": {"path": "/tmp"}}}`
- **When** `load_config(path=<that_file>)` is called
- **Then** it SHALL raise `ValueError` whose message contains `"agent"`

#### Scenario: Missing llm subkey under agent raises ValueError mentioning llm

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML file that parses to
  `{"agent": {"provider": "openai"}, "targets": {"default": {"path": "/tmp"}}}`
- **When** `load_config(path=<that_file>)` is called
- **Then** it SHALL raise `ValueError` whose message contains `"llm"`
