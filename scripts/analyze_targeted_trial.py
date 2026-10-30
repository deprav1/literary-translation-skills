"""Resolve the frozen trial's masked votes without changing thresholds or texts."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import difflib
import hashlib
import json
from math import comb
from pathlib import Path
import random

from run_targeted_trial import (ROOT, TRIAL, COMPARISONS, ARMS, SHARED, EDIT,
                                read, write, check_frozen, validate_edit)
from run_fresh_generations import inspect_events


def exact_sign(wins, losses):
    n = wins+losses
    if not n:
        return 1.0
    return min(1.0, 2*sum(comb(n, k) for k in range(min(wins, losses)+1))/(2**n))


def holm(pvalues):
    result = {}; previous = 0.0; m = len(pvalues)
    for i, (name, p) in enumerate(sorted(pvalues.items(), key=lambda item: (item[1], item[0]))):
        previous = max(previous, min(1.0, (m-i)*p))
        result[name] = previous
    return result


def normal(text):
    return ' '.join(text.split())


def masked_input(comparison, judge_number, workspace):
    left, right = COMPARISONS[comparison]
    texts = {arm: {r['id']: r['text'] for r in read(workspace/arm/'output.json')['items']} for arm in [left, right]}
    rng = random.Random(f'targeted-20261030:{comparison}:{judge_number}')
    mapping = {}; items = []
    for source in read(TRIAL/'natural-source.json')['items']:
        order = [left, right]; rng.shuffle(order)
        mapping[source['id']] = dict(zip(['A', 'B'], order))
        items.append({**source, 'A': texts[order[0]][source['id']], 'B': texts[order[1]][source['id']]})
    rng.shuffle(items)
    return mapping, {'items': items, 'rubric': (ROOT/'skills/literary-translation-evaluation/references/rubric.md').read_text(encoding='utf8')}


def literal_instruction(function):
    tree = ast.parse((ROOT/'scripts/run_targeted_trial.py').read_text(encoding='utf8'))
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    assignment = next(n for n in ast.walk(func) if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'instruction' for t in n.targets))
    return ast.literal_eval(assignment.value)


def aggregate(workspace):
    check_frozen()
    selection = {r['id']: r for r in read(TRIAL/'selection.json')}
    all_sources = {r['id']: r for r in read(TRIAL/'natural-source.json')['items']}
    expected = set(all_sources)
    texts = {arm: {r['id']: r['text'] for r in read(workspace/arm/'output.json')['items']} for arm in ARMS}
    assert all(set(rows) == expected for rows in texts.values())
    summaries = {}; detailed = {}; findings = []
    for name, (treatment, control) in COMPARISONS.items():
        per_item = {id: [] for id in expected}; per_judge = []
        for judge in range(1, 4):
            phase = f'judge_{name}_{judge}'
            output = read(workspace/phase/'output.json')['items']
            mapping = read(workspace/'masked-mappings'/f'{phase}.json')
            expected_mapping, expected_input = masked_input(name, judge, workspace)
            assert mapping == expected_mapping, f'Changed masked mapping: {phase}'
            assert read(workspace/phase/'input.json') == expected_input, f'Changed masked presentation: {phase}'
            assert len(output) == len(expected) and {r['id'] for r in output} == expected
            counts = Counter()
            for row in output:
                id = row['id']; order = mapping[id]
                vote = order[row['overall']] if row['overall'] in ['A', 'B'] else row['overall']
                duplicate = normal(texts[treatment][id]) == normal(texts[control][id])
                if duplicate:
                    vote = 'tie'
                counts[vote] += 1
                per_item[id].append({'judge': judge, 'vote': vote, 'raw_overall': row['overall'],
                                     'reason': row['reason'], 'exact_duplicate': duplicate})
                for finding in row['findings']:
                    findings.append({'comparison': name, 'judge': judge, 'id': id,
                        'arm': order[finding['candidate']], **{k: v for k, v in finding.items() if k != 'candidate'}})
            per_judge.append({'judge': judge, 'counts': dict(counts),
                              'net': counts[treatment]-counts[control]})
        decisions = []
        for id, votes in sorted(per_item.items()):
            counts = Counter(v['vote'] for v in votes)
            chosen, n = counts.most_common(1)[0]
            decision = chosen if n >= 2 else 'tie'
            decisions.append({'id': id, 'decision': decision, 'stratum': selection[id]['stratum'],
                              'work_id': selection[id]['work_id'], 'judges': votes})
        counts = Counter(r['decision'] for r in decisions)
        by_work = {work: sum((r['decision'] == treatment)-(r['decision'] == control)
                             for r in decisions if r['work_id'] == work)
                   for work in sorted({r['work_id'] for r in decisions})}
        random_net = sum((r['decision'] == treatment)-(r['decision'] == control)
                         for r in decisions if r['stratum'] == 'random')
        summaries[name] = {'treatment': treatment, 'control': control, 'items': len(expected),
            'wins': counts[treatment], 'losses': counts[control], 'ties': counts['tie'], 'unclear': counts['unclear'],
            'net': counts[treatment]-counts[control], 'random_net': random_net,
            'work_nets': by_work, 'per_judge': per_judge,
            'exact_sign_p': exact_sign(counts[treatment], counts[control]),
            'adjudicated_safety': 'pending', 'integration_pass': False}
        detailed[name] = decisions
    adjusted = holm({name: row['exact_sign_p'] for name, row in summaries.items()})
    for name, row in summaries.items():
        row['holm_p'] = adjusted[name]
        row['pre_safety_gate'] = (row['net'] >= 6 and row['holm_p'] <= .05 and row['random_net'] >= 0
            and all(j['net'] >= 0 for j in row['per_judge'])
            and all(net >= 0 for net in row['work_nets'].values())
            and sum(net > 0 for net in row['work_nets'].values()) >= 2)
    return summaries, detailed, findings


def validate_manifests(workspace):
    check_frozen()
    frozen = read(TRIAL/'preregistration.json')
    prereg_sha = hashlib.sha256((TRIAL/'preregistration.json').read_bytes()).hexdigest()
    expected_phases = ({'synthetic_'+name for name in ['idiom', 'fidelity', 'memory']}
                       | {'synthetic_check', 'draft'} | set(ARMS)
                       | {f'judge_{name}_{j}' for name in COMPARISONS for j in range(1, 4)})
    sessions = set(); stages = []
    for folder in sorted(workspace.iterdir()):
        if not folder.is_dir() or not (folder/'manifest.json').exists():
            continue
        manifest = read(folder/'manifest.json')
        assert manifest['phase'] == folder.name
        assert hashlib.sha256((folder/'output.json').read_bytes()).hexdigest() == manifest['output_sha256']
        assert hashlib.sha256((folder/'input.json').read_bytes()).hexdigest() == manifest['input_sha256']
        assert hashlib.sha256((folder/'prompt.txt').read_bytes()).hexdigest() == manifest['prompt_sha256']
        instruction = (folder/'instruction.txt').read_text(encoding='utf8')[:-1]
        assert hashlib.sha256(instruction.encode()).hexdigest() == manifest['instruction_sha256']
        assert manifest['model'] == frozen['model'] and manifest['reasoning_effort'] == frozen['reasoning_effort']
        assert manifest['preregistration_sha256'] == prereg_sha
        assert manifest['fresh_session'] and manifest['tool_calls'] == 0 and manifest['exit_code'] == 0
        actual = inspect_events([json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf8').splitlines() if line.strip()])
        assert all(manifest[k] == v for k, v in actual.items())
        expected_prompt = instruction+'\n\nINPUTS\n'+json.dumps(read(folder/'input.json'), ensure_ascii=False)
        assert (folder/'prompt.txt').read_text(encoding='utf8') == expected_prompt
        assert manifest['session_id_sha256'] not in sessions
        sessions.add(manifest['session_id_sha256']); stages.append(manifest)
    assert {s['phase'] for s in stages} == expected_phases and len(stages) == 22
    # Reconstruct actual model inputs; matching arbitrary hashes alone is insufficient.
    sources = read(TRIAL/'natural-source.json')
    drafts = {r['id']: r['text'] for r in read(workspace/'draft/output.json')['items']}
    assert read(workspace/'draft/input.json') == sources
    for name in ['idiom', 'fidelity', 'memory']:
        phase = 'synthetic_'+name
        expected_input = read(TRIAL/'synthetic-inputs.json')[name]
        assert read(workspace/phase/'input.json') == expected_input
        expected_instruction = SHARED+EDIT+'\nSPECIALISED REVIEW\n'+(TRIAL/'candidates'/f'{name}.txt').read_text(encoding='utf8')
        assert (workspace/phase/'instruction.txt').read_text(encoding='utf8')[:-1] == expected_instruction
        validate_edit(read(workspace/phase/'output.json'), expected_input)
    for arm in ARMS:
        expected_input = read(TRIAL/'natural-source.json')
        expected_input['items'] = [{**r, 'draft': drafts[r['id']]} for r in sources['items']]
        expected_input['lexical_evidence'] = read(TRIAL/'lexical-evidence.json')
        expected_instruction = SHARED+EDIT
        if arm in ['idiom', 'fidelity']:
            expected_instruction += '\nSPECIALISED REVIEW\n'+(TRIAL/'candidates'/f'{arm}.txt').read_text(encoding='utf8')
        if arm.startswith('memory_'):
            packets = read(TRIAL/'memory-packets.json'); kind = arm.removeprefix('memory_')
            expected_input['items'] = [{**r, 'parallel_examples': packets[r['id']][kind]} for r in expected_input['items']]
        assert read(workspace/arm/'input.json') == expected_input
        assert (workspace/arm/'instruction.txt').read_text(encoding='utf8')[:-1] == expected_instruction
        validate_edit(read(workspace/arm/'output.json'), expected_input)
    expected_judge_instruction = SHARED+literal_instruction('judge')
    for name in COMPARISONS:
        for j in range(1, 4):
            phase = f'judge_{name}_{j}'
            assert (workspace/phase/'instruction.txt').read_text(encoding='utf8')[:-1] == expected_judge_instruction
    return stages


def diff_ranges(before, after):
    return [{'kind': tag, 'before_start': a, 'before_end': b, 'after_start': c, 'after_end': d,
             'before': before[a:b], 'after': after[c:d]}
            for tag, a, b, c, d in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes() if tag != 'equal']


def full_change_audit(workspace):
    drafts = {r['id']: r['text'] for r in read(workspace/'draft/output.json')['items']}
    sources = {r['id']: r for r in read(TRIAL/'natural-source.json')['items']}
    rows = []
    for arm in ARMS:
        for result in read(workspace/arm/'output.json')['items']:
            id = result['id']; before = drafts[id]
            if result['text'] == before:
                continue
            rows.append({'arm': arm, 'id': id, 'source': sources[id]['source'], 'draft': before,
                         'result': result['text'], 'source_sha256': hashlib.sha256(sources[id]['source'].encode()).hexdigest(),
                         'draft_sha256': hashlib.sha256(before.encode()).hexdigest(),
                         'result_sha256': hashlib.sha256(result['text'].encode()).hexdigest(),
                         'actual_diff': diff_ranges(before, result['text']), 'model_reported_changes': result['changes']})
    return rows


def final_gates(summaries, mechanism, safety):
    comparisons = {}
    for name, row in summaries.items():
        candidate = 'memory' if name.startswith('memory_') else name
        harms = safety.get(row['treatment'])
        safe = harms is not None and harms['major_critical'] == 0 and harms['minor'] <= 2
        comparisons[name] = bool(row['pre_safety_gate'] and mechanism.get(candidate, {}).get('pass') and safe)
        row['adjudicated_safety'] = harms if harms is not None else 'pending'
        row['integration_pass'] = comparisons[name]
    return {'idiom': comparisons['idiom'], 'fidelity': comparisons['fidelity'],
            'memory': comparisons['memory_plain'] and comparisons['memory_random']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args(); workspace = args.workspace.resolve()
    stages = validate_manifests(workspace)
    summaries, details, findings = aggregate(workspace)
    write(workspace/'analysis-summary.json', {'comparisons': summaries,
        'scope': 'Preregistered model-reviewed pilot; safety adjudication and mechanism gates still required.',
        'stages': len(stages)})
    write(workspace/'analysis-items.json', details)
    write(workspace/'findings-to-adjudicate.json', findings)
    write(workspace/'full-change-audit.json', full_change_audit(workspace))
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
