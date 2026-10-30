# Maintaining the blind preference pilot

Public frontend: <https://deprav1.github.io/literary-translation-skills/>.

## Architecture

- `site/` is a buildless HTML/CSS/JS site deployed by GitHub Pages Actions.
- `site/data.json` holds the current versioned corpus and post-choice attribution. Identity hiding is an interface property; source code is public.
- The current corpus contains 40 fragments; 36 are vote-eligible because four have identical baseline/reviewed outputs. Each local participant receives a deterministic cohort of 20 selected from the versioned corpus; different participant IDs may receive different cohorts. The backend vote allowlist contains only the 36 vote-eligible fragment IDs.
- `backend/worker.js` is a separate Cloudflare Worker. D1 stores votes and rate buckets. No browser API credential is needed or included.
- `backend/catalog.js` is an authoritative candidate allowlist generated from the same corpus. The server does not trust a client-supplied method label.
- The browser keeps a random participant ID, candidate order, and chosen votes in localStorage. The server stores only its dataset-scoped HMAC key.
- The UI waits for server acknowledgement before saying that a choice is in the shared counter. A network failure keeps the choice locally and offers an idempotent retry.

See [content provenance and privacy](../site/CONTENT.md), the [generation record](../site/METHODS.json), and [backend contract](../backend/README.md).

## Reproduce the isolated v5 generations

1. Prepare an English-only source pack outside this repository: `works` with full original story context, edition URLs and text hashes; `fragments` with stable IDs, work IDs and exact English text. Do not put historical Russian translations, prior outputs or chat history in it.
2. Run `python scripts/run_fresh_generations.py --source-pack /temporary/source-pack.json --workspace /temporary/new-run --model gpt-6.1-sol`. The workspace must not exist as a completed run; stage directories refuse overwrite. Calls are sequential and each phase starts a fresh ephemeral, tool-disabled session. No paid-provider key or account is configured by this script; it uses the user's configured Codex authentication.
3. Retain every first complete output and all failures. Do not silently retry literary alternatives until a preferred winner appears. Structural repair or a transport retry must remain explicit in the record.
4. After all eight phases complete, use `python scripts/publish_fresh_artifacts.py --workspace /temporary/new-run --source-pack /temporary/source-pack.json`. It publishes outputs, stage instructions, hashes and runtime summaries, excluding full stories, raw logs and composite prompts. Preserve the existing evidence set before starting a different published run.
5. Preserve the current catalog and dataset in the historical archive, then build the new dataset. The v5 builder derives its version from exact candidates and the execution record. Never relabel an old output as a new generation.
6. Validate packaging, source/translation anchors, stage coverage, artifact hashes and the frontend/backend catalogs. Deploy the matching backend before the frontend, and keep historical identities usable for erasure.

The baseline receives no skill instructions. Craft receives a source-linked plan, glossary and pilot calibration; QA receives that craft draft and source context. Evaluation sees anonymized frozen AI outputs only and does not select which generation to publish. No generator receives historical Russian text. Runtime isolation cannot exclude prior model training on these public works. This is a workflow comparison with different call counts, not a controlled estimate of a skill text's isolated effect.

The reading interface supports previous-round and numbered navigation, skips without votes, text-size controls and single-column layout. A skipped item remains available; it never enters the shared counter. Statistics use declared `workId` values. Distinct-browser counts are shown only for the whole dataset. `resultsViewedAt` and later choices' `resultsSeenBeforeChoice` remain local, so aggregate results cannot be filtered by that exposure.

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

Browser acceptance should cover: no identities before choice; reveal after choice; all assigned rounds; reload persistence; different cohort for a different browser ID; shared acknowledgement; duplicate retry; two independent browser IDs; aggregate consistency; failed API fallback; deletion; keyboard and narrow layout. Remove the test participants' votes afterward. Do not publish invented seed statistics.

The reading interface also supports previous-round and numbered navigation, local skips without votes, text-size controls and a single-column layout. Old valid states without a `skipped` field remain usable. A skipped item remains available in history; it never enters the shared counter. The current-results selector uses each round's explicit `comparisonGroup`, generated from the recorded review coverage. Browser totals are shown only for the whole dataset, because the API does not provide subgroup distinct-browser counts. `resultsViewedAt` and later choices' `resultsSeenBeforeChoice` are local history only; the server does not collect those flags, so aggregate results cannot be filtered by that exposure.

## Interpretation and abuse limits

Counts are preferences for these particular historical and generated outputs. One browser can cast one vote per fragment/version. A new device, cleared storage, or a forged public API client can create another pseudonymous participant. Origin checks and a daily hashed-IP limit deter ordinary mistakes and excessive requests; they do not turn the pilot into an authenticated research study. The dashboard calls the distinct identifiers browsers, not unique people.

Deleting votes retains a hashed erasure tombstone so delayed POSTs cannot recreate them. Browser identity loss prevents linking old choices to that browser. Infrastructure providers may process network metadata even though raw IPs are not stored in the D1 vote table.
