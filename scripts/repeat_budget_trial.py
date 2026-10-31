"""Independent second draw of the frozen budget pilot; never best-of sampling."""
from __future__ import annotations

import argparse
import inspect
from pathlib import Path
import random

import run_budget_trial as runner
import analyze_budget_trial as analysis
import verify_budget_trial as verifier
import route_budget_trial as routing
import final_budget_blind_audit as final
import budget_quality_veto as quality
import budget_prose_coverage_recovery as recovery
from budget_audit_format_adapter import decode
from run_budget_trial import ROOT, BASE, sha, write

REPEAT = BASE/'replication-2'
RAW_READ = runner.read
RAW_CALL = runner.call
SEEDS = {'budget-translation-20261030-candidates': 'replication2-candidates-20261031',
         20261031: 'replication2-prose-20261031', 20261032: 'replication2-final-20261031'}
SEEDS.update({'source-order-'+str(i): 'replication2-source-order-'+str(i) for i in range(9)})


class SeedAdapter:
    @staticmethod
    def Random(seed):
        return random.Random(SEEDS.get(seed, seed))


def freeze():
    target = REPEAT/'preregistration.json'; assert not target.exists()
    runner.check_frozen()
    code = ['run_budget_trial.py', 'analyze_budget_trial.py', 'verify_budget_trial.py',
            'translation_economics.py', 'route_budget_trial.py', 'final_budget_blind_audit.py',
            'budget_coverage_adapter.py', 'budget_prose_coverage_recovery.py',
            'budget_audit_format_adapter.py', 'budget_economic_gate.py', 'budget_quality_veto.py',
            'repeat_budget_trial.py', 'publish_budget_repeat.py']
    record = {'date': '2026-10-31', 'repeat': 2, 'outputs_observed': False,
        'plan_sha256': sha((REPEAT/'PLAN.md').read_bytes()),
        'base_preregistration_sha256': sha((BASE/'preregistration.json').read_bytes()),
        'first_run_record_sha256': sha((BASE/'results/record.json').read_bytes()),
        'code_sha256': {'scripts/'+name: sha((ROOT/'scripts'/name).read_bytes()) for name in code},
        'amendment_sha256': {p.name: sha(p.read_bytes()) for p in BASE.glob('*amendment.json')},
        'models': RAW_READ(BASE/'protocol.json')['models'], 'reasoning_effort': 'medium',
        'source_sha256': RAW_READ(BASE/'protocol.json')['source']['sha256'],
        'seeds': [{'base': seed, 'repeat': replacement} for seed, replacement in SEEDS.items()],
        'max_calls': 36, 'prices': 'Fixed30October quote for comparison, not a fresh invoice.',
        'reuse_first_run_inputs': 'English source/context and frozen instructions/examples only; never Russian outputs or findings.',
        'same_source_not_new_holdout': True, 'automatic_deployment': False}
    write(target, record)


def check_repeat():
    runner.check_frozen(); record = RAW_READ(REPEAT/'preregistration.json')
    assert record['plan_sha256'] == sha((REPEAT/'PLAN.md').read_bytes())
    assert record['base_preregistration_sha256'] == sha((BASE/'preregistration.json').read_bytes())
    assert record['first_run_record_sha256'] == sha((BASE/'results/record.json').read_bytes())
    for path, digest in record['code_sha256'].items():
        assert sha((ROOT/path).read_bytes()) == digest, path
    for name, digest in record['amendment_sha256'].items():
        assert sha((BASE/name).read_bytes()) == digest, name


def derived_read(path):
    path = Path(path)
    if path.name == 'output.json' and path.parent.name in ['prose_audit', 'final_prose']:
        derived = path.parent.parent/(path.parent.name+'-normalized.json')
        if derived.exists():
            return RAW_READ(derived)
    return RAW_READ(path)


