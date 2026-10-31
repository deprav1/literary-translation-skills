"""Decode a source-bound all-N coverage claim only when N matches its input set."""
from __future__ import annotations

import re
from pathlib import Path

import repeat_budget_trial as repeat
import budget_prose_coverage_recovery as recovery
from budget_audit_format_adapter import decode
from run_budget_trial import read, sha

METHOD_VALIDATE = repeat.RepeatRuntime.validate
TRANSPORT_VALIDATE = recovery.validate_transport


def explicit_coverage(values, items):
    by_source = {row['id']: [c['candidate_id'] for c in row['candidates']] for row in items}
    result = []
    for value in values:
        match = re.fullmatch(r'(q[0-9a-f]{10}): all (\d+) candidates read', value)
        if match:
            assert match[1] in by_source and len(by_source[match[1]]) == int(match[2]), 'Unmatched quantified coverage claim'
            result += by_source[match[1]]
        else:
            result += decode([value])
    assert len(result) == len(set(result)), 'Duplicate coverage claim'
    return result


def transport(output, items, *, pairs=None):
    return TRANSPORT_VALIDATE({**output, 'coverage': explicit_coverage(output['coverage'], items)}, items, pairs=pairs)


def method(self, output, items, *, pairs=None):
    return METHOD_VALIDATE(self, {**output, 'coverage': explicit_coverage(output['coverage'], items)}, items, pairs=pairs)


def activate():
    amendment = read(repeat.REPEAT/'coverage-amendment.json')
    assert amendment['adapter_sha256'] == sha(Path(__file__).read_bytes())
    repeat.RepeatRuntime.validate = method
    recovery.validate_transport = transport


if __name__ == '__main__':
    activate()
    repeat.main()
