import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from run_budget_trial import normalize_translation
from analyze_budget_trial import deduplicate, flags


class BudgetTranslationCoverageTests(unittest.TestCase):
    def setUp(self):
        self.source = [{'id': 'a'}, {'id': 'b'}]

    def test_missing_output_remains_visible_and_does_not_pass(self):
        result = normalize_translation({'items': [{'id': 'a', 'text': 'Русский текст.'}]}, self.source)
        self.assertFalse(result['coverage']['pass'])
        self.assertEqual(result['coverage']['missing'], ['b'])
        self.assertEqual(result['items'][1]['text'], '')

    def test_conflicting_duplicate_is_not_silently_best_of_selected(self):
        output = {'items': [{'id': 'a', 'text': 'Первый.'}, {'id': 'a', 'text': 'Второй.'}, {'id': 'b', 'text': 'Текст.'}]}
        result = normalize_translation(output, self.source)
        self.assertFalse(result['coverage']['pass'])
        self.assertTrue(result['coverage']['duplicates'][0]['conflicting'])
        self.assertEqual(result['items'][0]['text'], 'Первый.')

    def test_english_only_cannot_pass_as_russian(self):
        result = normalize_translation({'items': [{'id': 'a', 'text': 'English only.'}, {'id': 'b', 'text': 'Текст.'}]}, self.source)
        self.assertEqual(result['coverage']['wrong_language_or_empty'], ['a'])

    def test_identical_duplicate_is_a_warning_not_an_acceptance_failure(self):
        r = normalize_translation({'items': [{'id': 'a', 'text': 'Текст.'}, {'id': 'a', 'text': 'Текст.'},
                                             {'id': 'b', 'text': 'Другой.'}]}, self.source)
        self.assertTrue(r['coverage']['pass'])
        self.assertEqual(len(r['coverage']['duplicates']), 1)

    def test_repeated_claim_is_not_two_minor_errors(self):
        issue = {'source_id': 'a', 'candidate_id': 'v1', 'category': 'actor', 'source_quote': 'he', 'severity': 'minor'}
        coverage = {'missing': [], 'wrong_language_or_empty': [], 'duplicates': []}
        self.assertEqual(flags({'issues': [issue, issue], 'unresolved': []}, coverage), {})
        second = {**issue, 'category': 'number', 'source_quote': 'three'}
        self.assertEqual(flags({'issues': [issue, second], 'unresolved': []}, coverage), {'a': ['two_minor']})

    def test_major_or_unresolved_triggers_paid_routing(self):
        coverage = {'missing': [], 'wrong_language_or_empty': [], 'duplicates': []}
        issue = {'source_id': 'a', 'candidate_id': 'v1', 'category': 'actor', 'source_quote': 'he', 'severity': 'major'}
        result = flags({'issues': [issue], 'unresolved': [{'source_id': 'b'}]}, coverage)
        self.assertEqual(result, {'a': ['major'], 'b': ['unresolved']})
