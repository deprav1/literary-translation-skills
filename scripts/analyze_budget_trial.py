"""Frozen pilot scoring and charged online routing for Terra/Luna translation."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from run_budget_trial import (BASE, read, write, sources, call, prompt, translation_schema,
    audit_schema, validate_audit, normalize_translation, sha, check_frozen)
from translation_economics import manifest_cost, pipeline_cost

SEMANTIC = {'omission', 'addition', 'actor', 'negation_modality', 'number', 'time_direction', 'term_sense', 'speech_form', 'other'}
SEVERITY = {'minor': 1, 'major': 2, 'critical': 3}


def deduplicate(issues):
    result = {}
    for issue in issues:
        key = (issue['source_id'], issue['candidate_id'], issue['category'], issue['source_quote'])
        if key not in result or SEVERITY[issue['severity']] > SEVERITY[result[key]['severity']]:
            result[key] = issue
    return list(result.values())


def flags(output, coverage):
    result = defaultdict(set); counts = Counter()
    for issue in deduplicate(output['issues']):
        if issue['category'] not in SEMANTIC and issue['severity'] == 'minor':
            continue
        if issue['severity'] in ['major', 'critical']:
            result[issue['source_id']].add(issue['severity'])
        elif issue['category'] in SEMANTIC:
            counts[issue['source_id']] += 1
    for row in output['unresolved']:
        result[row['source_id']].add('unresolved')
    for id, count in counts.items():
        if count >= 2:
            result[id].add('two_minor')
    for id in coverage['missing']+coverage['wrong_language_or_empty']:
        result[id].add('coverage')
    for row in coverage['duplicates']:
        if row['conflicting']:
            result[row['id']].add('conflicting_duplicate')
    return {k: sorted(v) for k, v in result.items()}


def score(workspace, config):
    check_frozen(); items = sources(); ids = {r['id'] for r in items}; words = sum(len(r['source'].split()) for r in items)
    methods = ['sol_anchor']+[f+'_'+a for f in ['terra', 'luna'] for a in config['arms']]
    mapping = read(workspace/'candidate-mapping.json')
    proposed = {r['issue_id']: r for r in read(workspace/'issue-proposals.json')}
    decisions = read(workspace/'adjudicate/output.json')['decisions']; accepted = []; deferred = []
    assert len(decisions) == len(proposed) and {r['issue_id'] for r in decisions} == set(proposed)
    for decision in decisions:
        issue = {**proposed[decision['issue_id']], 'category': decision['category'], 'severity': decision['severity'],
                 'adjudication_reason': decision['reason']}
        if decision['decision'] == 'accept':
            accepted.append(issue)
        elif decision['decision'] == 'defer':
            deferred.append(issue)
    accepted = deduplicate(accepted)
    control = read(workspace/'calibration-mapping.json'); actual = {r['candidate_id'] for r in accepted}
    cal_correct = sum((cid in actual) == row['expected_issue'] for cid, row in control.items())
    false_major = any(r['candidate_id'] in control and not control[r['candidate_id']]['expected_issue']
                      and r['severity'] in ['major', 'critical'] for r in accepted)
    cal_pass = cal_correct >= 5 and not false_major
    normalized = {m: read(workspace/m/'normalized.json') for m in methods}
    by_method = {m: [r for r in accepted if r['source_id'] in ids and m in mapping[r['candidate_id']]] for m in methods}
    results = {}
    for method in methods:
        issues = by_method[method]
        counts = Counter(r['severity'] for r in issues if r['category'] in SEMANTIC)
        cov = normalized[method]['coverage']
        invalid = set(cov['missing']+cov['wrong_language_or_empty']+[r['id'] for r in cov['duplicates'] if r['conflicting']])
        counts['critical'] += len(invalid)
        results[method] = {'semantic_counts': dict(counts), 'major_critical_per1000words': (counts['major']+counts['critical'])*1000/words,
            'russian_issues': sum(r['category'] in ['calque_collocation', 'grammar', 'voice_rhythm'] for r in issues),
            'calques': sum(r['category'] == 'calque_collocation' for r in issues), 'coverage': cov,
            'deferred': sum(r['source_id'] in ids and method in mapping[r['candidate_id']] for r in deferred),
            'cold_translation_usd': manifest_cost(read(workspace/method/'manifest.json'), config['pricing'], cold=True)}
    pair_map = read(workspace/'pair-mapping.json'); pair_votes = {r['pair_id']: r for r in read(workspace/'prose_audit/output.json')['pairs']}
    comparisons = {}
    for name, (treatment, baseline) in config['pair_comparisons'].items():
        rows = []
        for pid, pair in pair_map.items():
            if pair['comparison'] != name:
                continue
            choice = 'tie' if pair.get('forced_tie') else pair_votes[pid]['choice']
            winner = pair[choice] if choice in ['A', 'B'] else choice
            rows.append({'id': pair['source_id'], 'decision': winner,
                         'reason': 'Exact duplicate texts' if pair.get('forced_tie') else pair_votes[pid]['reason']})
        count = Counter(r['decision'] for r in rows)
        comparisons[name] = {'wins': count[treatment], 'losses': count[baseline], 'ties': count['tie'],
                             'unclear': count['unclear'], 'net': count[treatment]-count[baseline], 'items': rows}
    planner_cost = manifest_cost(read(workspace/'planner/manifest.json'), config['pricing'], cold=True)
    selection = {}
    for family in ['terra', 'luna']:
        baseline = family+'_plain'; options = []
        for arm in config['arms'][1:]:
            method = family+'_'+arm; own = by_method[method]; previous = by_method[baseline]
            previous_keys = {(r['source_id'], r['category'], r['source_quote']) for r in previous}
            new_issues = [r for r in own if r['category'] in SEMANTIC
                          and (r['source_id'], r['category'], r['source_quote']) not in previous_keys]
            new_major = sum(r['severity'] in ['major', 'critical'] for r in new_issues)
            own_counts = Counter(r['source_id'] for r in own if r['category'] in SEMANTIC)
            prev_counts = Counter(r['source_id'] for r in previous if r['category'] in SEMANTIC)
            improved = sum(own_counts[id] < prev_counts[id] for id in ids)
            comp = comparisons[method+'_vs_plain']
            per_work = {work: sum((r['decision'] == method)-(r['decision'] == baseline) for r in comp['items']
                                  if next(s for s in items if s['id'] == r['id'])['work_id'] == work)
                        for work in {s['work_id'] for s in items}}
            quality_signal = (cal_pass and results[method]['coverage']['pass'] and new_major == 0
                and sum(r['severity'] == 'minor' for r in new_issues) <= 1
                and (improved >= 2 or (comp['net'] >= 2 and results[method]['calques'] <= results[baseline]['calques']))
                and sum(net >= 0 for net in per_work.values()) >= 2)
            guided_cost = results[method]['cold_translation_usd']+(planner_cost if arm in ['brief', 'memory'] else 0)
            cap = 1.25 if arm == 'guard' else 1.5
            economical = guided_cost <= results[baseline]['cold_translation_usd']*cap
            results[method]['pilot'] = {'quality_signal': quality_signal, 'cost_cap_pass': economical,
                'improved_fidelity_items': improved, 'new_major_critical': new_major,
                'new_minor': sum(r['severity'] == 'minor' for r in new_issues), 'per_work_preference_net': per_work,
                'cold_translation_and_fullplanner_usd': guided_cost}
            if quality_signal and economical:
                rank = (results[method]['semantic_counts'].get('critical', 0), results[method]['semantic_counts'].get('major', 0),
                        sum(results[method]['semantic_counts'].values()), comparisons[method+'_vs_anchor']['losses'], guided_cost, arm)
                options.append((rank, method))
        selection[family] = min(options)[1] if options else baseline
    result = {'model_results': results, 'comparisons': comparisons, 'selected': selection,
        'calibration': {'correct': cal_correct, 'total': 6, 'false_major': false_major, 'pass': cal_pass},
        'source_words': words, 'accepted_issues': accepted, 'deferred_issues': deferred,
        'candidate_promotion': 'None: development corpus and model audit only.'}
    write(workspace/'scored.json', result)
    return result


def production_audit(workspace, config, phase, translated, rows):
    items = []; candidate_to_source = {}
    for source in rows:
        cid = 'v'+sha((phase+source['id']).encode())[:14]; candidate_to_source[cid] = source['id']
        items.append({**source, 'candidates': [{'candidate_id': cid, 'text': translated[source['id']]}]})
    result = call(workspace, phase, config['models']['auditor'], prompt('production_audit'), {'items': items}, audit_schema())
    validate_audit(result, items)
    return result


def route_one(workspace, config, family, method):
    items = sources(); originals = {r['id']: r for r in items}
    result = read(workspace/method/'normalized.json'); current = {r['id']: r['text'] for r in result['items']}
    provenance = {r['id']: method for r in items}; coverage = result['coverage']
    audit_name = 'online_'+family+'_0'
    output = production_audit(workspace, config, audit_name, current, items)
    flagged = flags(output, coverage); history = [{'audit': audit_name, 'flagged': flagged}]
    chain = config['escalation'].get(family, ['anchor'])
    aid = [audit_name]; corrections = []
    for level, role in enumerate(chain, 1):
        if not flagged:
            break
        rows = [originals[id] for id in sorted(flagged)]
        inputs = {'items': [{**r, 'previous_translation': current[r['id']],
                             'audit_issues': [f for f in output['issues'] if f['source_id'] == r['id']]} for r in rows]}
        if method.endswith(('_brief', '_memory')):
            inputs['work_briefs'] = read(workspace/'brief-used.json')['works']
        phase = 'correct_'+family+'_'+str(level)
        translated = call(workspace, phase, config['models'][role], prompt('escalate'), inputs, translation_schema())
        normalized = normalize_translation(translated, rows); write(workspace/phase/'normalized.json', normalized)
        for r in normalized['items']:
            current[r['id']] = r['text']; provenance[r['id']] = phase
        corrections.append(phase); audit_name = 'online_'+family+'_'+str(level)
        output = production_audit(workspace, config, audit_name, current, rows); aid.append(audit_name)
        flagged = flags(output, normalized['coverage']); history.append({'audit': audit_name, 'flagged': flagged})
    accepted_words = sum(len(r['source'].split()) for r in items if r['id'] not in flagged)
    planner = read(workspace/'planner/manifest.json') if method.endswith(('_brief', '_memory')) else None
    prices = config['pricing']; accounting = {}
    for cold in [False, True]:
        accounting['cold' if cold else 'cache_adjusted'] = pipeline_cost(
            planner=manifest_cost(planner, prices, cold=cold) if planner else 0,
            translator=manifest_cost(read(workspace/method/'manifest.json'), prices, cold=cold),
            audits=[manifest_cost(read(workspace/n/'manifest.json'), prices, cold=cold) for n in aid],
            escalations=[manifest_cost(read(workspace/n/'manifest.json'), prices, cold=cold) for n in corrections],
            accepted_words=accepted_words, requested_words=sum(len(r['source'].split()) for r in items))
    receipt = {'family': family, 'selected': method, 'history': history, 'accounting': accounting,
        'final_items': [{'id': r['id'], 'text': current[r['id']], 'origin': provenance[r['id']],
                         'model_accepted': r['id'] not in flagged} for r in items],
        'unresolved_flags': flagged, 'audits_charged': aid, 'corrections_charged': corrections,
        'human_acceptance': False}
    write(workspace/'route-'+family+'.json', receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--route', action='store_true')
    args = parser.parse_args(); workspace = args.workspace.resolve(); config = read(BASE/'protocol.json')
    result = score(workspace, config)
    if args.route:
        for family, method in [*result['selected'].items(), ('anchor', 'sol_anchor')]:
            route_one(workspace, config, family, method)
    print({k: result[k] for k in ['selected', 'calibration', 'source_words', 'candidate_promotion']})


if __name__ == '__main__':
    main()
