import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from validate_budget_trial import validate


class PublishedBudgetTrialTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'evals/budget-translation-20261030/results/record.json').exists(), 'Pilot not complete yet')
    def test_saved_quality_and_full_cost_metrics_replay(self):
        result = validate()
        self.assertGreater(result['model_calls'], 20)
        self.assertEqual(set(result['selected']), {'terra', 'luna'})
