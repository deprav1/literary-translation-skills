"""Check the published pilot corpus and its backend allowlist; no literary score claimed."""
import json,hashlib,re,sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode('utf8')).hexdigest()
def main():
    data=json.loads((SITE/'data.json').read_text(encoding='utf8'));methods=json.loads((SITE/'METHODS.json').read_text(encoding='utf8'));selected=json.loads((SITE/'research/selected.json').read_text(encoding='utf8'))
    skilled=json.loads((SITE/'research/skilled.json').read_text(encoding='utf8'));baseline=json.loads((SITE/'research/baseline.json').read_text(encoding='utf8'))
    assert data['version']=='blind-v1-'+digest([selected,skilled,baseline])[:12]
    assert methods['dataset']==data['version'] and methods['manual_postediting'] is False
    assert len(data['rounds'])==6 and len({r['id'] for r in data['rounds']})==6
    registry={};original={r['id']:r for r in selected};s={r['id']:r['text'] for r in skilled};b={r['id']:r['text'] for r in baseline}
    for r in data['rounds']:
        assert len(r['candidates'])==3 and {c['method'] for c in r['candidates']}=={'skilled','published','baseline'}
        assert len({c['id'] for c in r['candidates']})==3
        assert r['source']==original[r['id']]['source_text']
        registry[r['id']]={c['id']:c['method'] for c in r['candidates']}
        for c in r['candidates']:
            expected={'skilled':s[r['id']],'baseline':b[r['id']],'published':original[r['id']]['human_text']}[c['method']]
            assert c['text']==expected and len(c['text'])>50
            assert urlsplit(c['sourceUrl']).scheme=='https'
    js=(ROOT/'backend/catalog.js').read_text(encoding='utf8');remote=json.loads(js.split('export const DATASETS = ',1)[1].rstrip().rstrip(';'))
    assert remote=={data['version']:registry}
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
    print(json.dumps({'dataset':data['version'],'rounds':6,'translations':18,'source_provenance':'matched to generation snapshots','backend_catalog':'exact match','static_assets':'present','limits':'Corpus transport and packaging, not literary quality or vote integrity against determined abuse.'}))
if __name__=='__main__':main()
