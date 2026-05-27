# Spec: SSHTransport tempfile.mktemp Deprecation Fix

## ADDED Requirements

### Requirement: SSHTransport SHALL NOT use deprecated tempfile.mktemp

`SSHTransport._ensure_control` currently uses `tempfile.mktemp(prefix="zsiga_ssh_")`
to generate a control socket path. `tempfile.mktemp` is deprecated since Python 3.12
due to a TOCTOU race condition: the filename is predictable and the file is not
created atomically, allowing an attacker to pre-create the path.

The implementation SHALL replace `tempfile.mktemp` with a secure alternative that
produces non-predictable paths (e.g., `secrets.token_hex`, `uuid4`, or
`tempfile.mkdtemp`-based approach). The public API and behavior of `SSHTransport`
SHALL remain unchanged — this is a security hardening fix only.

#### Scenario: ensure-control-does-not-use-mktemp

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** the source code of SSHTransport._ensure_control
- **When** the source is inspected for the string "mktemp"
- **Then** the string "mktemp" SHALL NOT appear in the method source

#### Scenario: control-path-is-in-system-temp-dir

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** an SSHTransport instance with host "example.com" and subprocess.run
  mocked to do nothing
- **When** _ensure_control is called
- **Then** the resulting _control_path SHALL start with the system temp directory
  (i.e. tempfile.gettempdir())

#### Scenario: two-transports-get-different-control-paths

- **testable**: true
- **target**: zsiga/transport.py::SSHTransport._ensure_control

- **Given** two SSHTransport instances with host "host1" and "host2" and
  subprocess.run mocked to do nothing
- **When** _ensure_control is called on both
- **Then** the two _control_path values SHALL be different strings