class RepeatRuntime:
    def __init__(self, workspace):
        self.workspace = workspace.resolve(); self.last_phase = None
        self.originals = []

    def set(self, module, name, value):
        self.originals.append((module, name, getattr(module, name)))
        setattr(module, name, value)

    def __enter__(self):
        check_repeat(); assert not self.workspace.is_relative_to(ROOT.resolve())
        self.workspace.mkdir(parents=True, exist_ok=True)
        marker = self.workspace/'repeat-workspace.json'
        metadata = {'repeat': 2, 'preregistration_sha256': sha((REPEAT/'preregistration.json').read_bytes())}
        if marker.exists():
            assert RAW_READ(marker) == metadata
        else:
            assert not any(self.workspace.iterdir()), 'New repeat must start in an empty workspace'
            write(marker, metadata)
        self.set(recovery, 'coverage_ids', decode)
        for module in [runner, analysis, verifier, routing, final, quality]:
            if hasattr(module, 'read'):
                self.set(module, 'read', derived_read)
        for module in [runner, analysis, routing, final]:
            self.set(module, 'call', self.call)
        for module in [runner, verifier, final]:
            self.set(module, 'random', SeedAdapter)
        self.set(runner, 'validate_audit', self.validate)
        self.set(analysis, 'validate_audit', self.validate)
        self.set(verifier, 'validate_audit', recovery.validate_transport)
        self.set(routing, 'validate_audit', self.validate)
        self.set(final, 'validate_with_empty', self.validate)
        self.set(routing, 'final_pairs', final.final_pairs)
        # Preserve the reviewed receipt correction without editing the base file.
        source = inspect.getsource(routing.route_one)
        old = "write(workspace/'route-'+family+'.json', receipt)"
        assert source.count(old) == 1
        self.originals.append((routing, 'route_one', routing.route_one))
        exec(compile(source.replace(old, "write(workspace/('route-'+family+'.json'), receipt)"),
                     '<replication2-reviewed-receipt-correction>', 'exec'), routing.__dict__)
        return self

    def __exit__(self, *_):
        for module, name, value in reversed(self.originals):
            setattr(module, name, value)

    def call(self, workspace, phase, model, task, inputs, schema):
        check_repeat(); assert workspace.resolve() == self.workspace
        folder = workspace/phase
        if folder.exists():
            manifest = RAW_READ(folder/'manifest.json')
            assert manifest['exit_code'] == 0 and manifest['runtime_error'] is None
            assert manifest['requested_model'] == model
            assert RAW_READ(folder/'input.json') == inputs and RAW_READ(folder/'schema.json') == schema
            assert (folder/'instruction.txt').read_text(encoding='utf8') == runner.ISOLATION+task+'\n'
            assert manifest['output_sha256'] == sha((folder/'output.json').read_bytes())
            result = RAW_READ(folder/'output.json')
            print('Reusing first completed request within repeat2:', phase, flush=True)
        else:
            result = RAW_CALL(workspace, phase, model, task, inputs, schema)
        manifest = RAW_READ(folder/'manifest.json')
        old_sessions = {s['session_id_sha256'] for s in RAW_READ(BASE/'results/record.json')['stages']}
        assert manifest['session_id_sha256'] not in old_sessions, 'A first-run session was reused'
        for other in workspace.glob('*/manifest.json'):
            if other.parent != folder:
                assert RAW_READ(other)['session_id_sha256'] != manifest['session_id_sha256']
        binding = {'repeat': 2, 'phase': phase, 'repeat_preregistration_sha256': sha((REPEAT/'preregistration.json').read_bytes()),
            'base_preregistration_sha256': manifest['preregistration_sha256'],
            'manifest_sha256': sha((folder/'manifest.json').read_bytes()), 'output_sha256': manifest['output_sha256']}
        if (folder/'repeat-binding.json').exists():
            assert RAW_READ(folder/'repeat-binding.json') == binding
        else:
            write(folder/'repeat-binding.json', binding)
        self.last_phase = phase
        return result

    def validate(self, output, items, *, pairs=None):
        phase = self.last_phase
        if phase not in ['prose_audit', 'final_prose']:
            return recovery.validate_transport(output, items, pairs=pairs)
        expected = {c['candidate_id'] for row in items for c in row['candidates']}
        claimed = set(decode(output['coverage'])); assert claimed <= expected
        assert pairs is not None and len(output['pairs']) == len(pairs)
        assert {r['pair_id'] for r in output['pairs']} == {r['pair_id'] for r in pairs}, 'No replacement preference votes permitted'
        missing = expected-claimed; supplement = {'coverage': [], 'issues': [], 'unresolved': [], 'pairs': []}
        completion_sha = None
        if missing:
            rows = [{**r, 'candidates': [c for c in r['candidates'] if c['candidate_id'] in missing]}
                    for r in items if any(c['candidate_id'] in missing for c in r['candidates'])]
            supplement = self.call(self.workspace, phase+'_coverage_completion',
                RAW_READ(BASE/'protocol.json')['models']['auditor'], runner.prompt('prose_audit'),
                {'items': rows, 'pairs': []}, runner.audit_schema(prose=True))
            recovery.validate_transport(supplement, rows, pairs=[])
            completion_sha = sha((self.workspace/(phase+'_coverage_completion')/'output.json').read_bytes())
        combined = {**output, 'coverage': sorted(claimed | set(decode(supplement['coverage']))),
            'issues': output['issues']+supplement['issues'], 'unresolved': output['unresolved']+supplement['unresolved']}
        recovery.validate_transport(combined, items, pairs=pairs)
        write(self.workspace/(phase+'-normalized.json'), combined)
        write(self.workspace/(phase+'-lineage.json'), {'raw_output_sha256': sha((self.workspace/phase/'output.json').read_bytes()),
            'completion_output_sha256': completion_sha, 'derived_output_sha256': sha((self.workspace/(phase+'-normalized.json')).read_bytes()),
            'required': len(expected), 'explicit_initial_candidate_coverage': len(claimed),
            'supplementary_candidates': sorted(missing), 'pairwise_votes_unchanged': True})
        self.last_phase = phase


