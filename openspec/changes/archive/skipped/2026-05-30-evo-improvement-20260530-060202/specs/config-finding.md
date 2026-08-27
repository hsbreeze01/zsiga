# config-finding

## ADDED Requirements

### Requirement: find-config-in-current-directory

`_find_config` SHALL return the path to `zsiga.yaml` in the current working directory when that file exists.

#### Scenario: zsiga-yaml-in-cwd

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing a file named `zsiga.yaml`
- **When** `_find_config()` is called with the current working directory set to that temporary directory
- **Then** it SHALL return a `Path` object pointing to `<tmpdir>/zsiga.yaml`

---

### Requirement: find-config-fallback-to-home

`_find_config` SHALL fall back to `~/.zsiga/zsiga.yaml` when no config file exists in the current working directory but one exists in the user's `.zsiga` directory.

#### Scenario: zsiga-yaml-in-home-zsiga

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** the current working directory does NOT contain `zsiga.yaml`
- **And** `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it SHALL return `Path.home() / ".zsiga" / "zsiga.yaml"`

---

### Requirement: find-config-raises-when-absent

`_find_config` SHALL raise `FileNotFoundError` when no `zsiga.yaml` exists in either the current directory or `~/.zsiga/`.

#### Scenario: no-config-anywhere

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** the current working directory does NOT contain `zsiga.yaml`
- **And** `~/.zsiga/zsiga.yaml` does NOT exist
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError`
