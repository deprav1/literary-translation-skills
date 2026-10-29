# Maintaining the blind preference pilot

Public frontend: <https://deprav1.github.io/literary-translation-skills/>.

## Architecture

- `site/` is a buildless HTML/CSS/JS site deployed by GitHub Pages Actions.
- `site/data.json` holds the current versioned corpus and post-choice attribution. Identity hiding is an interface property; source code is public.
- `backend/worker.js` is a separate Cloudflare Worker. D1 stores votes and rate buckets. No browser API credential is needed or included.
- `backend/catalog.js` is an authoritative candidate allowlist generated from the same corpus. The server does not trust a client-supplied method label.
- The browser keeps a random participant ID, candidate order, and chosen votes in localStorage. The server stores only its dataset-scoped HMAC key.
- The UI waits for server acknowledgement before saying that a choice is in the shared counter. A network failure keeps the choice locally and offers an idempotent retry.

See [content provenance and privacy](../site/CONTENT.md), the [generation record](../site/METHODS.json), and [backend contract](../backend/README.md).

## Updating the corpus

1. Select matched source/published-translation excerpts with documented reproduction rights and edition details. Prefer complete paragraphs. Do not insert a generated text under the published-translator label.
2. Generate both AI conditions independently using the same model/settings. Do not show either condition the published translation or the other generated output. Record prompts, model, date, and any subsequent editing honestly.
3. Update `site/research/selected.json`, `translation-input.json`, `skilled.json`, and `baseline.json`.
4. Run `python scripts/build_blind_catalog.py`. It derives a new dataset version from the exact corpus. If generation settings or conditions change, update the method record and versioning logic as well.
5. Run package/site validation and Node/Python tests. Inspect the actual page on desktop and phone.
6. Deploy the backend's matching catalog before making a new frontend version available. Do not merge statistics from different datasets. Preserve historical catalogs and an erasure plan if keeping votes from older versions.

The current builder emits the current dataset allowlist. It is not a migration tool for historical cohorts. Plan a multi-version rollout before replacing a live dataset with substantial participation.

## Deploying your own backend

Requires an authorized Cloudflare account with Workers and D1. The configuration contains a deployment resource ID, not an access token; a fork needs its own database.

```sh
npx wrangler login
npx wrangler d1 create your-votes-database
```

Replace the Worker name and D1 database name/ID in `backend/wrangler.jsonc` with your own resources. Set `ALLOWED_ORIGIN` to the exact Pages origin for your site. For accounts with multiple memberships, select your intended `CLOUDFLARE_ACCOUNT_ID` locally; it is not necessary to commit account identifiers.

```sh
npx wrangler d1 migrations apply your-votes-database --remote --config backend/wrangler.jsonc
npx wrangler secret put VOTE_SALT --config backend/wrangler.jsonc
npx wrangler deploy --config backend/wrangler.jsonc
```

Generate a strong unique salt and provide it through the secret command's input. Do not commit it or put it in the frontend. Keep it stable: changing the participant-key salt breaks association with existing votes and their deletion identifiers. Secret rotation requires a deliberate data-migration/erasure plan.

Set the returned HTTPS Worker endpoint in `site/config.json`. The Pages workflow publishes only `site/`; backend deployment is a separate operation. Do not put Cloudflare credentials in a public Pages artifact.

## Validation

```sh
python scripts/validate.py
python scripts/validate_site.py
python -m unittest discover -s tests -v
node --test site/tests/logic.test.mjs backend/worker.test.js
```

Browser acceptance should cover: no identities before choice; reveal after choice; all six rounds; reload persistence; shared acknowledgement; duplicate retry; two independent browser IDs; aggregate consistency; failed API fallback; deletion; keyboard and narrow layout. Remove the test participants' votes afterward. Do not publish invented seed statistics.

## Interpretation and abuse limits

Counts are preferences for these particular historical and generated outputs. One browser can cast one vote per fragment/version. A new device, cleared storage, or a forged public API client can create another pseudonymous participant. Origin checks and a daily hashed-IP limit deter ordinary mistakes and excessive requests; they do not turn the pilot into an authenticated research study. The dashboard calls the distinct identifiers browsers, not unique people.

Deleting votes retains a hashed erasure tombstone so delayed POSTs cannot recreate them. Browser identity loss prevents linking old choices to that browser. Infrastructure providers may process network metadata even though raw IPs are not stored in the D1 vote table.
