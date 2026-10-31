import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from repeat_budget_coverage_adapter import explicit_coverage


class QuantifiedCoverageTests(unittest.TestCase):
    def setUp(self):
        self.items = [{'id': 'q1234567890', 'candidates': [{'candidate_id': 'v11111111111111'},
                                                        {'candidate_id': 'v22222222222222'}]}]

    def test_all_n_names_exactly_the_candidates_of_the_identified_source(self):
        self.assertEqual(explicit_coverage(['q1234567890: all 2 candidates read'], self.items),
                         ['v11111111111111', 'v22222222222222'])

    def test_wrong_count_is_not_silently_completed(self):
        with self.assertRaises(AssertionError):
            explicit_coverage(['q1234567890: all 3 candidates read'], self.items)

    def test_unknown_source_does_not_create_coverage(self):
        with self.assertRaises(AssertionError):
            explicit_coverage(['q0000000000: all 2 candidates read'], self.items)
