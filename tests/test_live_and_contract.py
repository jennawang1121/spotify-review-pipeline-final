"""Transport is mocked. No paid API calls or real classification evidence."""
import copy
import csv
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from pipeline.common import ROOT, SOURCE_FIELDS, configuration, read_json, read_jsonl
from pipeline.contract import audit, export_records, row_sha
from pipeline.evaluation import evaluate
from pipeline.providers import Transport, billing_tokens, response_json
from pipeline.runner import run_pilot, run_checkpoint, validate_memo_result
from pipeline.store import records, status, ingest, import_predictions


def mock_provider(provider, request):
    if provider == "typesafe":
        values = {"topic": "access", "intent": "complaint", "severity": "2", "needs_review": "no"}
        answers = {}
        for key, question in request["questions"].items():
            if key == "sentiment":
                answers[key] = {"type": "score", "score": 1, "confidence": 1,
                                "probabilities": {str(i): int(i == 1) for i in range(5)}}
            else:
                value = values[key]
                answers[key] = {"type": "choice", "choice": value, "confidence": 1,
                                "probabilities": {option: int(option == value) for option in question["criteria"]}}
        return {"model": request["model"], "answers": answers, "usage": {"input_tokens": 100, "output_tokens": 50}}, "synthetic-provider-id"
    data = json.loads(request["input"])
    properties = request["text"]["format"]["schema"]["properties"]
    if "topic" in properties:
        result = {"topic": "access", "intent": "complaint", "severity": 2, "sentiment": -0.5,
                  "entities": [], "evidence_quote": data["review_text"], "needs_review": False}
    elif "issues" in properties:
        result = {"issues": [{"issue_id": row["issue_id"], "name": "Synthetic test issue"} for row in data["ranking"]]}
    else:
        claim = data["evidence"]["claims"][0]["claim_id"]
        result = {"priority_issue_id": data["evidence"]["ranking"][0]["issue_id"],
                  "recommendation": "Synthetic fixture: {{claim:" + claim + "}}.",
                  "alternatives": "Synthetic alternatives.", "limitations": "Synthetic data; no business recommendation.",
                  "claim_ids": [claim], "review_ids": [data["evidence"]["evidence"][0]["examples"][0]["review_id"]]}
    return {"model": request["model"], "status": "completed", "usage": {"input_tokens": 100, "output_tokens": 50,
        "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0}},
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(result)}]}]}, "synthetic-provider-id"


