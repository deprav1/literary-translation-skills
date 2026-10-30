"""Publish budget-pilot evidence after verifying private execution artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from run_budget_trial import ROOT, BASE, read, write, sha, sources
from verify_budget_trial import verify
from route_budget_trial import check_amendment
from analyze_budget_trial import score
from translation_economics import manifest_cost
from run_fresh_generations import inspect_events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args(); workspace = args.workspace.resolve()
    assert not workspace.is_relative_to(ROOT.resolve())
    check_amendment(); verify(workspace)
    destination = BASE/'results'; assert not destination.exists(), 'Never overwrite an evidence set'
    for name in ['publish_budget_trial.py', 'verify_budget_trial.py', 'budget_economic_gate.py', 'route_budget_trial.py']:
        assert subprocess.check_output(['git', 'show', 'HEAD:scripts/'+name], cwd=ROOT) == (ROOT/'scripts'/name).read_bytes()
    scored = score(workspace, read(BASE/'protocol.json'))
    assert (workspace/'economic-gates.json').exists() and (workspace/'final-prose-counts.json').exists()
    config = read(BASE/'protocol.json'); stages = []; sessions = set(); destination.mkdir()
    for folder in sorted(workspace.iterdir()):
        if not folder.is_dir() or not (folder/'attempt.json').exists():
            continue
        manifest = read(folder/'manifest.json')
        assert manifest['exit_code'] == 0 and manifest['runtime_error'] is None
        assert manifest['output_sha256'] == sha((folder/'output.json').read_bytes())
        assert manifest['input_sha256'] == sha((folder/'input.json').read_bytes())
        assert manifest['prompt_sha256'] == sha((folder/'prompt.txt').read_bytes())
        actual = inspect_events([json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf8').splitlines() if line.strip()])
        assert all(manifest[k] == value for k, value in actual.items())
        assert manifest['session_id_sha256'] not in sessions; sessions.add(manifest['session_id_sha256'])
        out = destination/folder.name; out.mkdir()
        for name in ['output.json', 'manifest.json', 'instruction.txt', 'normalized.json']:
            if (folder/name).exists():
                shutil.copyfile(folder/name, out/name)
        stages.append(manifest)
    assert len(stages) <= 36
    roots = ['brief-used.json', 'candidate-mapping.json', 'pair-mapping.json', 'calibration-mapping.json',
             'issue-proposals.json', 'scored.json', 'route-terra.json', 'route-luna.json', 'route-anchor.json',
             'final-pair-mapping.json', 'final-prose-counts.json', 'economic-gates.json']
    for name in roots:
        write(destination/name, read(workspace/name))
    production = set()
    for family in ['terra', 'luna', 'anchor']:
        receipt = read(workspace/('route-'+family+'.json'))
        production.update(receipt['audits_charged']); production.update(receipt['corrections_charged'])
    research = [s for s in stages if s['phase'] not in production and s['phase'] not in {'planner', 'sol_anchor'}
                and not s['phase'].startswith(('terra_', 'luna_'))]
    costs = {'all_pilot_model_calls_cold': sum(manifest_cost(s, config['pricing'], cold=True) for s in stages),
             'all_pilot_model_calls_cache_adjusted': sum(manifest_cost(s, config['pricing']) for s in stages),
             'research_audits_only_cold': sum(manifest_cost(s, config['pricing'], cold=True) for s in research),
             'meaning': 'Standard API list-price equivalents from dated quotes, not an actual Codex bill; subscription and backend tier not attested.'}
    write(destination/'research-cost.json', costs)
    record = {'date': '2026-10-31', 'preregistered_protocol_date': config['date'],
        'preregistration_commit': '9c85c22', 'routing_amendment_commit': '8717478',
        'preregistration_sha256': sha((BASE/'preregistration.json').read_bytes()),
        'routing_amendment_sha256': sha((BASE/'routing-amendment.json').read_bytes()),
        'publication_code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'stages': stages, 'model_calls': len(stages), 'source_items': len(sources()),
        'source_words': sum(len(r['source'].split()) for r in sources()),
        'requested_model_ids': config['models'], 'resolved_backend_snapshot_attested': False,
        'files': {p.relative_to(destination).as_posix(): sha(p.read_bytes()) for p in sorted(destination.rglob('*')) if p.is_file()},
        'quality_scope': 'Known development excerpts, one generation per arm, model audit only; no general literary certification.',
        'deployment': 'Evaluation skill updated for explicit quality-cost auditing; translation profiles remain experimental and no website candidates changed.',
        'runtime_evidence_checked': True, 'private_prompts_or_logs_published': False,
        'human_review': False, 'manual_candidate_text_edits': False,
        'economic_estimates': costs}
    write(destination/'record.json', record)
    print(json.dumps({'model_calls': len(stages), 'selected': scored['selected'], 'cost': costs,
                      'economic_gates': read(destination/'economic-gates.json')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
