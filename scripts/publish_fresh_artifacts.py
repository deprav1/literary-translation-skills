"""Copy completed generation evidence, excluding full stories, prompts and raw logs."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from run_fresh_generations import inspect_events, validate_source_pack

ROOT=Path(__file__).resolve().parents[1]
PHASES=['baseline','plan','pilot','calibration','skilled','critique','reviewed','evaluation']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--source-pack',type=Path,required=True)
    args=parser.parse_args()
    destination=ROOT/'site/research/fresh-v5'
    assert not destination.exists(), 'Never overwrite an evidence set'
    source=json.loads(args.source_pack.read_text(encoding='utf8'))
    validate_source_pack(source)
    expected={r['id'] for r in source['fragments']}
    manifests={}
    session_hashes=set()
    for phase in PHASES:
        folder=args.workspace/phase
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
        assert manifest['tool_calls']==0 and manifest['exit_code']==0 and manifest['fresh_session']
        assert manifest['output_sha256']==sha((folder/'output.json').read_bytes())
        events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
        event_evidence=inspect_events(events)
        session_hash=event_evidence['session_id_sha256']
        assert session_hash not in session_hashes, 'A generation reused a session'
        session_hashes.add(session_hash)
        manifest.update(event_evidence)
        manifests[phase]=manifest
    assert len({(m['model'],m['reasoning_effort']) for m in manifests.values()})==1
    assert len({manifests[phase]['source_pack_sha256'] for phase in ['baseline','skilled','reviewed']})==1
    for phase in ['baseline','skilled','reviewed']:
        rows=json.loads((args.workspace/phase/'output.json').read_text(encoding='utf8'))['translations']
        assert len(rows)==len(expected) and {row['id'] for row in rows}==expected
    destination.mkdir()
    for phase in PHASES:
        folder=destination/phase
        folder.mkdir()
        for name in ['output.json','manifest.json','instruction.txt']:
            if name=='manifest.json':
                (folder/name).write_text(json.dumps(manifests[phase],ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            else:
                shutil.copyfile(args.workspace/phase/name,folder/name)
    pack_bytes=json.dumps(source,ensure_ascii=False,sort_keys=True).encode()
    context=[{k:v for k,v in row.items() if k!='text'} for row in source['works']]
    skill_revision=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    first=manifests['baseline']
    baseline={row['id']:row['text'] for row in json.loads((args.workspace/'baseline/output.json').read_text(encoding='utf8'))['translations']}
    reviewed={row['id']:row['text'] for row in json.loads((args.workspace/'reviewed/output.json').read_text(encoding='utf8'))['translations']}
    record={
        'date':'2026-10-30','model':first['model'],'reasoning_effort':first['reasoning_effort'],
        'skill_revision':skill_revision,'source_pack_sha256':sha(pack_bytes),
        'source_context':context,'fragment_work_ids':{row['id']:row['work_id'] for row in source['fragments']},
        'stages':[{**m,'status':'done','artifact':phase+'/output.json','instruction':phase+'/instruction.txt'} for phase,m in manifests.items()],
        'outputs':{phase:manifests[phase]['output_sha256'] for phase in ['baseline','skilled','reviewed']},
        'reference_translations_supplied':False,'primary_agent_text_edits':False,'best_of_selection':False,
        'poll_methods':['published','baseline','reviewed'],
        'intermediate_condition':'Craft drafts remain in evidence, not as a separate voting card; unchanged QA outputs must not duplicate cards and split votes.',
        'non_voting_fragments':[id for id in baseline if ' '.join(baseline[id].split())==' '.join(reviewed[id].split())],
        'non_voting_policy':'Exclude exact whitespace-normalized baseline/reviewed duplicates from UI cohorts and the server allowlist. Preserve their first outputs in evidence; no regeneration to force differences.',
        'condition_call_counts':{'baseline':1,'craft_draft_including_preparation':4,'craft_plus_QA_including_preparation':6,'post_freeze_diagnostic_evaluation':1},
        'source_alignment':{'normalization':'Lowercase Unicode alphanumeric characters only, dropping punctuation, whitespace and zero-width markers. Every fragment must be contained in its declared work context.','checked_ids':[row['id'] for row in source['fragments']],'fragment_sha256':{row['id']:sha(row['source'].encode()) for row in source['fragments']}},
        'common_launch_options':['--ignore-user-config','--ephemeral','--skip-git-repo-check','--sandbox read-only','model_reasoning_effort=medium','project_doc_max_bytes=0','web_search=disabled','shell_tool=false','apps=false','plugins=false','memories=false','hooks=false','multi_agent=false','browser_use=false','computer_use=false','image_generation=false','skill_search=false','skip_host_skill_discovery=true'],
        'isolation':{'new_session_each_phase':True,'inline_inputs':True,'tools_used':0,'host_skills_disabled':True,'memory_disabled':True,'plugins_disabled':True,'network_tools_disabled':True,'baseline_skill_instructions':[]},
        'runtime_notes':['The installed CLI ignored the tools.view_image configuration key; there were no image inputs or image tool calls.','Host skill discovery was disabled using the installed experimental skip_host_skill_discovery feature.','The same model family performed generation, critique, editing and diagnostics. Separate contexts do not establish independent human validation.'],
        'limits':['Public-domain originals and historical translations may be present in model training. Runtime isolation does not remove that prior knowledge.','Source context is identical across the main conditions; craft and craft+QA intentionally receive additional plan, glossary and pilot calibration.','The reviewed condition is a revision of the craft draft, not an independently sampled translation.','Evaluation results are diagnostic; no candidate was selected, replaced or manually rewritten after evaluation.','Full original stories, complete prompts and raw CLI logs remain outside the public repository. Context URLs/hashes, exact stage instructions and generated artifacts are published.']
    }
    (destination/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'phases':len(PHASES),'fragments':len(expected),'destination':str(destination.relative_to(ROOT))}))


if __name__=='__main__':
    main()
