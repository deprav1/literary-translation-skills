"""Validate immutable generation/audit evidence before budget-pilot interpretation."""
from __future__ import annotations

import json
from pathlib import Path
import random

from run_budget_trial import (ROOT, BASE, read, sources, sha, ISOLATION, check_frozen,
                              normalize_translation, validate_audit, prompt)
from run_fresh_generations import inspect_events


def expected_models(config):
    result = {'planner': config['models']['planner'], 'sol_anchor': config['models']['anchor']}
    for family in ['luna', 'terra']:
        for arm in config['arms']:
            result[family+'_'+arm] = config['models'][family]
    for phase in ['source_audit_'+str(i) for i in range(9)]+['prose_audit', 'adjudicate']:
        result[phase] = config['models']['auditor']
    return result


def reconstruct(workspace, config):
    methods = ['sol_anchor']+[f+'_'+a for f in ['terra', 'luna'] for a in config['arms']]
    values = {}
    for method in methods:
        raw = read(workspace/method/'output.json')
        normal = normalize_translation(raw, sources())
        assert read(workspace/method/'normalized.json') == normal
        values[method] = {r['id']: r['text'] for r in normal['items']}
    mapping = {}; items = []; rng = random.Random('budget-translation-20261030-candidates')
    for source in sources():
        merged = {}; candidates = []
        for method in methods:
            text = values[method][source['id']]; key = ' '.join(text.split())
            if key in merged:
                mapping[merged[key]].append(method); continue
            cid = 'v'+sha((source['id']+method+'budget-hidden').encode())[:14]
            merged[key] = cid; mapping[cid] = [method]; candidates.append({'candidate_id': cid, 'text': text})
        rng.shuffle(candidates); items.append({**source, 'candidates': candidates})
    assert read(workspace/'candidate-mapping.json') == mapping
    assert read(workspace/'audit-input.json') == {'items': items}
    candidates = {r['id']: {m: c['candidate_id'] for c in r['candidates'] for m in mapping[c['candidate_id']]} for r in items}
    pairs = []; pmapping = {}; rng = random.Random(20261031)
    for name, (treatment, control) in config['pair_comparisons'].items():
        for row in items:
            order = [treatment, control]; rng.shuffle(order); pid = 'p'+sha((name+row['id']).encode())[:14]
            record = {'comparison': name, 'source_id': row['id'], 'A': order[0], 'B': order[1]}
            if candidates[row['id']][order[0]] == candidates[row['id']][order[1]]:
                pmapping[pid] = {**record, 'forced_tie': True}; continue
            pairs.append({'pair_id': pid, 'source_id': row['id'], 'A': candidates[row['id']][order[0]], 'B': candidates[row['id']][order[1]]})
            pmapping[pid] = record
    rng.shuffle(pairs); assert read(workspace/'pair-mapping.json') == pmapping
    assert read(workspace/'prose_audit/input.json') == {'items': items, 'pairs': pairs}
    validate_audit(read(workspace/'prose_audit/output.json'), items, pairs=pairs)
    for index, method in enumerate(methods):
        batch = [{k: v for k, v in r.items() if k != 'work_id'} for r in items]
        for row in batch:
            row['candidates'] = [c for c in row['candidates'] if method in mapping[c['candidate_id']]]
        if index == 0:
            cmapping = {}
            for row in read(BASE/'calibration.json'):
                sid = 'q'+sha(('budgetcontrol'+row['id']).encode())[:10]
                cid = 'v'+sha(('budgetcandidate'+row['id']).encode())[:14]
                batch.append({'id': sid, 'source': row['source'], 'context_before': row['context_before'],
                              'context_after': row['context_after'], 'candidates': [{'candidate_id': cid, 'text': row['text']}]})
                cmapping[cid] = {'source_id': sid, 'expected_issue': row['expected_issue']}
            assert read(workspace/'calibration-mapping.json') == cmapping
        random.Random('source-order-'+str(index)).shuffle(batch)
        assert read(workspace/f'source_audit_{index}/input.json') == {'items': batch}
        validate_audit(read(workspace/f'source_audit_{index}/output.json'), batch)
    proposals = []
    for phase in ['source_audit_'+str(i) for i in range(9)]+['prose_audit']:
        for index, row in enumerate(read(workspace/phase/'output.json')['issues']):
            proposals.append({'issue_id': phase+':'+str(index), 'origin': phase, **row})
    assert read(workspace/'issue-proposals.json') == proposals
    return items


