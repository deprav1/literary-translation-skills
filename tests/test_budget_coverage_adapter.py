import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from budget_coverage_adapter import validate_with_empty


class MissingTranslationAuditTests(unittest.TestCase):
    def test_empty_target_can_have_critical_omission_without_a_literal_quote(self):
        items = [{'id': 's1', 'source': 'He left.', 'candidates': [{'candidate_id': 'v1', 'text': ''}]}]
        output = {'coverage': ['v1'], 'issues': [{'source_id': 's1', 'candidate_id': 'v1', 'category': 'omission',
                  'severity': 'critical', 'source_quote': 'He left.', 'target_quote': '', 'reason': 'No translation'}], 'unresolved': []}
        self.assertEqual(len(validate_with_empty(output, items)), 1)

    def test_the_exception_does_not_allow_invented_quotes_in_real_text(self):
        items = [{'id': 's1', 'source': 'He left.', 'candidates': [{'candidate_id': 'v1', 'text': 'Он ушёл.'}]}]
        output = {'coverage': ['v1'], 'issues': [{'source_id': 's1', 'candidate_id': 'v1', 'category': 'omission',
                  'severity': 'critical', 'source_quote': 'He left.', 'target_quote': '', 'reason': 'No translation'}], 'unresolved': []}
        with self.assertRaises(AssertionError):
            validate_with_empty(output, items)
