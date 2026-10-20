# Cost calculator and explicit pilot

Real cold/warm benchmark completed: cold 107 calls, 76.03 seconds, US$0.007073404; warm zero calls and zero incremental API cost. See [report.md](report.md) for saved measurements, development failures, quality findings and explicitly incomplete full-run forecasts. All prices are editable in rates.csv. Six earlier quota failures still lack usage; project spend has a known subtotal and an unknown remainder.

## Offline replay (default; no key or network)

From the project root, point to one saved invocation's files:

```sh
python3 -m pipeline cost --calls runs/pilot-live/cost/INITIAL_RUN_ID/calls.jsonl --measurement runs/pilot-live/cost/INITIAL_RUN_ID/measurement.json --out-dir runs/cost-replay
```

Replace `INITIAL_RUN_ID` with the actual generated `initial-...` directory. Warm has its own directory. Never combine cold+warm attempts with a measurement covering only one invocation. Interrupted/resumed phases are separate measurements and cannot stand in for uninterrupted cold wall-time.

Each attempt has a unique request/call ID, role, provider/model, settings, phase/run ID, outcome, duration, raw usage and mutually exclusive billing tokens. Ordinary input excludes cached reads and cache writes. Output already includes billable reasoning; do not add reasoning a second time. Cost is billed units times dated USD-per-million rate divided by one million. Failed attempts are included. Missing usage/rates means UNKNOWN, not zero. Local compute cost is reported separately as unknown until measured.

## Paid execution

Fill local `.env` with the two provider keys. These commands explicitly allow paid calls; choose a budget before executing:

```sh
python3 -m pipeline pilot
python3 -m pipeline pilot --run-dir runs/pilot-live --phase initial --execute-paid --budget-usd 1.00
python3 -m pipeline pilot --run-dir runs/pilot-live --phase warm --execute-paid --budget-usd 1.00
```

The first command is preflight only. Later commands use the original cost_100 checksum, one worker, five verifier cases, and all four required roles. A fresh cold directory has no results or attempts. Budget reservations are persistent and shared across phases in that directory; unknown outcomes keep their reservations. This local cap is based on estimates, not a guarantee about delayed provider billing.

Artifacts: experiment `cost/pilot_records.jsonl` (100 statuses), `cost/pilot_calls.jsonl` (all invocations), plus per-invocation measurement/calls/report JSON. Saved request and response files enable usage inspection. Copy selected genuine evidence into the submission's `cost/` with a combined report after review; root cost/ now contains the completed benchmark evidence; development/ retains all earlier failed and recovery attempts.

## Projections and incomplete evidence

Optional `--scenarios scenarios.json` accepts an array of scenarios with name, source_rows, budget_usd, stages. Every stage specifies pilot_units, projected_units, and attempts_multiplier relative to observed attempt overhead. Use distinct nonempty texts for classification, routed cases for extraction, selected cases for verification, and one unit each for group/memo. Missing measured stages remain unknown.

Final report must include base, conservative and no-reuse cases: 660,622 original rows, 660,609 nonempty, 484,189 distinct nonempty. Do not call the 26.71% reduction in classifications a measured token/cost saving. The fixed pilot contains no >600-character texts, so long-text extraction requires separate development measurements. Full-source profiling found seven distinct texts routed by this threshold; see ../evidence/extraction-routing-profile.json. Strong-model fallback is disabled in the current pilot.

Current projection time is a one-worker sum of API durations, excluding local overhead/queueing. It is not yet the required full wall-time estimate. report.md also extrapolates actual stage wall times, including throttling, and shows budget warnings; full-corpus local work and long extraction still need measurements. Refresh at 500/10k. T3 remains incomplete until real cold/warm plus recovery evidence and the complete report exist.
