"""Deterministic grouping and reranking, independent of any model provider."""
import csv
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .common import atomic_text, write_csv, write_json
from .store import connect, records, status


RANK_FIELDS = ("rank", "issue_id", "complaint_count", "severity_sum", "mean_severity", "priority_score")


def group(db_path, label_config, membership_path):
    # Atomic streaming write avoids retaining all memberships in memory.
    import os
    import tempfile
    membership_path = Path(membership_path)
    membership_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=membership_path.parent, prefix=".membership-")
    count = 0
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("issue_id", "review_id"), lineterminator="\n")
            writer.writeheader()
            for record in records(db_path, label_config):
                prediction = record["prediction"]
                if record["status"] == "completed" and prediction["intent"] in ("complaint", "cancellation"):
                    writer.writerow({"issue_id": "issue-" + prediction["topic"], "review_id": record["review_id"]})
                    count += 1
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, membership_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"grouping_policy": "topic-v1", "memberships": count}


def rank(db_path, label_config, membership_path, output_dir):
    """Recompute from saved memberships. Reject invalid or duplicate contributions."""
    db = connect(db_path)
    totals = defaultdict(lambda: {"count": 0, "sum": 0, "evidence": []})
    kinds = set()
    try:
        db.execute("CREATE TEMP TABLE seen(issue_id TEXT, review_id TEXT, PRIMARY KEY(issue_id, review_id))")
        with open(membership_path, encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["issue_id", "review_id"]:
                raise ValueError("Membership needs issue_id,review_id headers.")
            for member in reader:
                issue_id, rid = member["issue_id"], member["review_id"]
                if not issue_id or not rid:
                    raise ValueError("Empty issue or review ID.")
                row = db.execute("""SELECT r.review_text,l.prediction_json,l.provenance_json
                    FROM reviews r JOIN labels l ON r.text_sha256=l.text_sha256
                    AND r.review_text=l.review_text AND l.label_config=? WHERE r.review_id=?""",
                    (label_config, rid)).fetchone()
                if row is None:
                    raise ValueError("Membership references unknown or incomplete review: " + rid)
                prediction = json.loads(row["prediction_json"])
                if prediction["intent"] not in ("complaint", "cancellation"):
                    raise ValueError("Only complaint/cancellation records may contribute: " + rid)
                try:
                    db.execute("INSERT INTO seen VALUES (?,?)", (issue_id, rid))
                except Exception as exc:
                    raise ValueError("Duplicate issue/review membership: " + rid) from exc
                kinds.add(json.loads(row["provenance_json"])["kind"])
                total = totals[issue_id]
                total["count"] += 1
                total["sum"] += prediction["severity"]
                if len(total["evidence"]) < 3:
                    total["evidence"].append({"review_id": rid, "quote": prediction["evidence_quote"],
                                              "needs_review": prediction["needs_review"]})
        if len(kinds) > 1:
            raise ValueError("Synthetic and provider outputs must never share business aggregates.")
        ranked = []
        for issue, total in totals.items():
            mean = Decimal(total["sum"]) / Decimal(total["count"])
            ranked.append({"issue_id": issue, "complaint_count": total["count"],
                           "severity_sum": total["sum"], "priority_score": total["sum"],
                           "mean_severity": str(mean.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))})
        ranked.sort(key=lambda row: (-row["priority_score"], row["issue_id"]))
        for index, row in enumerate(ranked, 1):
            row["rank"] = index
        claims = [{"claim_id": row["issue_id"] + ":" + field, "issue_id": row["issue_id"],
                   "metric": field, "value": row[field]} for row in ranked for field in RANK_FIELDS[2:]]
        evidence = [{"issue_id": row["issue_id"], "examples": totals[row["issue_id"]]["evidence"]}
                    for row in ranked]
        out = Path(output_dir)
        write_csv(out / "ranking.csv", ranked, RANK_FIELDS)
        write_csv(out / "claims.csv", claims, ("claim_id", "issue_id", "metric", "value"))
        write_json(out / "evidence_pack.json", {
            "schema": "a5-audit-v1-ranking", "label_config": label_config,
            "provenance_kinds": sorted(kinds), "coverage": status(db_path, label_config),
            "ranking": ranked, "claims": claims,
            "evidence": evidence, "sampling_note": "First three members per issue in saved membership order; illustrative, not representative sampling.",
            "limitations": ["Historical, self-selected reviews", "Cancellation is intent, not observed churn",
                            "Topic-level groups may combine distinct issues", "Human quote-support review required"]})
        return {"issues": len(ranked), "contributing_memberships": sum(x["count"] for x in totals.values()),
                "provenance_kinds": sorted(kinds), "ranking": ranked}
    finally:
        db.close()
