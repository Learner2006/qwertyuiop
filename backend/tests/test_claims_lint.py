"""Claims and terminology lint test (Milestone R3 / Finding F3).
Fails if any file under frontend/src, README.md, docs/, backend/app contains
an unverified or overstated claim phrase:
- 'pre-registered' / 'preregistered'
- 'out-of-sample' (banned outside docs/VALIDATION.md)
- 'without hindsight'
- 'established in advance'
- 'official'
- 'verified by'
- 'guarantee' (outside honest disclaimers such as 'not guaranteed', 'no guarantee',
  'does not guarantee', 'not a guaranteed')
"""

import os
import re
from typing import List, Tuple
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SCAN_PATHS = [
    os.path.join(REPO_ROOT, "frontend", "src"),
    os.path.join(REPO_ROOT, "backend", "app"),
    os.path.join(REPO_ROOT, "README.md"),
    os.path.join(REPO_ROOT, "docs"),
]

BANNED_EXACT_PATTERNS = [
    (re.compile(r"\bpre-registered\b", re.IGNORECASE), "pre-registered"),
    (re.compile(r"\bpreregistered\b", re.IGNORECASE), "preregistered"),
    (re.compile(r"\bwithout hindsight\b", re.IGNORECASE), "without hindsight"),
    (re.compile(r"\bestablished in advance\b", re.IGNORECASE), "established in advance"),
    (re.compile(r"\bofficial\b", re.IGNORECASE), "official"),
    (re.compile(r"\bverified by\b", re.IGNORECASE), "verified by"),
]

OUT_OF_SAMPLE_PATTERN = re.compile(r"\bout-of-sample\b", re.IGNORECASE)

# Allowed patterns for guarantee (disclaimers only)
ALLOWED_GUARANTEE_REGEX = re.compile(
    r"(not guaranteed|no guarantee|no guarantees|not a guaranteed|does not guarantee|do not guarantee|without guarantee)",
    re.IGNORECASE,
)
GUARANTEE_PATTERN = re.compile(r"\bguarante(?:e|ed|es|ing)\b", re.IGNORECASE)


def collect_files_to_scan() -> List[str]:
    files = []
    for p in SCAN_PATHS:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, _, filenames in os.walk(p):
                for f in filenames:
                    if f.endswith((".ts", ".tsx", ".py", ".md", ".json")):
                        files.append(os.path.join(root, f))
    return files


def test_claims_lint_no_banned_phrases():
    files = collect_files_to_scan()
    violations: List[str] = []

    for file_path in files:
        rel_path = os.path.relpath(file_path, REPO_ROOT)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                # 1. Exact banned patterns
                for pattern, phrase in BANNED_EXACT_PATTERNS:
                    if pattern.search(line):
                        violations.append(
                            f"{rel_path}:{line_no} contains banned phrase '{phrase}': {line.strip()}"
                        )

                # 2. out-of-sample (allowed ONLY in docs/VALIDATION.md)
                if rel_path != "docs/VALIDATION.md" and OUT_OF_SAMPLE_PATTERN.search(line):
                    violations.append(
                        f"{rel_path}:{line_no} contains banned phrase 'out-of-sample': {line.strip()}"
                    )

                # 3. guarantee (allowed ONLY inside disclaimers)
                if GUARANTEE_PATTERN.search(line):
                    if not ALLOWED_GUARANTEE_REGEX.search(line):
                        violations.append(
                            f"{rel_path}:{line_no} contains unmitigated 'guarantee': {line.strip()}"
                        )

    if violations:
        msg = f"Found {len(violations)} claims lint violation(s):\n" + "\n".join(violations)
        pytest.fail(msg)
