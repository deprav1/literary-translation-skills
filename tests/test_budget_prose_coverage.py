import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from budget_prose_coverage_recovery import coverage_ids, validate_transport
from budget_audit_format_adapter import decode


class AuditCoverageRecoveryTests(unittest.TestCase):
    def test_grouped_ids_can_be_decoded_without_inventing_missing_ids(self):
        values = ['q1234567890: v11111111111111, v22222222222222']
        self.assertEqual(coverage_ids(values), ['v11111111111111', 'v22222222222222'])

    def test_unknown_coverage_text_is_not_guessed(self):
        with self.assertRaises(AssertionError):
            coverage_ids(['all candidates were read'])

    def test_explicit_source_candidate_pair_decodes_without_a_model_retry(self):
        self.assertEqual(decode(['q1234567890/v11111111111111']), ['v11111111111111'])

    def test_emphasis_markers_do_not_create_a_false_quote_error(self):
        items = [{'id': 'q1', 'source': 'A *human* was there.',
                  'candidates': [{'candidate_id': 'v11111111111111', 'text': 'Там был человек.'}]}]
        output = {'coverage': ['v11111111111111'], 'issues': [{'source_id': 'q1', 'candidate_id': 'v11111111111111',
                  'category': 'speech_form', 'severity': 'minor', 'source_quote': 'A human was there.',
                  'target_quote': 'Там был человек.', 'reason': 'emphasis omitted'}], 'unresolved': []}
        validate_transport(output, items)

    def test_real_word_changes_in_citations_still_fail(self):
        items = [{'id': 'q1', 'source': 'A *human* was there.',
                  'candidates': [{'candidate_id': 'v11111111111111', 'text': 'Там был человек.'}]}]
        output = {'coverage': ['v11111111111111'], 'issues': [{'source_id': 'q1', 'candidate_id': 'v11111111111111',
                  'category': 'speech_form', 'severity': 'minor', 'source_quote': 'A robot was there.',
                  'target_quote': 'Там был человек.', 'reason': 'wrong entity'}], 'unresolved': []}
        with self.assertRaises(AssertionError):
            validate_transport(output, items)
