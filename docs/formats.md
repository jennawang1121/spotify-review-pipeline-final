# Saved data and grading format

The unmodified instructor contract is `course/GRADING_CONTRACT.md`; the adapter calls the instructor's `row_sha` implementation. Official source_sha256 hashes compact UTF-8 JSON of a list of the six original source strings, in order: review_id, review_text, review_rating, review_likes, app_version, review_timestamp. No trimming or Unicode normalization. Extra label fields are excluded.

Internal_source_sha256 additionally binds the full original CSV row dictionary for internal imports. It is distinct from the official hash. `prepare` writes an envelope with ID, internal hash and label_config; only review_text enters Jev state. Five questions request topic/intent/severity/sentiment/needs_review. Stars, first predictions and human answers are absent.

`import-results` accepts review_id, internal_source_sha256, label_config, provenance (kind/reference), and prediction containing topic, intent, severity, sentiment, entities, evidence_quote, needs_review. It validates complete labels and literal quote/entity membership before transactional caching. Validation alone does not authenticate a provider bill; the live runner separately saves requests, responses and usage. Synthetic fixtures carry synthetic_test provenance and cannot be exported as actual grading evidence.

Internal `export` keeps source fields, nested prediction, pending/quarantined/completed statuses and provenance. Official `export-grading` emits flat contract records and refuses pending or synthetic results, missing roles and invalid recovery checkpoints. Run the instructor checker afterward; export success alone is not a grading pass.

```sh
python3 -m pipeline export-grading --db path/to/source.sqlite --full-csv data/course/spotify_reviews_18months.csv --calls path/to/calls.jsonl --before path/to/checkpoint_before.json --after path/to/checkpoint_after.json --out grading
```

Completed official records include original ID/hash, seven common label fields, label_config and optional direct cache_source_id. Empty rows are quarantined with reason empty_review_text. Direct cache sources retain their actual enrich call and identical text/labels/config; IDs are never collapsed for business counts.

Grouping policy topic-v1 assigns completed complaint/cancellation records to issue-<topic>. A separate small model call names these issues, without changing membership. Ranking columns: rank, issue_id, complaint_count, severity_sum, mean_severity, priority_score. Score equals integer severity_sum; ties use issue_id ascending; mean is six-place HALF_UP. Claims expose only the four contract-approved numerical metrics.

Calls use official roles enrich/verify/group/memo and unique attempt IDs. Provider billing/timing/settings are extra evidence. Warm attempts use contract phase resume and are distinguished by invocation run IDs and measurement phase warm. Per-invocation costs remain separate.

Memo input contains saved claims and at most three examples per issue. Numeric placeholders are replaced with saved values and citations; source IDs are validated. Human review is still required for semantic support, alternatives and limitations.
