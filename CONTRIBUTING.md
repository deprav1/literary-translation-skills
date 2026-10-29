# Contributing

Thank you for improving these skills. Useful contributions include a clearer decision rule, a small counterexample, a language-pair nuance, a reader-validation improvement, or a portability fix.

## Before opening a pull request

1. Describe the concrete failure or missing capability.
2. Use a short synthetic, public-domain, or appropriately licensed source/target example.
3. Explain the expected editorial decision and its limits. Do not equate a stylistic preference with a demonstrated error.
4. Keep changes scoped. Avoid adding universal rules for one unusual sentence.
5. Keep required references inside each skill directory; a copied skill must work by itself.
6. Run:

```sh
python scripts/validate.py
python -m unittest discover -s tests -v
```

## Documentation

Keep the English and Russian READMEs consistent on behavior, installation, and limits. Source citations should say what the source actually supports. Do not describe a contractual resource as a craft handbook or a conformance check as a literary benchmark.

## Privacy and rights

Do not submit credentials, personal paths, private editorial logs, full books, complete translations, or unlicensed copied skill bundles. Small examples should be sufficient to reproduce a reasoning problem.

## License

By submitting a contribution, you agree to license your original contribution under this repository's MIT license. Third-party material needs compatible permission and attribution; linking a reference does not relicense it.
