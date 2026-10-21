# Spotify review evidence pipeline

**Finalization in progress — October 20, 2026.** All **100,000 selected nonempty reviews** have saved valid classifications; **13 empty reviews** are quarantined. Every selected ID and source hash has been rechecked against the original CSV. The final 5,000-row independent verification is running. Final memo, full grading export/checker, zero-call warm replay and final dashboard publication remain pending. See the [current evidence audit](docs/criteria-audit-2026-10-20.md).

- Public submission repository: https://github.com/jennawang1121/spotify-review-pipeline-final
- Dashboard: https://spotify-review-evidence.jenna851121.chatgpt.site — currently a **private read-only 100k version** with an explicit incomplete-verification snapshot. All 100,013 deployed IDs, hashes and statuses and all rankings match local results. Final recommendation, final verification metadata and public access are pending.
- Deadline: October 20, 2026, 11:59 pm Pacific, per the student's updated instruction.

## Question and scope

Where should Spotify focus the next quarter of product work at the end of this historical review window? The pipeline preserves original review evidence, produces constrained labels, calculates a reproducible issue ranking and asks a separate model role to draft a grounded recommendation.

The revised assignment accepts at least 100,000 successfully classified nonempty reviews. All 660,622 source rows were ingested and profiled. A deterministic selected scope contains 100,000 nonempty reviews and all 13 empty records; 560,609 other nonempty records remain outside this analysis, not classified or quarantined. See [scope selection](evidence/scope-100k.json), [scope explanation](docs/revised-scope.md), [full ingestion](evidence/ingestion.json) and [final classification audit](evidence/final-classification-audit/validation.json).

Efficiency is an additional student design objective, not an instructor cost limit. Exact-text reuse avoids repeat enrichment without dropping original IDs. The student approved a **USD 7 total API cap**, divided into USD 1 for prior experiments and USD 6 cumulatively for the final run. Unknown usage retains budget reservations. Hosting/local compute are excluded; usage-based API estimates are not reconciled invoices.

## Architecture and saved evidence

| Role | Responsibility | Implementation |
|---|---|---|
| Enrichment | Required topic, intent, severity, sentiment and review flag | Jev `jev-1.13.0`; deterministic short-text evidence/entity extraction, bounded OpenAI extraction for long texts |
| Verification | Blind seeded independent prediction without first-pass answers | OpenAI `gpt-6-luna`, effort `none`; 5% final sample |
| Grouping | Human-readable names for the fixed issue set | Separate OpenAI instructions and saved outputs; membership and all numbers computed by code |
| Memo | Recommendation, alternative, limitations, claim/review references | Separate OpenAI instructions and structured output; validated claims |

Code controls ingestion, exact-text caching, source hashes, schema checks, retries, spending reservations, queueing, membership and ranking. Model roles exchange saved artifacts rather than conversation histories. See [architecture](ARCHITECTURE.md), [prompts](prompts/), [configuration](config.json) and [format details](docs/formats.md).

The baseline counts each original complaint/cancellation ID once. Priority is the sum of severity; ties use issue ID ascending. Means use six decimal places with HALF_UP rounding. The [final saved-classification ranking](evidence/final-classification-audit/ranking.csv) is available; the final model memo is still pending.

## Evidence by rubric criterion

| Criterion | Evidence |
|---|---|
| D1 Code/setup/artifacts | This public repository, commands below, [data instructions](data/README.md) |
| D2 Architecture/schema/provenance | [Architecture](ARCHITECTURE.md), [formats](docs/formats.md), [source validation](evidence/final-classification-audit/validation.json) |
| D3 Reproducible numbers | [Final baseline ranking](evidence/final-classification-audit/ranking.csv), [claims](evidence/final-classification-audit/claims.csv); final memo audit pending |
| D4 Recommendation/alternatives/limits | [Completed 10k development evidence](evidence/checkpoint-10000/); final recommendation pending |
| T1 Golden 50/error analysis | [Per-field results](evals/golden_50_assisted_evaluation.json), [explanation](evals/golden_50_評估說明.md), [assistance provenance](evals/golden_50_assisted.provenance.json) |
| T2 Independent/system checks | [Real injection/control checks](evals/system-checks/README.md), [10k verification](evidence/checkpoint-10000/); final 5,000-row verification running |
| T3 Cost/recovery | [Measured cold/warm pilot](cost/report.md), [editable rates](cost/rates.csv), [10k forecast](cost/projection-100k-10k.json), [actual resume recording](evidence/recovery-10k/stop-resume.html) |
| W1 Coverage | [Ingestion](evidence/ingestion.json), [100k validation](evidence/final-classification-audit/validation.json), [selected scope](evidence/scope-100k.json) |
| W2 Runnable stages/resume | [Runner](pipeline/runner.py), [47 offline tests](tests/), [odd-tail recovery](evidence/final-cache-conflict-recovery.json) |
| W3 Ranking/deployed database | [Dashboard/backend code](dashboard/README.md), [prior live integration checks](evidence/dashboard-live-checks.json); final deployment pending |

