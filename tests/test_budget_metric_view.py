import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from budget_metric_view import model_metrics


class CriticalFragmentAccountingTests(unittest.TestCase):
    def test_empty_omission_and_missing_id_are_one_affected_fragment(self):
        data = {'model_results': {'luna_brief': {'coverage': {'missing': ['x'], 'wrong_language_or_empty': [],
                  'duplicates': [], 'pass': False}, 'russian_issues': 0, 'deferred': 0}},
                'accepted_issues': [{'source_id': 'x', 'candidate_id': 'v1', 'category': 'omission', 'severity': 'critical'}]}
        result = model_metrics(data, {'v1': ['luna_brief']})['luna_brief']
        self.assertEqual(result['critical_affected_items'], ['x'])
        self.assertEqual(result['operational_failed_items'], ['x'])
