# Apply a supported local correction

Use this for correction of an identified error. A requested stylistic rewrite or a structural revision may need a larger passage and separate editorial judgment. Exact replacement is an application safeguard, not a translation theory.

## Review before application

1. Read the source, context and current target. Record literal source evidence, a unique target anchor, the proposed replacement and why this is an error rather than an alternative.
2. The editor accepts, revises, rejects or defers each finding. A model proposal remains model-assisted. An uncertain reading or preference does not become an automatic correction.
3. For accepted local corrections, replace only the reviewed anchor. Do not regenerate sound paragraphs. Expand the anchor enough to preserve agreement, punctuation, viewpoint and sentence movement. If an edit crosses structure boundaries, review the larger unit explicitly.
4. Preserve full before/after blocks. Reread the actual result against the source and as prose. A mechanically applicable patch can still be wrong.

No actionable findings means no additional editing call. It does not mean error-free text: check previously supported and unresolved findings against the current artifact. Do not repeat a full audit just to obtain a different verdict.

## Optional file helper

Python 3.10+; standard library only. It needs no other skill, provider or repository files. It never calls a model. Preserve the input and create a separate output.

Input JSON:

```json
{"blocks":[{"id":"scene-1","source":"A large crowd waited.","target":"Большинство людей ждало.","protected_tokens":[]}]}
```

Decision JSON, with the SHA-256 of the exact input file bytes:

```json
{
  "input_sha256":"REPLACE_WITH_INPUT_FILE_SHA256",
  "findings":[{
    "finding_id":"f1",
    "block_id":"scene-1",
    "classification":"error",
    "decision":"accept",
    "source_quote":"A large crowd waited",
    "target_quote":"Большинство людей ждало",
    "replacement":"Большая толпа ждала",
    "decision_reason":"A large group does not establish that most people were present."
  }]
}
```

The example is synthetic; it illustrates evidence and assembly, not measured model quality. Run from the skill directory:

```sh
python scripts/apply_review_patch.py --input blocks.json --decisions decisions.json --output corrected.json
```

Only `error` findings with `accept` or `edit` decisions are applied. `edit` means the editor has supplied its revised approved replacement. `reject` and `defer` leave the text unchanged. Do not use this error-only helper to disguise an unrequested stylistic rewrite.

An empty replacement may remove an unsupported addition inside a block; erasing the entire target block is rejected.

Every finding needs a nonempty reason, source quote and target anchor from the stated block. Anchors must occur exactly once; enlarge repeated anchors instead of guessing an occurrence. Approved overlapping changes fail as a batch. A stale hash, unknown/duplicate ID or a broken declared token sequence also stops before output is written. Do not repair such failures by replacing the whole block with a guessed version.

`protected_tokens` is an optional ordered list of exact inline markers already present in the target, including repeated markers. Their spelling and sequence must survive. This checks declared markers, not all markup, links or EPUB conformance.

The new artifact contains the preserved blocks and an application receipt with applied findings, skipped decisions and full changed blocks. A subsequent pass preserves previous receipts in `application_history` and binds its new input hash to the preceding artifact. `post_apply_read` and `literary_quality_verified` remain false: mechanical application cannot perform the required editorial rereading. The input file is never overwritten, and an existing output is not replaced.
