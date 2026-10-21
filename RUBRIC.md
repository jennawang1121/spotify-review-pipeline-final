# Rubric-to-evidence tracker

Current finalization status, October 20, 2026. This is an evidence map, not an awarded or predicted grade. The complete source is ingested; the selected minimum scope has 100,000 valid classifications and 13 empty quarantines. Independent final verification and memo generation are still running.

| Criterion | Evidence | Remaining work / limitation |
|---|---|---|
| D1 Accessible setup/artifacts | Public GitHub repository, runnable standard-library Python, offline calculator, schema and UI source | Final artifacts/release and final link check |
| D2 Architecture/schema/provenance | Four separate roles/instructions; exact original IDs and hashes; validated final classifications | Final role handoffs and export/checker report |
| D3 Correct numerical evidence | All 100k baseline scores computed offline; production SQL agrees on every ranking; every deployed ID/hash/status matched | Final memo numeric/citation audit |
| D4 Recommendation/alternatives/limits | Historical development recommendations; final analysis is available | Final model recommendation and student argument review |
| T1 Human gold/per-field/error analysis | 50 student-supplied references, frozen-model predictions and per-field diagnostics; assistance is disclosed | Fully independent human provenance is not established for assisted severity/entity/quote fields. Do not describe diagnostic agreement as certified accuracy |
| T2 Independent/system checks | Blind seeded verification, real injection/control tests, planted-error detection, inspected final examples | Complete final 5,000 selected checks; report failed checks and valid comparisons separately |
| T3 Measured cost/recovery | Actual fixed cold/warm 100, editable-rate calculator, real resume recording, bounded retries/budget, saved timeout/conflict evidence | Final cost/runtime report; unknown provider usage remains unknown with reservations held |
| W1 Coverage | Full 660,622 ingestion; all selected 100,000 nonempty reviews valid; 13 empty quarantines | Final unmodified checker. The other 560,609 nonempty reviews are outside the selected scope |
| W2 Runnable staged program | Arbitrary-CSV runner, completed 100/500/10k, final classifications, 47 offline tests | Final downstream completion and measured zero-call warm replay |
| W3 Deployed product | Private read-only 100k Worker/D1 dashboard; all IDs/hashes/statuses and all rankings match local results | Replace pending verification/memo metadata, validate final view and enable authorized public access |

## Current evidence links

- [Complete classification/source audit](evidence/final-classification-audit/validation.json)
- [Final deterministic ranking](evidence/final-classification-audit/ranking.csv)
- [Deployed database integrity](evidence/dashboard-classification-private-checks.json)
- [Inspected final model/engineering failures](evals/final-inspected-failures.md)
- [Golden 50 diagnostics](evals/golden_50_assisted_evaluation.json)
- [Assistance provenance](evals/golden_50_assisted.provenance.json)
- [Real system checks](evals/system-checks/README.md)
- [Measured 100-review cold/warm](cost/report.md)
- [10k passing checker](evidence/checkpoint-10000/official-check-complete-lineage.json)
- [Actual terminal interruption/resume recording](evidence/recovery-10k/stop-resume.html)
- [Detailed current audit](docs/criteria-audit-2026-10-20.md)

Do not hide failures, replace unknown usage with zero, relabel assistant-edited reference fields as independently human, or describe the final assignment as complete while publication and downstream evidence remain unfinished.
