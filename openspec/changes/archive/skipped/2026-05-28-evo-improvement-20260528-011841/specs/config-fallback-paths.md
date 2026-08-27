# config-fallback-paths

Behavioural spec for `_find_config()` home-directory fallback and precedence logic.

## ADDED Requirements

### Requirement: config-find-home-fallback

`_find_config()` SHALL search `zsiga.yaml` in the current working directory first,
then in `~/.zsiga/zsiga.yaml`. If only the home-directory candidate exists,
it SHALL return that path.

#### Scenario: Falls back to home directory when cwd has no config

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory with no `zsiga.yaml` file in it, used as cwd,
  AND `~/.zsiga/zsiga.yaml` exists (simulated via monkeypatch of `Path.home()`)
- **When** `_find_config()` is called
- **Then** the returned `Path` SHALL point to `~/.zsiga/zsiga.yaml` and
  `result.exists()` SHALL be `True`

#### Scenario: Prefers cwd config over home config

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing `zsiga.yaml`,
  AND `~/.zsiga/zsiga.yaml` also exists (simulated),
  AND cwd is set to the temporary directory
- **When** `_find_config()` is called
- **Then** the returned `Path` SHALL be `Path("zsiga.yaml")` (cwd-relative),
  NOT the home-directory path
