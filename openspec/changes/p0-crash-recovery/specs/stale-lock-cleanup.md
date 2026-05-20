# Spec: Stale Lock PID Cleanup

## ADDED Requirements

### REQ-LOCK-01: Detect and Clean Stale Lock Files

When `acquire_lock()` finds an existing lock file with a PID that is no longer
alive, it SHALL clean up the stale lock and re-acquire it instead of failing.

#### Scenario: Stale lock from dead process

- **Given** `data/lock.pid` exists containing PID `12345`
- **And** PID `12345` is not running (process does not exist)
- **When** `acquire_lock()` is called
- **Then** the stale lock file SHALL be removed
- **And** a new lock SHALL be acquired with the current PID
- **And** a warning SHALL be printed: `"⚠️ Stale lock detected (dead PID 12345), cleaning up"`

#### Scenario: Active lock from running process

- **Given** `data/lock.pid` exists containing PID `12345`
- **And** PID `12345` is running
- **When** `acquire_lock()` is called
- **Then** the lock SHALL NOT be acquired
- **And** the existing error message SHALL be shown: `"❌ Another zsiga daemon is running (PID 12345)"`

#### Scenario: Lock file with non-numeric content

- **Given** `data/lock.pid` exists containing `"garbage"`
- **When** `acquire_lock()` is called
- **Then** the stale lock SHALL be treated as invalid and cleaned up
- **And** a new lock SHALL be acquired
