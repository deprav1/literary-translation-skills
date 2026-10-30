"""Verify v5 corpus transport, generation evidence and historical catalogs."""
import hashlib
import json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
RESEARCH=SITE/'research'
FRESH=RESEARCH/'fresh-v5'
PHASES=['baseline','plan','pilot','calibration','skilled','critique','reviewed','evaluation']


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode('utf8')).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    data=load(SITE/'data.json'); methods=load(SITE/'METHODS.json')
    selected=load(RESEARCH/'selected.json')+load(RESEARCH/'corpus_candidates.json')
    generations={name:load(FRESH/name/'output.json')['translations'] for name in ['baseline','skilled','reviewed']}
    record=load(FRESH/'record.json'); legacy=load(RESEARCH/'legacy_catalog.json')
    assert data['version']=='blind-v5-'+digest([selected,generations,record])[:12]
    assert methods['dataset']==data['version'] and methods['reference_translations_supplied'] is False
    assert methods['primary_agent_text_edits'] is False and methods['best_of_selection'] is False
    expected={row['id'] for row in selected}
    assert len(expected)==len(selected)==len(data['rounds'])==40 and data['cohortSize']==20
    assert set(record['fragment_work_ids'])==expected
    assert set(record['source_alignment']['checked_ids'])==expected
    assert all(record['source_alignment']['fragment_sha256'][row['id']]==hashlib.sha256(row['source_text'].encode()).hexdigest() for row in selected)
    for rows in generations.values():
        assert len(rows)==len(expected) and {row['id'] for row in rows}==expected
    stages={row['phase']:row for row in record['stages']}
    assert set(stages)==set(PHASES)
    session_hashes=set()
    for phase in PHASES:
        manifest=load(FRESH/phase/'manifest.json')
        assert manifest['output_sha256']==hashlib.sha256((FRESH/phase/'output.json').read_bytes()).hexdigest()
        assert manifest['tool_calls']==0 and manifest['exit_code']==0 and manifest['fresh_session']
        assert manifest['model']==record['model'] and manifest['reasoning_effort']==record['reasoning_effort']
        assert stages[phase]['status']=='done' and stages[phase]['output_sha256']==manifest['output_sha256']
        assert set(manifest['observed_runtime_item_types']) <= {'agent_message','reasoning','error'}
        session_hashes.add(manifest['session_id_sha256'])
    assert len(session_hashes)==len(PHASES)
    assert load(FRESH/'baseline/manifest.json')['skill_files_sha256']=={}
    for phase in ['baseline','skilled','reviewed']:
        manifest=load(FRESH/phase/'manifest.json')
        assert manifest['source_pack_sha256']==record['source_pack_sha256']
        assert record['outputs'][phase]==manifest['output_sha256']
    for phase in ['critique','evaluation']:
        audit=load(FRESH/phase/'output.json')
        assert len(audit['coverage'])==len(expected) and set(audit['coverage'])==expected
        assert all(finding['id'] in expected and finding['reason'] for finding in audit['findings'])
    review=load(FRESH/'reviewed/output.json'); critique=load(FRESH/'critique/output.json')
    assert len(review['decisions'])==len(critique['findings'])
    assert {d['finding_id'] for d in review['decisions']}=={f['finding_id'] for f in critique['findings']}
    assert all(d['decision'] in {'accept','edit','reject','defer'} and d['reason'] for d in review['decisions'])
    by_id={row['id']:row for row in selected}
    by_method={method:{row['id']:row['text'] for row in rows} for method,rows in generations.items()}
    changed={id for id in expected if by_method['skilled'][id]!=by_method['reviewed'][id]}
    accepted={d['finding_id'] for d in review['decisions'] if d['decision'] in {'accept','edit'}}
    assert changed=={finding['id'] for finding in critique['findings'] if finding['finding_id'] in accepted}
    assert changed<=set(review['post_edit_checked_ids'])
    registry={}
    for row in data['rounds']:
        assert row['id'] in expected and row['source']==by_id[row['id']]['source_text']
        assert row['comparisonGroup']=='isolated' and row['workId']==record['fragment_work_ids'][row['id']]
        assert len(row['candidates'])==3 and {c['method'] for c in row['candidates']}==set(record['poll_methods'])
        assert len({c['id'] for c in row['candidates']})==3
        eligible=' '.join(by_method['baseline'][row['id']].split())!=' '.join(by_method['reviewed'][row['id']].split())
        assert row['votingEligible']==eligible
        if eligible:
            registry[row['id']]={c['id']:c['method'] for c in row['candidates']}
        for candidate in row['candidates']:
            text=by_id[row['id']]['human_text'] if candidate['method']=='published' else by_method[candidate['method']][row['id']]
            assert candidate['text']==text and len(text)>20
            assert candidate['id']==digest([row['id'],candidate['method'],text])[:16]
            assert urlsplit(candidate['sourceUrl']).scheme=='https'
    catalog=load_catalog(ROOT/'backend/catalog.js')
    assert catalog=={**legacy,data['version']:registry} and data['previousDataset'] in legacy
    anchors={'wilde-extra-01':('walls of a round city','стены круглого города'), 'wilde-extra-02':('many lutes','многих лютней'), 'wilde-extra-07':('a young man who wore a cloak','юноша в двухцветном плаще'), 'wilde-extra-08':('touched the hand','коснулся руки'), 'wilde-extra-09':('I was blind once','я был слепым'), 'wilde-extra-10':('painted raiment','разрисованной одежды'), 'wilde-extra-11':('you forgave me my sins','отпустил мне грехи'), 'wilde-extra-12':('passed out of the city','вышел из города'), 'cat-01':('to-morrow I die','завтра я умру'), 'cat-06':('gold-fish','золотая рыбка'), 'cat-07':("Pluto—this was the cat's name",'Плутон — так назывался кот'), 'cat-10':('splotch of white','белое пятно')}
    for id,(en,ru) in anchors.items():
        assert en.lower() in by_id[id]['source_text'].lower() and ru.lower() in by_id[id]['human_text'].lower(), f'misaligned pair: {id}'
    class Assets(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for attr,value in attrs:
                if attr not in {'src','href'} or not value or urlsplit(value).scheme or value.startswith('#'): continue
                path=(SITE/unquote(urlsplit(value).path)).resolve()
                assert path.is_relative_to(SITE.resolve()) and path.exists(), value
    Assets().feed((SITE/'index.html').read_text(encoding='utf8'))
    for font in (SITE/'assets/fonts').glob('*.woff2'):
        assert font.read_bytes()[:4]==b'wOF2'
    assert len(registry)==36 and methods['voting_fragments']==36
    assert {row['id'] for row in data['rounds'] if not row['votingEligible']}==set(record['non_voting_fragments'])
    print(json.dumps({'dataset':data['version'],'rounds':len(data['rounds']),'voting_fragments':len(registry),'translations':120,'generation_stages':len(stages),'baseline_skill_instructions':0,'context_consistent':True,'catalog_consistent':True,'limits':'Evidence and packaging checks do not prove literary quality or eliminate training-data contamination.'}))


def load_catalog(path):
    return json.loads(path.read_text(encoding='utf8').split('export const DATASETS = ',1)[1].strip().rstrip(';'))


if __name__=='__main__':
    main()
