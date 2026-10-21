# Spotify Review Evidence dashboard

Cloudflare Worker backend + D1 database + browser UI. Browsing makes no model calls. Provider credentials are never deployed. The final-scope database contains 100,000 saved classifications plus 13 empty-text quarantines. Final verification/memo metadata is published separately; staging snapshots explicitly show pending work.

`src/backend.js` serves SQL queries; `src/index.html`, `client.js` and `style.css` implement the UI. `db/schema.ts` and immutable generated `drizzle/` migrations own the schema. Data is loaded separately, never embedded into schema migrations. `data/seed.json` contains compact analysis metadata and verifier outcomes, not the full 100k review table. Verification is stored in bounded 500-row analysis values and reassembled by the backend.

## Local database and preview

With the saved final run restored under `runs/final-100k/`, run from the repository root:

```sh
python3 -m pipeline.dashboard_local
cd dashboard
npm ci
npm run build
npm run validate
npm run dev
```

Node 22.13+ is needed for the local SQLite adapter. The production Worker uses D1 and has no npm runtime dependencies. The preview uses persistent `.sites-runtime/preview.sqlite`, the same schema and the same API handler. No model keys are required. Build output is `dist/server/index.js`; edit `src/` and regenerate.

## Production database loading

The existing Site identity and `DB` binding are in `.openai/hosting.json`. Sites applies schema migrations before deployment. The real initial 100k import used an owner-private staging version; rows were uploaded idempotently in bounded batches, and then the importer was removed from the deployed build. The normal build rejects POST requests, including `/api/import`.

To rebuild this authorized owner-private setup only, an explicit `SITES_PRIVATE_IMPORT=1` build enables the saved temporary importer from `scripts/private-import-handler.js`. Publish that build privately, upload saved records with `python3 -m pipeline.dashboard_upload --restart` from the root, then build with that variable unset and publish the normal read-only version **before** changing access to public. Never use the temporary importer on a public Site. Service credentials are supplied through hidden terminal input and are not saved.

## Metadata and checks

After final pipeline completion and memo review:

```sh
python3 -m pipeline.dashboard_export --run-dir runs/final-100k --summary evidence/final-100k/summary.json --memo evidence/final-100k/memo.editorial.md --out dashboard/data/seed.json --external
python3 -m pipeline.dashboard_check --private
```

The metadata exporter rejects pending classification rows and synthetic provenance. Publish the exact built/pushed source through Sites. Once public, run `python3 -m pipeline.dashboard_check` without credentials. This compares **every** original ID, source hash and status, all ranked counts/scores/means, representative complete source/prediction payloads, final verification coverage and the recommendation's issue reference.

API routes: `/api/summary`, `/api/issues`, `/api/reviews`, `/api/reviews/:id`, `/api/recommendation`, `/api/quality`, `/api/integrity?page=N`. Integrity pages hash ordered groups of 1,000 ID/hash/status triples. The issue endpoint recalculates counts and severity sums from saved records, using deterministic HALF_UP means. SQL filters and pagination never invoke a model. Golden reference answers and student evaluation reports stay outside the website.
