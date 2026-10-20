"""Prepare a reproducible reduced analysis scope offline; never label reviews."""
import argparse
import csv
import hashlib
import heapq
from pathlib import Path

from .common import ROOT, SOURCE_FIELDS, file_sha, read_json, write_json
from .contract import row_sha


def select_ids(rows, count, seed):
    if count < 1:
        raise ValueError("Classification target must be positive.")
    ranked = ((hashlib.sha256((seed + ":" + row["review_id"]).encode()).hexdigest(), row["review_id"])
              for row in rows if row["review_text"].strip())
    chosen = heapq.nsmallest(count, ranked)
    if len(chosen) != count:
        raise ValueError("Fewer nonempty source reviews than the requested target.")
    return {rid for _, rid in chosen}


def prepare_scope(source, destination, count=100000):
    source, destination = Path(source), Path(destination)
    manifest = read_json(ROOT / "course/manifest.json")
    expected = manifest["files"]["spotify_reviews_18months.csv"]["sha256"]
    if file_sha(source) != expected:
        raise ValueError("Scope preparation requires the unchanged official source.")
    if destination.exists():
        raise ValueError("Choose a new scope directory; do not overwrite a frozen scope.")
    seed = manifest["samples"]["seed"]
    with source.open(encoding="utf-8-sig", newline="") as handle:
        selected = select_ids(csv.DictReader(handle), count, seed)
    # The same ID-only seed extends the existing course samples without choosing
    # short, cheap, easy, or favorable reviews. Human answers are never read.
    nested = {}
    for name in ("cost_100.csv", "checkpoint_500.csv", "analysis_10000.csv", "golden_50_to_label.csv"):
        with (ROOT / "data/course" / name).open(encoding="utf-8-sig", newline="") as handle:
            ids = {row["review_id"] for row in csv.DictReader(handle)}
        nested[name] = {"total": len(ids), "included": len(ids & selected)}
    if count >= 10050 and any(item["total"] != item["included"] for item in nested.values()):
        raise ValueError("Reduced scope unexpectedly excludes fixed development/golden IDs.")
    destination.mkdir(parents=True)
    output = destination / "analysis.csv"
    hashes = destination / "source_hashes.csv"
    texts, ids = set(), set()
    empty = 0
    with source.open(encoding="utf-8-sig", newline="") as handle, output.open("w", encoding="utf-8", newline="") as out, hashes.open("w", encoding="utf-8", newline="") as hash_out:
        writer = csv.DictWriter(out, fieldnames=SOURCE_FIELDS, lineterminator="\n")
        hash_writer = csv.writer(hash_out, lineterminator="\n")
        writer.writeheader()
        hash_writer.writerow(["review_id", "source_sha256"])
        for row in csv.DictReader(handle):
            is_empty = not row["review_text"].strip()
            if row["review_id"] not in selected and not is_empty:
                continue
            if row["review_id"] in ids:
                raise ValueError("Duplicate source ID.")
            ids.add(row["review_id"])
            writer.writerow({key: row[key] for key in SOURCE_FIELDS})
            hash_writer.writerow([row["review_id"], row_sha(row)])
            empty += is_empty
            if not is_empty:
                texts.add(row["review_text"])
    if file_sha(source) != expected or len(ids) - empty != count:
        raise ValueError("Source changed or scope count mismatch; do not use this output.")
    report = {"status": "prepared_not_classified", "source_sha256": expected,
              "source_rows_ingested": manifest["profile"]["records"], "analysis_rows": len(ids),
              "nonempty_classification_target": count, "empty_text_quarantines": empty,
              "nonempty_outside_analysis_scope": manifest["assignment_scope"]["nonempty_to_classify"] - count,
              "unique_nonempty_texts": len(texts), "exact_text_reuse_rows": count - len(texts),
              "long_text_unique_extractions": sum(len(text) > 600 for text in texts),
              "analysis_sha256": file_sha(output), "source_hashes_sha256": file_sha(hashes),
              "seed": seed, "selection": "Lowest SHA-256(seed + ':' + review_id) among nonempty rows; retain source order; include all empty rows separately.",
              "fixed_samples": nested, "human_answers_read": False, "new_api_calls": 0,
              "limitations": "A deterministic sample of historical self-selected reviews; sample totals are not full-source totals. Outside-scope reviews remain in the full ingestion store and are not claimed as classified."}
    write_json(destination / "manifest.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(ROOT / "data/course/spotify_reviews_18months.csv"))
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--count", type=int, default=100000)
    args = parser.parse_args()
    import json
    print(json.dumps(prepare_scope(args.source, args.out_dir, args.count), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