The 10k development checkpoint passed the unmodified instructor checker: [result](evidence/checkpoint-10000/official-check-complete-lineage.json), [complete-lineage export](evidence/grading-checkpoint-10000-complete-lineage/). This does not certify the pending final export. Historical failed checks remain preserved and are not the current passing result.

## Run locally

Python 3.9+; the pipeline uses the standard library. Obtain the original course ZIP using [data/README.md](data/README.md). Keep source CSV bytes unchanged. Commands run from the repository root.

```sh
python3 -m unittest discover -s tests -v
python3 -m pipeline pilot
```

The second command is an unpaid preflight. Provider execution requires local `.env` keys and an explicit `--execute-paid` flag. Copy the blank `.env.example`; never commit real keys. The existing run directories should be resumed, never reset or duplicated to bypass their cumulative limits.

Example for a new, intentionally paid small input (choose a new directory and an explicit budget):

```sh
python3 -m pipeline checkpoint --input path/to/reviews.csv --run-dir runs/my-checkpoint --phase initial --execute-paid --budget-usd 0.10
python3 -m pipeline checkpoint --input path/to/reviews.csv --run-dir runs/my-checkpoint --phase resume --execute-paid --budget-usd 0.10
```

For unchanged saved outputs, `--phase warm` verifies cache reuse. Actual measurements—not the presence of this option—establish zero new calls.

### Offline calculator: no API keys or network

```sh
python3 -m pipeline cost --calls cost/measurements/initial-1b0438bf5b944a9cb4f27bdbdda9459c/calls.jsonl --measurement cost/measurements/initial-1b0438bf5b944a9cb4f27bdbdda9459c/measurement.json --out-dir runs/offline-cost-replay
```

The fixed, unchanged 100-review cold pilot used one worker and all four roles: **107 successful calls, USD 0.007073404, 76.029452 seconds**. Its measured warm replay made **zero new calls**, cost USD 0 and took 0.020588 seconds. Editable rates are in `cost/rates.csv`; failed/unknown usage and interrupted runs remain separate. The completed 10k checkpoint cost USD 0.476171044 incrementally and its warm replay also made zero new calls.

### Offline ranking from a saved run

```sh
python3 -m pipeline --config config-final-100k.json group --db runs/final-100k/source.sqlite --out runs/replay-membership.csv
python3 -m pipeline --config config-final-100k.json rank --db runs/final-100k/source.sqlite --membership runs/replay-membership.csv --out-dir runs/ranking-replay
```

These commands make no model calls. Final portable grading artifacts and their checker command will be added after downstream execution completes.

See [inspected final-sample failures](evals/final-inspected-failures.md) and [production database integrity checks](evidence/dashboard-classification-private-checks.json).

## Evaluation and limitations

The Golden 50 contains student-supplied labels with disclosed assistant corrections to severity/entities and assistant-extracted evidence quotes. It is **not a fully independent human reference for every field**. On this mixed reference, topic/intent/severity agreement is 62%/78%/66%; this small diagnostic evaluation is not population accuracy. Golden answers were never supplied as model inputs or used to tune prompts. Detailed row differences and provenance are in `evals/`.

Independent verifier agreement is a model-to-model comparison, not human accuracy. `needs_review` flags and disagreements remain visible. The assignment specifies no minimum accuracy threshold, but independent-human provenance remains a material limitation for the human-label criterion.

Historical, self-selected reviews do not identify account revenue, plan tier, actual churn or causal effects. Cancellation language is expressed intent. Severity means functional or explicit financial/privacy/data harm, not anger or star rating. Exact duplicates retain separate original IDs in rankings. Prompt-injection tests use labelled synthetic control text; those cases never populate business results.

The final odd queue item was accidentally dispatched twice. The first saved classification was retained; the differing second result triggered a conflict and stopped execution. The queue admission bug is repaired, a regression test passes, and both real billed attempts remain visible. [Recovery evidence](evidence/final-cache-conflict-recovery.json).
