# Designing a useful translation comparison

## Declare the question before generation

Reader preference, source fidelity, literary effect and correction effort are different outcomes. Choose the primary question, item selection and stopping point before seeing winners. Include varied voices and difficulties; do not select only the cases where a preferred workflow succeeds.

Keep a fixed source edition and stable excerpt IDs. Align each historical translation to the exact source scene by events and boundaries; translations can split or combine paragraphs. Store edition attribution and excerpt hashes. A generated text must never replace the historical text under a translator's name.

## Keep conditions interpretable

For a claim about a skill, hold the model, settings, source and available context constant except for the declared treatment. For a claim about an entire workflow, record differing models, context, calls, editing and cost; do not attribute the whole effect to the skill alone.

Use isolated generator contexts. Do not give the baseline the skill, the other outputs or the historical translation. If exposure occurs, mark the affected items and present them as an unblinded comparison. An instruction to forget a translation is not isolation. Keep such items in a separate group; do not silently pool them into a controlled score.

Record actual prompts, skill revision, inputs, output hashes, model/settings and all post-editing. Preserve the first complete generation unless repeated sampling was declared beforehand. Record failures and retries, not just retained answers.

## Collect and interpret judgments

Randomize presentation, retain the assigned order, and allow no-preference or insufficient-context responses. A skip creates no vote and must not silently count as a win or loss. If identities or aggregate results were shown before later choices, those later choices are no longer fully blind; disclose this exposure or end the blind session.

Keep preference votes separate from source-based diagnoses and corrections. Repeated fragments from one work and multiple votes from one browser are not independent people or books. Report counts and denominators with percentages; small samples and convenience sampling limit generalization. Automatic metrics, model consensus and a correctly serialized rubric do not establish literary superiority.

## Version changes

A text correction or a new generation creates a new comparison version. Preserve earlier votes and their deletion path, keep personal history available where possible, and do not combine counts from changed candidates. Freeze the exact tested texts and condition record before publication.
