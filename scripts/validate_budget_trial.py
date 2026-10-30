"""Replay published budget-pilot metrics and accounting without model calls."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile

from run_budget_trial import BASE, read, sources, sha, check_frozen
from analyze_budget_trial import score
from budget_economic_gate import gate
from translation_economics import manifest_cost, pipeline_cost


def validate():
    if (BASE/'prose-coverage-amendment.json').exists():
        from budget_prose_coverage_recovery import activate
        activate()
    check_frozen(); results = BASE/'results'; record = read(results/'record.json')
    assert record['preregistration_sha256'] == sha((BASE/'preregistration.json').read_bytes())
    assert record['routing_amendment_sha256'] == sha((BASE/'routing-amendment.json').read_bytes())
    for name, digest in record['files'].items():
        assert sha((results/name).read_bytes()) == digest, name
    sessions = set(); config = read(BASE/'protocol.json')
    for stage in record['stages']:
        manifest = read(results/stage['phase']/'manifest.json')
        assert manifest == stage and stage['exit_code'] == 0 and stage['runtime_error'] is None
        assert stage['tool_calls'] == 0 and stage['fresh_session'] and stage['reasoning_effort'] == 'medium'
        assert stage['session_id_sha256'] not in sessions; sessions.add(stage['session_id_sha256'])
        assert stage['model'] == stage['requested_model'] and stage['model'] in set(config['models'].values())
        assert sha((results/stage['phase']/'output.json').read_bytes()) == stage['output_sha256']
    assert len(sessions) == record['model_calls'] <= 36
    if (results/'prose-audit-lineage.json').exists():
        from budget_audit_format_adapter import decode
        lineage = read(results/'prose-audit-lineage.json')
        assert lineage['raw_output_sha256'] == sha((results/'prose_audit/output.json').read_bytes())
        assert lineage['completion_output_sha256'] == sha((results/'prose_coverage_completion/output.json').read_bytes())
        assert lineage['derived_output_sha256'] == sha((results/'prose-audit-normalized.json').read_bytes())
        raw = read(results/'prose_audit/output.json'); supplement = read(results/'prose_coverage_completion/output.json')
        combined = read(results/'prose-audit-normalized.json')
        assert combined == {**raw, 'coverage': sorted(set(decode(raw['coverage'])) | set(decode(supplement['coverage']))),
                            'issues': raw['issues']+supplement['issues'], 'unresolved': raw['unresolved']+supplement['unresolved']}
    # score() emits a working report; execute only in an isolated copy.
    with tempfile.TemporaryDirectory(prefix='budget-replay-') as temporary:
        workspace = Path(temporary)/'results'; shutil.copytree(results, workspace)
        expected = score(workspace, config)
        assert expected == read(results/'scored.json')
    original = {r['id']: r for r in sources()}; total_words = sum(len(r['source'].split()) for r in original.values())
    for family in ['terra', 'luna', 'anchor']:
        receipt = read(results/('route-'+family+'.json')); final = receipt['final_items']
        assert len(final) == len(original) and {r['id'] for r in final} == set(original)
        assert receipt['human_acceptance'] is False
        accepted_words = sum(len(original[r['id']]['source'].split()) for r in final if r['model_accepted'])
        for row in final:
            assert row['model_accepted'] == (row['id'] not in receipt['unresolved_flags'])
            translated = {r['id']: r['text'] for r in read(results/row['origin']/'normalized.json')['items']}
            assert translated[row['id']] == row['text']
        for cold in [False, True]:
            model = receipt['selected']; guided = model.endswith(('_brief', '_memory'))
            expected_cost = pipeline_cost(
                planner=manifest_cost(read(results/'planner/manifest.json'), config['pricing'], cold=cold) if guided else 0,
                translator=manifest_cost(read(results/model/'manifest.json'), config['pricing'], cold=cold),
                audits=[manifest_cost(read(results/n/'manifest.json'), config['pricing'], cold=cold) for n in receipt['audits_charged']],
                escalations=[manifest_cost(read(results/n/'manifest.json'), config['pricing'], cold=cold) for n in receipt['corrections_charged']],
                accepted_words=accepted_words, requested_words=total_words)
            assert expected_cost == receipt['accounting']['cold' if cold else 'cache_adjusted']
    pair_map = read(results/'final-pair-mapping.json'); votes = {r['pair_id']: r['choice'] for r in read(results/'final_prose/output.json')['pairs']}
    counts = {f: {'wins': 0, 'losses': 0, 'ties': 0, 'unclear': 0} for f in ['terra', 'luna']}
    for pid, pair in pair_map.items():
        assert 'terra' not in pid and 'luna' not in pid
        choice = 'tie' if pair.get('forced_tie') else votes[pid]
        label = ('wins' if pair[choice] == pair['treatment'] else 'losses') if choice in ['A', 'B'] else ('ties' if choice == 'tie' else 'unclear')
        counts[pair['family']][label] += 1
    assert counts == read(results/'final-prose-counts.json')
    outcomes = {}
    for family in ['terra', 'luna']:
        outcomes[family] = gate(calibration_pass=read(results/'scored.json')['calibration']['pass'],
            route=read(results/('route-'+family+'.json')), anchor_route=read(results/'route-anchor.json'),
            prose_losses=counts[family]['losses'], corpus_items=30)
    assert outcomes == read(results/'economic-gates.json')
    return {'model_calls': len(sessions), 'source_words': total_words, 'selected': read(results/'scored.json')['selected'],
            'development_economic_gate': {f: r['development_economic_gate'] for f, r in outcomes.items()},
            'limit': 'Artifact and accounting replay only; requested model identities and model-based quality judgments are not human validation.'}


if __name__ == '__main__':
    print(json.dumps(validate(), ensure_ascii=False))
