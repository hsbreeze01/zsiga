# Spec: LocalTransport Error Handling

## MODIFIED Requirements

### Requirement: LocalTransport.run_shell SHALL handle subprocess exceptions gracefully

`LocalTransport.run_shell` MUST catch `subprocess.TimeoutExpired` and generic
`Exception` and return a structured error dict — consistent with the contract
already established by `SSHTransport.run_shell`.

This ensures both transport implementations share the same error-return
contract so callers need not special-case `LocalTransport`.

#### Scenario: local-transport-timeout-returns-error-dict

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a LocalTransport instance
- **When** run_shell is called and subprocess.run raises subprocess.TimeoutExpired
- **Then** the return value is a dict with exit_code == -1, stdout == "", and
  stderr containing the substring "Timeout"

#### Scenario: local-transport-oserror-returns-error-dict

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a LocalTransport instance
- **When** run_shell is called and subprocess.run raises an OSError with
  message "No space left on device"
- **Then** the return value is a dict with exit_code == -1, stdout == "",
  and stderr equal to str(exception)

#### Scenario: local-transport-normal-execution-unchanged

- **testable**: true
- **target**: zsiga/transport.py::LocalTransport.run_shell

- **Given** a LocalTransport instance
- **When** run_shell is called and subprocess.run completes normally with
  returncode 42, stdout "out", stderr "err"
- **Then** the return value is {"exit_code": 42, "stdout": "out", "stderr": "err"}
