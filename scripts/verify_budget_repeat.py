"""Verify every replication phase, including paid routing and supplementary audits."""
from __future__ import annotations

import argparse
from pathlib import Path

import repeat_budget_trial as repeat
from run_budget_trial import ROOT, BASE, read, sha, sources, normalize_translation
from run_fresh_generations import inspect_events
import analyze_budget_trial as analysis
import verify_budget_trial as core
import budget_quality_veto as quality
from translation_economics import manifest_cost, pipeline_cost
from budget_economic_gate import gate


def expected_phases(root, config):
    phases = core.expected_models(config)
    phases['final_prose'] = config['models']['auditor']
    for family in ['terra', 'luna', 'anchor']:
        receipt = repeat.RAW_READ(root/('route-'+family+'.json'))
        for phase in receipt['audits_charged']:
            phases[phase] = config['models']['auditor']
        for phase in receipt['corrections_charged']:
            level = int(phase.rsplit('_', 1)[1])
            role = config['escalation'].get(family, ['anchor'])[level-1]
            phases[phase] = config['models'][role]
    for phase in ['prose_audit', 'final_prose']:
        if repeat.RAW_READ(root/(phase+'-lineage.json'))['completion_output_sha256'] is not None:
            phases[phase+'_coverage_completion'] = config['models']['auditor']
    return phases


def private_verify(workspace):
    repeat.check_repeat(); config = repeat.RAW_READ(BASE/'protocol.json')
    for name, digest in repeat.RAW_READ(BASE/'results/record.json')['files'].items():
        assert sha((BASE/'results'/name).read_bytes()) == digest, 'First realization changed: '+name
    with repeat.RepeatRuntime(workspace):
        core.verify(workspace)
        expected = expected_phases(workspace, config)
        folders = {p.parent.name for p in workspace.glob('*/attempt.json')}
        assert folders == set(expected) and len(folders) <= 36
        sessions = set(); old = {r['session_id_sha256'] for r in repeat.RAW_READ(BASE/'results/record.json')['stages']}
        for phase, model in expected.items():
            p = workspace/phase; m = repeat.RAW_READ(p/'manifest.json'); binding = repeat.RAW_READ(p/'repeat-binding.json')
            assert m['phase'] == phase and m['requested_model'] == m['model'] == model
            assert m['reasoning_effort'] == 'medium' and m['exit_code'] == 0 and m['runtime_error'] is None
            assert m['tool_calls'] == 0 and m['fresh_session']
            assert m['session_id_sha256'] not in sessions | old; sessions.add(m['session_id_sha256'])
            assert binding['manifest_sha256'] == sha((p/'manifest.json').read_bytes())
            assert binding['repeat_preregistration_sha256'] == sha((repeat.REPEAT/'preregistration.json').read_bytes())
            for key in ['input', 'output', 'prompt']:
                assert m[key+'_sha256'] == sha((p/(key+('.txt' if key == 'prompt' else '.json'))).read_bytes())
            actual = inspect_events([__import__('json').loads(line) for line in (p/'events.jsonl').read_text(encoding='utf8').splitlines() if line.strip()])
            assert all(m[key] == value for key, value in actual.items())
        return {'repeat': 2, 'verified_model_calls': len(sessions), 'no_run1_session_reuse': True,
                'all_phase_models_bindings_and_runtime_checked': True}


