# Evaluating lower-cost translation workflows

Use this when the user asks whether a less expensive translator plus guidance can replace a stronger model economically. Evidence that extra editing barely helps a strong model does not answer this question.

## Separate the hypotheses

- **Instruction effect:** same translator, source/context, number of calls and resources; change only the declared instruction.
- **Information package:** add a glossary, relevant examples or a stronger planner's handoff. Attribute gains to that package; a larger information budget is not an isolated skill-text effect.
- **Pipeline substitution:** compare all costs and final accepted quality of the lower-cost route against an equally checked strong-model route.

Freeze exact model IDs, settings, source selection, instructions, reference access and stopping/routing rules. Give lower-cost translators the actual English source rather than a strong model's already polished Russian draft when testing first-pass generation. Keep the strong translation as a comparator, never as ground truth. If model access fails, preserve the attempt instead of silently substituting a different model/version.

## Audit what could fail

Check coverage and meaning before fluency: omissions/additions, agency, negation/modality, quantities, chronology/direction, term sense, speech layers and meaningful repetition/form. Separately assess Russian collocation, syntax, register, voice and rhythm, preserving deliberate strangeness. Report exact spans and uncertainty. Do not let smooth Russian average away a major source failure.

Hide model/method identities. Source-fidelity reviews should see one candidate per source in a review context; reserve side-by-side alternatives for declared pairwise preferences. Identical texts are deterministic ties; propagate one accepted issue to all exact aliases. Repeated proposals about the same issue are not multiple errors. A stronger-model reviewer can still be wrong or prefer its own style. Calibration examples and a second source-grounded challenge help diagnose the audit; they do not establish human validation.

Report meaningful error categories per requested source-word denominator, coverage failures, prose preferences, per-work outcomes and reviewer disagreements. Distinguish errors already present in the draft from introduced harms. Source-selected hard examples, known development excerpts and synthetic defects are useful diagnostics, not a fresh confirmation set.

## Charge the whole route

Keep measured usage separate from a price-equivalent estimate and an actual bill. Verify the applicable current [model prices](https://developers.openai.com/api/docs/pricing), service tier, cache treatment and context class. For OpenAI usage, reported output tokens include reasoning; do not add reasoning tokens again. Check the current provider's accounting instead of assuming this convention is universal.

Record:

- translator cost and latency;
- the full planning/retrieval cost for the measured workload, with clearly hypothetical amortization scenarios separately;
- operational audits, failed calls, retries, escalation and post-correction checks;
- research-only judging separately, without treating an audit used for production routing as free;
- cost per 1,000 requested source words and per 1,000 words accepted under the stated model/human criterion;
- retained lower-cost output and escalation fractions.

If a plain route also needs auditing or correction, charge those steps consistently. Preserve missing or unresolved units in the requested denominator and exclude them from accepted words. A cheap draft requiring frequent strong-model rescue may be more expensive overall.

## Spend context and calls deliberately

Reuse validated drafts and findings for resumption or a declared post-editing test. Bind them to their source/draft, decision and instruction versions; invalidate affected units when those inputs change. This does not replace fresh generations or fresh auditors when the experiment requires them. Historical feedback has a cost and exposure history even when no new call is made.

For an accepted local correction, return a short replacement and assemble it against the checked draft; do not pay to regenerate unrelated paragraphs. Skip an editor call with no actionable findings, retaining unresolved issues. Measure error discovery and guided correction separately; one cannot stand in for the other.

For providers with prompt caching, keep useful stable context in a separate prefix block and place the provider's supported cache boundary there when needed. An identical beginning inside a changing message may not be reused. Verify current API semantics; do not add padding or extra warm-up generations merely to obtain a hit. Charge ordinary input, cached reads and cache writes once, at their actual lifetimes. Report observed usage, including zero hits, instead of treating a requested cache flag as realized savings. Keep provider/harness overhead in cost comparisons when execution routes differ.

## Decide within the evidence

Define practical quality/cost targets before results. A development signal permits another experiment or an explicitly optional experimental profile, not a claim of proven general literary quality. Confirm with fresh works, repeated generation where relevant, uncertainty estimates appropriate to clustered excerpts, and qualified bilingual review of hard/disputed cases. Do not alter thresholds or select successful passages after seeing outcomes. An inconclusive result is not proof of equivalence; an unsafe or uneconomic route should remain unpromoted.
