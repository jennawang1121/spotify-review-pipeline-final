"""Offline checkpoint feedback and deterministic ranking replay."""
import argparse
from collections import Counter
from pathlib import Path

from .common import configuration, file_sha, read_json, read_jsonl, write_json
from .costing import load_rates, replay
from .ranking import rank
from .store import records


def summarize(run_dir, output):
    root, output = Path(run_dir), Path(output)
    config = read_json(root / "label_configuration.json")
    measurements = [read_json(path) for path in sorted((root / "cost").glob("*/measurement.json"))]
    if not measurements or not any(m["outcome"] == "completed" for m in measurements):
        raise ValueError("Complete the checkpoint before reporting its final results.")
    rows = list(records(root / "source.sqlite", config["label_config"]))
    if any(row["status"] == "pending" for row in rows):
        raise ValueError("Pending records remain; this is not a completed checkpoint.")
    predictions = [r["prediction"] for r in rows if r["status"] == "completed"]
    verified = list(read_jsonl(root / "verification.jsonl"))
    calls = list(read_jsonl(root / "cost/pilot_calls.jsonl"))
    from .common import ROOT
    aggregate_measurement = {"evidence_kind": "real_checkpoint" if all(m["evidence_kind"] == "real_pilot" for m in measurements) else "mixed_or_synthetic",
                             "input_records": len(rows), "completed_records": len(predictions),
                             "wall_seconds": sum(m["wall_seconds"] for m in measurements), "local_compute_usd": None}
    costs = replay(calls, load_rates(ROOT / "cost/rates.csv"), aggregate_measurement)
    ranking_dir = output / "ranking-replay"
    ranking = rank(root / "source.sqlite", config["label_config"], root / "membership.csv", ranking_dir)
    matches = {name: file_sha(ranking_dir / name) == file_sha(root / "analysis" / name)
               for name in ("ranking.csv", "claims.csv")}
    if not all(matches.values()):
        raise ValueError("Saved ranking or claims do not match deterministic replay.")
    result = {"status": "completed_final_scope" if len(predictions) >= 100000 else "completed_development_checkpoint", "new_api_calls_for_report": 0,
              "source_rows": len(rows), "completed": len(predictions),
              "quarantined": sum(r["status"] == "quarantined" for r in rows),
              "label_config": config["label_config"], "input_sha256": read_json(root / "run_manifest.json")["input_sha256"],
              "measurements": measurements, "costs_this_experiment": costs,
              "calls_by_stage": dict(Counter(c["stage"] for c in calls)),
              "outcomes": dict(Counter(c["outcome"] for c in calls)),
              "seed_provenance": read_json(root / "seed_provenance.json") if (root / "seed_provenance.json").exists() else None,
              "quality": {"meaning": "Independent model-to-model agreement, NOT human accuracy.",
                          "sample_size": len(verified), "sample_seed": config["verification_seed"],
                          "agreement_counts": {field: sum(v["first_prediction"][field] == v["independent_prediction"][field] for v in verified)
                                               for field in ("topic", "intent", "severity", "needs_review")},
                          "sentiment_mean_absolute_difference": sum(v["sentiment_absolute_difference"] for v in verified) / len(verified) if verified else None,
                          "sentiment_within_tolerance_count": sum(v["sentiment_absolute_difference"] <= config["sentiment_evaluation_tolerance"] for v in verified),
                          "sentiment_tolerance": config["sentiment_evaluation_tolerance"],
                          "needs_review_count": sum(p["needs_review"] for p in predictions),
                          "intent_counts": dict(Counter(p["intent"] for p in predictions)),
                          "categorical_disagreement_ids": [v["review_id"] for v in verified if v["disagreements"]]},
              "ranking_replay_matches": matches, "ranking": ranking["ranking"],
              "limitations": ["Partial-cache checkpoint; do not call this a cold measurement.",
                              "Reused pilot classification costs are historical, excluded from incremental checkpoint spend.",
                              "Human golden evaluation and recorded recovery remain separate required evidence.",
                              ("Final scope is a selected 100k subset, not all 660609 nonempty source reviews." if len(predictions) >= 100000 else "Sample ranking is not the final 100k recommendation.")]}
    write_json(output / "summary.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    summary = summarize(args.run_dir, args.out_dir)
    print({"completed": summary["completed"], "api_usd": summary["costs_this_experiment"]["total_api_usd"],
           "ranking_replay_matches": summary["ranking_replay_matches"], "saved_to": args.out_dir})


if __name__ == "__main__":
    main()
