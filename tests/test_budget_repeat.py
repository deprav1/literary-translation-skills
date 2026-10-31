import random
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import repeat_budget_trial as repeat
import run_budget_trial as base
import verify_budget_trial as verifier


class RepeatIsolationTests(unittest.TestCase):
    def test_repeat_changes_display_seeds_not_source_or_methods(self):
        old = random.Random(20261031).sample(range(100), 10)
        new = repeat.SeedAdapter.Random(20261031).sample(range(100), 10)
        self.assertNotEqual(old, new)
        self.assertEqual(new, repeat.SeedAdapter.Random(20261031).sample(range(100), 10))

    def test_repeat_runtime_restores_frozen_base_helpers(self):
        call = base.call; rand = verifier.random
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(repeat, 'check_repeat'), patch.object(repeat.Path, 'read_bytes', return_value=b'preregistration'):
                with repeat.RepeatRuntime(Path(folder)):
                    self.assertIsNot(base.call, call)
                    self.assertIs(verifier.random, repeat.SeedAdapter)
        self.assertIs(base.call, call)
        self.assertIs(verifier.random, rand)

    def test_nonempty_unknown_workspace_cannot_be_repurposed(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'unrelated.txt').write_text('Keep this', encoding='utf8')
            with patch.object(repeat, 'check_repeat'), patch.object(repeat.Path, 'read_bytes', return_value=b'preregistration'):
                with self.assertRaises(AssertionError):
                    with repeat.RepeatRuntime(Path(folder)):
                        pass
