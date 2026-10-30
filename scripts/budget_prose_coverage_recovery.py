"""Preserve malformed audit output; complete only missing Russian-review coverage.

Candidate texts and all original pairwise decisions remain unchanged. Grouped
coverage strings are parsed as explicit IDs; missing IDs receive one blind
supplementary review without new pairwise votes. A derived view has raw lineage.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

import run_budget_trial as runner
import analyze_budget_trial as analysis
import verify_budget_trial as verifier
import budget_coverage_adapter as empty_adapter
from run_budget_trial import BASE, ROOT, read, write, sha

ORIGINAL_READ = read


def coverage_ids(values):
    result = []
    for value in values:
        if re.fullmatch(r'v[0-9a-f]{14}', value):
            result.append(value)
        else:
            assert re.fullmatch(r'q[0-9a-f]{10}: (?:v[0-9a-f]{14})(?:, v[0-9a-f]{14})*', value), 'Unrecognized coverage serialization'
            result += re.findall(r'v[0-9a-f]{14}', value)
    assert len(result) == len(set(result)), 'Duplicate coverage IDs'
    return result


def validate_transport(output, items, *, pairs=None):
    candidates = {c['candidate_id']: (r, c) for r in items for c in r['candidates']}
    assert set(coverage_ids(output['coverage'])) == set(candidates)
    for issue in output['issues']:
        source, target = candidates[issue['candidate_id']]
        assert issue['source_id'] == source['id']
        # Remove only literal emphasis markers and normalize whitespace; never
        # repair spelling or invent an absent quote to make a judgment pass.
        canon = lambda text: ' '.join(text.replace('*', '').split())
        assert issue['source_quote'] and canon(issue['source_quote']) in canon(source['source'])
        if not target['text']:
            assert issue['category'] == 'omission' and issue['severity'] == 'critical'
            assert issue['target_quote'] in ['', '[empty]', '[missing]', '[No translation]']
        else:
            assert issue['target_quote'] and canon(issue['target_quote']) in canon(target['text'])
    for row in output['unresolved']:
        assert candidates[row['candidate_id']][0]['id'] == row['source_id']
    if pairs is not None:
        assert len(output['pairs']) == len(pairs) and {r['pair_id'] for r in output['pairs']} == {r['pair_id'] for r in pairs}


def derived_read(path):
    path = Path(path)
    if path.name == 'output.json' and path.parent.name == 'prose_audit':
        derived = path.parent.parent/'prose-audit-normalized.json'
        if derived.exists():
            return ORIGINAL_READ(derived)
    return ORIGINAL_READ(path)


def activate():
    amendment = ORIGINAL_READ(BASE/'prose-coverage-amendment.json')
    assert amendment['adapter_sha256'] == sha(Path(__file__).read_bytes())
    empty_adapter.activate()
    for module in [runner, analysis, verifier]:
        module.read = derived_read
        module.validate_audit = validate_transport


def complete(workspace):
    activate()
    original = ORIGINAL_READ(workspace/'prose_audit/output.json')
    inputs = ORIGINAL_READ(workspace/'prose_audit/input.json')
    expected = {c['candidate_id'] for r in inputs['items'] for c in r['candidates']}
    claimed = set(coverage_ids(original['coverage'])); assert claimed <= expected
    missing = expected-claimed
    missing_items = [{**r, 'candidates': [c for c in r['candidates'] if c['candidate_id'] in missing]}
                     for r in inputs['items'] if any(c['candidate_id'] in missing for c in r['candidates'])]
    config = ORIGINAL_READ(BASE/'protocol.json')
    assert missing_items, 'This recovery must not create an unnecessary review'
    supplementary = runner.call(workspace, 'prose_coverage_completion', config['models']['auditor'],
        runner.prompt('prose_audit'), {'items': missing_items, 'pairs': []}, runner.audit_schema(prose=True))
    validate_transport(supplementary, missing_items, pairs=[])
    combined = {**original, 'coverage': sorted(claimed | set(coverage_ids(supplementary['coverage']))),
        'issues': original['issues']+supplementary['issues'],
        'unresolved': original['unresolved']+supplementary['unresolved']}
    validate_transport(combined, inputs['items'], pairs=inputs['pairs'])
    assert combined['pairs'] == original['pairs']
    write(workspace/'prose-audit-normalized.json', combined)
    write(workspace/'prose-audit-lineage.json', {'raw_output_sha256': sha((workspace/'prose_audit/output.json').read_bytes()),
        'completion_output_sha256': sha((workspace/'prose_coverage_completion/output.json').read_bytes()),
        'derived_output_sha256': sha((workspace/'prose-audit-normalized.json').read_bytes()),
        'explicit_initial_candidate_coverage': len(claimed), 'required': len(expected),
        'supplementary_candidates': sorted(missing), 'pairwise_votes_unchanged': True,
        'normalization': 'Decode grouped coverage IDs; validation ignores emphasis markers only. No model text or preference is rewritten.'})
    runner.adjudicate(workspace, config)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--phase', choices=['complete', 'verify', 'route'], default='complete')
    args = parser.parse_args(); workspace = args.workspace.resolve()
    if args.phase == 'complete':
        complete(workspace)
    elif args.phase == 'verify':
        activate(); print('Verified stages', len(verifier.verify(workspace)))
    else:
        import final_budget_blind_audit as final
        final.activate = activate
        final.validate_with_empty = validate_transport
        # The final launcher forwards the same --workspace argument only.
        import sys
        sys.argv = [sys.argv[0], '--workspace', str(workspace)]
        final.main()


if __name__ == '__main__':
    main()
