---
name: literary-translation-evaluation
description: Evaluate literary translations with context, hard-failure gates, pairwise human review and explicit limits. Use for comparing candidates or designing a repeatable evaluation; it does not replace a qualified editor.
license: MIT
---

# Literary translation evaluation

Use this skill when the task is to compare candidate translations, measure a translation workflow, or prepare a small evaluation set. It is an assessment protocol, not a generator of a universal quality score.

## Fix the unit and evidence

Record the source edition, source and target languages, genre, audience, candidate IDs, and the scope (`excerpt`, `sample`, or `full`). Read the complete scene or paragraph range needed to resolve agents, viewpoint, modality, chronology, cultural references, and recurring terms. For files, record the hashes of the actual source and target artifacts. Do not treat a remembered sentence, a model confidence value, or a valid JSON response as evidence of quality.

## Apply gates before soft scores

Check each candidate for:

- omissions, additions, mistranslation, negation or modality drift, and broken event order;
- wrong agents, viewpoint, gender, names, titles, terminology, or recurring labels;
- lost quotation layers, register, voice, intentional ambiguity, imagery, or meaningful repetition;
- violated format or task constraints.

Record the exact source and target span for every gate failure. A severe failure stays visible; later fluency cannot average it away.

## Compare candidates

Keep preference collection separate from diagnostic assessment: do not remove candidates because of a reviewer verdict before collecting the declared preference comparison. Use a blind pairwise choice when the question is reader preference: randomize A/B order, allow `tie` and `not enough context`, and reveal identities only after the choice. Add span notes for any material difference. For a scored review, use the six dimensions in [rubric.md](references/rubric.md): meaning and completeness, voice and viewpoint, context and continuity, imagery and rhythm, cultural and terminological fit, and target-language prose. A score is a compact summary of notes, never a substitute for them.

Prefer paragraph or scene context over sentence-only prompts. Keep the source, candidate texts, choice, difficult-choice flag, error spans, and reviewer comment together so later adjudication can inspect the same evidence.

## Adjudicate and report

Classify findings as `error`, `possible_issue`, `valid_alternative`, or `preference`. Keep severity separate from confidence. An LLM judge may propose findings and draft questions. For an automated assessment, adjudicate against the source and label the result as model-assisted; do not imply human review. Professional-quality acceptance requires a qualified bilingual reviewer. A second call to the same model is self-review, not evidence of independent validation.

Report the assigned scope, actual coverage, gate failures, pairwise choices or dimension notes, disagreements, accepted decisions, and unresolved limits. Do not call a preference pilot a benchmark of general literary quality. Do not infer human proofreading, reader behavior, or TTS quality from automatic scores.

See [rubric.md](references/rubric.md) for anchors and a minimal record shape. When an accepted decision must be applied to a real translation, continue with the separately installable `literary-translation-qa` skill.
