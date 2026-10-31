"""Publish repeat2 separately and compare realizations without best-of selection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

import repeat_budget_trial as repeat
from run_budget_trial import BASE, ROOT, sha, write
from run_fresh_generations import inspect_events
from translation_economics import manifest_cost
from budget_metric_view import model_metrics
import analyze_budget_trial as analysis
import verify_budget_trial as verifier
import budget_quality_veto as quality


def stability(first, second, first_routes, second_routes, first_final, second_final):
    result = {}
    for name, initial in first['comparisons'].items():
        latest = second['comparisons'][name]
        sign = lambda n: (n > 0)-(n < 0)
        result[name] = {'run1': {k: initial[k] for k in ['wins', 'losses', 'ties', 'unclear', 'net']},
                        'run2': {k: latest[k] for k in ['wins', 'losses', 'ties', 'unclear', 'net']},
                        'direction_same': sign(initial['net']) == sign(latest['net'])}
    pipeline = {}
    for family in ['terra', 'luna', 'anchor']:
        a = first_routes[family]; b = second_routes[family]
        pipeline[family] = {'run1_selected': a['selected'], 'run2_selected': b['selected'],
            'run1_cold': a['accounting']['cold'], 'run2_cold': b['accounting']['cold'],
            'run1_prose': first_final.get(family), 'run2_prose': second_final.get(family),
            'run1_escalated_items': sum(r['origin'] != a['selected'] for r in a['final_items']),
            'run2_escalated_items': sum(r['origin'] != b['selected'] for r in b['final_items'])}
    return {'comparisons': result, 'pipelines': pipeline,
            'independent_source_items': 30, 'realizations': 2,
            'rule': 'No best-of selection or pooling as60independent sources; model judges only, not confirmation.'}


def publish(workspace):
    repeat.check_repeat(); target = repeat.REPEAT/'results'
    assert not target.exists(), 'Never overwrite repeat evidence'
    with repeat.RepeatRuntime(workspace):
        verifier.verify(workspace)
        config = repeat.RAW_READ(BASE/'protocol.json')
        scored = analysis.score(workspace, config)
        quality.assess(workspace)
        manifests = []; sessions = set()
        first_sessions = {s['session_id_sha256'] for s in repeat.RAW_READ(BASE/'results/record.json')['stages']}
        for folder in sorted(workspace.iterdir()):
            if not folder.is_dir() or not (folder/'attempt.json').exists():
                continue
            manifest = repeat.RAW_READ(folder/'manifest.json')
            binding = repeat.RAW_READ(folder/'repeat-binding.json')
            assert manifest['exit_code'] == 0 and manifest['runtime_error'] is None
            assert manifest['session_id_sha256'] not in sessions | first_sessions
            sessions.add(manifest['session_id_sha256'])
            assert binding['repeat_preregistration_sha256'] == sha((repeat.REPEAT/'preregistration.json').read_bytes())
            assert binding['manifest_sha256'] == sha((folder/'manifest.json').read_bytes())
            for key in ['input', 'output', 'prompt']:
                suffix = '.txt' if key == 'prompt' else '.json'
                assert sha((folder/(key+suffix)).read_bytes()) == manifest[key+'_sha256']
            actual = inspect_events([json.loads(l) for l in (folder/'events.jsonl').read_text(encoding='utf8').splitlines() if l.strip()])
            assert all(manifest[k] == v for k, v in actual.items())
            manifests.append(manifest)
        assert len(manifests) <= 36
        target.mkdir()
        for manifest in manifests:
            phase = manifest['phase']; folder = target/phase; folder.mkdir()
            for name in ['output.json', 'manifest.json', 'repeat-binding.json', 'instruction.txt', 'normalized.json']:
                if (workspace/phase/name).exists():
                    shutil.copyfile(workspace/phase/name, folder/name)
        roots = ['brief-used.json', 'candidate-mapping.json', 'pair-mapping.json', 'calibration-mapping.json',
            'issue-proposals.json', 'scored.json', 'route-terra.json', 'route-luna.json', 'route-anchor.json',
            'final-pair-mapping.json', 'final-prose-counts.json', 'economic-gates.json', 'quality-cost-verdict.json']
        for phase in ['prose_audit', 'final_prose']:
            roots += [phase+'-normalized.json', phase+'-lineage.json']
        for name in roots:
            write(target/name, repeat.RAW_READ(workspace/name))
        metrics = {'parent_scored_sha256': sha((target/'scored.json').read_bytes()),
                   'models': model_metrics(scored, repeat.RAW_READ(workspace/'candidate-mapping.json'))}
        write(target/'quality-metrics.json', metrics)
        production = set()
        for family in ['terra', 'luna', 'anchor']:
            route = repeat.RAW_READ(workspace/('route-'+family+'.json'))
            production |= set(route['audits_charged']) | set(route['corrections_charged'])
        research = [s for s in manifests if s['phase'] not in production and s['phase'] not in {'planner', 'sol_anchor'}
                    and not s['phase'].startswith(('terra_', 'luna_'))]
        costs = {'all_calls_cold': sum(manifest_cost(s, config['pricing'], cold=True) for s in manifests),
                 'all_calls_cache_adjusted': sum(manifest_cost(s, config['pricing']) for s in manifests),
                 'research_audits_only_cold': sum(manifest_cost(s, config['pricing'], cold=True) for s in research),
                 'basis': 'Fixed30October2026StandardAPIlist-price equivalent, not invoice or subscription charge.'}
        write(target/'research-cost.json', costs)
        first = repeat.RAW_READ(BASE/'results/scored.json')
        routes = lambda root: {f: repeat.RAW_READ(root/('route-'+f+'.json')) for f in ['terra', 'luna', 'anchor']}
        compare = stability(first, scored, routes(BASE/'results'), routes(target),
                            repeat.RAW_READ(BASE/'results/final-prose-counts.json'), repeat.RAW_READ(target/'final-prose-counts.json'))
        write(target/'stability.json', compare)
        first_brief = repeat.RAW_READ(BASE/'results/brief-used.json')['works']; second_brief = repeat.RAW_READ(target/'brief-used.json')['works']
        overlap = {}
        for work in second_brief:
            original = next(w for w in first_brief if w['work_id'] == work['work_id'])
            terms = lambda w: {r['term'].lower().strip() for r in w['glossary']}
            a = terms(original); b = terms(work)
            overlap[work['work_id']] = {'run1_terms': sorted(a), 'run2_terms': sorted(b),
                                       'common': sorted(a & b), 'jaccard': len(a & b)/len(a | b) if a | b else 1}
        write(target/'brief-overlap.json', {'run1_brief_sha256': sha((BASE/'results/brief-used.json').read_bytes()),
            'run2_brief_sha256': sha((target/'brief-used.json').read_bytes()), 'work_terms': overlap,
            'scope': 'Post-generation diagnostic only; neither brief selected or fed to the other run.'})
        record = {'date': '2026-10-31', 'replication': 2, 'model_calls': len(manifests), 'stages': manifests,
            'repeat_preregistration_sha256': sha((repeat.REPEAT/'preregistration.json').read_bytes()),
            'base_preregistration_sha256': sha((BASE/'preregistration.json').read_bytes()),
            'first_record_sha256': sha((BASE/'results/record.json').read_bytes()),
            'no_session_overlap_with_first': True, 'manual_candidate_edits': False, 'human_review': False,
            'best_of_selection': False, 'new_source_holdout': False, 'source_items': 30,
            'costs': costs, 'files': {p.relative_to(target).as_posix(): sha(p.read_bytes()) for p in sorted(target.rglob('*')) if p.is_file()},
            'scope': 'Two stochastic realizations on the same development items; not efficacy proof or approval for defaults.'}
        write(target/'record.json', record)
    print({'repeat2_calls': len(manifests), 'selected': scored['selected'], 'costs': costs})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args(); publish(args.workspace.resolve())


if __name__ == '__main__':
    main()
