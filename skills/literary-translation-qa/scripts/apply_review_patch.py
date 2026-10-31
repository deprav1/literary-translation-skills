"""Apply adjudicated exact-span corrections; no model calls or quality certification."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_tokens(text, tokens):
    require(isinstance(tokens, list) and all(isinstance(t, str) and t for t in tokens), 'Invalid protected token list')
    if tokens:
        pattern = '|'.join(re.escape(t) for t in sorted(set(tokens), key=len, reverse=True))
        require(re.findall(pattern, text) == tokens, 'Declared protected token sequence changed')


def apply_reviews(pack, review, input_sha256):
    require(isinstance(pack, dict) and isinstance(pack.get('blocks'), list), 'Expected blocks array')
    require(isinstance(review, dict) and review.get('input_sha256') == input_sha256, 'Stale or missing input hash')
    require(isinstance(review.get('findings'), list), 'Expected findings array')
    blocks = {}; operations = {}; applied = []; skipped = []; seen = set()
    for block in pack['blocks']:
        require(isinstance(block, dict), 'Invalid block')
        key = block.get('id')
        require(isinstance(key, str) and key and key not in blocks, 'Empty or duplicate block ID')
        require(isinstance(block.get('source'), str) and isinstance(block.get('target'), str), 'Expected source/target text')
        check_tokens(block['target'], block.get('protected_tokens', []))
        blocks[key] = block
    for finding in review['findings']:
        require(isinstance(finding, dict), 'Invalid finding')
        fid = finding.get('finding_id'); key = finding.get('block_id')
        require(isinstance(fid, str) and fid and fid not in seen, 'Empty or duplicate finding ID')
        seen.add(fid)
        require(isinstance(key, str) and key in blocks, 'Unknown block ID')
        block = blocks[key]; decision = finding.get('decision'); kind = finding.get('classification')
        require(decision in ['accept', 'edit', 'reject', 'defer'], 'Unknown editorial decision')
        require(kind in ['error', 'possible_issue', 'valid_alternative', 'preference'], 'Unknown classification')
        reason = finding.get('decision_reason')
        require(isinstance(reason, str) and reason.strip(), 'Missing decision reason')
        source = finding.get('source_quote'); anchor = finding.get('target_quote')
        require(isinstance(source, str) and source and source in block['source'], 'Source quote mismatch')
        require(isinstance(anchor, str) and anchor and block['target'].count(anchor) == 1, 'Target anchor must occur exactly once')
        if decision in ['reject', 'defer']:
            skipped.append({'finding_id': fid, 'decision': decision, 'classification': kind})
            continue
        require(kind == 'error', 'Only adjudicated errors can be automatically applied')
        replacement = finding.get('replacement')
        require(isinstance(replacement, str) and replacement != anchor, 'Missing or unchanged replacement')
        start = block['target'].index(anchor)
        operations.setdefault(key, []).append((start, start+len(anchor), replacement, fid))
        applied.append({'finding_id': fid, 'block_id': key, 'decision': decision,
                        'source_quote': source, 'before': anchor, 'after': replacement, 'reason': reason})
    result = copy.deepcopy(pack); changed = []
    for block in result['blocks']:
        key = block['id']; ops = sorted(operations.get(key, [])); before = block['target']; after = before
        require(all(left[1] <= right[0] for left, right in zip(ops, ops[1:])), 'Overlapping approved edits')
        for start, end, replacement, _ in reversed(ops):
            after = after[:start]+replacement+after[end:]
        require(not ops or bool(after.strip()), 'Correction would erase the whole target block')
        check_tokens(after, block.get('protected_tokens', []))
        block['target'] = after
        if after != before:
            changed.append({'block_id': key, 'before_full': before, 'after_full': after})
    if 'application' in pack:
        require(isinstance(pack['application'], dict), 'Invalid previous application receipt')
        history = pack.get('application_history', [])
        require(isinstance(history, list), 'Invalid application history')
        result['application_history'] = copy.deepcopy(history)+[copy.deepcopy(pack['application'])]
    result['application'] = {'input_sha256': input_sha256, 'applied': applied, 'not_applied': skipped,
                             'changed_blocks': changed, 'post_apply_read': False, 'literary_quality_verified': False}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        require(args.output.resolve() not in [args.input.resolve(), args.decisions.resolve()], 'Output must be a separate file')
        raw = args.input.read_bytes(); review = json.loads(args.decisions.read_text(encoding='utf-8-sig'))
        result = apply_reviews(json.loads(raw.decode('utf-8-sig')), review, hashlib.sha256(raw).hexdigest())
        encoded = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode('utf8')
        with args.output.open('xb') as stream:
            stream.write(encoded)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({'applied': len(result['application']['applied']),
                      'changed_blocks': len(result['application']['changed_blocks']),
                      'output_sha256': hashlib.sha256(encoded).hexdigest(), 'literary_quality_verified': False}))


if __name__ == '__main__':
    main()
