"""Do not mistake a clean online audit for absence of known retained errors."""
from __future__ import annotations

from collections import defaultdict

from run_budget_trial import read, write, sources
from analyze_budget_trial import deduplicate, SEMANTIC


def canon(text):
    return ' '.join(text.replace('*', '').split())


def assess(workspace):
    scored = read(workspace/'scored.json'); mapping = read(workspace/'candidate-mapping.json')
    receipts = {family: read(workspace/('route-'+family+'.json')) for family in ['terra', 'luna', 'anchor']}
    residual = defaultdict(list)
    for family, receipt in receipts.items():
        texts = {r['id']: r['text'] for r in receipt['final_items']}
        for issue in scored['accepted_issues']:
            if issue['source_id'] not in texts or issue['candidate_id'] not in mapping:
                continue
            if receipt['selected'] not in mapping[issue['candidate_id']] or issue['category'] not in SEMANTIC:
                continue
            if issue['target_quote'] and canon(issue['target_quote']) in canon(texts[issue['source_id']]):
                residual[family].append(issue)
    pairs = read(workspace/'final-pair-mapping.json'); candidate_family = {}
    for pair in pairs.values():
        candidate_family[pair['treatment']] = pair['family']
        other = pair['B'] if pair['A'] == pair['treatment'] else pair['A']
        candidate_family[other] = 'anchor'
    pending = defaultdict(list)
    for issue in read(workspace/'final_prose/output.json')['issues']:
        if issue['category'] in SEMANTIC and issue['severity'] in ['major', 'critical']:
            pending[candidate_family[issue['candidate_id']]].append(issue)
    words = sum(len(r['source'].split()) for r in sources()); details = {}
    for family in receipts:
        unique = {}; critical = 0; major = 0
        for issue in residual[family]:
            key = (issue['source_id'], issue['category'], canon(issue['source_quote']))
            if key not in unique or issue['severity'] == 'critical':
                unique[key] = issue
        issues = list(unique.values()); major = sum(r['severity'] == 'major' for r in issues)
        critical = sum(r['severity'] == 'critical' for r in issues)
        final = receipts[family]['final_items']
        details[family] = {'retained_research_confirmed_issues': issues, 'known_major': major, 'known_critical': critical,
            'known_major_critical_per1000words': (major+critical)*1000/words,
            'pending_final_semantic_major_proposals': pending[family],
            'original_translator_word_fraction': sum(len(next(s for s in sources() if s['id'] == r['id'])['source'].split())
                                                   for r in final if r['origin'] == receipts[family]['selected'])/words}
    original_gates = read(workspace/'economic-gates.json'); verdicts = {}
    for family in ['terra', 'luna']:
        conditions = {'no_known_critical': details[family]['known_critical'] == 0,
            'known_major_density_margin': details[family]['known_major_critical_per1000words'] <= details['anchor']['known_major_critical_per1000words']+.5,
            'no_pending_final_major_claims': not pending[family] and not pending['anchor']}
        verdicts[family] = {'original_operational_gate': original_gates[family]['development_economic_gate'],
            'additional_quality_conditions': conditions,
            'development_quality_cost_signal': original_gates[family]['development_economic_gate'] and all(conditions.values()),
            'scope': 'Development signal only. Retained exact spans prove persistence, not that all absent spans or all unreported errors are fixed.'}
    result = {'quality': details, 'verdicts': verdicts,
              'principle': 'Research error knowledge vetoes unsafe conclusions; it is not free input to production routing and does not create extra correction calls.'}
    write(workspace/'quality-cost-verdict.json', result)
    return result
