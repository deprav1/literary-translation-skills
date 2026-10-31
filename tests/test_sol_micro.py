import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import sol_micro_trial as trial


class SmallSolTrialTests(unittest.TestCase):
    def test_saved_trial_replays_without_new_model_calls(self):
        if not (trial.BASE/'results/record.json').exists():
            self.skipTest('Trial not completed yet')
        with patch.object(trial, 'call', side_effect=AssertionError('No model calls during replay')):
            trial.verify()

    def test_cache_writes_replace_input_charge(self):
        usage = {'input_tokens': 2000, 'cached_input_tokens': 1000,
                 'cache_write_input_tokens': 500, 'output_tokens': 100}
        self.assertAlmostEqual(trial.cost(usage), .00335)
        self.assertAlmostEqual(trial.cost(usage, True), .005)

    def test_fresh_translation_prefix_contains_only_english_sources(self):
        prefix = trial.prefix()
        self.assertNotIn('draft', prefix.lower())
        self.assertFalse(any('\u0400' <= c <= '\u04ff' for c in prefix))
        self.assertEqual(sum(len(r['source'].split()) for r in trial.sources()), 594)
        for arm in ['plain', 'meaning', 'voice']:
            self.assertTrue((prefix+'\n\nTASK\n'+trial.TASKS[arm]).startswith(prefix))

    def test_budget_gate_does_not_assume_future_cache_hits(self):
        p = {'max_calls': 6, 'max_input_tokens': 200000, 'max_output_tokens': 12000,
             'next_call_reserve': .14, 'usd_stop_limit': .60}
        expensive = [{'usage': [{'input_tokens': 160000, 'cached_input_tokens': 159000,
                                'output_tokens': 15000}]}]
        with patch.object(trial, 'check', return_value=p):
            with self.assertRaises(AssertionError): trial.allowed(expensive)
            with self.assertRaises(AssertionError): trial.allowed([{'usage': []}]*6)


if __name__ == '__main__':
    unittest.main()
