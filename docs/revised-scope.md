# Revised assignment scope — received 2026-10-06

The user supplied [revised instructor guidelines](assignment-revised-2026-10-06.txt) and explicitly confirmed the alternative minimum of 100,000. Its overview and Definition of Done permit at least 100,000 source IDs and at least 100,000 valid nonempty classifications. Efficiency remains the user's design goal; rubric compliance remains the acceptance criterion.

## Frozen analysis scope

- Preserve the existing complete ingestion: 660,622 source IDs and original hashes, including all 13 empty texts.
- Target 100,000 **nonempty successfully classified records**, plus the 13 empty-text quarantines: 100,013 analysis IDs. Failures/pending rows do not count toward the 100,000 success target.
- Select the lowest SHA-256(seed + ':' + original review_id) values using the course seed. Selection uses neither labels nor text difficulty, length, sentiment, stars or predicted topic. Preserve original source order and six source values.
- This extends the official development sampling sequence: all fixed 100, 500 and 10,000 IDs and all 50 original golden texts are included. Golden answers are never read by the selector or model requests.
- The selected scope has 78,099 distinct nonempty texts; exact-text reuse avoids 21,901 first classifications while counting each original ID in the final aggregates. One distinct text requires the long-text extraction route.
- Keep the other 560,609 nonempty reviews in the full ingestion store, explicitly outside this analysis scope. Do not call them classified, failed, or empty-text quarantines. Memo/dashboard numbers describe the 100k sample, not the entire source or Spotify's customer population.

Preparation was entirely offline and does not claim model completion. [Scope manifest](../evidence/scope-100k.json) records source/output checksums and sample inclusion. Local generated CSV/hash index: `data/scope-100k/`. Reproduce in a fresh directory:

```sh
python3 -m pipeline.scope --out-dir data/scope-100k-reproduced
```

## Required deployed product

The revised document requires a deployed dashboard, deployed backend and database. Store processed reviews, issue membership, aggregates, claims and the checked AI recommendation. The backend retrieves these saved values; the dashboard shows overall coverage/metrics, issue ranking and a recommendation linked to issue IDs, review evidence and saved numbers. Page views and filtering need no additional model calls. Provide the live URL and access instructions in the README; verify displayed values against offline ranking. This product is planned, not yet deployed. Hosting/runtime costs remain unmeasured.

## Budget and time estimate

Initial estimates below are extrapolations from the real fixed-100 cold measurement, **not actual 100k bills or runtimes**. Each stage has its own denominator; grouping and memo occur once. The 500 and 10k checkpoints must refresh this estimate.

| Scenario | Known API subtotal | Known modeled stage wall hours, one worker |
|---|---:|---:|
| Exact-text reuse, 5% blind verification | US$4.6925 | 14.54 |
| 20% more attempts, 10% verification | US$6.1479 | 20.76 |
| No classification reuse, 5% verification | US$5.8872 | 17.84 |

One long-text extraction, large-scope local processing and deployment costs are unmeasured; totals remain unknown. Six historical quota failures also have unresolved usage and are not treated as free. The authorized US$1 experiment budget has not increased. No 100k paid run has started. [Editable scenarios](../cost/scenarios-100k.json) and [projection details](../cost/projection-100k.json) preserve assumptions. Original full-source scenarios remain as a comparison and to satisfy the unchanged calculator specification.

```sh
python3 -m pipeline cost --calls cost/measurements/initial-1b0438bf5b944a9cb4f27bdbdda9459c/calls.jsonl --measurement cost/measurements/initial-1b0438bf5b944a9cb4f27bdbdda9459c/measurement.json --scenarios cost/scenarios-100k.json --out-dir runs/100k-cost-replay
```

## Version discrepancy to disclose

The revised text still includes a coverage-point formula with denominators 660,622 and 660,609, plus older full-source instructions elsewhere. The ZIP's contract and manifest predate the relaxation. Preserve these originals unchanged; document the user's explicit instructor update and the exact selected scope. The original checker accepts an explicit analysis reference and can validate subset consistency, but a local pass does not settle the instructor's final grading denominator or certify full-source completion. Do not present a self-calculated grade as an official grade.

## Refresh after the completed 500 checkpoint

[Actual checkpoint evidence](../evidence/checkpoint-500/README.md): 500 completed, 379 new unique classifications, 406 successful new calls, US$0.024163929 incremental API cost, 605.62 seconds; warm replay zero calls. The 500-based 100k known API subtotals are **US$4.70 base / US$6.16 conservative / US$5.89 without classification reuse**. One-worker stage-time extrapolations rose to **34.04 / 45.46 / 42.51 hours** because observed provider latency was slower. These remain projections with unmeasured extraction, local work and hosting; measure bounded concurrency and 10k before committing to final runtime. [Latest assumptions](../cost/scenarios-100k-500.json) and [latest projections](../cost/projection-100k-500.json) use 379 new unique classifications and 25 verifier cases as denominators, not 500 paid classifications.

Offline reuse after the 500 run imported 479 distinct saved labels into the prepared next scopes. They cover **1,437 of 10,000 development IDs** and **10,477 of 100,000 selected nonempty final IDs**, with 13 final empty quarantines and zero additional API calls. The remaining final pending count is 89,523 original IDs (77,620 distinct unseen texts). This is cache preparation, not a completed 10k/100k staged run. See [preparation evidence](../evidence/next-checkpoints-prepared.json).
