"""Compare student-completed golden labels to saved predictions; no model calls."""
import csv
import json
from collections import Counter, defaultdict

from .common import read_jsonl
from .store import validate_prediction


def evaluate(golden_path, prediction_path, config):
    with open(golden_path, encoding="utf-8-sig", newline="") as handle:
        golden = list(csv.DictReader(handle, strict=True))
    if len(golden) != 50 or len({r["review_id"] for r in golden}) != 50:
        raise ValueError("Expected all 50 unique original golden IDs.")
    expected = {}
    for row in golden:
        for field in ("topic", "intent", "severity", "sentiment", "entities", "evidence_quote", "needs_review"):
            if not row.get(field, "").strip():
                raise ValueError("Golden labels are incomplete; the student must label every field before evaluation.")
        if row["needs_review"].strip().lower() not in ("true", "false"):
            raise ValueError("Golden needs_review must be true or false.")
        prediction = {"topic": row["topic"].strip(), "intent": row["intent"].strip(),
                      "severity": int(row["severity"]), "sentiment": float(row["sentiment"]),
                      "entities": json.loads(row["entities"]), "evidence_quote": row["evidence_quote"],
                      "needs_review": row["needs_review"].strip().lower() == "true"}
        validate_prediction(prediction, row["review_text"], config["taxonomy"])
        expected[row["review_id"]] = (prediction, row["review_text"])
    observed = {}
    for row in read_jsonl(prediction_path):
        rid = row["review_id"]
        if rid not in expected:
            continue
        if rid in observed:
            raise ValueError("Duplicate golden prediction ID.")
        observed[rid] = row
    counts, confusion = Counter(), defaultdict(Counter)
    errors, cases = {"severity": [], "sentiment": []}, []
    for rid, (gold, text) in expected.items():
        record = observed.get(rid, {})
        prediction = record.get("prediction") if "prediction" in record else {k: record.get(k) for k in gold}
        valid = record.get("status") == "completed"
        if valid:
            try:
                validate_prediction(prediction, text, config["taxonomy"])
            except (ValueError, TypeError):
                valid = False
        counts["valid_predictions"] += int(valid)
        detail = {"review_id": rid, "valid_prediction": valid, "expected": gold,
                  "predicted": prediction if valid else None}
        for field in ("topic", "intent", "severity", "needs_review", "entities"):
            actual = prediction[field] if valid else None
            matches = valid and (set(actual) == set(gold[field]) if field == "entities" else actual == gold[field])
            counts[field + "_correct"] += int(matches)
            detail[field + "_correct"] = matches
            if field in ("topic", "intent"):
                confusion[field][str(gold[field]) + " -> " + str(actual if valid else "<missing/invalid>")] += 1
        if valid:
            errors["severity"].append(abs(prediction["severity"] - gold["severity"]))
            difference = abs(prediction["sentiment"] - gold["sentiment"])
            errors["sentiment"].append(difference)
            counts["sentiment_within_tolerance"] += int(difference <= config["sentiment_evaluation_tolerance"])
            detail["evidence_substring_valid"] = True
            detail["quote_support"] = "Requires human inspection; substring membership does not establish support."
        counts["gold_needs_review"] += int(gold["needs_review"])
        counts["predicted_needs_review"] += int(valid and prediction["needs_review"])
        counts["needs_review_true_positive"] += int(valid and gold["needs_review"] and prediction["needs_review"])
        cases.append(detail)
    return {"evaluation_scope": "student-labelled golden 50; not instructor benchmark", "total_cases": 50,
            "valid_predictions": counts["valid_predictions"], "missing_or_invalid_predictions": 50 - counts["valid_predictions"],
            "agreement": {field: counts[field + "_correct"] / 50 for field in ("topic", "intent", "severity", "needs_review", "entities")},
            "mae_on_valid_predictions": {field: sum(values) / len(values) if values else None for field, values in errors.items()},
            "mae_denominator": counts["valid_predictions"],
            "sentiment_tolerance": config["sentiment_evaluation_tolerance"],
            "sentiment_within_tolerance_fraction": counts["sentiment_within_tolerance"] / 50,
            "gold_needs_review_count": counts["gold_needs_review"],
            "needs_review_precision": counts["needs_review_true_positive"] / counts["predicted_needs_review"] if counts["predicted_needs_review"] else None,
            "needs_review_recall": counts["needs_review_true_positive"] / counts["gold_needs_review"] if counts["gold_needs_review"] else None,
            "topic_counts": dict(Counter(value[0]["topic"] for value in expected.values())),
            "confusion": {field: dict(values) for field, values in confusion.items()}, "cases": cases,
            "limitations": ["50 cases are diagnostic, not a precise population estimate.",
                            "Missing predictions count as incorrect in agreement; MAE covers valid predictions only.",
                            "Inspect entity omissions/additions and semantic quote support manually."]}
