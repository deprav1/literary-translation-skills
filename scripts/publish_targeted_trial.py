"""Publish only completed, adjudicated trial evidence; never raw logs/full works."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from analyze_targeted_trial import (aggregate, validate_manifests, full_change_audit,
    mechanism_results, safety_results, final_gates, object_sha)
from run_targeted_trial import ROOT, TRIAL, read, write, check_frozen


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args(); workspace = args.workspace.resolve()
    assert not workspace.is_relative_to(ROOT.resolve())
    for name in ['run_targeted_trial.py', 'analyze_targeted_trial.py', 'publish_targeted_trial.py']:
        path = 'scripts/'+name
        committed_source = subprocess.check_output(['git', 'show', 'HEAD:'+path], cwd=ROOT)
        assert committed_source == (ROOT/path).read_bytes(), 'Commit analysis infrastructure before publishing evidence: '+name
    check_frozen()
    destination = TRIAL/'results'
    assert not destination.exists(), 'Never overwrite trial evidence'
    stages = validate_manifests(workspace)
    summaries, items, findings = aggregate(workspace)
    changes = full_change_audit(workspace)
    mechanism, mstatus = mechanism_results(workspace)
    safety, sstatus = safety_results(workspace, changes, findings)
    assert mstatus == sstatus == 'complete', 'Adjudication is required before publication'
    integration = final_gates(summaries, mechanism, safety)
    gold = read(workspace.parent/'synthetic-gold.json')
    committed = read(TRIAL/'synthetic-gold-commitment.json')['sha256']
    serialization = None
    for line_end in ['LF', 'CRLF']:
        for final_newline in [False, True]:
            text = json.dumps(gold, ensure_ascii=False, indent=2)+ ('\n' if final_newline else '')
            if line_end == 'CRLF':
                text = text.replace('\n', '\r\n')
            if hashlib.sha256(text.encode()).hexdigest() == committed:
                serialization = {'encoding': 'utf8', 'json_indent': 2, 'ensure_ascii': False,
                                 'line_endings': line_end, 'final_newline': final_newline}
    assert serialization, 'Published gold must reconstruct the preregistered byte commitment'
    destination.mkdir()
    for manifest in stages:
        phase = manifest['phase']; folder = destination/phase; folder.mkdir()
        for name in ['output.json', 'manifest.json', 'instruction.txt']:
            shutil.copyfile(workspace/phase/name, folder/name)
        assert sha(folder/'output.json') == manifest['output_sha256']
    (destination/'masked-mappings').mkdir()
    for path in sorted((workspace/'masked-mappings').glob('*.json')):
        shutil.copyfile(path, destination/'masked-mappings'/path.name)
    shutil.copyfile(workspace.parent/'synthetic-gold.json', destination/'synthetic-gold.json')
    assert sha(destination/'synthetic-gold.json') == committed
    (destination/'rubric-used.md').write_text(read(workspace/'judge_idiom_1/input.json')['rubric'], encoding='utf8', newline='\n')
    write(destination/'judgments.json', items)
    write(destination/'source-findings.json', findings)
    write(destination/'full-change-audit.json', changes)
    for name in ['synthetic-primary-review.json', 'safety-adjudication.json']:
        write(destination/name, read(workspace/name))
    summary = {'comparisons': summaries, 'mechanism': mechanism, 'safety': safety,
               'integration_eligible': integration,
               'meaning': 'Internal model-reviewed evidence on this frozen sample; not human literary certification.'}
    write(destination/'summary.json', summary)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    prereg_commit = subprocess.check_output(['git', 'log', '--diff-filter=A', '--format=%H', '--',
        'evals/targeted-review-20261030/preregistration.json'], cwd=ROOT, text=True).splitlines()[-1]
    record = {'date': '2026-10-30', 'preregistration_commit': prereg_commit,
        'preregistration_sha256': sha(TRIAL/'preregistration.json'), 'analysis_revision': revision,
        'runner_sha256': sha(ROOT/'scripts/run_targeted_trial.py'),
        'analysis_sha256': sha(ROOT/'scripts/analyze_targeted_trial.py'),
        'publisher_sha256': sha(Path(__file__)), 'model': 'gpt-6.1-sol', 'reasoning_effort': 'medium',
        'natural_items': 30, 'synthetic_items': 36, 'source_works': 3, 'source_authors': 2,
        'stages': stages, 'synthetic_gold_commitment_serialization': serialization,
        'synthetic_gold_sha256': sha(destination/'synthetic-gold.json'),
        'rubric_sha256': sha(destination/'rubric-used.md'),
        'mapping_sha256': {p.name: sha(p) for p in sorted((destination/'masked-mappings').glob('*.json'))},
        'safety_adjudication_sha256': sha(destination/'safety-adjudication.json'),
        'synthetic_primary_review_sha256': sha(destination/'synthetic-primary-review.json'),
        'summary_sha256': sha(destination/'summary.json'), 'judgments_sha256': sha(destination/'judgments.json'),
        'human_review': False, 'candidate_texts_manually_changed': False,
        'claim_scope': 'A fixed excerpt pilot with correlated same-family model judges; sign/Holm is an operational gate, not population-level proof.',
        'deployment': 'No candidate eligible; existing installed skills unchanged.' if not any(integration.values())
                      else 'Eligible candidates need scoped technical integration; eligibility is not deployment.',
        'limits': ['One generation per condition; no model-sampling replication.',
                   'Challenge-selected and random paragraphs are convenience samples from three works by two authors.',
                   'Public sources may have appeared in training.',
                   'English WordNet senses were supplied equally; Russian corpus lookup was not performed in isolated calls.',
                   'Memory results concern information selection, not isolated instruction text.',
                   'Safety adjudication may veto deployment but cannot add preference wins.',
                   'Full sources, raw CLI logs, composed private prompts and temporary local paths are not published.']}
    write(destination/'record.json', record)
    print(json.dumps({'stages': len(stages), 'integration_eligible': integration,
                      'destination': destination.relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    main()
