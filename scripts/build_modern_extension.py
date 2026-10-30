"""Extend the frozen classic pilot with an independently generated modern batch."""
import json
from pathlib import Path
from build_blind_catalog import digest, load

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'site/research'
EVIDENCE = 'fresh-modern-20261030'


def assemble():
    archive = load(RESEARCH/'archive-v5.json')
    selected = load(RESEARCH/'modern.json')
    record = load(RESEARCH/EVIDENCE/'record.json')
    outputs = {method: load(RESEARCH/EVIDENCE/method/'output.json')['translations']
               for method in ['baseline', 'skilled', 'reviewed']}
    expected = {row['id'] for row in selected}
    assert len(expected) == len(selected) == 8
    for rows in outputs.values():
        assert len(rows) == len(expected) and {row['id'] for row in rows} == expected
    translations = {method: {row['id']: row['text'] for row in rows} for method, rows in outputs.items()}
    rounds = list(archive['data']['rounds'])
    for row in selected:
        candidates = []
        for method in record['poll_methods']:
            text = row['human_text'] if method == 'published' else translations[method][row['id']]
            candidates.append({
                'id': digest([row['id'], method, text])[:16], 'method': method, 'text': text,
                'credit': row['translator'] if method == 'published' else 'GPT-6.1 Sol · medium · 30.10.2026',
                'note': ('Опубликованный перевод; текст не исправлялся для сравнения. ' if method == 'published'
                         else 'Новая изолированная генерация без опубликованного перевода во входе. ')
                        + 'Кори Доктороу · 2006 · CC BY-NC-SA 2.5. AI-переводы — производные версии.',
                'sourceUrl': row['human_url'] if method == 'published' else './METHODS.json',
                'license': row['license'], 'licenseUrl': row['license_url'],
            })
        eligible = ' '.join(translations['baseline'][row['id']].split()) != ' '.join(translations['reviewed'][row['id']].split())
        rounds.append({'id': row['id'], 'author': row['author'], 'title': row['title'],
                       'tag': '2006 · ' + row['tag'], 'source': row['source_text'],
                       'sourceUrl': row['source_url'], 'comparisonGroup': 'isolated',
                       'votingEligible': eligible, 'workId': 'sysadmin', 'era': 'contemporary',
                       'candidates': candidates})
    version = 'blind-v6-' + digest([archive['data'], selected, outputs, record])[:12]
    data = {**archive['data'], 'version': version, 'previousDataset': archive['data']['version'],
            'rounds': rounds, 'featuredWorkIds': ['sysadmin']}
    registry = {r['id']: {c['id']: c['method'] for c in r['candidates']}
                for r in rounds if r['votingEligible']}
    methods = {
        'dataset': version, 'generated_on': '2026-10-30',
        'selection': '40 frozen classic excerpts plus 8 fixed excerpts from one 2006 story. Convenience preference pilot, not a representative benchmark.',
        'model': record['model'], 'reasoning_effort': record['reasoning_effort'],
        'poll_methods': record['poll_methods'], 'voting_fragments': len(registry),
        'generation_records': ['research/fresh-v5/record.json', f'research/{EVIDENCE}/record.json'],
        'classic_methodology': 'research/archive-v5.json',
        'same_source_context_within_each_batch': True, 'reference_translations_supplied': False,
        'primary_agent_text_edits': False, 'best_of_selection': False, 'human_editing': False,
        'qualification': archive['methods']['qualification'],
        'modern_batch': {'fragments': len(selected), 'works': 1, 'year': 2006,
                         'qa_changed_fragments': len(record['qa_changed_fragment_ids']),
                         'license': 'CC BY-NC-SA 2.5', 'record': f'research/{EVIDENCE}/record.json',
                         'source_context': 'Complete English story, excluding foreword and licence text. No published Russian input.',
                         'limits': 'One contemporary author and one story. Not representative of contemporary literature. Russian attribution and licence are asserted by two digital mirrors; original Computerra publication was not inspected.'},
        'cohorts': 'Up to 20 passages; eligible modern passages are included first, then classic works. No repeat overlapping excerpts.',
        'voting_eligibility': archive['methods']['voting_eligibility'] + ' The same duplicate rule applies to the modern batch.',
        'interpretation': 'Preferences for these frozen outputs only. Era, author and genre are confounded; do not attribute differences between works to skills. Results can be filtered by work.',
    }
    return data, methods, registry


def main():
    data, methods, registry = assemble()
    legacy_path = RESEARCH/'legacy_catalog.json'
    legacy = load(legacy_path)
    classic = load(RESEARCH/'archive-v5.json')['data']
    legacy[classic['version']] = {r['id']: {c['id']: c['method'] for c in r['candidates']}
                                 for r in classic['rounds'] if r['votingEligible']}
    for path, value in [(ROOT/'site/data.json', data), (ROOT/'site/METHODS.json', methods), (legacy_path, legacy)]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    (ROOT/'backend/catalog.js').write_text('// Generated versioned candidate allowlist.\nexport const DATASETS = '+json.dumps({**legacy, data['version']: registry}, ensure_ascii=False, indent=2)+';\n', encoding='utf8')
    print(json.dumps({'dataset': data['version'], 'rounds': len(data['rounds']), 'eligible': len(registry)}))


if __name__ == '__main__':
    main()
