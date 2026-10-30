# Synthetic worked examples

These short examples were written for this repository. They demonstrate intended review behavior, not a measured translation-quality benchmark.

## 1. Uncertainty must remain uncertainty

**Request:** Review these two sentences only.

**Source:** “Perhaps she had left. He could not know.”

**Target:** «Она ушла. Он этого не знал.»

**Assessment:** `error`. The target asserts the departure as fact and turns inability to know into ordinary lack of knowledge.

**Possible correction:** «Возможно, она ушла. Он не мог этого знать.»

**Scope:** This establishes an issue in the supplied excerpt. It says nothing about the rest of a book's voice or quality.

## 2. A confident reviewer can still be wrong

**Source:** “He climbed the stairs from the reception to the first floor.”

**Candidate target:** «Он поднялся от стойки регистрации на второй этаж.»

**Reviewer's suggestion:** Replace «второй» with «первый»; confidence: high.

**Decision:** `defer`, unless wider context establishes the locale and layout. British *first floor* often means the level above the ground floor; American usage often differs. A staircase and a reception desk provide evidence, not a universal rule. Keep a significant unresolved reading visible rather than blindly replacing the number.

## 3. Quoting a proposal is not quoting the narrator

**Source:** “A woman in a blue jacket approached her.”

**Current target:** `К ней подошла женщина в синем куртке.`

**Reviewer's proposal:** `«К ней подошла женщина в синей куртке».`

**Decision:** `edit`. The agreement correction is justified. The quotation marks only present the proposal; they do not belong in ordinary narration.

**Exact final block:** `К ней подошла женщина в синей куртке.`

## 4. Another image can be a faithful choice

An expression such as “a blanket of silence” might, in context, become «тишина окутала комнату». A different syntactic form is not automatically a loss. If a literal blanket recurs as a motif elsewhere, however, that wider pattern may favor another choice.

**Decision:** `valid_alternative` or `preference`, until context establishes a functional difference. Explain the effect; do not manufacture an error to justify editing.

## Prompt recipes

### Worked evaluation: smoothness does not repair a lost action

Synthetic source: *Perhaps Mara had locked it. I tried the handle twice. Nothing. No sound from inside.*

- Candidate A: «Может быть, Мара заперла дверь. Я дважды дёрнул ручку. Ничего. Изнутри ни звука.»
- Candidate B: «Мара заперла дверь. Я прислушался, но в доме царила тишина.»

Using the evaluation rubric: A retains the uncertainty, attempted opening, count, and clipped rhythm. B fails the content gate: it asserts the lock as fact, substitutes listening for trying the handle, and drops “twice.” Its readable prose cannot cancel these errors. This is a source-based diagnostic result; reader preference should be collected separately, without excluding B beforehand. The isolated text does not establish a whole-book voice score or real-reader quality.

Self-check of the Russian checklist: «Мара положила свою руку на мою» can require both possessives to distinguish owners. «Было решено не записывать имён» may deliberately hide the agent. Neither warrants automatic pronoun deletion or an invented subject.

These are worked editorial examples, not independent model trials or measured evidence that a skill improves translations.

### Translate a scene

```text
Use $literary-translation-craft. Translate this scene into Russian.
Preserve the close viewpoint and understated discomfort. Keep the recurring
object labels stable. If a meaningful ambiguity cannot survive naturally,
explain your choice after the translation, not inside the fiction.
```

### Review a sample

```text
Use $literary-translation-qa in sample mode. Compare the supplied source and
target passages. List only supported errors and meaningful stylistic trade-offs.
Do not apply changes automatically. State which material you actually reviewed.
```

### Prepare an EPUB

```text
Use $epub-translation-production. Build a new edition from these accepted
translation blocks. Preserve links, notes, images, and intended emphasis.
Report the exact file hash, structural checks, and visual checks separately.
TTS in a named reader has not yet been tested.
```

### Coordinate a long translation

```text
Use $literary-translation-craft for the supplied work. Prepare an evidence-linked
brief and glossary, then calibrate on contrasting scenes before scaling.
Record the actual model, context, input versions and outputs at each stage.
Assign simpler passages to a cheaper model only if it is available, authorized
and performs adequately on the pilot. Keep source review and target editing
separate and recheck substantive edits. Report stages that were not run.
```

### Compare workflows without contaminating the baseline

```text
Use $literary-translation-evaluation to design this comparison before generation.
Keep identical source excerpts and isolated candidate contexts. Record whether
published translations were visible, preserve all first complete outputs and
their revisions, and keep exposed items in a separately reported group.
Collect preference and source-based error judgments as different outcomes.
```
