# Sources, design references, and limits

Reviewed for the initial public edition on 2026-10-29. This is not an exhaustive bibliography of translation studies. The research pass also checked public skill discovery and evaluation repositories; their files were not copied into this project.

## Literary and professional principles

| Source | What it supports | What it does not establish |
|---|---|---|
| [ALTA: Guidelines for Evaluating Literary Translation](https://literarytranslators.org/guidelines-for-hiring-and-promotion-decisions/) | Translation as literary and scholarly production; attention to style, voice, tone, nuance, and cultural knowledge | Our exact review stages, JSON records, or a rule forbidding all explicitation |
| [ALTA Resources](https://literarytranslators.org/resources/) | Professional resources, organizations, mentorship, and related guidance | A judgment on a particular sentence or this repository's entire workflow |
| [Authors Guild: Literary Translation Model Contract](https://www.authorsguild.org/member-services/literary-translation-model-contract/) | Translator credit, creative labor, and professional/contractual context | Sentence-level craft rules or proof that an AI review is independent |
| [EPUBCheck](https://github.com/w3c/epubcheck) | Technical EPUB conformance validation | Translation fidelity, aesthetic merit, or real-reader TTS quality |
| [European Commission: Translation quality](https://translation.ec.europa.eu/languages-and-translation-european-commission/translation-quality_en) | Fit-for-purpose translation, bilingual revision, monolingual review, audience and context | A literary scoring formula or an endorsement of AI judging |
| [PEN America: 2023 Manifesto on Literary Translation](https://pen.org/report/translation-manifesto/) | Translator voice, cultural and historical context, ethical visibility of creative labor | A sentence-level checklist or an automatic quality test |
| [IIIT: Translation Strategies and Guidelines](https://iiit.org/en/research-tools/resources/translation-strategies-and-guidelines/) | Read the work or a sufficient passage before translating; preserve voice and problem areas | A universal rule for every genre or language pair |

Some source pages may be unavailable or change. A URL and access date do not mean every linked document has been read. Do not expand a general principle into a claim that a professional association endorses this implementation.

The scope modes, evidence levels, exact patch records, and adversarial treatment of reviewer suggestions are this project's own editorial/engineering choices. Synthetic examples illustrate those choices; they are not borrowed book passages.

## Repository design references

- [openai/skills](https://github.com/openai/skills): discoverable skill directories, concise entrypoints, and resources scoped to a skill.
- [anthropics/skills](https://github.com/anthropics/skills): self-contained skill layout and practical examples.
- [vercel-labs/skills](https://github.com/vercel-labs/skills): discovery and installation conventions across agent hosts.
- [Agent Skills specification](https://agentskills.io/specification): interoperable skill packaging conventions.

These repositories informed organization and installation guidance. Their content has not been bundled or relicensed here. Upstream repositories may contain mixed licenses; check the license of any actual file you reuse. This project does not infer a blanket license from a GitHub metadata field.

## Evaluation and discovery references

| Source | What we used | Boundary |
|---|---|---|
| [LiteraryTranslation](https://github.com/marzenakrp/LiteraryTranslation) | Paragraph-level context, blind pairwise preference, span-level error annotations, and the need for human intervention | Research data and annotations are not bundled; the repository reports persistent critical errors |
| [Last Translation Benchmark](https://github.com/zouharvi/last-translation-benchmark) | Verification rules as explicit gates before aggregate comparison | A hard-example benchmark is not a literary-quality score for ordinary prose |
| [RULER/VERSE](https://github.com/sheikhshafayat/ruler-verse) | Separate expert-rubric checks from questions about literary effects and style | LLM evaluation remains a proposal or triage layer without qualified review |
| [skills.sh discovery](https://skills.sh/) and [deusyu/translate-book](https://github.com/deusyu/translate-book) | Discovery of installable workflows, manifest hashes, resumable book pipelines, and context windows | Popularity is not evidence of literary quality; this project does not import its parallel-agent or external-tool pipeline |

The compact evaluation skill in this repository is an original synthesis of these principles. It keeps hard failures, soft dimensions, pairwise choices, and reviewer limits separate so the blind pilot can be used without claiming a general benchmark.

## Repository scan (2026-10-29)

Stars and forks are a discovery signal, not proof of literary quality. Counts below were read from the public GitHub API on this date and will drift.

| Repository | Stars / forks | License | Useful idea retained here | Boundary |
|---|---:|---|---|---|
| [yihong0618/bilingual_book_maker](https://github.com/yihong0618/bilingual_book_maker) | 9,913 / 1,294 | MIT | Session context, glossary learning, tag classification, and format-aware book output | External providers and a full application are outside this skills collection |
| [andrewyng/translation-agent](https://github.com/andrewyng/translation-agent) | 5,814 / 713 | MIT | Draft → reflection → revision and explicit glossary/evaluation limits | The repository calls itself a demonstration, not mature software |
| [deusyu/translate-book](https://github.com/deusyu/translate-book) | 2,166 / 261 | MIT | Manifest hashes, resumable chunks, neighboring context, and preflight structure checks | Its parallel-agent and Calibre/Pandoc pipeline is not copied |
| [minghao-wu/transagents](https://github.com/minghao-wu/transagents) | 606 / 29 | Apache-2.0 | Separate translator, critic, and publication-style roles; documented omissions and cultural-consistency failures | The paper's multi-agent system and data are not bundled |
| [sukamenev/booktrans](https://github.com/sukamenev/booktrans) | 53 / 4 | MIT | Book passport, context-sensitive glossary, correction queue, and human acceptance | A runnable whole-book application is outside this repository |
| [hydropix/TranslateBooksWithLLMs](https://github.com/hydropix/TranslateBooksWithLLMs) | 2,554 / 338 | AGPL-3.0 | Style presets and checkpoints were reviewed as useful concepts | AGPL application code is not imported into this MIT project |

The scan also found small or unlicensed candidates and gated research releases. They remain references only when their evidence is useful; popularity alone never promotes code or instructions into this repository.

### Implementation inspection

The following paths were read directly, beyond repository descriptions. File counts come from complete, non-truncated Git trees; they describe repository breadth, not translation volume or effectiveness.

| Inspected revision | Scope and evidence | Integration decision |
|---|---|---|
| [translation-agent utils.py](https://github.com/andrewyng/translation-agent/blob/e0fc605acbb5d78cb7a58a98bc8bd8f0056df49c/src/translation_agent/utils.py) | 24 repository files; initial-translation and reflection functions | Use evidence-based critique. A second prompt to the same model does not establish independent validation. |
| [bbm-plan SKILL.md](https://github.com/yihong0618/bilingual_book_maker/blob/e1027a4823e98f668ef950740b6f805ec30bd3b2/.agents/skills/bbm-plan/SKILL.md) | 304 repository files; task routing, disk checkpoints, explicit EPUB classification | Retain classification and persistent state ideas. The skill depends on its application checkout and assumes bilingual output; our instructions keep the user's chosen output. |
| [BookTrans translation prompt](https://github.com/sukamenev/booktrans/blob/45366f1c248d2293f8b9e1328730863cec7bdc5c/src/booktrans/prompts/translate.md), [editing prompt](https://github.com/sukamenev/booktrans/blob/45366f1c248d2293f8b9e1328730863cec7bdc5c/src/booktrans/prompts/edit.md), [Russian rules](https://github.com/sukamenev/booktrans/blob/45366f1c248d2293f8b9e1328730863cec7bdc5c/src/booktrans/langs/ru.md) | 224 repository files; separate source-free editing, poetry handling, quotation policy, target-language checks | Retain separate fluency and fidelity passes; recheck changes against the source. Do not adopt remembered quotations as verified, mandatory footnotes, universal meter preservation, or unconditional grammatical rewrites. |

The TransAgents root LICENSE contains Apache-2.0 while its README badge says CC BY 4.0. Treat individual data/output rights as unresolved; no source text, outputs, or third-party implementation was imported. Applications above were inspected, not installed or executed against provider accounts.

The pasted Argon response was used as a candidate list, not as authority. Its useful Russian-target checks were converted into conditional review questions rather than hard rules to delete pronouns, passive voice, or foreignness. Named books and translator examples were not copied into prompts or few-shot data; they need edition, rights, and context checks before any separate use.

## Attribution and book profiles

Optional profiles name works to identify their intended scope. They contain original editorial notes, not official translations, full books, or long source excerpts. Book authors and publishers retain their rights. The repository's MIT license covers its original material only.
