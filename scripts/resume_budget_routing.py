"""Resume paid routing after a receipt-path bug; reuse every completed request."""
from __future__ import annotations

import inspect
from pathlib import Path

import run_budget_trial as runner
import analyze_budget_trial as analysis
import route_budget_trial as routing
import final_budget_blind_audit as final
from budget_audit_format_adapter import activate
from budget_coverage_adapter import replay_or_call
from budget_prose_coverage_recovery import validate_transport
from run_budget_trial import BASE, read, sha


def main():
    amendment = read(BASE/'routing-receipt-amendment.json')
    assert amendment['adapter_sha256'] == sha(Path(__file__).read_bytes())
    activate()
    for module in [runner, analysis, routing, final]:
        module.call = replay_or_call
    routing.validate_audit = validate_transport
    final.validate_with_empty = validate_transport
    routing.final_pairs = final.final_pairs
    # Correct only Path/str operator grouping in the frozen receipt writer.
    source = inspect.getsource(routing.route_one)
    old = "write(workspace/'route-'+family+'.json', receipt)"
    new = "write(workspace/('route-'+family+'.json'), receipt)"
    assert source.count(old) == 1
    exec(compile(source.replace(old, new), '<recorded-receipt-path-correction>', 'exec'), routing.__dict__)
    routing.main()
    import budget_quality_veto
    assert read(BASE/'quality-veto-amendment.json')['code_sha256'] == sha(Path(budget_quality_veto.__file__).read_bytes())
    budget_quality_veto.assess(Path(__import__('sys').argv[__import__('sys').argv.index('--workspace')+1]).resolve())


if __name__ == '__main__':
    main()