def verify(workspace, *, require_audits=True):
    check_frozen(); config = read(BASE/'protocol.json'); expected = expected_models(config)
    if not require_audits:
        expected = {k: v for k, v in expected.items() if not k.startswith(('source_audit', 'prose_audit', 'adjudicate'))}
    sessions = set(); manifests = []
    for phase, model in expected.items():
        folder = workspace/phase; manifest = read(folder/'manifest.json')
        assert manifest['phase'] == phase and manifest['model'] == manifest['requested_model'] == model
        assert manifest['reasoning_effort'] == config['reasoning_effort'] == 'medium'
        assert manifest['preregistration_sha256'] == sha((BASE/'preregistration.json').read_bytes())
        assert manifest['exit_code'] == 0 and manifest['runtime_error'] is None and manifest['tool_calls'] == 0
        assert manifest['fresh_session'] and manifest['session_id_sha256'] not in sessions
        sessions.add(manifest['session_id_sha256']); manifests.append(manifest)
        for name in ['input', 'output', 'prompt']:
            suffix = '.txt' if name == 'prompt' else '.json'
            assert manifest[name+'_sha256'] == sha((folder/(name+suffix)).read_bytes())
        instruction = (folder/'instruction.txt').read_text(encoding='utf8')[:-1]
        assert sha(instruction.encode()) == manifest['instruction_sha256']
        raw = instruction+'\n\nINPUTS\n'+json.dumps(read(folder/'input.json'), ensure_ascii=False)
        assert (folder/'prompt.txt').read_text(encoding='utf8') == raw
        actual = inspect_events([json.loads(l) for l in (folder/'events.jsonl').read_text(encoding='utf8').splitlines() if l.strip()])
        assert all(manifest[k] == v for k, v in actual.items())
        if phase == 'planner':
            assert read(folder/'input.json') == {'items': sources()} and instruction == ISOLATION+prompt('planner')
        elif phase == 'sol_anchor' or phase.startswith(('luna_', 'terra_')):
            arm = 'plain' if phase == 'sol_anchor' else phase.split('_', 1)[1]
            task = prompt('plain'); inputs = {'items': sources()}
            if arm != 'plain':
                task += '\n'+(BASE/'profiles/guard.txt').read_text(encoding='utf8').strip()
            if arm in ['brief', 'memory']:
                inputs['work_briefs'] = read(workspace/'brief-used.json')['works']
                task += '\n'+(BASE/'profiles/brief.txt').read_text(encoding='utf8').strip()
            if arm == 'memory':
                examples = read(BASE/'examples.json'); lookup = {r['id']: r for r in examples['examples']}
                inputs['parallel_examples'] = {w: [lookup[id] for id in ids] for w, ids in examples['selection'].items()}
                task += '\n'+(BASE/'profiles/memory.txt').read_text(encoding='utf8').strip()
            assert read(folder/'input.json') == inputs and instruction == ISOLATION+task
        else:
            name = 'source_audit' if phase.startswith('source_audit_') else phase
            assert instruction == ISOLATION+prompt(name)
    # Independently reconstruct deterministic planner normalization.
    output = read(workspace/'planner/output.json'); by_id = {r['id']: r for r in sources()}; normalized = []; drops = []
    for work in output['works']:
        entries = []
        for entry in work['glossary']:
            original = by_id.get(entry['source_id'])
            joined = '\n'.join(original[k] for k in ['context_before', 'source', 'context_after']) if original else ''
            supported = bool(original and original['work_id'] == work['work_id'] and entry['evidence'] and entry['evidence'] in joined)
            if supported and len(entry['russian'].split()) <= 6 and len(entries) < 4:
                entries.append(entry)
            else:
                drops.append({'work_id': work['work_id'], 'entry': entry, 'reason': 'unsupported, oversized or beyond4entrybudget'})
        normalized.append({'work_id': work['work_id'], 'brief': ' '.join(work['brief'].split()[:80]),
                           'glossary': entries, 'unresolved': work['unresolved'][:3]})
    assert read(workspace/'brief-used.json') == {'works': normalized, 'dropped': drops,
        'parent_output_sha256': sha((workspace/'planner/output.json').read_bytes())}
    if require_audits:
        reconstruct(workspace, config)
    assert len(list(workspace.glob('*/attempt.json'))) <= 36
    return manifests
