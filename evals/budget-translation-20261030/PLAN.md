# Lower-cost translation audit — frozen development pilot

2026-10-30. User goal: improve Terra/Luna translation enough to save money. This replaces the earlier strong-Sol-polishing question; that earlier result cannot establish effects on weaker translators.

## Fixed roles and material

Translators: `gpt-6.1-terra` and `gpt-6-luna`, medium reasoning. Sol (`gpt-6.1-sol`, medium) plans and audits, and makes a separately labelled strong translation anchor. There is no shared Sol draft given to the cheap translators. Each cheap condition translates directly from English in one call. Do not silently replace a requested model with another version or with Tencent.

Use the former30source excerpts, source/context hash recorded in protocol.json, for DEVELOPMENT ONLY. They were already seen in earlier analysis; they are not a new confirmation holdout. The old Russian outputs, old audit findings and reference translations of these passages are excluded from generator inputs. Same English paragraph and two neighboring paragraphs each side for all conditions. No outputs or votes on the public site change.

## New candidate search

The new search prioritizes compact terminology/context handoff for smaller models: [EN→RU retrieval terminology research](https://aclanthology.org/2026.wmt-main.40/), [MAPS](https://aclanthology.org/2024.tacl-1.13/) and [Hy-MT2's task modes](https://github.com/Tencent-Hunyuan/Hy-MT2). These are supporting mechanisms, not proof on Terra/Luna. Vendor-bound Hy-MT2 skill requires a different model/backend and is not installed. Third-party bundles, weights and data are not copied.

## Translation matrix

For EACH cheap model:

1. Plain: short translation request, no craft profile.
2. Guard: concise source facts, uncertainty, Russian collocation/voice check INSIDE the same translation call.
3. Brief: Guard plus a short source-derived Sol brief/glossary shared across the work.
4. Memory: Brief plus two small matching parallel micro-examples per work, authored/reviewed by the assistant, not human-certified examples or translations of test passages.

One Sol planning call prepares work briefs using source ONLY; no full test translation. Normalize deterministically: at most80brief words and4supported glossary entries per work; preserve the first entries and log any discarded unsupported/oversize data. No tuning after seeing cheap outputs. Brief/Memory are information-and-orchestration packages; only Guard vs Plain isolates the added instruction. All eight translator calls share the output contract. One fresh Sol direct translation is an anchor, not ground truth.

## Audit redesign

Freeze models, inputs, profiles, seeds, schemas, prices and rules before model calls. Every request is a fresh tool-disabled CLI session with host skills, memory, plugins and network tools disabled. Preserve first complete outputs and all failures; no best-of. Actual raw ids, omissions, duplicated conflicting ids and wrong-language responses are recorded as operational failures; never silently retry a weak model until it looks good. First duplicate is the deterministic view; conflicting duplicates block acceptance.

Construct anonymous per-item candidate ids, independently shuffle display order, merge only exact whitespace-equivalent texts and retain aliases. No model/condition names reach reviewers. Nine separate fresh source-audit contexts each see one candidate per natural source; variants are never side-by-side in source auditing. A source audit checks semantic propositions first: omission, addition, actor, negation/modality, number, time/direction, term sense, speech layer, meaningful form/repetition. A separate Russian/voice audit checks calques, syntax, collocation and intentional literary effects, with explicit pairwise ties/unclear. Sol anchor is audited too. Proposed errors need exact source/target spans and severity. A third fresh context adjudicates the proposals; primary source review may reject unsupported findings, never rewrite frozen candidates or manufacture wins.

Main quality outputs: confirmed major/critical and minor fidelity errors per1000REQUESTED English words, coverage failures, Russian-prose/voice issue density, paired preference counts within EACH cheap model and against anchor, per-work results and disagreements. Scores cannot average away a major failure. Multiple repeated judge proposals count as one accepted issue, not independent errors. Different audit roles are not independent human votes.

Six calibration controls with opaque source/candidate ids, no work labels, and matched field structure (three clear defects, three valid unusual/literal readings) accompany source auditing; they are excluded from corpus scores. If fewer5/6 are handled correctly or a clean control gets a false major, source-audit reliability is flagged and no quality/economic promotion is permitted. This calibration does not prove literary expertise.

## Cost and conditional escalation

Use the dated official Standard API quote in protocol.json. CLI usage is NOT an invoice: report list-price-equivalent scenarios, observed token counts, cold-input scenario, cache-adjusted scenario, time and uncertainty about actual service tier/subscription billing. Output tokens ALREADY include reasoning; do not add reasoning tokens again. Unknown/nonzero cache-write semantics require a flagged estimate. Below272kinputtokens only; long-context, Fast and regional uplifts are not silently assumed away. Separate raw translator cost, full planning cost, actual online audit/escalation cost, and research-only evaluation cost.

Select one eligible low-cost profile per cheap model by the fixed ranking in protocol.json (fallback Plain if no skill signal). Measure one standalone production-style Sol audit for selected Luna, selected Terra and the Sol anchor, with model identities hidden. Do not divide the actual planner cost among experimental arms: each hypothetical guided pipeline pays the FULL planning call once for this workload. Per-book amortization beyond measured scope is a clearly hypothetical sensitivity, not observed whole-book economics.

On an online audit flag (major/critical, unresolved meaning, or2minor fidelity issues), retranslate only flagged excerpts. Luna→Terra→Sol, Terra→Sol; Sol anchor gets at most one Sol correction. Each correction is followed by an actual source audit; all tokens, false alarms and failed work are charged. Stop at the prescribed limit and mark unresolved words unaccepted. Do not charge a free human or research judge as an operational step while using it to avoid escalation. Up to36model calls total, including research-only auditing. Dollar cost per1000requested source words and per1000model-accepted source words; denominator excludes missing/unresolved/flagged-major units. Report retained weak-model word fraction and escalation fraction.

## Pilot outcome and confirmation

Use the fixed pilot signal/economic rules in protocol.json. Report opportunities and failures by model instead of one universal old net+6/Holm gate. Item bootstrap is descriptive with only3works; no finding here is a general proof or a human literary acceptance. No mandatory default or installed-skill promotion from this development corpus. A fresh60+item,6+work confirmation set and qualified bilingual examination of hard/disputed cases are required for a broad efficacy claim.

## Engineering evidence

Keep full sources, raw CLI logs and composed prompts outside the public repository. Publish only attributed excerpt inputs already public, original instructions, normalized planner outputs with raw lineage, model outputs, sanitized manifests, audit decisions, metrics and cost assumptions. Do not change frozen old experiment files to make this new protocol pass. Run repository validation and tests before delivery.
