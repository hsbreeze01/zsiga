"""Secret scanning for pre-deliver deterministic verification."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_SECRET_PATTERNS = [
    ("api_key", re.compile(r"(?i)\b(api[_-]?key)\b\s*[:=]\s*['\"]?([A-Za-z0-9._-]{24,})")),
    ("token", re.compile(r"(?i)\b(token)\b\s*[:=]\s*['\"]?([A-Za-z0-9._-]{24,})")),
    ("password", re.compile(r"(?i)\b(password|passwd|pwd)\b\s*[:=]\s*['\"]?([^'\"\s]{12,})")),
    ("secret", re.compile(r"(?i)\b(secret)\b\s*[:=]\s*['\"]?([A-Za-z0-9._-]{24,})")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

_PLACEHOLDER_RE = re.compile(
    r"(?i)(your-|example|placeholder|dummy|fake|test|xxxx|xxx|"
    r"\$\{[A-Z0-9_]+\}|<[^>]+>)"
)


@dataclass
class SecretFinding:
    kind: str
    line_number: int
    excerpt: str


@dataclass
class SecretScanResult:
    findings: list[SecretFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.findings

    def summary(self) -> str:
        if self.passed:
            return "未发现疑似 secret"
        examples = ", ".join(
            f"{f.kind}@+{f.line_number}" for f in self.findings[:5]
        )
        return f"发现 {len(self.findings)} 个疑似 secret: {examples}"


def scan_diff_for_secrets(diff_content: str) -> SecretScanResult:
    findings: list[SecretFinding] = []
    for idx, line in enumerate(diff_content.splitlines(), start=1):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        added = line[1:].strip()
        if not added or _PLACEHOLDER_RE.search(added):
            continue
        for kind, pattern in _SECRET_PATTERNS:
            if pattern.search(added):
                findings.append(
                    SecretFinding(
                        kind=kind,
                        line_number=idx,
                        excerpt=_redact(added[:160]),
                    )
                )
                break
    return SecretScanResult(findings=findings)


def _redact(text: str) -> str:
    return re.sub(
        r"([A-Za-z0-9._-]{6})[A-Za-z0-9._-]{8,}([A-Za-z0-9._-]{4})",
        r"\1…\2",
        text,
    )

