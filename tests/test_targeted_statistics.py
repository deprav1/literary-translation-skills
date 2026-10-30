import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
SPEC = importlib.util.spec_from_file_location('targeted_analysis', ROOT/'scripts/analyze_targeted_trial.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PreregisteredStatisticsTests(unittest.TestCase):
    def test_no_decisive_items_is_not_evidence_for_improvement(self):
        self.assertEqual(MODULE.exact_sign(0, 0), 1)

    def test_sign_test_is_two_sided_and_counts_only_decisive_items(self):
        self.assertEqual(MODULE.exact_sign(6, 0), .03125)
        self.assertEqual(MODULE.exact_sign(0, 6), .03125)
        self.assertEqual(MODULE.exact_sign(3, 3), 1)

    def test_multiple_hypotheses_cannot_use_unadjusted_success(self):
        result = MODULE.holm({'one': .03125, 'two': .2, 'three': .5, 'four': 1})
        self.assertEqual(result['one'], .125)
        self.assertGreater(result['one'], .05)

    def test_holm_stepdown_adjustment_is_monotone(self):
        self.assertEqual(MODULE.holm({'a': .001, 'b': .01, 'c': .03, 'd': .9}),
                         {'a': .004, 'b': .03, 'c': .06, 'd': .9})

    def test_memory_requires_both_comparisons_and_completed_safety(self):
        rows = {name: {'pre_safety_gate': True, 'treatment': 'memory_relevant' if name.startswith('memory_') else name}
                for name in ['idiom', 'fidelity', 'memory_plain', 'memory_random']}
        mechanisms = {name: {'pass': True} for name in ['idiom', 'fidelity', 'memory']}
        safety = {name: {'major_critical': 0, 'minor': 0} for name in ['idiom', 'fidelity', 'memory_relevant']}
        self.assertTrue(MODULE.final_gates(rows, mechanisms, safety)['memory'])
        rows['memory_random']['pre_safety_gate'] = False
        self.assertFalse(MODULE.final_gates(rows, mechanisms, safety)['memory'])
        del safety['idiom']
        self.assertFalse(MODULE.final_gates(rows, mechanisms, safety)['idiom'])

    def test_a_major_regression_vetoes_an_otherwise_positive_gate(self):
        rows = {name: {'pre_safety_gate': True, 'treatment': 'memory_relevant' if name.startswith('memory_') else name}
                for name in ['idiom', 'fidelity', 'memory_plain', 'memory_random']}
        mechanisms = {name: {'pass': True} for name in ['idiom', 'fidelity', 'memory']}
        safety = {name: {'major_critical': 0, 'minor': 0} for name in ['idiom', 'fidelity', 'memory_relevant']}
        safety['fidelity']['major_critical'] = 1
        self.assertFalse(MODULE.final_gates(rows, mechanisms, safety)['fidelity'])

    def test_actual_diff_keeps_changes_not_named_by_the_model(self):
        changes = MODULE.diff_ranges('Она сидела. Он ушёл.', 'Она лежала. Он остался.')
        self.assertGreaterEqual(len(changes), 2)
        self.assertTrue(any('уш' in change['before'] or 'ост' in change['after'] for change in changes))


if __name__ == '__main__':
    unittest.main()
