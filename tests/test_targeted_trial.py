import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('targeted_trial', ROOT/'scripts/run_targeted_trial.py')
MODULE = importlib.util.module_from_spec(SPEC)
import sys
sys.path.insert(0, str(ROOT/'scripts'))
SPEC.loader.exec_module(MODULE)


class TargetedTransportTests(unittest.TestCase):
    def setUp(self):
        self.inputs = {'items': [{'id': 'x', 'source': 'She lay on the bed.', 'draft': 'Она сидела на кровати.'}]}

    def test_an_unaccounted_rewrite_is_rejected(self):
        result = {'items': [{'id': 'x', 'text': 'Она лежала на кровати.', 'changes': []}]}
        with self.assertRaises(AssertionError):
            MODULE.validate_edit(result, self.inputs)

    def test_a_finding_cannot_cite_another_source(self):
        result = {'items': [{'id': 'x', 'text': 'Она лежала на кровати.', 'changes': [
            {'source_quote': 'He stood outside', 'draft_quote': 'сидела', 'reason': 'wrong posture'}]}]}
        with self.assertRaises(AssertionError):
            MODULE.validate_edit(result, self.inputs)

    def test_justified_local_change_has_traceable_spans(self):
        result = {'items': [{'id': 'x', 'text': 'Она лежала на кровати.', 'changes': [
            {'source_quote': 'lay', 'draft_quote': 'сидела', 'reason': 'lying rather than sitting'}]}]}
        MODULE.validate_edit(result, self.inputs)

    def test_missing_or_duplicate_coverage_is_rejected(self):
        item = {'id': 'x', 'text': 'Она сидела на кровати.', 'changes': []}
        with self.assertRaises(AssertionError):
            MODULE.validate_edit({'items': [item, item]}, self.inputs)


if __name__ == '__main__':
    unittest.main()
