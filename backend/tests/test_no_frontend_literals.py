"""Frontend literal fallbacks and provenance honesty test (Milestone R6 / Finding F11).

Scans frontend/src (*.ts, *.tsx) to guarantee:
1. No non-zero numeric fallbacks (e.g. `|| 241`, `?? 1.08`, `|| 1296`) that mask
   missing or failed backend API responses.
2. No hardcoded dataset hashes (e.g. `d997afe4...`) in frontend presentation code.
3. No hardcoded fake timestamps (e.g. `2026-01-25T09:00:00Z`).
4. Provenance metadata is computed dynamically from the parquet file at runtime.
"""

import os
import re
from typing import List
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND_SRC = os.path.join(REPO_ROOT, "frontend", "src")

# Patterns prohibited in frontend code
SUSPICIOUS_PATTERNS = [
    (
        re.compile(r"(\|\||\?\?)\s*[1-9][0-9]*(\.[0-9]+)?\b"),
        "non-zero numeric fallback (|| or ?? with non-zero number)",
    ),
    (
        re.compile(r"d997afe4[0-9a-fA-F]*"),
        "hardcoded parquet SHA-256 hash in UI code",
    ),
    (
        re.compile(r"2026-01-25T09:00:00Z"),
        "hardcoded fake cutoff timestamp default",
    ),
    (
        re.compile(r"2026-10-24T16:49:00Z"),
        "hardcoded fake build timestamp default",
    ),
]


def collect_frontend_source_files() -> List[str]:
    files = []
    for root, _, filenames in os.walk(FRONTEND_SRC):
        for f in filenames:
            if f.endswith((".ts", ".tsx")):
                files.append(os.path.join(root, f))
    return sorted(files)


def test_no_hardcoded_frontend_literals_or_fallbacks():
    files = collect_frontend_source_files()
    assert len(files) > 0, "No frontend files found to scan"

    violations: List[str] = []
    for file_path in files:
        rel_path = os.path.relpath(file_path, REPO_ROOT)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                    continue

                for pattern, desc in SUSPICIOUS_PATTERNS:
                    if pattern.search(line):
                        violations.append(
                            f"{rel_path}:{line_no} [{desc}]: {stripped}"
                        )

    if violations:
        msg = f"Found {len(violations)} frontend literal violation(s):\n" + "\n".join(violations)
        pytest.fail(msg)


def test_provenance_schema_has_no_hardcoded_fallbacks():
    from backend.app.schemas import ProvenanceMetadata

    # Assert fields don't have hardcoded default hashes or sizes
    model_fields = ProvenanceMetadata.model_fields
    assert model_fields["snapshot_sha256"].default is None or model_fields["snapshot_sha256"].is_required()
    assert model_fields["snapshot_size_kb"].default is None or model_fields["snapshot_size_kb"].is_required()
    assert model_fields["snapshot_record_count"].default is None or model_fields["snapshot_record_count"].is_required()


def test_provenance_computed_dynamically_from_file():
    from backend.app.services.prepare import DataManager
    from backend.app.config import settings

    dm = DataManager.get_instance()
    fmeta = dm.file_metadata

    assert "sha256" in fmeta
    assert len(fmeta["sha256"]) == 64
    assert fmeta["filename"] == os.path.basename(settings.DATA_PATH)
    assert fmeta["size_kb"] > 0
    assert fmeta["record_count"] > 0
