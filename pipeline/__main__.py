import argparse
import json
import random
import sys
from pathlib import Path

from .common import ROOT, atomic_text, configuration, read_json, read_jsonl, write_json, write_jsonl
from .costing import load_rates, project, replay
from .jev import build_request
from .ranking import group, rank
from .store import connect, import_predictions, ingest, pending, records, status


def main(argv=None):
    parser = argparse.ArgumentParser(description="Spotify pipeline: offline by default; pilot --execute-paid explicitly enables API calls.")
    parser.add_argument("--config", default=str(ROOT / "config.json"))
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("doctor", help="Show prerequisites and implementation status (default).")
    p = sub.add_parser("ingest", help="Read and profile an arbitrary source CSV without model calls.")
    p.add_argument("input_csv")
    p.add_argument("--db", required=True)
    p.add_argument("--report", required=True)
    for name in ("status", "prepare", "import-results", "export", "group", "rank", "verification-sample"):
        p = sub.add_parser(name)
        p.add_argument("--db", required=True)
        if name in ("prepare", "export", "group", "verification-sample"):
            p.add_argument("--out", required=True)
        if name == "prepare":
            p.add_argument("--limit", type=int, default=100)
        if name == "verification-sample":
            p.add_argument("--count", type=int, required=True)
        if name == "import-results":
            p.add_argument("input_jsonl")
        if name == "rank":
            p.add_argument("--membership", required=True)
            p.add_argument("--out-dir", required=True)
    p = sub.add_parser("cost", help="Replay saved usage and prices OFFLINE, including failed attempts.")
    p.add_argument("--calls", required=True)
    p.add_argument("--measurement", required=True)
    p.add_argument("--rates", default=str(ROOT / "cost" / "rates.csv"))
    p.add_argument("--scenarios", help="Optional JSON array with stage-specific projection denominators.")
    p.add_argument("--out-dir", required=True)
    p = sub.add_parser("evaluate", help="Offline comparison to all 50 STUDENT-completed golden labels.")
    p.add_argument("--golden", required=True)
    p.add_argument("--predictions", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("export-grading", help="Export contract-format records from actual saved complete evidence.")
    p.add_argument("--db", required=True)
    p.add_argument("--full-csv", required=True)
    p.add_argument("--calls", required=True)
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p.add_argument("--out", required=True)
    for name in ("pilot", "checkpoint"):
        p = sub.add_parser(name, help="Zero-cost preflight by default; paid execution is explicit.")
        p.add_argument("--input", default=str(ROOT / "data" / "course" / "cost_100.csv") if name == "pilot" else None,
                       required=name == "checkpoint")
        p.add_argument("--run-dir", default=str(ROOT / "runs" / "pilot-live") if name == "pilot" else None,
                       required=name == "checkpoint")
        p.add_argument("--phase", choices=("initial", "resume", "warm"), default="initial")
        p.add_argument("--execute-paid", action="store_true")
        p.add_argument("--budget-usd")
        p.add_argument("--stop-after", type=int)
    args = parser.parse_args(argv)
    config = configuration(args.config)
    command = args.command or "doctor"
    if hasattr(args, "db") and command != "ingest" and not Path(args.db).is_file():
        raise ValueError("Source database does not exist; ingest first.")
    if command == "doctor":
        files = ("GRADING_CONTRACT.md", "COST_CALCULATOR.md", "cost_100.csv", "golden_50_to_label.csv",
                 "checkpoint_500.csv", "analysis_10000.csv", "spotify_reviews_18months.csv", "manifest.json", "check_submission.py")
        progress = read_json(ROOT / "evidence" / "pilot-progress.json") if (ROOT / "evidence" / "pilot-progress.json").exists() else {}
        result = {"phase": progress.get("status", "course-data-ingested-provider-setup-pending"), "network_calls_this_command": 0,
                  "course_files": {name: (ROOT / "data" / "course" / name).is_file() for name in files},
                  "implemented": ["ingestion", "exact-text cache", "offline Jev request builder",
                                  "result validation/import", "blind verifier sample", "group/rank/claims",
                                  "course row hashes/ranking/export adapter", "golden evaluation command",
                                  "offline cost arithmetic/projections", "persistent budget reservations",
                                  "explicit paid pilot: Jev/OpenAI, bounded retries, four model roles, warm cache"],
                  "pending": ["refresh 100k cost/time forecasts at measured checkpoints",
                              "human golden labels and evaluation", "verifier/memo quality review",
                              "recorded recovery demonstration", "100k successful nonempty classifications",
                              "deployed dashboard/backend/database", "publication"],
                  "paid_execution_requires": ["pilot --execute-paid", "--budget-usd", "local provider keys"],
                  "label_config": config["label_config"]}
    elif command == "ingest":
        result = ingest(args.input_csv, args.db)
        write_json(args.report, result)
    elif command == "status":
        result = status(args.db, config["label_config"])
    elif command == "prepare":
        def requests():
            for row in pending(args.db, config["label_config"], args.limit):
                yield {"review_id": row["review_id"], "internal_source_sha256": row["internal_source_sha256"],
                       "label_config": config["label_config"], "stage": "enrichment", "paid_execution": False,
                       "request": build_request(row["review_text"], config)}
        write_jsonl(args.out, requests())
        result = {"saved_to": args.out, "network_calls": 0, "note": "Prepared requests only; no provider execution."}
    elif command == "import-results":
        result = import_predictions(args.db, config, read_jsonl(args.input_jsonl))
    elif command == "export":
        write_jsonl(args.out, records(args.db, config["label_config"]))
        result = {"saved_to": args.out, "format": "INTERNAL, not instructor grading export"}
    elif command == "verification-sample":
        db = connect(args.db)
        try:
            ids = [row[0] for row in db.execute("SELECT review_id FROM reviews WHERE empty=0 ORDER BY review_id")]
            if not 0 <= args.count <= len(ids):
                raise ValueError("Verification sample count exceeds nonempty population or is negative.")
            selected = sorted(random.Random(config["verification_seed"]).sample(ids, args.count))
            rows = []
            for rid in selected:
                text = db.execute("SELECT review_text FROM reviews WHERE review_id=?", (rid,)).fetchone()[0]
                rows.append({"review_id": rid, "review_text": text, "seed": config["verification_seed"],
                             "prompt": config["prompts"]["verification"], "taxonomy": config["taxonomy"]})
            write_jsonl(args.out, rows)
        finally:
            db.close()
        result = {"sample_size": len(selected), "saved_to": args.out, "first_predictions_included": False}
    elif command == "group":
        result = group(args.db, config["label_config"], args.out)
    elif command == "rank":
        result = rank(args.db, config["label_config"], args.membership, args.out_dir)
    elif command in ("pilot", "checkpoint"):
        from .runner import run_pilot, run_checkpoint
        runner = run_pilot if command == "pilot" else run_checkpoint
        result = runner(args.input, config, args.run_dir, args.phase, args.budget_usd,
                        args.execute_paid, args.stop_after)
    elif command == "evaluate":
        from .evaluation import evaluate
        result = evaluate(args.golden, args.predictions, config)
        write_json(args.out, result)
    elif command == "export-grading":
        from .contract import export_grading
        result = export_grading(args.db, config, args.full_csv, args.calls, args.before, args.after, args.out)
    elif command == "cost":
        result = replay(read_jsonl(args.calls), load_rates(args.rates), read_json(args.measurement))
        projections = [project(result, scenario) for scenario in read_json(args.scenarios)] if args.scenarios else []
        result["projections"] = projections
        write_json(Path(args.out_dir) / "report.json", result)
        lines = ["# Offline cost replay", "", "Evidence kind: **%s**" % result["evidence_kind"], "",
                 "API total USD: %s" % (result["total_api_usd"] if result["total_api_usd"] is not None else "UNKNOWN"),
                 "Known API subtotal USD: " + result["known_api_usd"],
                 "Attempts with unknown charges: " + str(result["unknown_charge_attempts"]),
                 "Measured end-to-end wall seconds: " + str(result["measurement"]["wall_seconds"]), "",
                 "This command made zero API calls. It does not certify the authenticity of supplied usage.", "",
                 "See report.json for stage details, measured denominators and any modeled projections."]
        atomic_text(Path(args.out_dir) / "report.md", "\n".join(lines) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        sys.exit(2)
