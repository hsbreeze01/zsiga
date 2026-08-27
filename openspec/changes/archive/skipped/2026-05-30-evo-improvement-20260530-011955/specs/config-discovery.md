# config-discovery — Configuration File Discovery

## ADDED Requirements

### Requirement: Config file search path priority

`_find_config()` SHALL search a fixed list of candidate paths in priority order and return the first path that exists on the filesystem.

#### Scenario: Returns current directory config when it exists

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a file named `zsiga.yaml` exists in the current working directory
- **When** `_find_config()` is called
- **Then** it SHALL return `Path("zsiga.yaml")`

#### Scenario: Falls back to home directory config

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** `zsiga.yaml` does NOT exist in the current working directory AND a file at `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it SHALL return `Path.home() / ".zsiga" / "zsiga.yaml"`

#### Scenario: Raises FileNotFoundError when no config found

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** neither `zsiga.yaml` nor `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError` with a message containing "zsiga.yaml not found"
