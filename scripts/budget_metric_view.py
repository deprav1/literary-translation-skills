"""Separate unique failed fragments from repeated operational diagnostics."""
from __future__ import annotations

from analyze_budget_trial import SEMANTIC


def model_metrics(scored, aliases):
    rows = {}
    for method, row in scored['model_results'].items():
        issues = [issue for issue in scored['accepted_issues'] if issue['candidate_id'] in aliases
                  and method in aliases[issue['candidate_id']] and issue['category'] in SEMANTIC]
        critical = {issue['source_id'] for issue in issues if issue['severity'] == 'critical'}
        coverage = row['coverage']
        operational = set(coverage['missing']+coverage['wrong_language_or_empty']
                          +[item['id'] for item in coverage['duplicates'] if item['conflicting']])
        critical |= operational
        rows[method] = {'minor_fidelity_issues': sum(issue['severity'] == 'minor' for issue in issues),
            'major_fidelity_issues': sum(issue['severity'] == 'major' for issue in issues),
            'critical_affected_items': sorted(critical), 'operational_failed_items': sorted(operational),
            'russian_issues': row['russian_issues'], 'unresolved': row['deferred'], 'coverage_pass': coverage['pass']}
    return rows
