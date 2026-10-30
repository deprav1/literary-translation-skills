"""Infrastructure recovery for source audits of an actually missing translation.

No candidate text, prompt, model or threshold changes. Empty candidates have no
literal target substring; their critical omission evidence is the recorded empty
output itself. Existing completed calls are reused byte-for-byte, never sampled
again. This adapter is used only if the original strict quote checker stops.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import run_budget_trial as runner
import analyze_budget_trial as analysis
import verify_budget_trial as verifier
from run_budget_trial import BASE, ROOT, read, sha

ORIGINAL_VALIDATE = runner.validate_audit
ORIGINAL_CALL = runner.call


def validate_with_empty(output, items, *, pairs=None):
    candidates = {c['candidate_id']: (r, c) for r in items for c in r['candidates']}
    ordinary = []; empty_evidence = []
    for issue in output['issues']:
        source, target = candidates[issue['candidate_id']]
        if target['text']:
            ordinary.append(issue); continue
        assert issue['source_id'] == source['id']
        assert issue['severity'] == 'critical' and issue['category'] == 'omission'
        assert issue['source_quote'] and issue['source_quote'] in source['source']
        assert issue['target_quote'] in ['', '[empty]', '[missing]', '[No translation]', '']
        empty_evidence.append(issue)
    ORIGINAL_VALIDATE({**output, 'issues': ordinary}, items, pairs=pairs)
    return empty_evidence


def replay_or_call(workspace, phase, model, task, inputs, schema):
    folder = workspace/phase
    if not folder.exists():
        return ORIGINAL_CALL(workspace, phase, model, task, inputs, schema)
    manifest = read(folder/'manifest.json')
    assert manifest['exit_code'] == 0 and manifest['runtime_error'] is None
    assert manifest['requested_model'] == model and manifest['output_sha256'] == sha((folder/'output.json').read_bytes())
    assert read(folder/'input.json') == inputs and read(folder/'schema.json') == schema
    assert (folder/'instruction.txt').read_text(encoding='utf8') == runner.ISOLATION+task+'\n'
    print(json.dumps({'phase': phase, 'status': 'reuse-first-complete-output', 'new_call': False}), flush=True)
    return read(folder/'output.json')


def activate():
    amendment = read(BASE/'coverage-validation-amendment.json')
    assert amendment['adapter_sha256'] == sha(Path(__file__).read_bytes())
    runner.validate_audit = validate_with_empty
    analysis.validate_audit = validate_with_empty
    verifier.validate_audit = validate_with_empty
    runner.call = replay_or_call


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--phase', choices=['audit', 'route', 'verify'], required=True)
    args = parser.parse_args(); workspace = args.workspace.resolve(); activate()
    config = read(BASE/'protocol.json')
    if args.phase == 'audit':
        runner.source_audit(workspace, config)
        runner.prose_audit(workspace, config)
        runner.adjudicate(workspace, config)
    elif args.phase == 'route':
        import route_budget_trial as routing
        routing.validate_audit = validate_with_empty
        routing.call = replay_or_call
        result = analysis.score(workspace, config)
        verifier.verify(workspace)
        for family, method in [*result['selected'].items(), ('anchor', 'sol_anchor')]:
            routing.route_one(workspace, config, family, method)
        counts = routing.final_pairs(workspace, config); anchor = read(workspace/'route-anchor.json')
        outcomes = {family: routing.gate(calibration_pass=result['calibration']['pass'],
            route=read(workspace/('route-'+family+'.json')), anchor_route=anchor,
            prose_losses=counts[family]['losses'], corpus_items=30) for family in ['terra', 'luna']}
        runner.write(workspace/'economic-gates.json', outcomes)
        print(outcomes)
    else:
        print('Verified stages:', len(verifier.verify(workspace)))


if __name__ == '__main__':
    main()
