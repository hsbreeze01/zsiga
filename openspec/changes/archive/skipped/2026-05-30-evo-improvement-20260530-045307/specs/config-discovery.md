# config-discovery

## ADDED Requirements

### Requirement: config file discovery

`_find_config` SHALL search candidate paths in order and return the first
existing file, or raise `FileNotFoundError` if none exist.

#### Scenario: finds config in current directory

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** a file named `zsiga.yaml` exists in the current working directory
- **When** `_find_config()` is called
- **Then** the returned path SHALL be `Path("zsiga.yaml")`

#### Scenario: finds config in home directory when cwd has none

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory and a file at
  `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** the returned path SHALL equal `Path.home() / ".zsiga" / "zsiga.yaml"`

#### Scenario: raises FileNotFoundError when no config exists anywhere

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory and no `zsiga.yaml` in `~/.zsiga/`
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError`