def published_verify():
    repeat.check_repeat(); root = repeat.REPEAT/'results'; record = repeat.RAW_READ(root/'record.json')
    assert record['repeat_preregistration_sha256'] == sha((repeat.REPEAT/'preregistration.json').read_bytes())
    assert record['first_record_sha256'] == sha((BASE/'results/record.json').read_bytes())
    for name, digest in repeat.RAW_READ(BASE/'results/record.json')['files'].items():
        assert sha((BASE/'results'/name).read_bytes()) == digest, 'First realization changed: '+name
    for name, digest in record['files'].items():
        assert sha((root/name).read_bytes()) == digest, name
    config = repeat.RAW_READ(BASE/'protocol.json'); expected = expected_phases(root, config)
    assert {r['phase'] for r in record['stages']} == set(expected)
    assert len(record['stages']) == record['model_calls'] <= 36
    sessions = set(); old = {r['session_id_sha256'] for r in repeat.RAW_READ(BASE/'results/record.json')['stages']}
    for stage in record['stages']:
        p = root/stage['phase']; assert repeat.RAW_READ(p/'manifest.json') == stage
        assert stage['model'] == stage['requested_model'] == expected[stage['phase']] and stage['reasoning_effort'] == 'medium'
        assert stage['exit_code'] == 0 and stage['runtime_error'] is None and stage['tool_calls'] == 0
        assert stage['session_id_sha256'] not in sessions | old; sessions.add(stage['session_id_sha256'])
        assert stage['output_sha256'] == sha((p/'output.json').read_bytes())
        binding = repeat.RAW_READ(p/'repeat-binding.json')
        assert binding['manifest_sha256'] == sha((p/'manifest.json').read_bytes())
        assert binding['repeat_preregistration_sha256'] == record['repeat_preregistration_sha256']
    # Run pure scoring in an external copy; never rewrite published artifacts.
    import tempfile, shutil
    with tempfile.TemporaryDirectory(prefix='budget-repeat-replay-') as temp:
        workspace = Path(temp)/'repeat'; shutil.copytree(root, workspace)
        for name in ['prose_audit', 'final_prose']:
            lineage = repeat.RAW_READ(root/(name+'-lineage.json'))
            assert lineage['raw_output_sha256'] == sha((root/name/'output.json').read_bytes())
            assert lineage['derived_output_sha256'] == sha((root/(name+'-normalized.json')).read_bytes())
            assert repeat.RAW_READ(root/(name+'-normalized.json'))['pairs'] == repeat.RAW_READ(root/name/'output.json')['pairs']
        # Scoring needs only the derived read adapter, not a new model call or workspace marker.
        old_reads = [(m, m.read) for m in [analysis, quality]]
        try:
            analysis.read = repeat.derived_read; quality.read = repeat.derived_read
            scored = analysis.score(workspace, config)
            assert scored == repeat.RAW_READ(root/'scored.json')
            assert quality.assess(workspace) == repeat.RAW_READ(root/'quality-cost-verdict.json')
        finally:
            for m, func in old_reads:
                m.read = func
    originals = {r['id']: r for r in sources()}; total_words = sum(len(r['source'].split()) for r in originals.values())
    routes = {f: repeat.RAW_READ(root/('route-'+f+'.json')) for f in ['terra', 'luna', 'anchor']}
    for family, receipt in routes.items():
        assert len(receipt['final_items']) == 30 and {r['id'] for r in receipt['final_items']} == set(originals)
        accepted = sum(len(originals[r['id']]['source'].split()) for r in receipt['final_items'] if r['model_accepted'])
        for r in receipt['final_items']:
            assert r['text'] == next(t['text'] for t in repeat.RAW_READ(root/r['origin']/'normalized.json')['items'] if t['id'] == r['id'])
        for cold in [False, True]:
            cost = pipeline_cost(planner=manifest_cost(repeat.RAW_READ(root/'planner/manifest.json'), config['pricing'], cold=cold)
                    if receipt['selected'].endswith(('_brief', '_memory')) else 0,
                translator=manifest_cost(repeat.RAW_READ(root/receipt['selected']/'manifest.json'), config['pricing'], cold=cold),
                audits=[manifest_cost(repeat.RAW_READ(root/p/'manifest.json'), config['pricing'], cold=cold) for p in receipt['audits_charged']],
                escalations=[manifest_cost(repeat.RAW_READ(root/p/'manifest.json'), config['pricing'], cold=cold) for p in receipt['corrections_charged']],
                requested_words=total_words, accepted_words=accepted)
            assert cost == receipt['accounting']['cold' if cold else 'cache_adjusted']
    counts = repeat.RAW_READ(root/'final-prose-counts.json')
    outcome = {f: gate(calibration_pass=repeat.RAW_READ(root/'scored.json')['calibration']['pass'], route=routes[f],
                      anchor_route=routes['anchor'], prose_losses=counts[f]['losses'], corpus_items=30) for f in ['terra', 'luna']}
    assert outcome == repeat.RAW_READ(root/'economic-gates.json')
    return {'repeat': 2, 'model_calls': len(sessions), 'selected': repeat.RAW_READ(root/'scored.json')['selected'],
            'economic_gates': {f: r['development_economic_gate'] for f, r in outcome.items()}, 'human_validation': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--published', action='store_true')
    args = parser.parse_args()
    print(published_verify() if args.published else private_verify(args.workspace.resolve()))


if __name__ == '__main__':
    main()
