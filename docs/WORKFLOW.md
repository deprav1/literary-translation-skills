# A practical literary translation workflow

## 1. Agree on the task

Identify the source and target languages, edition, genre, audience, available context, and requested result. Distinguish an original text from an intermediary translation. An excerpt, a sample review, a full book, and an EPUB release are different scopes.

For a book, use a versioned translation brief and a manageable chapter map. Record source locations for important decisions about voices, character knowledge, forms of address, names, recurring images, and ambiguous meanings. The source remains authoritative; the passport, glossary and summaries are editable aids. For two paragraphs, a concise statement of viewpoint and intended tone may be enough.

## 2. Translate a representative passage first

Before scaling a long project, translate representative scenes that expose different voices and formal challenges. Read them both against the source and as target-language writing. Adjust the plan where needed; do not scale an obviously calqued approach merely because its JSON is valid.

When more than one model is available and authorized, assign planning, difficult passages, and adjudication to a capable coordinator/editor. A less costly model may draft passages only after a representative sample shows acceptable performance. Route wordplay, verse, plot-critical ambiguity, or inadequate drafts to a more capable translator/editor when available. Record actual model roles and do not claim a model or independent reviewer that was not used. If only one model is available, label self-review and report unresolved difficulties.

Record decisions about names, titles, terms by sense, forms of address, recurring formulas, and poetry. A project glossary is revisable. It must not turn a provisional choice into a claim of unique correctness.

## 3. Preserve function and effect

Reordering, idiomatic substitution, necessary explicitation, and compensation can be faithful. Smoothing away intentional broken speech or compressing a pivotal scene can be unfaithful even when the result reads well.

Ask what each detail does: establishes a viewpoint, moves an action, repeats a ritual, carries irony, or changes emotional temperature. Preserve that function rather than counting matching words.

For chunked work, split on meaningful scene or paragraph boundaries, retaining enough adjacent source context. Supply only relevant accepted decisions and, where useful, the prior accepted ending. Clearly mark read-only context so it is not translated as part of the passage. A separate proposal records any newly discovered term or uncertainty.

## 4. Review in two directions

**Source-based review:** actions, agents, facts, qualifications, chronology, spatial relations, cultural meaning, repetition, omissions, and additions.

**Target-language editing:** syntax, collocation, rhythm, paragraph movement, register, dialogue, and voice.

A smoother alternative is not automatically a correction. A literal alternative is not automatically more precise. Classify the issue and make the reasoning visible.

For a comparison study, add [literary-translation-evaluation](../skills/literary-translation-evaluation/SKILL.md): apply content, context, and form gates first, then use blind pairwise choices or dimension notes. Keep the actual context, candidate identities, reviewer disagreements, and coverage with the result. Preference counts describe the tested set; they do not establish general literary quality.

Before scoring, confirm that source and historical translation cover the same events and boundaries. For a skill-effect comparison, isolate the generators and hold other conditions constant; record any reference exposure. Keep contaminated or differently generated items in a separate results group. See [comparison design](../skills/literary-translation-evaluation/references/comparison-design.md).

## 5. Adjudicate before writing

Use `accept`, `edit`, `reject`, or `defer`:

- `accept`: the proposed correction is supported and usable as written;
- `edit`: the issue is real but the proposed replacement needs adjustment;
- `reject`: the alleged error is unsupported or the current wording is valid;
- `defer`: more context or specialist evidence is needed.

Record the complete source context and complete before/after target block. Exclude quotation marks that only format a suggestion in a report. A skipped patch remains unresolved until explicitly handled.

After applying a change, reread the actual result for new errors in grammar, attribution, punctuation, referents, and inline markup.

Recheck substantive edits against the source. Assemble the actual accepted passages in reading order, then read across boundaries and inspect book-level continuity of voices, relationships, names, address, and recurring images. When a glossary decision changes, find and inspect occurrences of that meaning; retranslate only passages whose accepted text needs it.

## 6. Keep book work resumable

For long tasks, use nonoverlapping output responsibilities and one editor responsible for accepted changes. A reviewer should not also silently rewrite the publication artifact.

Keep checkpoints based on actual files, not intentions. Before restarting work, inspect any still-live worker/process and preserve validated completed chunks. Resume the first missing or invalid part. Use the model/provider chosen for the task; do not silently swap in an external translation service.

The [execution record](../skills/literary-translation-craft/references/execution-record.json) distinguishes planned work from completed stages. Record the source and decision versions, actual model roles, references/context read, draft, source review, target editing and post-edit check. `not_run` is preferable to implying a stage happened. A short excerpt can state the same facts without a file.

These are collaboration practices, not an instruction to spawn parallel agents without the user's or host's authorization.

## 7. Release the exact reviewed text

A new edition gets a separate output path, an input/output hash link, and the exact accepted decision set. Technical checks must run against that output. A later stylesheet pass must not reconstruct the book from an older textual edition.

Check reading order, navigation, all internal targets, notes, media, metadata, and meaningful emphasis. Inspect actual renders at narrow and wide widths and with larger text. Poetic columns require a deliberate adaptation, not a blanket CSS rule.

## Evidence levels

| Stage | Evidence | What it does not prove |
|---|---|---|
| Delivered | Expected text blocks exist | Meaning or literary quality |
| Read | Assigned review coverage is recorded | Error-free or human-proofread text |
| Adjudicated | Specific reasons and decisions | Correct application of patches |
| Applied | Exact before/after and post-edit reading | Correct final assembly |
| Artifact verified | Target hash and structural reports | Literary quality or reader layout |
| Rendered | Engine, viewport, content and screenshots | Every reading app or TTS voice |
| Reader tested | Named app, settings and observed behavior | Universal reader compatibility |

Finish when the requested scope is closed. Further full passes need a concrete purpose. Report unresolved substantive issues and genuine limitations without presenting technical success as artistic perfection.
