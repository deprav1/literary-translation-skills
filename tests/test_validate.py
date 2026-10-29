import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('skill_validation', ROOT / 'scripts' / 'validate.py')
VALIDATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATION)


class PackagingBehaviorTests(unittest.TestCase):
    def test_repository_is_valid(self):
        report = VALIDATION.validate_repository(ROOT)
        self.assertTrue(report['ok'], report['errors'])

    def test_every_skill_survives_standalone_copy(self):
        for original in sorted((ROOT / 'skills').iterdir()):
            if not original.is_dir():
                continue
            with self.subTest(skill=original.name), tempfile.TemporaryDirectory() as temp:
                installed = Path(temp) / original.name
                shutil.copytree(original, installed)
                self.assertEqual(VALIDATION.validate_skill(installed), [])

    def test_missing_reference_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            installed = Path(temp) / 'literary-translation-qa'
            shutil.copytree(ROOT / 'skills' / installed.name, installed)
            (installed / 'references' / 'review-decision.json').unlink()
            errors = VALIDATION.validate_skill(installed)
            self.assertTrue(any('missing local reference' in error for error in errors))

    def test_standalone_license_notice_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            installed = Path(temp) / 'literary-translation-qa'
            shutil.copytree(ROOT / 'skills' / installed.name, installed)
            (installed / 'LICENSE').unlink()
            errors = VALIDATION.validate_skill(installed)
            self.assertTrue(any('needs its LICENSE' in error for error in errors))

    def test_reference_cannot_depend_on_parent_project(self):
        with tempfile.TemporaryDirectory() as temp:
            installed = Path(temp) / 'literary-translation-qa'
            shutil.copytree(ROOT / 'skills' / installed.name, installed)
            (Path(temp) / 'private-context.md').write_text('not part of this skill', encoding='utf8')
            with (installed / 'SKILL.md').open('a', encoding='utf8') as stream:
                stream.write('\n[Context](../private-context.md)\n')
            errors = VALIDATION.validate_skill(installed)
            self.assertTrue(any('escapes package' in error for error in errors))

    def test_publication_check_rejects_book_file(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / 'repository'
            shutil.copytree(ROOT, copied, ignore=shutil.ignore_patterns('.git', '__pycache__'))
            (copied / 'unintended-book.epub').write_bytes(b'not for publication')
            report = VALIDATION.validate_repository(copied)
            self.assertFalse(report['ok'])
            self.assertTrue(any('must not be published' in error for error in report['errors']))


if __name__ == '__main__':
    unittest.main()
