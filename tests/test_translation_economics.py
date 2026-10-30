import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from translation_economics import usage_cost, pipeline_cost


class TranslationCostTests(unittest.TestCase):
    rates = {'input': 1, 'cached_input': .05, 'output': 5}

    def test_reasoning_is_not_charged_twice(self):
        u = {'input_tokens': 1000, 'output_tokens': 500, 'reasoning_output_tokens': 400}
        self.assertAlmostEqual(usage_cost(u, self.rates), .0035)

    def test_cached_and_cold_scenarios_differ(self):
        u = {'input_tokens': 1000, 'cached_input_tokens': 800, 'output_tokens': 100}
        self.assertAlmostEqual(usage_cost(u, self.rates), .00074)
        self.assertAlmostEqual(usage_cost(u, self.rates, cold=True), .0015)

    def test_unknown_cache_write_semantics_stop_the_quote(self):
        with self.assertRaises(ValueError):
            usage_cost({'input_tokens': 1000, 'cache_write_input_tokens': 100, 'output_tokens': 100}, self.rates)

    def test_unaccepted_words_do_not_create_false_savings(self):
        r = pipeline_cost(planner=.2, translator=.1, audits=[.3], escalations=[.4],
                          accepted_words=500, requested_words=1000)
        self.assertAlmostEqual(r['usd_equivalent'], 1)
        self.assertAlmostEqual(r['usd_per_1000_requested_words'], 1)
        self.assertAlmostEqual(r['usd_per_1000_model_accepted_words'], 2)


if __name__ == '__main__':
    unittest.main()
