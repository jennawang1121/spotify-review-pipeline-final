# Assignment evidence audit — October 20, 2026

Status: finalization in progress. This is not a predicted grade. The current deadline is October 20, 2026 at 11:59 pm Pacific, per the student's update.

| Criterion | Current evidence | Still required |
|---|---|---|
| D1 Accessible code/setup | Public GitHub repository; prior clean-copy tests; 45 current offline tests | Final artifact sync and clean-copy rerun |
| D2 Architecture/schema/provenance | Four distinct model roles; source IDs/hashes; all 100,000 classifications validated | Final downstream handoffs and official export |
| D3 Correct calculations/citations | All final classifications rechecked against the original CSV; deterministic final ranking generated | Final memo citation audit and full checker |
| D4 Recommendation | Development memos and final issue ranking | Final model memo, argument review, alternatives and limitations |
| T1 Golden 50 | Student labels with disclosed assistant corrections; 50 actual predictions; per-field differences | Fully independent human provenance is not established for assisted fields; disclose this limitation |
| T2 Independent/system tests | Blind development verification; real injection/control tests; planted errors detected | Final seeded 5,000-row model verification is running; inspect disagreements |
| T3 Cost/recovery | Actual fixed cold/warm 100; offline calculator; real interruption/resume recording; bounded budget/retries | Final cost/runtime reconciliation; unknown-usage reservations remain explicit |
| W1 Coverage | All 660,622 source rows ingested; selected 100,000 nonempty classified; 13 empty quarantined | Final official checker; 560,609 nonempty rows are outside the selected scope |
| W2 Runnable stages | Arbitrary CSV runner; 100/500/10k completed; odd-tail queue bug repaired with regression test | Final verification/group/memo and zero-call warm replay |
| W3 Deployed product | Existing private 500-row Worker/D1 dashboard | Final database import, final metadata, removal of temporary importer, public access and live checks |

## Recovery

The final odd queue item was dispatched twice before the first result committed. Different real responses triggered the immutable-cache safeguard. The first saved classification and both billed responses are preserved. The queue now tracks admitted IDs. All 45 tests pass, including a three-row/two-worker regression test. No saved classification was overwritten. See [repair evidence](../evidence/final-cache-conflict-recovery.json).

## Spending and publication

The student explicitly approved a USD 7 total API cap. Historical experiments reserve USD 1; final processing has a cumulative USD 6 cap. Unknown costs retain reservations rather than being counted as zero. Hosting and local compute are excluded from API totals. Dashboard public access is authorized only after final data update and validation.

Sites archive uploads currently return a service HTTP 522. The final import source is pushed, but it has not been deployed; the existing private 500-row publication remains live. This does not affect local classification or verification.
