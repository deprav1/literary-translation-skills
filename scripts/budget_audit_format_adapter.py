"""Decode an explicit source-id/candidate-id audit notation without a new call."""
from __future__ import annotations

import re
from pathlib import Path

import budget_prose_coverage_recovery as recovery
from run_budget_trial import BASE, read, sha

BASE_DECODE = recovery.coverage_ids


def decode(values):
    normalized = []
    for value in values:
        match = re.fullmatch(r'(q[0-9a-f]{10})/(v[0-9a-f]{14})', value)
        normalized.append(match[2] if match else value)
    return BASE_DECODE(normalized)


def activate():
    amendment = read(BASE/'audit-format-amendment.json')
    assert amendment['adapter_sha256'] == sha(Path(__file__).read_bytes())
    recovery.activate()
    recovery.coverage_ids = decode


if __name__ == '__main__':
    activate()
    recovery.main()
