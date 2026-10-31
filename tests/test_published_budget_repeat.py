import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_budget_repeat import published_verify


class PublishedSecondRealizationTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'evals/budget-translation-20261030/replication-2/results/record.json').exists(),
                         'Second realization not published yet')
    def test_no_first_run_reuse_and_repeated_costs_replay(self):
        result = published_verify()
        self.assertEqual(result['repeat'], 2)
        self.assertEqual(set(result['selected']), {'terra', 'luna'})
        self.assertFalse(result['human_validation'])
