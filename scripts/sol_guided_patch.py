"""Separate conditional editing test; old findings are explicitly supplied diagnostic hints."""
from __future__ import annotations

import argparse
from pathlib import Path

import sol_patch_trial as core

ROOT = core.ROOT
BASE = core.BASE/'guided'
PARENT = core.BASE


def cached_findings():
    pairs, mapping = core.prior.pair_inputs(core.OLD)
    ordinary = {p['source_id']: p['B' if mapping[p['pair_id']]['treatment_side'] == 'A' else 'A']['candidate_id'] for p in pairs}
    findings = []; seen = set()
    for name in ['judge1', 'judge2']:
        for f in core.read(core.OLD/name/'output.json')['issues']:
            if f['candidate_id'] != ordinary[f['source_id']]: continue
            key = f['source_id'], f['source_quote'], f['target_quote']
            if key in seen: continue
            seen.add(key)
            findings.append({'finding_id': 'f'+str(len(findings)+1), **{k: v for k, v in f.items() if k != 'candidate_id'}})
    return findings


def combined_usage(root):
    return [core.read(p)['usage'] for folder in [PARENT/'results', root] for p in folder.glob('*/manifest.json')]


def invoke(root, name, task, inputs, schema, limit):
    previous = combined_usage(root)
    assert len(previous) < 4
    assert sum(u['input_tokens'] for u in previous)+15000 <= 50000
    assert sum(u['output_tokens'] for u in previous)+limit <= 8000
    assert sum(max(core.response_cost(u), core.response_cost(u, True)) for u in previous)+(15000*2.5+limit*10)/1e6 <= .25
    return core.call(root, name, task, inputs, schema, limit)


def summarize(root):
    findings = cached_findings(); decisions = core.read(root/'patch/output.json')['decisions']
    core.validate_issues(findings, {r['id']: r['text'] for r in core.drafts()})
    patched = core.apply_patch_list(findings, decisions)
    assert patched == core.read(root/'patched.json')
    changed = [r['id'] for r in patched if r['text'] != next(d['text'] for d in core.drafts() if d['id'] == r['id'])]
    votes = {}; statuses = {}; severe = []
    if changed:
        for name, second in [('judge1', False), ('judge2', True)]:
            pairs, mapping = core.pair_pack(patched, second); output = core.read(root/name/'output.json')
            choices = {r['pair_id']: r['choice'] for r in output['pairs']}
            assert len(choices) == len(output['pairs']) == 8 and set(choices) == set(mapping)
            texts = {(p['source_id'], p[s]['candidate_id']): p[s]['text'] for p in pairs for s in ['A', 'B']}
            core.validate_issues(output['issues'], texts, True)
            counts = {'wins': 0, 'losses': 0, 'ties': 0, 'unclear': 0}; statuses[name] = {}
            for p in pairs:
                i = p['source_id']; side = mapping[p['pair_id']]['patched_side']; choice = choices[p['pair_id']]
                if p['A']['text'] == p['B']['text']: assert choice == 'tie'
                s = choice if choice in ['tie', 'unclear'] else 'win' if choice == side else 'loss'
                statuses[name][i] = s; counts[{'win': 'wins', 'loss': 'losses', 'tie': 'ties', 'unclear': 'unclear'}[s]] += 1
                target = p[side]['candidate_id']; control = p['B' if side == 'A' else 'A']['candidate_id']
                for f in output['issues']:
                    if f['source_id'] != i or f['candidate_id'] != target or f['severity'] == 'minor': continue
                    if not any(x['source_id'] == i and x['candidate_id'] == control and x['source_quote'] == f['source_quote'] and x['severity'] != 'minor' for x in output['issues']):
                        severe.append({'judge': name, **f})
            counts['net'] = counts['wins']-counts['losses']; votes[name] = counts
    wins = [i for i in core.prior.IDS if statuses and statuses['judge1'][i] == statuses['judge2'][i] == 'win']
    losses = [i for i in core.prior.IDS if statuses and statuses['judge1'][i] == statuses['judge2'][i] == 'loss']
    disagreements = [i for i in core.prior.IDS if statuses and statuses['judge1'][i] != statuses['judge2'][i]]
    work = {r['id']: r['work_id'] for r in core.prior.sources()}
    ms = [core.read(p) for p in root.glob('*/manifest.json')]
    assert {m['phase'] for m in ms} == ({'patch', 'judge1', 'judge2'} if changed else {'patch'})
    assert len({m['response_id_sha256'] for m in ms}) == len(ms)
    usage = combined_usage(root); costs = {m['phase']: core.response_cost(m['usage']) for m in ms}
    cold = sum(core.response_cost(u, True) for u in usage); observed = sum(core.response_cost(u) for u in usage)
    incoming = sum(u['input_tokens'] for u in usage); outgoing = sum(u['output_tokens'] for u in usage)
    assert len(usage) <= 4 and incoming <= 50000 and outgoing <= 8000 and max(cold, observed) <= .25
    return {'scope': 'conditional editing with known diagnostic hints', 'source_items': 8, 'source_words': 594,
        'guided_model_calls': len(ms), 'combined_new_model_calls': len(usage), 'cached_findings': findings,
        'decisions': decisions, 'changed_ids': changed, 'votes': votes, 'stable_wins': wins, 'stable_losses': losses,
        'disagreements': disagreements, 'new_severe_proposals': severe,
        'exploratory_signal': len(votes) == 2 and all(v['net'] >= 2 for v in votes.values()) and len(wins) >= 2 and
            len({work[i] for i in wins}) >= 2 and len(losses) <= 1 and not severe,
        'human_validation': False, 'default_changed': False,
        'economics': {'combined_input_tokens': incoming, 'combined_output_tokens': outgoing,
            'combined_cold_usd_equivalent': cold, 'combined_observed_cache_usd_equivalent': observed,
            'guided_phase_costs': costs, 'cached_tokens': sum((u.get('input_tokens_details') or {}).get('cached_tokens', 0) for u in usage),
            'cache_write_tokens': sum((u.get('input_tokens_details') or {}).get('cache_write_tokens', 0) for u in usage),
            'historical_draft_cost': core.read(core.OLD/'summary.json')['economics']['phases']['plain'],
            'historical_comparative_feedback_cost': sum(core.read(core.OLD/'summary.json')['economics']['phases'][n] for n in ['judge1', 'judge2']),
            'actual_billing_known': False}}


