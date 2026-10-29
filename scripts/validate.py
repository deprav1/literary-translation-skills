"""Validate public skill packaging and local links; never claim literary quality."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'literary-translation-craft', 'literary-translation-qa',
    'literary-translation-evaluation',
    'epub-translation-production', 'amatka-literary-ru',
    'ngai-gimmick-ru', 'blank-space-ru-translation',
}
IGNORED = {'.git', '__pycache__', '.venv', '.wrangler'}
BOOK_EXTENSIONS = {'.epub', '.pdf', '.docx', '.mp3', '.wav', '.zip'}
LINK = re.compile(r'\[[^\]\n]+\]\(([^)\n]+)\)')
PRIVATE_PATH = re.compile(
    r'(?:[A-Za-z]:[\\/]+' + 'Users' + r'[\\/]|/'
    + 'Users' + r'/[^/\s]+/|/' + 'home' + r'/[^/\s]+/)'
)
TOKEN = re.compile(r'\b(?:ghp_|github_pat_|gho_)[A-Za-z0-9_]{20,}\b|\bsk-[A-Za-z0-9]{24,}\b')


def source_files(root: Path):
    for p in sorted(root.rglob('*')):
        if p.is_file() and not any(part in IGNORED for part in p.relative_to(root).parts):
            yield p


def local_link_errors(file: Path, boundary: Path) -> list[str]:
    errors = []
    for match in LINK.finditer(file.read_text(encoding='utf8')):
        value = match[1].strip().strip('<>')
        url = urlsplit(value)
        if url.scheme or url.netloc or not url.path:
            continue
        target = (file.parent / unquote(url.path)).resolve()
        if not target.is_relative_to(boundary.resolve()):
            errors.append(f'{file.name}: local link escapes package: {value}')
        elif not target.exists():
            errors.append(f'{file.name}: missing local reference: {value}')
    return errors


def validate_skill(directory: Path) -> list[str]:
    directory = Path(directory).resolve()
    entry = directory / 'SKILL.md'
    if not entry.is_file():
        return [f'{directory.name}: missing SKILL.md']
    text = entry.read_text(encoding='utf8')
    parts = text.split('---', 2)
    if len(parts) != 3 or parts[0].strip():
        return [f'{directory.name}: missing YAML frontmatter']
    front = parts[1]
    name = re.search(r'^name:\s*([a-z0-9-]+)\s*$', front, re.M)
    description = re.search(r'^description:\s*(\S[^\n]+)$', front, re.M)
    errors = []
    if not name or name[1] != directory.name or len(name[1]) > 64:
        errors.append(f'{directory.name}: name must match its folder')
    if not description or len(description[1]) > 1024:
        errors.append(f'{directory.name}: description is missing or too long')
    if not re.search(r'^license:\s*MIT\s*$', front, re.M):
        errors.append(f'{directory.name}: license must be MIT')
    notice = directory / 'LICENSE'
    if not notice.is_file():
        errors.append(f'{directory.name}: standalone package needs its LICENSE notice')
    elif 'The above copyright notice and this permission notice' not in notice.read_text(encoding='utf8'):
        errors.append(f'{directory.name}: incomplete MIT notice')
    for file in source_files(directory):
        if file.suffix == '.md':
            errors.extend(local_link_errors(file, directory))
        elif file.suffix == '.json':
            try:
                json.loads(file.read_text(encoding='utf8'))
            except (ValueError, OSError) as exc:
                errors.append(f'{directory.name}: invalid JSON {file.name}: {exc}')
    return errors


def validate_repository(root: Path) -> dict:
    root = Path(root).resolve()
    errors = []
    directories = sorted(p for p in (root / 'skills').glob('*') if p.is_dir())
    if {p.name for p in directories} != EXPECTED:
        errors.append(f'Expected exactly the {len(EXPECTED)} documented skill directories')
    for directory in directories:
        errors.extend(validate_skill(directory))
    for name in ['README.md', 'README.ru.md', 'LICENSE', 'CONTRIBUTING.md']:
        if not (root / name).is_file():
            errors.append(f'Missing public repository file: {name}')
    checked = 0
    for file in source_files(root):
        checked += 1
        relative = file.relative_to(root)
        if file.suffix.lower() in BOOK_EXTENSIONS:
            errors.append(f'Book/audio/archive file must not be published here: {relative}')
            continue
        if file.name == '.env' or file.name.startswith('.env.'):
            errors.append(f'Environment file must not be published here: {relative}')
            continue
        if file.suffix.lower() == '.woff2':
            if not file.is_relative_to(root / 'site' / 'assets' / 'fonts') or file.read_bytes()[:4] != b'wOF2':
                errors.append(f'Unexpected font asset: {relative}')
            continue
        try:
            text = file.read_text(encoding='utf8')
        except UnicodeDecodeError:
            errors.append(f'Unexpected non-UTF-8 file: {relative}')
            continue
        if PRIVATE_PATH.search(text):
            errors.append(f'Personal machine path found in {relative}')
        if TOKEN.search(text):
            errors.append(f'Credential-shaped string found in {relative}')
        if file.suffix == '.md':
            errors.extend(local_link_errors(file, root))
    return {
        'skills': len(directories), 'files_checked': checked,
        'errors': errors, 'ok': not errors,
        'limits': 'Packaging and common accidental disclosures only; not a comprehensive secret scan or literary-quality test.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', type=Path, help='Validate one independently copied skill directory')
    args = parser.parse_args()
    if args.skill:
        errors = validate_skill(args.skill)
        result = {'skill': args.skill.name, 'errors': errors, 'ok': not errors}
    else:
        result = validate_repository(ROOT)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
