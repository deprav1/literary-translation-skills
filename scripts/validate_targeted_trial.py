"""Replay published trial commitments and gates, not literary-quality judgments."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from run_targeted_trial import TRIAL, COMPARISONS, ARMS, read, check_frozen
from analyze_targeted_trial import (aggregate, full_change_audit, mechanism_results,
                                   safety_results, final_gates)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate():
    check_frozen(); results = TRIAL/'results'; record = read(results/'record.json')
    expected = ({'synthetic_'+name for name in ['idiom', 'fidelity', 'memory']}
                | {'synthetic_check', 'draft'} | set(ARMS)
                | {f'judge_{name}_{j}' for name in COMPARISONS for j in range(1, 4)})
    assert len(record['stages']) == 22 and {r['phase'] for r in record['stages']} == expected
    sessions = set()
    for stage in record['stages']:
        folder = results/stage['phase']; manifest = read(folder/'manifest.json')
        assert manifest == stage and stage['fresh_session'] and stage['tool_calls'] == 0 and stage['exit_code'] == 0
        assert stage['model'] == record['model'] == 'gpt-6.1-sol' and stage['reasoning_effort'] == 'medium'
        assert stage['preregistration_sha256'] == record['preregistration_sha256'] == sha(TRIAL/'preregistration.json')
        assert stage['session_id_sha256'] not in sessions; sessions.add(stage['session_id_sha256'])
        assert sha(folder/'output.json') == stage['output_sha256']
        assert hashlib.sha256((folder/'instruction.txt').read_text(encoding='utf8')[:-1].encode()).hexdigest() == stage['instruction_sha256']
        assert set(stage['observed_runtime_item_types']) <= {'agent_message', 'reasoning', 'error'}
    assert sha(results/'synthetic-gold.json') == read(TRIAL/'synthetic-gold-commitment.json')['sha256'] == record['synthetic_gold_sha256']
    assert sha(results/'rubric-used.md') == record['rubric_sha256']
    for name, value in record['mapping_sha256'].items():
        assert sha(results/'masked-mappings'/name) == value
    for name, key in [('summary.json', 'summary_sha256'), ('judgments.json', 'judgments_sha256'),
                      ('safety-adjudication.json', 'safety_adjudication_sha256'),
                      ('synthetic-primary-review.json', 'synthetic_primary_review_sha256')]:
        assert sha(results/name) == record[key]
    summaries, judgments, findings = aggregate(results)
    changes = full_change_audit(results)
    assert read(results/'judgments.json') == judgments
    assert read(results/'source-findings.json') == findings
    assert read(results/'full-change-audit.json') == changes
    mechanism, mstatus = mechanism_results(results)
    safety, sstatus = safety_results(results, changes, findings)
    assert mstatus == sstatus == 'complete'
    integration = final_gates(summaries, mechanism, safety)
    published = read(results/'summary.json')
    assert published['comparisons'] == summaries and published['mechanism'] == mechanism
    assert published['safety'] == safety and published['integration_eligible'] == integration
    assert record['human_review'] is False and record['candidate_texts_manually_changed'] is False
    return {'stages': len(sessions), 'natural_items': 30, 'synthetic_items': 36,
            'integration_eligible': integration,
            'limits': 'Replay of frozen artifacts, masked ordering and gates; not independent human literary evaluation.'}


if __name__ == '__main__':
    print(json.dumps(validate(), ensure_ascii=False))
