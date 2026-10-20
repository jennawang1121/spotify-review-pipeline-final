# Real 500-review development checkpoint

Completed 2026-10-06 using unchanged `checkpoint_500.csv`. All 500 original IDs have schema-valid saved classifications; 479 distinct texts are represented. This is a **partial-cache expansion**, not a cold 500 benchmark. The separate unchanged, cold/warm 100 benchmark remains the required cost deliverable.

| Measurement | Initial checkpoint | Warm replay |
|---|---:|---:|
| Completed original IDs | 500 | 500 |
| IDs already covered at start | 112 | 500 |
| New unique text classifications | 379 | 0 |
| New calls: classification / verify / group / memo | 379 / 25 / 1 / 1 | 0 / 0 / 0 / 0 |
| Failed attempts | 0 | 0 |
| Incremental API USD | 0.024163929 | 0 |
| End-to-end seconds | 605.623295 | 0.068811 |

One worker; Jev `jev-1.13.0`; OpenAI `gpt-6-luna`, effort `none`; no strong-model fallbacks. The 100 saved classifications from the cold benchmark covered 112 checkpoint IDs. Another nine original IDs reused newly classified texts. Prior classification cost of US$0.005455254 belongs to the prior experiment; adding it gives US$0.029619183 for the labels plus this checkpoint's new downstream calls, excluding the prior benchmark's separate downstream tasks. Do not bill inherited cache hits as new requests.

The checkpoint adds US$0.024163929 to the project's prior known US$0.016565190, yielding **US$0.040729119 known API subtotal**. Six earlier quota failures still have unknown usage; the complete project total remains unknown and their reservations remain intact. The US$1 experiment allocation is unchanged.

[Summary JSON](summary.json) includes measurements, quality diagnostics and the exact ranking. [Call/status/measurement files](../../cost/checkpoint-500/) preserve all 406 real calls and 500 records. The original request/response files remain in `runs/checkpoint-500/`; inherited provenance points to `runs/pilot-benchmark/`. Publish these source artifacts with the final repository/release. This local report is not a deployment or an official grading result.

## Feedback and error analysis

Independent seeded sample: 25 original IDs, verifier sees only original text and taxonomy. The first prediction is compared afterward. [Saved predictions and disagreements](verification.jsonl) include every sampled case.

| Field | Agreement |
|---|---:|
| Topic | 23/25 |
| Intent | 25/25 |
| Severity | 21/25 |
| needs_review | 17/25 |
| Sentiment within predeclared 0.25 tolerance | 23/25 |

Sentiment mean absolute difference: 0.0852. Thirteen cases have at least one categorical disagreement. These are model-to-model diagnostics, **not human accuracy**; both models can agree and still be wrong. The student Golden 50 remains unfilled.

Assistant inspection of the saved development cases suggests the following concrete follow-ups. These are review hypotheses, not student labels or accepted corrections; saved predictions remain unchanged.

- `b4f4440f-d952-405d-bf7b-f19fb0adf484`: a request to restore playlist search. Jev says usability/severity 1; verifier says catalog/severity 3. Both call it a request, although the reported removal and criticism may trigger complaint precedence. Agreement on intent therefore does not establish correctness. Inspect the search-versus-playlist boundary and lost-function-versus-pure-request distinction.
- `e5e6c55f-3069-4b7c-9807-f8b5d5bf2726`: ad complaints mentioning premium. Jev says usability, verifier billing. The taxonomy says a paid-plan mention alone is insufficient for billing, so the verifier should not automatically overwrite Jev.
- `3bfefa06-133c-419b-a435-1fea919d6a44`: ad load, severity 2 versus 3. `4a806587-0dde-4fb4-b4f1-f5c7d197c927` and `bcdf315e-c82d-41f0-9fcd-ba5933dfe77e`: crashing/connection failure, severity 4 versus 3. Inspect whether a core task is clearly blocked or merely degraded; do not infer impact from star ratings or anger.
- All eight needs_review disagreements are Jev=true and verifier=false, including short praise and under-specified issues. Jev flags 265/500 overall (53%). Automatically escalating every flag would substantially increase costs and human work. Clarify flag meaning using development cases, evaluate it separately, and freeze decisions before evaluating the human golden set. No 53% paid escalation has been performed.
- Exact-substring checks validate quote/entity provenance, not semantic completeness. For the playlist-search case, deterministic extraction captures `playlist` but omits `search function`; inspect these omissions during human evaluation.

## Ranking and memo review

Saved membership produces identical `ranking.csv` and `claims.csv` on offline replay. Usability leads this sample at severity sum **158** from **64** complaint/cancellation records; playback follows at **147** from **44**. The gap is small enough that inspected label boundaries matter. These are development-sample results, not the final 100k recommendation.

The [raw memo](memo.md) correctly cites the saved figures, but incorrectly says classifications are “incomplete or potentially mixed.” All 500 are completed; independent human correctness evaluation is incomplete, and topic groups are broad. Preserve the raw response. [Editorial copy](memo-editorial.md) corrects this distinction and explicitly states the sample size; student review is still required. Numeric citation checks did not catch this nonnumeric semantic error, which is a useful documented limitation.

## Offline reproduction

```sh
python3 -m pipeline.checkpoint_report --run-dir runs/checkpoint-500 --out-dir runs/checkpoint-500-report-replay
python3 -m pipeline cost --calls cost/checkpoint-500/initial-415aa52bbae7499c993774b98324f613/calls.jsonl --measurement cost/checkpoint-500/initial-415aa52bbae7499c993774b98324f613/measurement.json --scenarios cost/scenarios-100k-500.json --out-dir runs/100k-cost-from-500
```

Both commands are offline. The 500-based 100k projection is approximately US$4.70 known API subtotal (base), US$6.16 (conservative), and US$5.89 (no classification reuse). The observed one-worker stage-time extrapolation is 34.04 / 45.46 / 42.51 hours, respectively. These exclude unmeasured extraction/local work and hosting. Provider latency was materially slower than in the 100 pilot; do not use the earlier time estimate as a promise. A bounded concurrency experiment and the 10k checkpoint are still needed before choosing final-scale runtime settings.
