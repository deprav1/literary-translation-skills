# Working on this repository

This is a public collection of literary-translation instructions, not a translation service or book repository.

- Keep each skill independently installable: required references stay inside its folder. Do not link from a skill into another skill or repository-level docs as a required dependency.
- Keep instructions concise and specific; detailed examples belong in references or examples.
- Distinguish sourced professional principles, original editorial decisions, and technical engineering practices.
- Do not turn a single book's profile into a universal translation rule.
- Do not include private paths, credentials, personal audit logs, books, full translations, or copied third-party skill bundles.
- Preserve user intent and authorization. A skill must not force a whole-book process on an excerpt request or authorize external uploads.
- Document uncertainty and meaningful limitations. Do not claim automated validators prove literary quality.
- Run `python scripts/validate.py` and `python -m unittest discover -s tests -v` before proposing a change.
