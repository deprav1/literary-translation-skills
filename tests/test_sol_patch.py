import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import sol_patch_trial as trial


class TargetedPatchTests(unittest.TestCase):
    def test_cache_writes_are_not_double_charged(self):
        usage = {'input_tokens': 2000, 'output_tokens': 100,
                 'input_tokens_details': {'cached_tokens': 1000, 'cache_write_tokens': 500}}
        self.assertAlmostEqual(trial.response_cost(usage), .00335)
        self.assertAlmostEqual(trial.response_cost(usage, True), .005)

    def test_mixed_cache_lifetimes_are_charged_once(self):
        usage = {'input_tokens': 12000, 'output_tokens': 0,
                 'input_tokens_details': {'cached_tokens': 4000, 'cache_write_tokens': 7000,
                    'cache_write_tokens_details': {'ttl_30m_tokens': 3000, 'ttl_12h_tokens': 4000}}}
        self.assertAlmostEqual(trial.response_cost(usage), .0299)

    def test_assembly_changes_only_accepted_span(self):
        findings = [{'finding_id': 'f1', 'source_id': 's1', 'target_quote': 'старая фраза'}]
        decisions = [{'finding_id': 'f1', 'decision': 'accept', 'replacement': 'новая фраза'}]
        with patch.object(trial, 'drafts', return_value=[{'id': 's1', 'text': 'А старая фраза Б.'}, {'id': 's2', 'text': 'Без правок.'}]), patch.object(trial.prior, 'IDS', ['s1', 's2']):
            self.assertEqual(trial.apply_patch_list(findings, decisions), [{'id': 's1', 'text': 'А новая фраза Б.'}, {'id': 's2', 'text': 'Без правок.'}])
            with self.assertRaises(AssertionError): trial.apply_patch_list(findings, decisions*2)

    def test_shared_cache_block_has_no_russian_or_prior_findings(self):
        b = trial.body('task', {}, {'type': 'object'}, 100)
        shared = b['input'][0]['content'][0]
        self.assertFalse(any('\u0400' <= c <= '\u04ff' for c in shared['text']))
        self.assertEqual(shared['prompt_cache_breakpoint']['mode'], 'explicit')
        self.assertEqual(b['tools'], [])

    def test_published_replay_makes_no_model_calls(self):
        if not (trial.BASE/'results/record.json').exists(): self.skipTest('Not completed yet')
        with patch.object(trial, 'call', side_effect=AssertionError('No inference during replay')):
            trial.verify()
