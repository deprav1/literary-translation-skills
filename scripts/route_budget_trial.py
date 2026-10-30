"""Versioned routing correction: carry every actual audit trigger to retranslation."""
from __future__ import annotations

import argparse

from run_budget_trial import (ROOT, BASE, read, write, sources, call, prompt, translation_schema,
    normalize_translation, sha, audit_schema, validate_audit, schema_object, array, STRING)
from analyze_budget_trial import score, flags, production_audit
from verify_budget_trial import verify
from translation_economics import manifest_cost, pipeline_cost
from budget_economic_gate import gate


def check_amendment():
    frozen = read(BASE/'routing-amendment.json')
    for name, digest in frozen['code_sha256'].items():
        assert sha((ROOT/name).read_bytes()) == digest, name


def route_one(workspace, config, family, method):
    check_amendment()
    originals = {r['id']: r for r in sources()}; initial = read(workspace/method/'normalized.json')
    current = {r['id']: r['text'] for r in initial['items']}; coverage = initial['coverage']
    provenance = {id: method for id in originals}; aid = []; corrections = []; history = []
    audit_name = 'online_'+family+'_0'
    output = production_audit(workspace, config, audit_name, current, sources()); aid.append(audit_name)
    flagged = flags(output, coverage); history.append({'audit': audit_name, 'flagged': flagged})
    for level, role in enumerate(config['escalation'].get(family, ['anchor']), 1):
        if not flagged:
            break
        rows = [originals[id] for id in sorted(flagged)]
        inputs = {'items': [{**r, 'previous_translation': current[r['id']],
            'audit_issues': [f for f in output['issues'] if f['source_id'] == r['id']],
            'unresolved_meaning': [f for f in output['unresolved'] if f['source_id'] == r['id']],
            'operational_trigger': flagged[r['id']]} for r in rows]}
        if method.endswith(('_brief', '_memory')):
            inputs['work_briefs'] = read(workspace/'brief-used.json')['works']
        phase = 'correct_'+family+'_'+str(level)
        raw = call(workspace, phase, config['models'][role], prompt('escalate'), inputs, translation_schema())
        normalized = normalize_translation(raw, rows); write(workspace/phase/'normalized.json', normalized)
        for row in normalized['items']:
            current[row['id']] = row['text']; provenance[row['id']] = phase
        corrections.append(phase); audit_name = 'online_'+family+'_'+str(level)
        output = production_audit(workspace, config, audit_name, current, rows); aid.append(audit_name)
        flagged = flags(output, normalized['coverage']); history.append({'audit': audit_name, 'flagged': flagged})
    accepted = sum(len(r['source'].split()) for id, r in originals.items() if id not in flagged)
    prices = config['pricing']; accounting = {}
    for cold in [False, True]:
        guided = method.endswith(('_brief', '_memory'))
        accounting['cold' if cold else 'cache_adjusted'] = pipeline_cost(
            planner=manifest_cost(read(workspace/'planner/manifest.json'), prices, cold=cold) if guided else 0,
            translator=manifest_cost(read(workspace/method/'manifest.json'), prices, cold=cold),
            audits=[manifest_cost(read(workspace/n/'manifest.json'), prices, cold=cold) for n in aid],
            escalations=[manifest_cost(read(workspace/n/'manifest.json'), prices, cold=cold) for n in corrections],
            accepted_words=accepted, requested_words=sum(len(r['source'].split()) for r in sources()))
    receipt = {'family': family, 'selected': method, 'history': history, 'accounting': accounting,
        'final_items': [{'id': id, 'text': current[id], 'origin': provenance[id], 'model_accepted': id not in flagged} for id in originals],
        'unresolved_flags': flagged, 'audits_charged': aid, 'corrections_charged': corrections,
        'human_acceptance': False, 'routing_version': 'all-trigger-evidence-v1'}
    write(workspace/'route-'+family+'.json', receipt)


def final_pairs(workspace, config):
    import random
    anchor = {r['id']: r for r in read(workspace/'route-anchor.json')['final_items']}
    items = []; mapping = {}; pairs = []; rng = random.Random(20261032)
    for source in sources():
        candidates = [{'candidate_id': 'a'+source['id'], 'text': anchor[source['id']]['text']}]
        for family in ['terra', 'luna']:
            result = next(r for r in read(workspace/('route-'+family+'.json'))['final_items'] if r['id'] == source['id'])
            cid = family[0]+source['id']; candidates.append({'candidate_id': cid, 'text': result['text']})
            order = [cid, 'a'+source['id']]; rng.shuffle(order); pid = family+':'+source['id']
            mapping[pid] = {'family': family, 'source_id': source['id'], 'A': order[0], 'B': order[1], 'treatment': cid}
            if ' '.join(result['text'].split()) == ' '.join(anchor[source['id']]['text'].split()):
                mapping[pid]['forced_tie'] = True
            else:
                pairs.append({'pair_id': pid, 'source_id': source['id'], 'A': order[0], 'B': order[1]})
        rng.shuffle(candidates); items.append({**source, 'candidates': candidates})
    rng.shuffle(pairs); write(workspace/'final-pair-mapping.json', mapping)
    task = prompt('prose_audit')
    output = call(workspace, 'final_prose', config['models']['auditor'], task,
                  {'items': items, 'pairs': pairs}, audit_schema(prose=True))
    validate_audit(output, items, pairs=pairs)
    losses = {'terra': 0, 'luna': 0}; counts = {'terra': {'wins': 0, 'losses': 0, 'ties': 0, 'unclear': 0},
                                              'luna': {'wins': 0, 'losses': 0, 'ties': 0, 'unclear': 0}}
    votes = {r['pair_id']: r['choice'] for r in output['pairs']}
    for pid, pair in mapping.items():
        choice = 'tie' if pair.get('forced_tie') else votes[pid]
        label = ('wins' if pair[choice] == pair['treatment'] else 'losses') if choice in ['A', 'B'] else ('ties' if choice == 'tie' else 'unclear')
        counts[pair['family']][label] += 1
    write(workspace/'final-prose-counts.json', counts)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=__import__('pathlib').Path, required=True)
    args = parser.parse_args(); workspace = args.workspace.resolve(); check_amendment()
    verify(workspace); config = read(BASE/'protocol.json'); result = score(workspace, config)
    for family, method in [*result['selected'].items(), ('anchor', 'sol_anchor')]:
        route_one(workspace, config, family, method)
    counts = final_pairs(workspace, config); outcomes = {}
    anchor = read(workspace/'route-anchor.json')
    for family in ['terra', 'luna']:
        outcomes[family] = gate(calibration_pass=result['calibration']['pass'],
            route=read(workspace/('route-'+family+'.json')), anchor_route=anchor,
            prose_losses=counts[family]['losses'], corpus_items=30)
    write(workspace/'economic-gates.json', outcomes)
    print(outcomes)


if __name__ == '__main__':
    main()
