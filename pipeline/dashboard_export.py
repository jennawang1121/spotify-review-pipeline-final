"""Export completed real pipeline evidence for the database-backed dashboard."""
import argparse
from pathlib import Path

from .common import ROOT, read_json, read_jsonl, write_json
from .store import records


def export(run_dir, summary_path, memo_path, destination, external=False):
    root = Path(run_dir)
    config = read_json(root / "label_configuration.json")
    rows = list(records(root / "source.sqlite", config["label_config"]))
    summary = read_json(summary_path)
    if len(rows) != summary["source_rows"] or any(r["status"] == "pending" for r in rows):
        raise ValueError("Dashboard export requires completed, matching run evidence.")
    if any(r["status"] == "completed" and r["provenance"]["kind"] != "provider_response" for r in rows):
        raise ValueError("Synthetic predictions cannot populate the business dashboard.")
    seed = {"revision": "checkpoint-%s-" % len(rows) + config["label_config"][:12],
            "reviews": rows, "summary": summary, "memo": Path(memo_path).read_text(),
            "raw_memo": (root / "memo.md").read_text(),
            "recommendation": read_json(root / "memo.structured.json"),
            "names": read_json(root / "issue_names.json"), "pack": read_json(root / "analysis/evidence_pack.json"),
            "taxonomy": config["taxonomy"], "verification": list(read_jsonl(root / "verification.jsonl")),
            "final_scope": read_json(ROOT / "evidence/scope-100k.json")}
    if external:
        seed['revision'] = 'final-100013-' + config['label_config'][:12]
        seed['external_count'] = len(rows)
        seed['metadata_version'] = 'final-reviewed-v1'
        seed['reviews'] = []
        seed['summary']['project_cost'] = read_json(ROOT / 'evidence/final-100k/project-cost.json')
        editorial = ROOT / 'evidence/final-100k/memo.structured.editorial.json'
        if editorial.exists():seed['recommendation'] = read_json(editorial)
    write_json(destination, seed)
    return {"records": len(rows), "new_model_calls": 0, "saved_to": str(destination)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--memo", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--external", action="store_true")
    args = p.parse_args()
    print(export(args.run_dir, args.summary, args.memo, args.out, args.external))
