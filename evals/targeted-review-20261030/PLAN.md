# Targeted translation-skill trial — preregistration

Date: 2026-10-30. Model: gpt-6.1-sol, reasoning medium. Scope: EN→RU literary-excerpt review. This is an internal model-evaluated experiment, not human literary certification.

## Question and frozen candidates

Test (I) idiom/collocation evidence review, (F) proposition-level fidelity audit, and (M) relevant parallel-example selection. Candidate instruction texts live in `candidates/`; they are experimental inputs, not installable published skills. Existing 48 pilot excerpts are development material only and are excluded from the confirmation source set.

## Stage 1: mechanism checks

Each candidate receives 12 newly authored fixtures: eight declared error cases plus four clean controls with literal idioms, different term senses, passive agency or intentional unusual voice. Gold labels are kept out of generation inputs. A single fresh call produces each candidate's review. Source-specific evidence/project examples are explicit fixtures, not outside facts silently invented by a judge.

Pass all: at least 90% of eight planted defects resolved (therefore 8/8), at most 10% false substantive edits of four clean controls (therefore 0/4), no new meaning/voice failure. Spelling-only or harmless punctuation normalization is not a false substantive edit. Every fixture is adjudicated against its complete source and frozen requirement, not merely a substring regex. Failure stops that candidate from production integration. All candidate results remain reported.

## Stage 2: natural-source confirmation

Select 30 new excerpts from three CC-licensed works, ten per work, before any Russian drafts are generated. Half are source-defined difficult passages and half seeded random eligible passages. No two selected source windows overlap in the same work. Corpus includes Doctorow's I, Row-Boat and I, Robot plus the complete-prologue context of Watts' Blindsight. Record exact edition URLs, licence basis, narrative boundaries, paragraph indices, source/context hashes and selection rule. Full downloaded stories/raw logs stay outside the public repository.

One fresh call generates a shared initial translation. Five separate fresh editing calls each receive that exact draft and the same source/context, model/settings and output contract:

- E: compact generic source-and-Russian review, no specialised skill.
- I: E contract plus idiom profile; same lexical evidence as E.
- F: E contract plus fidelity profile; same lexical evidence as E.
- M-relevant: same E editing prompt plus source-relevant published parallel examples.
- M-random: same E editing prompt plus seeded randomly selected examples, with the same count and combined source/target word count matched within15%; accidental relevance is permitted.

The memory profile is checked for mechanism in stage 1. In confirmation its operational intervention is deterministic example selection, using the SAME editor instruction for both memory arms. Any M effect is attributed to the information-selection package, not isolated instruction text. Relevant examples are selected from the former pilot's attributed published pairs, never the confirmation source itself. E/I/F do not receive these translations. No published Russian reference for a confirmation passage is supplied.

Lexical notes must be fixed using English sources before examining candidate drafts. They are equal across E/I/F and memory arms. The final record distinguishes actual supplied evidence from general advice; no fabricated corpus lookup is permitted. No tools or network are available inside generator/judge sessions.

## Masked assessment

Four preregistered comparisons: I vs E, F vs E, M-relevant vs E, M-relevant vs M-random. Each is assessed by three fresh tool-disabled judge sessions. Independently permute A/B per item and judge, and hide method names, instructions, examples and prior assessments. Judges see only exact English context and the pair. They may return A, B, tie or unclear; separate meaning and Russian-prose judgments; exact quotations are required for claimed failures. Majority 2/3 gives the item decision; absent majority is tie. Exact whitespace-normalized duplicate outputs are deterministically ties regardless of any model preference; raw votes remain visible. Judges from one model family are correlated and are not human validation.

The primary editor adjudicates all claimed harmful changes and factual disagreements against the frozen source. Primary error adjudication may veto an unsafe integration; it cannot add new wins to make a failed statistical gate pass. Masked votes remain preserved. Automatic file validation checks transport and evidence, not literary quality.

## Integration gate, fixed before outputs

A candidate must pass stage 1 and its natural comparison(s), all of:

1. Positive net preference of at least six out of 30 items.
2. Two-sided exact paired sign test on decisive items; ties and unclear stay in reports but are excluded from this test. Holm correction across FOUR comparisons; family alpha .05. Memory must pass both its comparisons.
3. No new major/critical fidelity error; at most two adjudicated minor harmful edits.
4. Net preference on the random-control half is nonnegative.
5. Each of three judge sessions has nonnegative net preference.
6. Each of the three works has nonnegative net preference, and at least two works have a positive net.

Report effect counts, denominator, judge disagreement, errors, calls, elapsed time and token volume. A synthetic-only success or suggestive natural trend does not pass. Do not reinterpret nonsignificance as equivalence. If no candidate passes, publish the negative result and keep unproven instructions outside installed skills.

## No tuning after confirmation

Keep first complete outputs, no best-of. Technical failures and retries retain their artifacts/reasons; do not regenerate only a losing arm. Do not change candidate instructions, source selection, reference packets, thresholds or judges after seeing confirmation outputs. A new version needs a new holdout. Fix infrastructure-only failures with an explicit record and unchanged substantive inputs. One sample per generation condition does not establish robustness across model sampling. Excerpts within one work, batch-generated outputs and same-family judges are correlated. The sign/Holm calculation is an operational internal gate, not a calibrated population-level proof across books. Familiar public sources may have been present in pretraining.

## Deployment

Integrate only successful, narrowly scoped changes into existing craft/QA resources, preserving independently installable packages. State exactly the tested model, material and internal-evaluation limit. Never overwrite frozen public voting texts or mix their votes. Validate packaging and tests before any source delivery. Default English/Russian role profiles, books and unrelated host settings are outside scope.
