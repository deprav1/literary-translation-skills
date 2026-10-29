# Context handoff for a long translation

Use this only when work is divided into scenes or chunks. It does not require parallel agents, another provider, or a whole-book upload.

## Input for the current passage

- Stable passage ID and exact source text; enough preceding/following source to resolve references, marked read-only and excluded from the requested output.
- Relevant voice and viewpoint decisions, with the source locations that support them.
- Glossary entries by sense: entity ID, aliases, target rendering, grammatical features when relevant, evidence location, and status (`proposed`, `accepted`, `disputed`). Keep different entities with identical names separate.
- A short rolling summary with source locations and unresolved questions. Treat it as a navigation aid: consult the source when it conflicts with a detail, and avoid feeding future revelations into an earlier character's knowledge.

## After translation

Return the passage plus separate proposals for new terms, aliases, voice changes, and unresolved readings. Never embed this handoff in the narrative. Reconcile conflicts against source context before updating accepted choices; model consensus alone is insufficient.

Keep the source and output versions, brief/glossary version, completed passage IDs, and pending decisions in a checkpoint. A changed term invalidates only passages where its intended sense occurs; inspect those occurrences before retranslation. Resume actual missing or outdated work rather than repeating the book.

## Worked handoff (synthetic)

Earlier source: Mara calls her younger brother *Finch* as a nickname. The chapter also names a bird on the gate.

- Entity `person-2`: alias *Finch*, accepted nickname «Зяблик»; Mara uses informal address.
- Sense `bird-finch`: ordinary bird «зяблик», not an alias of `person-2`.
- Current source: *“Finch?” Mara called. The finch on the gate did not move.*
- Translation: «— Зяблик? — позвала Мара. Зяблик на калитке не шелохнулся.»
- Check: the first occurrence is a call to the brother; the second is the bird. Keep that deliberate echo. A glossary search alone cannot prove which occurrence denotes which entity.

This demonstrates a decision and its evidence, not a measured model improvement.
