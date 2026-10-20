"""Adapter to the unmodified instructor helper shipped with the course ZIP."""
import importlib.util
import json
import shutil
from pathlib import Path

from .common import ROOT, file_sha, read_json, read_jsonl, write_json, write_jsonl


spec = importlib.util.spec_from_file_location("course_audit", ROOT / "course" / "check_submission.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
row_sha = audit.row_sha
profile = audit.profile
VERSION = audit.VERSION


def export_records(db_path, label_config):
    from .store import records
    for record in records(db_path, label_config):
        if record["status"] == "pending":
            raise ValueError("Unprocessed records remain. Save an internal snapshot; do not misrepresent it as a final export.")
        out = {"review_id": record["review_id"], "source_sha256": record["source_sha256"],
               "status": record["status"]}
        if record["status"] == "completed":
            if record["provenance"]["kind"] != "provider_response":
                raise ValueError("Synthetic results cannot be exported as course results.")
            out.update(record["prediction"])
            out["label_config"] = label_config
            if record["cache_source_id"]:
                out["cache_source_id"] = record["cache_source_id"]
        else:
            out["reason"] = record["reason"]
        yield out


def export_grading(db_path, config, full_csv, calls_path, before_path, after_path, destination):
    """Create a new export only from actual saved evidence; never fabricate calls/checkpoints."""
    from .store import connect, records
    from .ranking import group, rank
    import tempfile
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Choose a new export directory; existing submitted evidence is not overwritten.")
    completed = set()
    expected = {}
    for record in records(db_path, config["label_config"]):
        expected[record["review_id"]] = record["source_sha256"]
        if record["status"] == "pending":
            raise ValueError("Unprocessed records remain; final grading export is not ready.")
        if record["status"] == "completed":
            completed.add(record["review_id"])
            if record["provenance"]["kind"] != "provider_response":
                raise ValueError("Synthetic records cannot be exported as course evidence.")
    remaining = dict(expected)
    for row in audit.csv_rows(full_csv):
        rid = row["review_id"]
        if rid in remaining:
            if row_sha(row) != remaining.pop(rid):
                raise ValueError("Analysis row differs from the supplied full source.")
    if remaining:
        raise ValueError("Analysis IDs missing from full source.")
    before, after = read_json(before_path), read_json(after_path)
    for snapshot in (before, after):
        ids = snapshot.get("completed_ids")
        if not isinstance(ids, list) or any(not isinstance(x, str) for x in ids) or len(set(ids)) != len(ids):
            raise ValueError("Malformed checkpoint completed_ids.")
    if not set(before["completed_ids"]) or not set(before["completed_ids"]) < set(after["completed_ids"]) <= completed:
        raise ValueError("Need a real nonempty before checkpoint and additional completions after resume.")
    calls = list(read_jsonl(calls_path))
    roles = {call.get("role") for call in calls if call.get("outcome") == "succeeded"}
    if roles != {"enrich", "verify", "group", "memo"}:
        raise ValueError("Saved model-call evidence must include all four roles, including group naming.")
    if any(call.get("evidence_kind") == "synthetic_test" for call in calls):
        raise ValueError("Synthetic calls cannot be exported as actual evidence.")
    db = connect(db_path)
    try:
        metadata = json.loads(db.execute("SELECT value FROM meta WHERE key='ingestion'").fetchone()[0])
    finally:
        db.close()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(dir=destination.parent, prefix=".grading-"))
    try:
        write_json(temporary / "run.json", {"version": VERSION, "analysis_count": len(expected),
                   "analysis_sha256": metadata["file_sha256"], "classification_input_fields": ["review_text"],
                   "allow_multi_issue": False})
        write_json(temporary / "ingestion.json", profile(full_csv))
        write_jsonl(temporary / "records.jsonl", export_records(db_path, config["label_config"]))
        group(db_path, config["label_config"], temporary / "membership.csv")
        rank(db_path, config["label_config"], temporary / "membership.csv", temporary)
        write_jsonl(temporary / "calls.jsonl", calls)
        write_json(temporary / "checkpoint_before.json", before)
        write_json(temporary / "checkpoint_after.json", after)
        temporary.rename(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {"exported": str(destination), "records": len(expected), "completed": len(completed),
            "next": "Run the unmodified course checker; export alone does not certify a passing audit."}
