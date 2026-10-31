import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'skills/literary-translation-qa/scripts/apply_review_patch.py'
SPEC = importlib.util.spec_from_file_location('review_patch', SCRIPT)
PATCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PATCH)


def encode(pack):
    return (json.dumps(pack, ensure_ascii=False)+'\n').encode('utf8')


def finding(**changes):
    return {'finding_id': 'f1', 'block_id': 'b1', 'classification': 'error', 'decision': 'accept',
            'source_quote': 'large crowd', 'target_quote': 'Большинство людей',
            'replacement': 'Большая толпа', 'decision_reason': 'Size does not establish a majority.', **changes}


class ReviewedLocalPatchTests(unittest.TestCase):
    def setUp(self):
        self.pack = {'blocks': [{'id': 'b1', 'source': 'A large crowd waited.', 'target': 'Большинство людей ждало.'},
                                {'id': 'b2', 'source': 'Silence.', 'target': 'Тишина.'}]}
        self.digest = hashlib.sha256(encode(self.pack)).hexdigest()

    def review(self, *findings):
        return {'input_sha256': self.digest, 'findings': list(findings)}

    def test_only_approved_span_changes_and_input_is_preserved(self):
        original = copy.deepcopy(self.pack)
        result = PATCH.apply_reviews(self.pack, self.review(finding()), self.digest)
        self.assertEqual(result['blocks'][0]['target'], 'Большая толпа ждало.')
        self.assertEqual(result['blocks'][1], original['blocks'][1])
        self.assertEqual(self.pack, original)
        self.assertFalse(result['application']['post_apply_read'])
        self.assertFalse(result['application']['literary_quality_verified'])
        # Applicability does not repair agreement outside the chosen anchor.
        widened = finding(target_quote='Большинство людей ждало', replacement='Большая толпа ждала')
        corrected = PATCH.apply_reviews(self.pack, self.review(widened), self.digest)
        self.assertEqual(corrected['blocks'][0]['target'], 'Большая толпа ждала.')

    def test_stale_hash_bad_quotes_duplicate_ids_and_anchors_fail(self):
        for bad in [self.review(finding(source_quote='small crowd')), self.review(finding(target_quote='несуществующая цитата')),
                    self.review(finding(), finding())]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                PATCH.apply_reviews(self.pack, bad, self.digest)
        with self.assertRaises(ValueError):
            PATCH.apply_reviews(self.pack, self.review(finding()), '0'*64)
        self.pack['blocks'][0]['target'] += ' Большинство людей.'
        with self.assertRaises(ValueError):
            PATCH.apply_reviews(self.pack, self.review(finding()), self.digest)

    def test_subsequent_pass_preserves_previous_application_receipt(self):
        first = PATCH.apply_reviews(self.pack, self.review(finding()), self.digest)
        digest = hashlib.sha256(encode(first)).hexdigest()
        second = PATCH.apply_reviews(first, {'input_sha256': digest, 'findings': [finding(
            finding_id='f2', source_quote='waited', target_quote='ждало', replacement='ждала',
            decision_reason='Retain agreement with the new subject.') ]}, digest)
        self.assertEqual(second['application_history'], [first['application']])
        self.assertEqual(second['application']['input_sha256'], digest)
        self.assertEqual(second['blocks'][0]['target'], 'Большая толпа ждала.')

    def test_overlapping_replacements_are_rejected_as_a_batch(self):
        second = finding(finding_id='f2', target_quote='людей ждало', replacement='толпа ждала')
        with self.assertRaises(ValueError):
            PATCH.apply_reviews(self.pack, self.review(finding(), second), self.digest)

    def test_preferences_cannot_be_applied_and_deferred_findings_do_not_change_text(self):
        with self.assertRaises(ValueError):
            PATCH.apply_reviews(self.pack, self.review(finding(classification='preference')), self.digest)
        result = PATCH.apply_reviews(self.pack, self.review(finding(decision='defer', classification='possible_issue')), self.digest)
        self.assertEqual(result['blocks'], self.pack['blocks'])
        self.assertEqual(result['application']['applied'], [])

    def test_declared_inline_tokens_cannot_disappear_or_be_reordered(self):
        self.pack['blocks'][0]['target'] = '<em>Большинство людей</em> ждало.'
        self.pack['blocks'][0]['protected_tokens'] = ['<em>', '</em>']
        f = finding(target_quote='<em>Большинство людей</em>', replacement='Большая толпа')
        with self.assertRaises(ValueError):
            PATCH.apply_reviews(self.pack, self.review(f), self.digest)
        valid = PATCH.apply_reviews(self.pack, self.review(finding()), self.digest)
        self.assertEqual(valid['blocks'][0]['protected_tokens'], ['<em>', '</em>'])

    def test_deletion_is_local_and_cannot_empty_a_block(self):
        self.pack['blocks'][0]['target'] = 'Большинство людей очень ждало.'
        result = PATCH.apply_reviews(self.pack, self.review(finding(target_quote='очень ', replacement='')), self.digest)
        self.assertEqual(result['blocks'][0]['target'], 'Большинство людей ждало.')
        with self.assertRaises(ValueError):
            PATCH.apply_reviews(self.pack, self.review(finding(target_quote=self.pack['blocks'][0]['target'], replacement='')), self.digest)

    def test_standalone_cli_keeps_existing_files_and_writes_no_output_on_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); standalone = folder/'apply_review_patch.py'
            shutil.copyfile(SCRIPT, standalone)
            (folder/'input.json').write_bytes(encode(self.pack))
            (folder/'decisions.json').write_text(json.dumps(self.review(finding(target_quote='Большинство людей ждало', replacement='Большая толпа ждала')), ensure_ascii=False), encoding='utf8')
            args = [sys.executable, str(standalone), '--input', str(folder/'input.json'), '--decisions', str(folder/'decisions.json'), '--output', str(folder/'result.json')]
            done = subprocess.run(args, cwd=folder, capture_output=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            previous = (folder/'result.json').read_bytes()
            repeat = subprocess.run(args, cwd=folder, capture_output=True)
            self.assertNotEqual(repeat.returncode, 0)
            self.assertEqual((folder/'result.json').read_bytes(), previous)
            bad = self.review(finding()); bad['input_sha256'] = '0'*64
            (folder/'decisions.json').write_text(json.dumps(bad), encoding='utf8')
            args[-1] = str(folder/'failed.json')
            self.assertNotEqual(subprocess.run(args, cwd=folder, capture_output=True).returncode, 0)
            self.assertFalse((folder/'failed.json').exists())

    def test_replays_the_two_experimental_repairs_without_regeneration(self):
        read = lambda p: json.loads(p.read_text(encoding='utf8'))
        sources = {r['id']: r for r in read(ROOT/'evals/targeted-review-20261030/natural-source.json')['items']}
        baseline = read(ROOT/'evals/sol-micro-20261031/results/plain/output.json')['items']
        evidence = read(ROOT/'evals/sol-patch-20261031/guided/results/summary.json')
        pack = {'blocks': [{'id': r['id'], 'source': sources[r['id']]['source'], 'target': r['text']} for r in baseline]}
        digest = hashlib.sha256(encode(pack)).hexdigest(); decisions = {d['finding_id']: d for d in evidence['decisions']}
        findings = [finding(finding_id=f['finding_id'], block_id=f['source_id'], source_quote=f['source_quote'],
                    target_quote=f['target_quote'], decision=decisions[f['finding_id']]['decision'],
                    replacement=decisions[f['finding_id']]['replacement'], decision_reason=decisions[f['finding_id']]['reason']) for f in evidence['cached_findings']]
        result = PATCH.apply_reviews(pack, {'input_sha256': digest, 'findings': findings}, digest)
        actual = [{'id': b['id'], 'text': b['target']} for b in result['blocks']]
        expected = read(ROOT/'evals/sol-patch-20261031/guided/results/patched.json')
        self.assertEqual(actual, expected)
        self.assertEqual(len(result['application']['changed_blocks']), 2)


if __name__ == '__main__':
    unittest.main()
