# Spotify Review Evidence dashboard

Cloudflare Worker backend + D1 SQLite database + browser UI. No runtime model provider credentials or model calls. Data is real saved pipeline output; the first read idempotently imports the versioned seed into migrated database tables. Subsequent API reads query that database. The current seed is the 500-review development checkpoint, not a completed 100k run.

`src/backend.js` owns read-only API routes; `src/index.html`, `client.js` and `style.css` implement the UI. Build embeds them into one Worker, avoiding a frontend framework and runtime dependency bundle. Drizzle dependencies are schema/build tooling only; the deployed Worker has no npm runtime imports. `db/schema.ts` and generated `drizzle/` own schema changes. Never put review datasets in migration SQL.

API routes: `/api/summary`, `/api/issues`, `/api/reviews`, `/api/reviews/:original_id`, `/api/recommendation`, `/api/quality`. The issue endpoint recalculates count/severity sum/half-up means from database records. Recommendation, claims, shared taxonomy, verification and source provenance are also stored in the database. No public data-write endpoint is exposed.

From this directory, with Node 22+:

```sh
npm ci
npm run build
npm run validate
npm run dev
```

Local preview uses a persisted real SQLite file, the same Drizzle schema and the same Worker API handler. Production uses the logical `DB` D1 binding declared in `.openai/hosting.json`. The Sites publishing workflow applies schema migrations before uploading the Worker. Build output is `dist/server/index.js`; edit `src/` and regenerate, rather than editing generated output. Publish through Sites tools with the exact built-source commit and archive; preserve the existing project ID.

To export a later fully completed pipeline checkpoint, from the parent pipeline folder:

```sh
python3 -m pipeline.dashboard_export --run-dir runs/checkpoint-500 --summary evidence/checkpoint-500/summary.json --memo evidence/checkpoint-500/memo-editorial.md --out dashboard/data/seed.json
```

The exporter rejects pending rows and synthetic classification provenance. Inspect the memo argument, refresh the seed, build and republish. Data revisions have separate database keys. The source contains public CC0 course review extracts, exact original hashes and saved predictions; it never includes `.env`, provider keys or human golden answers.
