# One original review through the final pipeline

Original ID `470b836e-9027-4e6f-9673-c0aad1b03c0b` is a review describing repeated login errors. Its selected-source SHA-256 is `a61ba90a993f718abc613df3eeb335df14266266cf4bb6d079f2aa02c14b27e7`. The exact review and source fields are in the saved-run database; its classifier export is in `grading/records.jsonl` inside the [submission archive](https://github.com/jennawang1121/spotify-review-pipeline-final/releases/tag/final-100k).

| Stage | Saved result and link |
|---|---|
| Enrichment | Jev assigned `access`, `complaint`, severity `4`, sentiment `-0.91`, `needs_review=false`. The saved verbatim quote begins “Shows an error every time I try to log in.” The record carries its source hash and label configuration. |
| Independent verification | The seeded verifier, without first-pass labels, also assigned `access`, `complaint`, severity `4`, and `needs_review=false`; sentiment `-0.85`. Its saved request ID is `7f03c1ca216f49118236f92429b55d3c`. See [verification export](../evidence/final-100k/verification.jsonl). This agreement is between models, not proof of ground-truth accuracy. |
| Membership | Its complaint status placed the original ID once in `issue-access` in `grading/membership.csv`. |
| Ranking | That issue has 1,411 contributing complaint/cancellation records, severity sum and priority score 5,333, and ranks fifth. See [ranking](../evidence/final-100k/ranking-replay/ranking.csv) and `issue-access:priority_score` in the archive's `grading/claims.csv`. The single review's severity contributes 4 to that sum. |
| Recommendation | The [final memo](../evidence/final-100k/memo.editorial.md) cites this original ID as an access example and cites `issue-access:priority_score` for the issue-level comparison. The recommendation prioritizes usability; this trace shows how a considered alternative is grounded. |

A failure is also traceable: independent verification for `1118521e-67a6-4966-9148-cf73f5f555e4` returned a quote that changed source spelling `dere` to `there`. Both bounded attempts failed exact-quote validation, so its verifier outcome remains failed, is excluded from the 4,990 valid comparisons, and its first-pass classification is preserved. See [quality feedback](../evidence/final-100k/quality-feedback.md). No model output was silently corrected to raise agreement.
