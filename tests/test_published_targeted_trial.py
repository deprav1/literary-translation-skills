from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from validate_targeted_trial import validate


class PublishedTrialEvidenceTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'evals/targeted-review-20261030/results/record.json').exists(), 'Trial evidence not published yet')
    def test_published_decisions_replay_from_frozen_evidence(self):
        result = validate()
        self.assertEqual(result['stages'], 22)
        self.assertEqual(result['natural_items'], 30)
        self.assertEqual(result['synthetic_items'], 36)


if __name__ == '__main__':
    unittest.main()