class LiveAndContractTests(unittest.TestCase):
    def test_checkpoint_pages_seed_reuse_empty_quarantine_and_warm(self):
        config = configuration()
        calls = []
        def factory(*args):
            def send(provider, request):
                calls.append(provider)
                return mock_provider(provider, request)
            return Transport(*args, send=send)
        with tempfile.TemporaryDirectory() as temporary, patch("pipeline.providers.time.sleep"):
            root = Path(temporary)
            source = root / "invented.csv"
            run = root / "run"
            with source.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=SOURCE_FIELDS)
                writer.writeheader()
                for index in range(207):
                    text = "Invented access problem " + str(index)
                    if index == 205:
                        text = "Invented access problem 0"
                    if index == 206:
                        text = "  "
                    writer.writerow(dict(zip(SOURCE_FIELDS, ["fixture-" + str(index), text, "1", "0", "", "2023-01-01"])))
            with patch("pipeline.providers.urllib.request.urlopen", side_effect=AssertionError("Network forbidden")):
                plan = run_checkpoint(source, config, run, "initial", None)
            self.assertEqual(plan["input_records"], 207)
            self.assertEqual(plan["verification_sample_size"], 11)
            self.assertFalse(run.exists())
            ingest(source, run / "source.sqlite")
            seed = next(records(run / "source.sqlite", config["label_config"]))
            seed["prediction"] = {"topic": "access", "intent": "complaint", "severity": 2,
                                  "sentiment": -0.5, "entities": [], "evidence_quote": seed["source"]["review_text"], "needs_review": False}
            seed["provenance"] = {"kind": "synthetic_test", "reference": "invented seed fixture"}
            import_predictions(run / "source.sqlite", config, [seed])
            result = run_checkpoint(source, config, run, "initial", "1", True, None, factory, {})
            self.assertEqual(result["new_unique_results"], 204)
            self.assertEqual(calls.count("typesafe"), 204)
            self.assertEqual(calls.count("openai"), 13)
            measurement = read_json(next((run / "cost").glob("initial-*/measurement.json")))
            self.assertEqual(measurement["input_records"], 207)
            self.assertEqual(measurement["completed_records"], 206)
            self.assertEqual(measurement["quarantined_records"], 1)
            self.assertEqual(measurement["result_cache_hits"], 2)
            self.assertTrue(all(r["review_id"] != "fixture-206" for r in read_jsonl(run / "verification.jsonl")))
            run_checkpoint(source, config, run, "warm", "1", True, None, factory, {})
            self.assertEqual(len(calls), 217)
            with self.assertRaisesRegex(ValueError, "experiment exists"):
                run_checkpoint(source, config, run, "initial", "1", True, None, factory, {})

    def test_memo_source_id_digits_are_citations_but_literal_metrics_fail(self):
        rid = "a78d831a-69f4-428a-9235-cfdd9775c509"
        result = {"priority_issue_id": "issue-test", "recommendation": "Count {{claim:count}}, source " + rid,
                  "alternatives": "Other options.", "limitations": "Sample only.",
                  "claim_ids": ["count", "unused"], "review_ids": [rid]}
        valid = validate_memo_result(result, {"count": {}, "unused": {}}, {rid}, ["issue-test"])
        self.assertEqual(valid["claim_ids"], ["count"])
        self.assertEqual(result["claim_ids"], ["count", "unused"])
        for bad in (" 20 complaints", " 00000000-0000-0000-0000-000000000000"):
            changed = dict(result, recommendation=result["recommendation"] + bad)
            with self.assertRaisesRegex(ValueError, "Uncontrolled numerical"):
                validate_memo_result(changed, {"count": {}, "unused": {}}, {rid}, ["issue-test"])

    def test_insufficient_quota_stops_without_pointless_retries(self):
        def denied(provider, request):
            body = io.BytesIO(b'{"error":{"code":"credit_balance_exhausted","type":"insufficient_quota","message":"do not save this"}}')
            raise urllib.error.HTTPError("https://api.openai.com/v1/responses", 429, "quota", {}, body)
        with tempfile.TemporaryDirectory() as temporary, patch("pipeline.providers.time.sleep"):
            from pipeline.providers import openai_request, schema_object
            config = configuration()
            transport = Transport(temporary, config, "1", "initial", "synthetic-quota", {}, send=denied)
            try:
                with self.assertRaisesRegex(ValueError, "bounded attempts"):
                    transport.call("openai", "verify", "verification", openai_request(config, "Test", {}, schema_object({})), [], response_json)
                paths = list((Path(temporary) / "attempts").glob("*.json"))
                self.assertEqual(len(paths), 1)
                event = read_json(paths[0])
                self.assertEqual(event["provider_error_code"], "credit_balance_exhausted")
                self.assertNotIn("do not save this", paths[0].read_text())
                self.assertIsNone(event["calculated_usd"])
            finally:
                transport.close()

    def test_jev_rounded_probabilities_do_not_trigger_paid_retries(self):
        from pipeline.jev import build_request, parse_labels
        config = configuration()
        response, _ = mock_provider("typesafe", build_request("Invented example", config))
        response["answers"]["sentiment"]["probabilities"] = {"0": 0.93, "1": 0.02, "2": 0.04, "3": 0, "4": 0}
        self.assertEqual(parse_labels(response, config)["labels"]["sentiment"], -0.5)
        response["answers"]["sentiment"]["probabilities"]["0"] = 0.70
        with self.assertRaisesRegex(ValueError, "probability distribution"):
            parse_labels(response, config)

    def test_course_hash_uses_six_fields_only_and_no_normalization(self):
        row = dict(zip(SOURCE_FIELDS, ["id", "é\n text ", "1", "0", "", "2023-01-01"]))
        digest = row_sha(row)
        row["human_topic"] = "secret answer"
        self.assertEqual(row_sha(row), digest)
        row["review_text"] = row["review_text"].strip()
        self.assertNotEqual(row_sha(row), digest)

    def test_usage_partitions_input_and_keeps_unknown_categories_visible(self):
        usage = {"input_tokens": 1000, "output_tokens": 500,
                 "input_tokens_details": {"cached_tokens": 200, "cache_write_tokens": 300},
                 "output_tokens_details": {"reasoning_tokens": 250}}
        self.assertEqual(billing_tokens("openai", usage), {"input": 500, "cached_input": 200, "cache_write": 300, "output": 500})
        del usage["input_tokens_details"]["cache_write_tokens"]
        self.assertIsNone(billing_tokens("openai", usage))
        self.assertIsNone(billing_tokens("typesafe", None))

    def test_preflight_needs_no_credentials_and_dispatches_nothing(self):
        with patch("pipeline.providers.urllib.request.urlopen", side_effect=AssertionError("Network forbidden")):
            result = run_pilot(ROOT / "data/course/cost_100.csv", configuration(), ROOT / "runs/not-created-by-preflight", "initial", None)
        self.assertEqual(result["paid_calls"], 0)
        self.assertFalse((ROOT / "runs/not-created-by-preflight").exists())

    def test_blank_golden_cannot_be_presented_as_an_evaluation(self):
        with self.assertRaisesRegex(ValueError, "student must label"):
            evaluate(ROOT / "data/course/golden_50_to_label.csv", "/does/not/exist", configuration())

    def test_missing_predictions_are_errors_and_mae_is_unknown(self):
        # Invented text and labels only; no student golden answers supplied.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fields = ["review_id", "review_text", "topic", "intent", "severity", "sentiment",
                      "entities", "evidence_quote", "needs_review"]
            with (root / "synthetic-gold.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for index in range(50):
                    writer.writerow(dict(zip(fields, [str(index), "Invented example", "other", "unclear",
                                                       1, 0, "[]", "Invented example", "true"])))
            (root / "empty-predictions.jsonl").write_text("")
            result = evaluate(root / "synthetic-gold.csv", root / "empty-predictions.jsonl", configuration())
            self.assertEqual(result["missing_or_invalid_predictions"], 50)
            self.assertTrue(all(value == 0 for value in result["agreement"].values()))
            self.assertEqual(result["mae_on_valid_predictions"], {"severity": None, "sentiment": None})
            self.assertEqual(result["mae_denominator"], 0)

    def test_full_mocked_pilot_resume_warm_and_course_ranking(self):
        # Actual development texts are used only to exercise plumbing with fake responses.
        # The temporary results are explicitly synthetic and deleted after this test.
        count = []
        def factory(*args):
            def send(provider, request):
                count.append(provider)
                return mock_provider(provider, request)
            return Transport(*args, send=send)
        config = configuration()
        with tempfile.TemporaryDirectory() as temporary, patch("pipeline.providers.time.sleep"):
            root = Path(temporary)
            source = ROOT / "data/course/cost_100.csv"
            result = run_pilot(source, config, root, "initial", "1", True, 10, factory, {})
            self.assertEqual(result["status"], "stopped_after_saved_progress")
            self.assertEqual(len(count), 10)
            result = run_pilot(source, config, root, "resume", "1", True, None, factory, {})
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(count), 107)  # 100 enrich, 5 verify, group, memo.
            events = list(read_jsonl(root / "cost/pilot_calls.jsonl"))
            self.assertEqual({e["role"] for e in events}, {"enrich", "verify", "group", "memo"})
            self.assertTrue(all(e["evidence_kind"] == "synthetic_test" for e in events))
            before = set(read_json(root / "checkpoint_before.json")["completed_ids"])
            after = set(read_json(root / "checkpoint_after.json")["completed_ids"])
            self.assertTrue(before < after)
            self.assertTrue(all(not (set(e["review_ids"]) & before) for e in events if e["role"] == "enrich" and e["phase"] == "resume"))
            warm = run_pilot(source, config, root, "warm", "1", True, None, factory, {})
            self.assertEqual(warm["new_unique_results"], 0)
            self.assertEqual(len(count), 107)
            reports = [read_json(p) for p in (root / "cost").glob("warm-*/report.json")]
            self.assertEqual(reports[0]["total_api_usd"], "0")
            self.assertEqual(reports[0]["measurement"]["completed_records"], 100)
            self.assertEqual(len(list(read_jsonl(root / "cost/pilot_records.jsonl"))), 100)
            with self.assertRaisesRegex(ValueError, "Synthetic"):
                list(export_records(root / "source.sqlite", config["label_config"]))
            # Exercise the unmodified instructor checker on this isolated synthetic fixture.
            ref = audit.reference(source, source)
            folder = root / "synthetic-grading"
            folder.mkdir()
            from pipeline.common import write_json, write_jsonl
            import shutil
            write_json(folder / "run.json", {"version": audit.VERSION, "analysis_count": 100,
                       "analysis_sha256": ref["analysis_sha256"], "classification_input_fields": ["review_text"], "allow_multi_issue": False})
            write_json(folder / "ingestion.json", ref["ingestion"])
            shutil.copyfile(root / "cost/pilot_records.jsonl", folder / "records.jsonl")
            shutil.copyfile(root / "cost/pilot_calls.jsonl", folder / "calls.jsonl")
            for name in ("membership.csv", "checkpoint_before.json", "checkpoint_after.json"):
                shutil.copyfile(root / name, folder / name)
            for name in ("ranking.csv", "claims.csv"):
                shutil.copyfile(root / "analysis" / name, folder / name)
            check = audit.audit(folder, ref)
            self.assertEqual(check["status"], "pass", check["issue_counts"])
            # Passing here verifies adapter shape only, NOT real model execution.

    def test_invalid_response_retries_once_and_retains_all_usage(self):
        config = configuration()
        with tempfile.TemporaryDirectory() as temporary, patch("pipeline.providers.time.sleep"):
            transport = Transport(temporary, config, "1", "initial", "synthetic-retry", {}, send=mock_provider)
            from pipeline.jev import build_request
            try:
                with self.assertRaisesRegex(ValueError, "bounded attempts"):
                    transport.call("typesafe", "enrich", "classification", build_request("Test", config), ["test-id"],
                                   lambda result: (_ for _ in ()).throw(ValueError("Planted malformed output")))
                attempts = list((Path(temporary) / "attempts").glob("*.json"))
                self.assertEqual(len(attempts), 2)
                self.assertTrue(all(read_json(p)["calculated_usd"] is not None for p in attempts))
            finally:
                transport.close()

    def test_transient_failure_retries_bounded_and_reserves_unknown_charge(self):
        config = configuration()
        counter = []
        def fail(provider, request):
            counter.append(1)
            raise urllib.error.URLError("Synthetic timeout")
        with tempfile.TemporaryDirectory() as temporary, patch("pipeline.providers.time.sleep"):
            transport = Transport(temporary, config, "1", "initial", "synthetic-timeout", {}, send=fail)
            from pipeline.jev import build_request, parse_labels
            try:
                with self.assertRaises(ValueError):
                    transport.call("typesafe", "enrich", "classification", build_request("Test", config), ["test-id"], lambda x: parse_labels(x, config))
                self.assertEqual(len(counter), 3)
                self.assertEqual(transport.ledger.snapshot()["unresolved_attempts"], 3)
            finally:
                transport.close()

    def test_budget_rejection_happens_before_network_dispatch(self):
        config = configuration()
        with tempfile.TemporaryDirectory() as temporary:
            transport = Transport(temporary, config, "0", "initial", "synthetic-budget", {}, send=lambda *args: self.fail("Dispatched without budget"))
            from pipeline.jev import build_request
            try:
                with self.assertRaisesRegex(ValueError, "Budget cap"):
                    transport.call("typesafe", "enrich", "classification", build_request("Test", config), ["test-id"], lambda x: x)
            finally:
                transport.close()


if __name__ == "__main__":
    unittest.main()
