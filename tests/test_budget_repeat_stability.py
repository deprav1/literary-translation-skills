import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from publish_budget_repeat import stability


class RepeatStabilityReportingTests(unittest.TestCase):
    def test_repeat_reports_both_outcomes_and_does_not_choose_the_better(self):
        def assessment(net):
            return {'comparisons': {'terra_brief_vs_plain': {'wins': max(0, net), 'losses': max(0, -net),
                    'ties': 30-abs(net), 'unclear': 0, 'net': net}}}
        receipt = {'selected': 'terra_plain', 'accounting': {'cold': {'usd_equivalent': .1}},
                   'final_items': [{'origin': 'terra_plain'}]}
        routes = {family: receipt for family in ['terra', 'luna', 'anchor']}
        result = stability(assessment(3), assessment(-2), routes, routes, {}, {})
        row = result['comparisons']['terra_brief_vs_plain']
        self.assertEqual(row['run1']['net'], 3)
        self.assertEqual(row['run2']['net'], -2)
        self.assertFalse(row['direction_same'])
        self.assertEqual(result['independent_source_items'], 30)
        self.assertEqual(result['realizations'], 2)
