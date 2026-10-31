---
name: literary-translation-qa
description: Independently assess a literary excerpt or full translation, distinguish errors from valid stylistic choices, and adjudicate exact corrections before applying them. Use for source-based translation review.
license: MIT
---

# Literary translation QA

## Scope and evidence

Choose `excerpt`, `sample`, or `full` from the user's request. Assessing two paragraphs does not require auditing a novel. For a full review, record the assigned blocks, actual reading coverage, and missing blocks.

For files, extract fresh source/target pairs from the current artifacts and record their hashes. For chat passages, quote the versions actually supplied. Do not substitute a remembered sentence or an old proposed revision for the current text. State when comparison is limited to an intermediary translation.

Confirm that each pair covers the same events and start/end boundaries before judging quality. A correctly keyed record can still contain a neighboring paragraph or a truncated translation. Flag a pairing defect separately, repair its provenance, and reassess the corrected pair; never attribute a corpus alignment failure to the translator.

When a batch uses structured IDs, validate allowed IDs, missing entries, conflicting duplicates and language/empty-output failures before accepting it. Model-generated identifiers are data, not a reliable join key until checked. Keep the raw response; do not silently reassign an approximate ID or shift the following passages by position. A missing structured item is an operational coverage failure even when a plausible translation exists under an unknown ID; distinguish it from an established semantic omission.

## Evaluate in context

Read the whole passage and enough adjacent material to identify agents, speakers, viewpoint, gender, modality, negation, sequence, physical actions, and cultural meaning. Idioms, titles, euphemisms, and spatial terms such as *first floor* require context and locale.

Classify findings:

- `error`: a supported semantic, grammatical, or formal distortion;
- `possible_issue`: context or specialist knowledge is still insufficient;
- `valid_alternative`: both choices are defensible; explain the trade-off;
- `preference`: a matter of taste, with no required correction.

Severity and confidence are different. A high-confidence model verdict is not automatic acceptance. A metaphor or explicit phrase is not an error merely because the source uses different words. Conversely, fluent summary does not excuse lost actions, sensory details, or refrains.

For a book, review continuity of names, inflection, forms of address, work titles, terms by meaning, and plot-bearing repetitions. Length ratios, digit differences, Latin-script detection, and frequency counts are leads to inspect, not quality scores.

## Decide before editing

A reviewer creates candidates. An editor then records `accept`, `edit`, `reject`, or `defer` with a reason specific to that passage. A significant deferred issue remains open. Copying the same “confirmed after review” sentence into every record is not evidence of individual judgment.

For a local correction, retain the exact source quote, a unique current target anchor, replacement and decision reason. Ask for that replacement rather than a fresh version of every paragraph. Keep unaffected wording literally unchanged. Skip the editor when no actionable findings remain; a clean report does not resolve earlier supported findings or deferred readings.

For file batches, use [local repair](references/local-repair.md) and the optional standalone [patch helper](scripts/apply_review_patch.py): it checks the input hash, anchors, overlapping edits and declared protected tokens before producing a separate artifact. Keep source context and complete before/after blocks. Widen the anchor when needed for a grammatical correction; structural or voice revisions may require a larger explicitly reviewed passage. Quotation marks formatting a suggestion do not automatically belong in narration. Applicability checks do not establish correctness.

Use the [decision template](references/review-decision.json) for a substantial project. A short excerpt can use the same distinctions in prose; a JSON log is not mandatory for a chat answer.

After applying an accepted change, reread the entire target passage and compare it with the source. Check new punctuation, agreement, pronouns, attribution, emotional coloring, emphasis, and link scope. A skipped or mismatched patch is not “fixed.”

## Report the actual result

Keep these evidence levels separate: delivered, read, adjudicated, applied, artifact-verified, rendered, reader-tested. A list of reviewed IDs records claimed coverage, not absence of errors or human proofreading. Two models may share a mistaken assumption.

State whether this was self-review, a separate model review, or qualified human review, and whether reference translations or earlier findings were visible. A different prompt or role in the same conversation is not an independent assessment. A verified no-change decision is valid; do not manufacture corrections to demonstrate activity.

Check the review's own coverage and quoted evidence too. If an audit omits items, preserve its first findings and mark the gap; a supplementary review should cover the missing material without replacing earlier preferences. A later clean model report does not erase an earlier supported defect that remains in the actual text. Repeated flags about the same source issue are not independent errors or successful fixes.

Close the requested scope. Do not repeat full reviews without a concrete new risk. State limits without calling the translation flawless. Technical EPUB conformance, browser layout, and real-reader TTS are separate claims. For electronic-book production, use an appropriate tool or installed skill if available; this review skill is independently usable.
