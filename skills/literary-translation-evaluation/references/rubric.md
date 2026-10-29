# Compact evaluation rubric

This rubric is an original synthesis for small, traceable literary-translation evaluations. It is not a replacement for a professional review panel.

## Gates

Mark each gate `pass`, `fail`, or `unclear` before assigning dimension scores.

| Gate | Question |
|---|---|
| Content | Are actions, agents, facts, negation, modality, and sequence preserved? |
| Context | Does the candidate resolve pronouns, viewpoint, time, space, names, and recurring terms consistently? |
| Form | Are quotation layers, paragraphing, lineation, requested markup, and other explicit constraints preserved? |

`fail` requires a quoted source span, the candidate span, and a short explanation. `unclear` remains open until more context or a specialist check is available.

## Dimensions

Score 0–4 only after the gates:

| Dimension | 0 | 2 | 4 |
|---|---|---|---|
| Meaning and completeness | unrelated or materially wrong | mixed fidelity with visible losses | complete and well-supported |
| Voice and viewpoint | voice or focalization replaced | partly retained, partly flattened | distinct and controlled |
| Context and continuity | contradictions or unstable terms | some unresolved continuity | coherent with surrounding text |
| Imagery and rhythm | effect routinely erased | some effects survive | effects recreated with justified changes |
| Cultural and terminological fit | misleading or unresearched | defensible but uneven | researched and fit for context |
| Target-language prose | unreadable or mechanical | understandable with awkward passages | natural without hiding source effects |

Intermediate scores need notes. Do not average away a failed gate; report the gate separately from the mean.

Scores are optional and may be omitted when a dimension is unassessable. The record below illustrates fields, not a validation schema. Record gates per candidate and decisions per finding so one candidate's error cannot contaminate another's result.

## Minimal record

```json
{
  "item": "stable source or fragment id",
  "scope": "excerpt|sample|full",
  "source_hash": "optional hash of the checked edition",
  "candidate_ids": ["A", "B"],
  "gate_results": {
    "A": {"content": "pass", "context": "unclear", "form": "pass"},
    "B": {"content": "fail", "context": "unclear", "form": "pass"}
  },
  "pairwise_choice": "A|B|tie|not_enough_context",
  "scores": {"A": {"meaning": 4, "voice": 3}},
  "findings": [{"candidate_id": "B", "kind": "error", "severity": "major", "confidence": "high", "source": "...", "candidate": "...", "reason": "..."}],
  "finding_decisions": [{"finding_index": 0, "decision": "accept|edit|reject|defer", "reason": "specific reason"}],
  "limits": ["actual limitation"]
}
```

The record is a trace, not a claim that the numbers are objective or that an automatic judge can replace a bilingual human.
