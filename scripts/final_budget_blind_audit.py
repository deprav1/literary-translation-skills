"""Mask final routed-model identifiers before the final prose comparison."""
from __future__ import annotations

import random
from pathlib import Path

from run_budget_trial import BASE, read, write, sources, sha, prompt, audit_schema, call
from budget_coverage_adapter import activate, validate_with_empty


def final_pairs(workspace, config):
    anchor = {r['id']: r for r in read(workspace/'route-anchor.json')['final_items']}
    items = []; mapping = {}; pairs = []; rng = random.Random(20261032)
    for source in sources():
        acid = 'v'+sha(('finalanchor'+source['id']).encode())[:14]
        candidates = [{'candidate_id': acid, 'text': anchor[source['id']]['text']}]
        for family in ['terra', 'luna']:
            result = next(r for r in read(workspace/('route-'+family+'.json'))['final_items'] if r['id'] == source['id'])
            cid = 'v'+sha(('final'+family+source['id']).encode())[:14]
            candidates.append({'candidate_id': cid, 'text': result['text']})
            order = [cid, acid]; rng.shuffle(order)
            pid = 'p'+sha(('finalpair'+family+source['id']).encode())[:14]
            mapping[pid] = {'family': family, 'source_id': source['id'], 'A': order[0], 'B': order[1], 'treatment': cid}
            if ' '.join(result['text'].split()) == ' '.join(anchor[source['id']]['text'].split()):
                mapping[pid]['forced_tie'] = True
            else:
                pairs.append({'pair_id': pid, 'source_id': source['id'], 'A': order[0], 'B': order[1]})
        rng.shuffle(candidates); items.append({**source, 'candidates': candidates})
    rng.shuffle(pairs); write(workspace/'final-pair-mapping.json', mapping)
    inputs = {'items': items, 'pairs': pairs}
    # Generated metadata carries no model names. Source fiction can contain any words.
    assert all('terra' not in r['pair_id'] and 'luna' not in r['pair_id'] for r in pairs)
    output = call(workspace, 'final_prose', config['models']['auditor'], prompt('prose_audit'), inputs, audit_schema(prose=True))
    validate_with_empty(output, items, pairs=pairs)
    counts = {f: {'wins': 0, 'losses': 0, 'ties': 0, 'unclear': 0} for f in ['terra', 'luna']}
    votes = {r['pair_id']: r['choice'] for r in output['pairs']}
    for pid, pair in mapping.items():
        choice = 'tie' if pair.get('forced_tie') else votes[pid]
        label = ('wins' if pair[choice] == pair['treatment'] else 'losses') if choice in ['A', 'B'] else ('ties' if choice == 'tie' else 'unclear')
        counts[pair['family']][label] += 1
    write(workspace/'final-prose-counts.json', counts)
    return counts


def main():
    amendment = read(BASE/'final-mask-amendment.json')
    assert amendment['adapter_sha256'] == sha(Path(__file__).read_bytes())
    activate()
    import route_budget_trial as routing
    routing.validate_audit = validate_with_empty
    routing.final_pairs = final_pairs
    routing.main()


if __name__ == '__main__':
    main()
