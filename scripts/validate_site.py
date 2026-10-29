"""Check the published pilot corpus and its backend allowlist; no literary score claimed."""
import json,hashlib,re,sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode('utf8')).hexdigest()
def main():
    data=json.loads((SITE/'data.json').read_text(encoding='utf8'));methods=json.loads((SITE/'METHODS.json').read_text(encoding='utf8'));selected=json.loads((SITE/'research/selected.json').read_text(encoding='utf8'))+json.loads((SITE/'research/corpus_candidates.json').read_text(encoding='utf8'))
    skilled=json.loads((SITE/'research/skilled.json').read_text(encoding='utf8'));baseline=json.loads((SITE/'research/baseline.json').read_text(encoding='utf8'));reviewed=json.loads((SITE/'research/reviewed.json').read_text(encoding='utf8'));legacy=json.loads((SITE/'research/legacy_catalog.json').read_text(encoding='utf8'))
    assert data['version']=='blind-v3-'+digest([selected,skilled,baseline,reviewed])[:12]
    assert methods['dataset']==data['version'] and methods['manual_postediting'] is False
    assert len(data['rounds'])>=30 and data.get('cohortSize')==20 and len({r['id'] for r in data['rounds']})==len(data['rounds'])
    registry={};original={r['id']:r for r in selected};s={r['id']:r['text'] for r in skilled};b={r['id']:r['text'] for r in baseline};v={r['id']:r['text'] for r in reviewed}
    for r in data['rounds']:
        assert len(r['candidates'])==4 and {c['method'] for c in r['candidates']}=={'skilled','published','baseline','reviewed'}
        assert len({c['id'] for c in r['candidates']})==4
        assert r['source']==original[r['id']]['source_text']
        registry[r['id']]={c['id']:c['method'] for c in r['candidates']}
        for c in r['candidates']:
            expected={'skilled':s[r['id']],'baseline':b[r['id']],'published':original[r['id']]['human_text'],'reviewed':v[r['id']]}[c['method']]
            assert c['text']==expected and len(c['text'])>20
            assert urlsplit(c['sourceUrl']).scheme=='https'
    js=(ROOT/'backend/catalog.js').read_text(encoding='utf8');remote=json.loads(js.split('export const DATASETS = ',1)[1].rstrip().rstrip(';'))
    assert remote=={**legacy,data['version']:registry}
    # Reviewed regression anchors identify the previously shifted Wilde pairs.
    anchors={'wilde-extra-01':('walls of a round city','стены круглого города'), 'wilde-extra-02':('many lutes','многих лютней'), 'wilde-extra-07':('a young man who wore a cloak','юноша в двухцветном плаще'), 'wilde-extra-08':('touched the hand','коснулся руки'), 'wilde-extra-09':('I was blind once','я был слепым'), 'wilde-extra-10':('painted raiment','разрисованной одежды'), 'wilde-extra-11':('you forgave me my sins','отпустил мне грехи'), 'wilde-extra-12':('passed out of the city','вышел из города')}
    for id,(en,ru) in anchors.items():
        assert en.lower() in original[id]['source_text'].lower() and ru.lower() in original[id]['human_text'].lower(), f'misaligned pair: {id}'
    assert methods['reviewed_sha256']==digest(reviewed)
    class Assets(HTMLParser):
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            for attr in ['src','href']:
                value=attrs.get(attr)
                if not value or urlsplit(value).scheme or value.startswith('#'):continue
                p=(SITE/unquote(urlsplit(value).path)).resolve();assert p.is_relative_to(SITE.resolve()) and p.exists(),value
    Assets().feed((SITE/'index.html').read_text(encoding='utf8'))
    for font in (SITE/'assets/fonts').glob('*.woff2'):assert font.read_bytes()[:4]==b'wOF2'
    assert (SITE/'assets/fonts/golostext-OFL.txt').exists() and (SITE/'assets/fonts/literata-OFL.txt').exists()
    print(json.dumps({'dataset':data['version'],'rounds':len(data['rounds']),'cohortSize':data['cohortSize'],'translations':len(data['rounds'])*4,'source_provenance':'matched to generation snapshots','backend_catalog':'exact match','static_assets':'present','limits':'Corpus transport and packaging, not literary quality or vote integrity against determined abuse.'}))
if __name__=='__main__':main()
