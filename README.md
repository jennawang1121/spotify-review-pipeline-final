# Spotify review evidence pipeline

**Final analysis completed — October 20, 2026.** All **100,000 selected nonempty reviews** have valid saved classifications; **13 empty reviews** are explicitly quarantined. The seeded independent sample has **4,990 valid comparisons and 10 visible failures**. The measured full warm replay made **zero new API calls**. The official checker reports `review_required` solely for six missing token-usage fields across three failed requests; classification coverage and ranking checks have no reported issues. This is not a claim of perfect model accuracy or an awarded grade.

- Public submission repository: https://github.com/jennawang1121/spotify-review-pipeline-final
- Dashboard: https://spotify-review-evidence.jenna851121.chatgpt.site
- Portable evidence: [final-100k release](https://github.com/jennawang1121/spotify-review-pipeline-final/releases/tag/final-100k)
- Final recommendation (student endorsed the proposed direction on October 20): [editorially checked memo](evidence/final-100k/memo.editorial.md), [raw model draft](evidence/final-100k/memo.raw.md), [audit](evidence/final-100k/memo-audit.json).
- Total known project API cost: **USD 4.702716959**; including outstanding reservations: **USD 4.722227834**, below the approved USD 7 cap. This is a usage-based estimate, not an invoice. Hosting/local compute are excluded. [Detailed ledger summary](evidence/final-100k/project-cost.json).

For the rubric item-by-item review, see the [full-mark risk audit](docs/full-mark-audit-2026-10-20.md).

## Grader snapshot

The full source has 660,622 rows; the final selected scope has 100,000 classified nonempty reviews plus 13 empty quarantines. Exact-text reuse accounts for 21,901 selected original IDs. Golden 50 agreement against the student-authored and student-reviewed reference with disclosed assistant preparation is topic 62%, intent 78%, and exact severity 66%; these are diagnostic comparisons. The independent 5,000-ID sample produced 4,990 valid comparisons and 10 visible failures; among valid comparisons, topic agreement was 4,479/4,990 and severity agreement 4,440/4,990. The final run's recorded non-warm stage invocations sum to 45,659.283 seconds (12.68 hours); this is a sum of measured invocations, not a single uninterrupted wall-clock clock or an API-duration sum. The project known API cost is $4.702716959, with $0.019510875 unresolved reservation. See [final measurements](evidence/final-100k/summary.json), [cost](evidence/final-100k/project-cost.json), and [a real review's full evidence path](docs/one-review-trace.md).

The original course [dataset archive and download instructions](data/README.md) identify the source. The unchanged 97,400,616-byte CSV has SHA-256 `1fc85de68a304dd8978b537cfa58793d5f41cbaf417fa32cb53899f83a2fcef6` ([full ingestion report](evidence/ingestion.json)). The reproducible final selected-scope hash is `b87ca3b10e8ff88d3a4a203f69ae9a9dc8c36fa4ed67ea8e1e3dda4363808842`.

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

The baseline counts each original complaint/cancellation ID once. Priority is the sum of severity; ties use issue ID ascending. Means use six decimal places with HALF_UP rounding. The [final saved-classification ranking](evidence/final-classification-audit/ranking.csv) is available; the [final memo and editorial audit](evidence/final-100k/) distinguish calculated ranks from product judgment.

## Evidence by rubric criterion

| Criterion | Evidence |
|---|---|
| D1 Code/setup/artifacts | This public repository, commands below, [data instructions](data/README.md) |
| D2 Architecture/schema/provenance | [Architecture](ARCHITECTURE.md), [formats](docs/formats.md), [source validation](evidence/final-classification-audit/validation.json) |
| D3 Reproducible numbers | [Final baseline ranking](evidence/final-classification-audit/ranking.csv), [claims](evidence/final-classification-audit/claims.csv); [memo audit](evidence/final-100k/memo-audit.json) |
| D4 Recommendation/alternatives/limits | [Final recommendation](evidence/final-100k/memo.editorial.md), alternatives and limitations |
| T1 Golden 50/error analysis | [Per-field results](evals/golden_50_assisted_evaluation.json), [explanation](evals/golden_50_評估說明.md), [assistance provenance](evals/golden_50_assisted.provenance.json) |
| T2 Independent/system checks | [Real injection/control checks](evals/system-checks/README.md), [Final verification and feedback](evidence/final-100k/quality-feedback.md): 4,990 valid / 10 failed |
| T3 Cost/recovery | [Measured cold/warm pilot](cost/report.md), [editable rates](cost/rates.csv), [10k forecast](cost/projection-100k-10k.json), [actual resume recording](evidence/recovery-10k/stop-resume.html) |
| W1 Coverage | [Ingestion](evidence/ingestion.json), [100k validation](evidence/final-classification-audit/validation.json), [selected scope](evidence/scope-100k.json) |
| W2 Runnable stages/resume | [Runner](pipeline/runner.py), [47 offline tests](tests/), [odd-tail recovery](evidence/final-cache-conflict-recovery.json) |
| W3 Ranking/deployed database | [Dashboard/backend code](dashboard/README.md), [final public integration checks](evidence/dashboard-final-public-checks.json) |

