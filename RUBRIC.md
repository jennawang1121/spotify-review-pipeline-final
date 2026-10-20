# Rubric-to-evidence tracker

Implementation status, not awarded points. Formal cold/warm complete: 107 successful cold calls across all four roles, zero warm calls. Development failures remain separately logged; six have unresolved usage. See [measured report](cost/report.md). These ten criteria require actual execution and review before claiming completion.

| Criterion | Current evidence | Remaining evidence |
|---|---|---|
| D1 Accessible code/setup/artifacts | Local Python CLI and documented commands | Public repo/release; clean setup and signed-out link check |
| D2 Architecture/schema/provenance | Four implemented roles, official row hash, export adapter; mock checker test passes | Pilot handoffs recorded; final full-corpus trace and checker still needed |
| D3 Numerical evidence | Deterministic membership/ranking/claims tested | Real full-run values and memo claims reproduced offline |
| D4 Recommendation/alternatives/limits | Structured memo generation and citation validation implemented | Real recommendation, alternatives, limitations and human argument review |
| T1 Human gold/evaluation | All50 reference rows complete; frozen-model predictions and actual diagnostic metrics saved in evals/golden_50_assisted_evaluation.json | Disclose AI-assisted severity/entity corrections and quote extraction; fully independent human annotation requirement is not established for assisted fields. Human review of disagreements remains. |
| T2 Independent/system checks | Blind seeded verifier implemented; synthetic validation tests | Five pilot plus 25 checkpoint blind predictions saved; development error analysis in evidence/checkpoint-500; eight real control/injection calls and planted-error detection saved; 50-case diagnostic evaluation now saved with explicit mixed human/AI reference provenance |
| T3 Measured cost/recovery | Offline arithmetic, real transport logging, budget/retry/resume implemented; mock tests | Actual cold/warm and real terminal stop/resume recording saved (`evidence/recovery-10k`); complete scale projections, reconcile unknown usage; screen video if separately required |
| W1 Coverage | All 660,622 source rows ingested and profiled; 13 empty; hashes match | Revised target: valid classifications for at least 100,000 nonempty rows; retain 13 empty quarantines and disclose selected scope, failures and old coverage-formula discrepancy |
| W2 Runnable staged pipeline | Real fixed-100 run; arbitrary-CSV checkpoint runner tested across multiple pages, seeded reuse and empty quarantine | Pilot validated against both providers; 500 completed with zero-call warm replay; 10k/100k executions remain |
| W3 Reproducible output + deployed product | Saved-membership replay and mock official ranking check | 500-scope Worker/D1/dashboard deployed; live counts and all eight rankings verified. Remaining: public grader access and final 100k data/recommendation update |

## Feedback at each checkpoint

Record quality metrics and representative mistakes; distinguish label errors from quote/entity omissions. Inspect verifier disagreements rather than averaging them away. Report all completed/pending/quarantined counts, every attempted call, unknown charges, cost per completed record and input row, and warm replay's incremental calls. Link the evidence for each criterion, then choose the smallest change that fixes a demonstrated problem.

Do not tune prompts on golden answer labels. Freeze development decisions separately and evaluate the held-out human labels honestly. A synthetic checker pass validates output shape only; no real classification, grading result or provider bill is certified by it.
