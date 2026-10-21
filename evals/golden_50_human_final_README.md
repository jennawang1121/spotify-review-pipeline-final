# Final student-supplied Golden 50

The student supplied [the completed v4 Excel workbook](golden_50_human_final.xlsx). The existing workbook validator confirms all 50 original IDs and review texts are unchanged, all seven label fields are present, and each evidence quote is an exact source substring. The exported [label table](golden_50_human_final.csv) is the current reference; [per-case evaluation](golden_50_human_final_evaluation.json) compares it with predictions that were already saved. This reevaluation made **zero** new model calls.

| Field | Final agreement |
|---|---:|
| Topic | 66% (33/50) |
| Intent | 86% (43/50) |
| Severity, exact | 88% (44/50) |
| Needs review | 68% (34/50) |
| Entities | 62% (31/50) |

Severity mean absolute error is **0.16**; sentiment mean absolute error is **0.1797**. These are diagnostic comparisons, not instructor-validated population accuracy. The JSON evaluation includes per-topic counts, confusion pairs, and every concrete disagreement. For inspected final-system examples and independent-check failures, see [final feedback](../evidence/final-100k/quality-feedback.md).

This v4 workbook arrived after the earlier assisted-reference evaluation. The earlier [labels](golden_50_assisted.csv), [scores](golden_50_assisted_evaluation.json), and [preparation history](golden_50_assisted.provenance.json) remain available. The v4 file changes two topic decisions, four intent decisions, twelve severity decisions, three sentiment values, forty needs-review flags, four entity lists, and nine quotes relative to that earlier reference. The saved model predictions and prompts were not changed for this reevaluation. Because the earlier evaluation existed before v4, v4 is **not claimed as a fresh blind holdout**; whether earlier feedback influenced the student's revisions is unknown. The [provenance record](golden_50_human_final.provenance.json) has the file hash and validation command.