The 10k development checkpoint passed the unmodified instructor checker: [result](evidence/checkpoint-10000/official-check-complete-lineage.json), [complete-lineage export](evidence/grading-checkpoint-10000-complete-lineage/). The final checker result is [review_required for unknown failed-request usage](evidence/final-100k/official-check.json); all such attempts remain in the export. Historical failed checks remain preserved and are not the current passing result.

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

These commands make no model calls. First download both ZIP files from the release and extract them into this checkout:

```sh
unzip spotify-100k-saved-run.zip
unzip spotify-100k-submission.zip
python3 course/check_submission.py check --reference runs/reference-final-100k.json --submission grading --out runs/offline-official-check.json
```

The saved reference is a convenience artifact generated from the course source. To independently regenerate it after obtaining the original CSV:

```sh
python3 course/check_submission.py reference --full data/course/spotify_reviews_18months.csv --analysis data/scope-100k/analysis.csv --out runs/reference-rebuilt.json
```

`spotify-100k-submission.zip` contains grading records, complete relevant call lineage, checkpoints, claims, membership, final analysis, verification, memo and cost evidence. `spotify-100k-saved-run.zip` contains the saved classification database, configuration and selected source. [SHA-256 manifest](evidence/final-artifact-manifest.json) identifies the exact archives. The final warm replay took 15.661 seconds with zero new calls ([measurement](evidence/final-100k/warm-check.json)). The original source is not a dependency of the offline ranking replay.

See [inspected final-sample failures](evals/final-inspected-failures.md) and [production database integrity checks](evidence/dashboard-classification-private-checks.json).

## Evaluation and limitations

The student supplied the substantive Golden 50 analysis: her [submitted workbook](evals/golden_50_student_submitted.xlsx) had 49/50 topics, all 50 intents, severities, sentiments and review flags, and 32/50 entity entries. She specified the remaining topic (C24) in chat, directed the severity corrections, and confirmed that all final rows reflect her own judgment ([field-level provenance and attestation](evals/golden_50_assisted.provenance.json)). The assistant converted entity entries to source-matching JSON and extracted verbatim quotes; the student reviewed and adopted the final rows, including their quotations. Those assistant preparation steps remain disclosed. This is a **student-authored and student-reviewed reference with assistant preparation**, not a claim that she typed every character of every field. Against this reference, topic/intent/severity agreement is 62%/78%/66%; this small diagnostic evaluation is not population accuracy. Golden answers were never supplied as model inputs or used to tune prompts. Detailed row differences and provenance are in `evals/`.

Independent verifier agreement is a model-to-model comparison, not human accuracy. `needs_review` flags and disagreements remain visible. The assignment specifies no minimum accuracy threshold, and the disclosed assistant contribution to formatting, corrections and quote extraction should be considered when assessing the human-label criterion.

Historical, self-selected reviews do not identify account revenue, plan tier, actual churn or causal effects. Cancellation language is expressed intent. Severity means functional or explicit financial/privacy/data harm, not anger or star rating. Exact duplicates retain separate original IDs in rankings. Prompt-injection tests use labelled synthetic control text; those cases never populate business results.

The final odd queue item was accidentally dispatched twice. The first saved classification was retained; the differing second result triggered a conflict and stopped execution. The queue admission bug is repaired, a regression test passes, and both real billed attempts remain visible. [Recovery evidence](evidence/final-cache-conflict-recovery.json).
