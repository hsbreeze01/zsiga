# Spec: SRE Intent Routing

## ADDED Requirements

### Requirement: SRE Intent Category Detection

The intent router SHALL recognize an `sre` intent category distinct from `code`. When the user input contains SRE-triggering keywords, the router MUST return `sre` as the intent type.

**Triggering keywords (Chinese and English):**
- 服务, 重启, 健康, 清理, 磁盘, 宕机, 日志, 进程, 监控
- service, restart, health, cleanup, disk, downtime, log, process, monitor, diagnose

#### Scenario: Detect SRE intent from Chinese keywords

- **testable**: true
- **target**: zsiga/intent_router.py::detect_intent
- **Given** the user input contains one or more SRE triggering keywords (e.g., "服务重启失败了")
- **When** `detect_intent` is called with that input
- **Then** the returned intent category SHALL be `"sre"`

#### Scenario: Detect SRE intent from English keywords

- **testable**: true
- **target**: zsiga/intent_router.py::detect_intent
- **Given** the user input contains English SRE keywords (e.g., "check disk usage on the server")
- **When** `detect_intent` is called with that input
- **Then** the returned intent category SHALL be `"sre"`

### Requirement: SRE and Code Intent Mutual Exclusivity

SRE intent and code intent MUST be mutually exclusive. When SRE keywords are detected, the router SHALL NOT return `"code"` even if the input also contains code-related terms.

#### Scenario: SRE keywords take precedence over ambiguous input

- **testable**: true
- **target**: zsiga/intent_router.py::detect_intent
- **Given** the user input contains both SRE keywords (e.g., "磁盘") and code keywords (e.g., "修复代码")
- **When** `detect_intent` is called with that input
- **Then** the returned intent SHALL be `"sre"`, not `"code"`

#### Scenario: Pure code input returns code intent

- **testable**: true
- **target**: zsiga/intent_router.py::detect_intent
- **Given** the user input contains only code-related terms (e.g., "修复这个函数的bug")
- **When** `detect_intent` is called with that input
- **Then** the returned intent SHALL be `"code"`, not `"sre"`

### Requirement: Default Intent Fallback

When no SRE or code keywords are matched, the router SHALL return `"code"` as the default intent to preserve backward compatibility.

#### Scenario: Unrecognized input defaults to code intent

- **testable**: true
- **target**: zsiga/intent_router.py::detect_intent
- **Given** the user input contains no recognizable SRE or code keywords (e.g., "你好")
- **When** `detect_intent` is called with that input
- **Then** the returned intent SHALL be `"code"`

### Requirement: SRE Keywords Set Extensibility

The SRE triggering keyword set SHALL be defined as a module-level constant (list or set) so it can be inspected and extended without modifying the detection function body.

#### Scenario: SRE keywords are accessible as a module constant

- **testable**: true
- **target**: zsiga/intent_router.py::SRE_KEYWORDS
- **Given** the intent_router module is imported
- **When** `SRE_KEYWORDS` is accessed
- **Then** it SHALL be a non-empty collection containing at minimum: "服务", "重启", "健康", "清理", "磁盘", "宕机", "日志", "进程", "监控"
