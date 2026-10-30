---
name: epub-translation-production
description: Build or revise a translated EPUB with immutable edition inputs, precise text and markup checks, responsive reading validation and traceable hashes. Use for EPUB delivery, not as a literary-quality substitute.
license: MIT
---

# Translated EPUB production

## Choose the exact edition

Record source and current target paths, hashes, and purposes. A published edition is an immutable input. Write a new edition to a unique path and refuse accidental overwrite. An explicitly identified working draft may be updated with a checkpoint; do not confuse it with a released file.

Apply only accepted editorial decisions. Connect the new artifact to the exact translated blocks, decision set, and builder version. A design pass must use the chosen current text, not recopy an obsolete file with a fixed name. Prefer writing an intermediate artifact, verifying it, and then completing delivery.

## Preserve meaning and structure

Preserve reading order, IDs, links, notes, media, and meaningful text form. Intentional structural changes need a declared purpose and allowlist: an added stylesheet, a translation note, a source correction, or an adaptation of complex markup. Byte-for-byte equality of every XML file is not the goal of a translated book.

Compare emphasis scope, nested quotations, visible anchor labels, and decorated initials as well as element counts. A new empty italic span, a whole paragraph accidentally inside an initial, or a label moved outside its link is a defect even when XML is valid.

Every final block must match its accepted translation. An English image does not become translated when metadata changes: provide appropriate translated alt text/caption, disclose the limitation, or prepare an explicitly authorized localized image.

Reconcile expected source block IDs with accepted output IDs before assembling. Account explicitly for missing, duplicated or deliberately merged/split blocks, including chapter-boundary paragraphs. A structurally valid EPUB can still contain a shifted or stale translation. Keep approved source/target correspondence separate from XML validity.

## Technical checks

- ZIP/CRC; `mimetype` first and uncompressed; XML, OPF, nav, spine, and NCX if present.
- Language metadata and document language; all local `href`/`src` targets, IDs, note references and backlinks; meaningful nonempty visible links.
- Media, fonts, and styles against the baseline and declared change allowlist.
- EPUBCheck when available: retain the tool version and full report. An unavailable tool is not a pass.
- Each report identifies the path and hash actually checked. A wrapper can verify identical hashes before and after an external validator.

Use the [release-record template](references/release-record.json) when producing an edition. No validator bundled with this repository replaces EPUBCheck or your book-specific checks.

## Design and reading aloud

Inspect real renders of the beginning, middle, ending, navigation, and difficult pages: poetry, tables, letters, illustrations. Check narrow and wide screens and enlarged text. Look at actual screenshots; zero measured overflow does not establish good typography.

Do not apply global `white-space: normal` or stack every table without understanding the book's forms. A poetic column may encode meaning or performance order. Preserve or explicitly adapt that order and inspect the result. Reader font and size controls should remain usable.

Keep Chromium rendering, a named EPUB reader, and TTS in that reader separate. Without a reader test, claim only the text-level and semantic-order evidence. Audio generation is another task; an EPUB for built-in reading aloud does not itself require an API key.

Deliver the exact artifact and concise limitations. EPUBCheck does not prove perfect translation, universal design, or flawless TTS.
