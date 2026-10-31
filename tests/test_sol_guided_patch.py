import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import sol_guided_patch as guided


class GuidedPatchEvidenceTests(unittest.TestCase):
    def test_only_exact_baseline_findings_are_reused(self):
        findings = guided.cached_findings()
        self.assertEqual(len(findings), 2)
        self.assertEqual(len({f['source_id'] for f in findings}), 2)
        guided.core.validate_issues(findings, {r['id']: r['text'] for r in guided.core.drafts()})

    def test_saved_guided_evidence_replays_without_inference(self):
        if not (guided.BASE/'results/record.json').exists(): self.skipTest('Not completed yet')
        with patch.object(guided.core, 'BASE', guided.BASE), patch.object(guided.core, 'call', side_effect=AssertionError('No inference')):
            guided.verify()