def run(workspace, phase):
    config = RAW_READ(BASE/'protocol.json')
    with RepeatRuntime(workspace) as runtime:
        if phase in ['generation', 'all']:
            runner.plan(workspace, config)
            for family in ['luna', 'terra']:
                for arm in config['arms']:
                    runner.translation(workspace, family+'_'+arm, config)
            runner.translation(workspace, 'sol_anchor', config)
        if phase in ['audit', 'all']:
            runner.source_audit(workspace, config); runner.prose_audit(workspace, config); runner.adjudicate(workspace, config)
        if phase in ['route', 'all']:
            verifier.verify(workspace); result = analysis.score(workspace, config)
            for family, method in [*result['selected'].items(), ('anchor', 'sol_anchor')]:
                routing.route_one(workspace, config, family, method)
            counts = final.final_pairs(workspace, config); anchor = derived_read(workspace/'route-anchor.json')
            outcomes = {family: routing.gate(calibration_pass=result['calibration']['pass'],
                route=derived_read(workspace/('route-'+family+'.json')), anchor_route=anchor,
                prose_losses=counts[family]['losses'], corpus_items=30) for family in ['terra', 'luna']}
            write(workspace/'economic-gates.json', outcomes); quality.assess(workspace)
            print('Repeat2 selected profiles:', result['selected'], flush=True)
        if phase == 'verify':
            print('Verified repeat2 core stages:', len(verifier.verify(workspace)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--phase', choices=['generation', 'audit', 'route', 'verify', 'all'], default='all')
    args = parser.parse_args()
    if args.freeze:
        freeze(); print('Frozen second realization before model calls'); return
    assert args.workspace
    run(args.workspace.resolve(), args.phase)


if __name__ == '__main__':
    main()
