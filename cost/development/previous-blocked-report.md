# Pilot progress — incomplete live experiment

Observed 2026-10-06. This is real execution evidence, not a complete cold/warm benchmark.

| Item | Observed result |
|---|---:|
| Original fixed cost_100 input IDs | 100 |
| Completed Jev enrichments | 100 |
| Jev attempts | 102 (100 succeeded; two parser-validation failures) |
| OpenAI verification attempts | 6 failed with HTTP 429 |
| OpenAI error identifiers captured on latest three attempts | credit_balance_exhausted / insufficient_quota |
| Successful verify / group / memo calls | 0 / 0 / 0 |
| Known API subtotal, USD | 0.005567226 |
| Attempts with unknown usage/charges | 6 |
| Complete API total | UNKNOWN |
| Local compute cost | UNKNOWN |
| Experiment budget, USD | 1.00 |
| Workers / maximum OpenAI output tokens | 1 / 1200 |
| Strong-model fallback fraction | 0 |
| Warm benchmark | Not run |

The first run saved 42 results before stopping on rounded Jev probabilities. Two-decimal values summing to 0.99 were incorrectly rejected. A bounded rounding tolerance was added and regression-tested; raw values and paid failed attempts were preserved. Resume classified the remaining 58 without re-enriching the saved 42, then reached the OpenAI credit block. A diagnostic resume reused all 100 results and captured the credit error. The quota detector now stops on this code/type without pointless retries; this fix is tested offline, with no further live retry after identifying the block.

All six failed OpenAI requests lack usage and retain budget reservations. This conservative accounting is not evidence they were charged. Reconcile with the provider dashboard. The known Jev subtotal uses actual usage and the dated rates.csv; it is not a provider invoice.

Source evidence: pilot_records.jsonl, pilot_calls.jsonl, and per-invocation files under measurements/. See ../evidence/live-parser-incident.json and ../evidence/pilot-progress.json. Requests/raw responses and checkpoints remain in local runs/pilot-live/. No credentials are logged.

No end-to-end accuracy, verified memo, full pilot throughput or full-run cost is claimed. Phase measurements include interruptions/failures. After API credit is restored, resume this experiment; then measure an uninterrupted fresh cold/warm benchmark within a separately allocated portion of the existing total budget. Include all earlier development charges in the project spend report.

Offline replay for any invocation (replace RUN_ID with a directory under measurements):

```sh
python3 -m pipeline cost --calls cost/measurements/RUN_ID/calls.jsonl --measurement cost/measurements/RUN_ID/measurement.json --out-dir runs/cost-replay
```

Still required: independent verification, group/memo execution, human golden evaluation, complete cold/warm evidence, base/conservative/no-reuse estimates including stage-specific wall time, and the 500/10k/full gates. Do not scale while the pilot is incomplete.