def run(root):
    core.frozen(); root.mkdir(exist_ok=False)
    schema = core.schema_object({'decisions': core.array(core.schema_object({'finding_id': core.STRING,
        'decision': {'type': 'string', 'enum': ['accept', 'reject', 'uncertain']}, 'replacement': core.STRING, 'reason': core.STRING}))})
    result = invoke(root, 'patch', core.PATCH, {'drafts': core.drafts(), 'proposed_issues': cached_findings()}, schema, 1500)
    patched = core.apply_patch_list(cached_findings(), result['decisions']); core.write(root/'patched.json', patched)
    if patched != core.drafts():
        schema = core.schema_object({'pairs': core.array(core.schema_object({'pair_id': core.STRING,
            'choice': {'type': 'string', 'enum': ['A', 'B', 'tie', 'unclear']}, 'reason': core.STRING})), 'issues': core.array(core.issue_schema())})
        for name, second in [('judge1', False), ('judge2', True)]:
            pairs, _ = core.pair_pack(patched, second)
            invoke(root, name, core.JUDGE, {'pairs': pairs}, schema, 2200)
    summary = summarize(root); target = BASE/'results'; target.mkdir(exist_ok=False)
    import shutil
    for p in root.glob('*/manifest.json'):
        (target/p.parent.name).mkdir()
        for name in ['manifest.json', 'output.json']: shutil.copyfile(p.parent/name, target/p.parent.name/name)
    core.write(target/'patched.json', patched); core.write(target/'summary.json', summary)
    core.write(target/'record.json', {'preregistration_sha256': core.sha((BASE/'preregistration.json').read_bytes()),
        'files': {p.relative_to(target).as_posix(): core.sha(p.read_bytes()) for p in sorted(target.rglob('*')) if p.is_file()}})
    print(core.json.dumps(summary, ensure_ascii=False), flush=True)


def verify():
    core.frozen(); root = BASE/'results'; record = core.read(root/'record.json')
    assert record['preregistration_sha256'] == core.sha((BASE/'preregistration.json').read_bytes())
    for name, digest in record['files'].items(): assert digest == core.sha((root/name).read_bytes()), name
    for p in root.glob('*/manifest.json'):
        m = core.read(p); assert m['status'] == 'completed' and m['fresh_request'] and m['tool_calls'] == 0
        assert m['preregistration_sha256'] == record['preregistration_sha256']
        assert m['output_sha256'] == core.sha((p.parent/'output.json').read_bytes())
    assert summarize(root) == core.read(root/'summary.json')
    print('Verified conditional guided edits and combined four-call budget; no independent quality claim')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'run', 'verify']); parser.add_argument('--workspace', type=Path)
    args = parser.parse_args(); core.BASE = BASE
    if args.action == 'freeze':
        assert not (BASE/'preregistration.json').exists()
        files = [Path(__file__), BASE/'PLAN.md', ROOT/'scripts/sol_patch_trial.py', ROOT/'scripts/sol_micro_trial.py',
                 core.prior.SOURCE, core.OLD/'plain/output.json', core.OLD/'summary.json',
                 core.OLD/'judge1/output.json', core.OLD/'judge2/output.json', PARENT/'results/record.json']
        core.write(BASE/'preregistration.json', {'date': '2026-10-31', 'outputs_observed': False,
            'files': {p.relative_to(ROOT).as_posix(): core.sha(p.read_bytes()) for p in files},
            'known_findings_sha256': core.sha(core.json.dumps(cached_findings(), ensure_ascii=False).encode())})
    elif args.action == 'run': run(args.workspace.resolve())
    else: verify()
