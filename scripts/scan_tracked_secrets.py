"""Fail CI when repository text contains a likely live credential.

This is a narrow guardrail, not a replacement for secret-manager controls or
history scanning. It reads tracked files and non-ignored untracked files, then
reports the file, line, and rule name—never a matched value.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("gitlab-token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[A-Za-z0-9_-]{35}\b")),
    ("telegram-bot-token", re.compile(r"\b\d{7,12}:[A-Za-z0-9_-]{30,}\b")),
    ("database-url-with-password", re.compile(r"\b(?:postgres|postgresql|mysql)://[^\s:@/]+:[^\s@/]+@", re.I)),
)


def scan_text(text: str) -> list[tuple[int, str]]:
    """Return line numbers and rule names without retaining credential text."""
    findings: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule_name, pattern in RULES:
            if pattern.search(line):
                findings.append((line_number, rule_name))
    return findings


def repository_files(repo_root: Path) -> list[Path]:
    """List tracked and non-ignored untracked files without entering ignored secrets."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return [repo_root / entry.decode("utf-8") for entry in result.stdout.split(b"\0") if entry]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    findings: list[str] = []
    for path in repository_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Binary and non-UTF-8 assets are not suitable for this text scan.
            continue
        for line_number, rule_name in scan_text(text):
            findings.append(f"{path.relative_to(repo_root)}:{line_number}: {rule_name}")

    if findings:
        print("Potential credential pattern(s) found; rotate and remove them before merging:")
        print("\n".join(findings))
        return 1

    print("No high-confidence credential patterns found in repository UTF-8 text files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
