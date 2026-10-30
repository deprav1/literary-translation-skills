import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from budget_economic_gate import gate


def receipt(cost, unresolved=False):
    return {'accounting': {'cold': {'requested_words': 1000, 'accepted_words': 0 if unresolved else 1000,
                                   'usd_equivalent': cost}},
            'unresolved_flags': {'x': ['major']} if unresolved else {},
            'final_items': [{'model_accepted': not unresolved}]}


class EconomicQualityGateTests(unittest.TestCase):
    def test_cheap_but_unresolved_does_not_pass(self):
        self.assertFalse(gate(calibration_pass=True, route=receipt(.01, True), anchor_route=receipt(1),
                              prose_losses=0, corpus_items=30)['development_economic_gate'])

    def test_saving_requires_all_costs_not_just_draft(self):
        self.assertFalse(gate(calibration_pass=True, route=receipt(.9), anchor_route=receipt(1),
                              prose_losses=0, corpus_items=30)['development_economic_gate'])

    def test_excess_prose_losses_veto_savings(self):
        self.assertFalse(gate(calibration_pass=True, route=receipt(.1), anchor_route=receipt(1),
                              prose_losses=4, corpus_items=30)['development_economic_gate'])

    def test_bounded_success_is_explicitly_only_a_development_gate(self):
        r = gate(calibration_pass=True, route=receipt(.5), anchor_route=receipt(1), prose_losses=3, corpus_items=30)
        self.assertTrue(r['development_economic_gate'])
        self.assertIn('development', r['claim'])
