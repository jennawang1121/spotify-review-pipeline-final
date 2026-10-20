"""Transactional source accounting with internal and official course row hashes."""
import csv
import json
import math
import sqlite3
from collections import Counter
from pathlib import Path

from .common import SOURCE_FIELDS, canonical, digest, file_sha
from .contract import row_sha


def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY, ordinal INTEGER UNIQUE NOT NULL,
            source_json TEXT NOT NULL, internal_source_sha256 TEXT NOT NULL,
            text_sha256 TEXT NOT NULL, review_text TEXT NOT NULL, empty INTEGER NOT NULL,
            source_sha256 TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS review_text_hash ON reviews(text_sha256);
        CREATE TABLE IF NOT EXISTS labels (
            label_config TEXT NOT NULL, text_sha256 TEXT NOT NULL, review_text TEXT NOT NULL,
            cache_source_id TEXT NOT NULL REFERENCES reviews(review_id),
            prediction_json TEXT NOT NULL, provenance_json TEXT NOT NULL,
            PRIMARY KEY(label_config, text_sha256)
        );
    """)
    if "source_sha256" not in {row[1] for row in db.execute("PRAGMA table_info(reviews)")}:
        with db:
            db.execute("ALTER TABLE reviews ADD COLUMN source_sha256 TEXT")
            for row in db.execute("SELECT review_id,source_json FROM reviews"):
                db.execute("UPDATE reviews SET source_sha256=? WHERE review_id=?",
                           (row_sha(json.loads(row["source_json"])), row["review_id"]))
    return db


def ingest(csv_path, db_path):
    source_sha = file_sha(csv_path)
    db = connect(db_path)
    try:
        existing = db.execute("SELECT value FROM meta WHERE key='ingestion'").fetchone()
        if existing:
            report = json.loads(existing[0])
            if report["file_sha256"] != source_sha:
                raise ValueError("This database belongs to a different source CSV; use a new database.")
            return report
        ratings, missing = Counter(), Counter()
        first_date, last_date = None, None
        total = empty_count = 0
        with db, open(csv_path, encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            if len(fields) != len(set(fields)) or not set(SOURCE_FIELDS).issubset(fields):
                raise ValueError("CSV needs unique headers including: " + ", ".join(SOURCE_FIELDS))
            for ordinal, row in enumerate(reader):
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("Malformed CSV row at logical record %d" % (ordinal + 1))
                if not row["review_id"].strip():
                    raise ValueError("Missing review_id at logical record %d" % (ordinal + 1))
                # Keep every supplied cell unchanged, including optional extra columns.
                # Model request builders explicitly select only review_text.
                raw = canonical(row)
                text = row["review_text"]
                empty = not text.strip()
                try:
                    db.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?)", (
                        row["review_id"], ordinal, raw, digest(raw), digest(text), text, int(empty), row_sha(row)))
                except sqlite3.IntegrityError as exc:
                    raise ValueError("Duplicate original review_id: " + row["review_id"]) from exc
                total += 1
                empty_count += int(empty)
                ratings[row["review_rating"]] += 1
                for field in SOURCE_FIELDS:
                    missing[field] += int(not row[field].strip())
                date = row["review_timestamp"]
                if date:
                    first_date = date if first_date is None else min(first_date, date)
                    last_date = date if last_date is None else max(last_date, date)
            if file_sha(csv_path) != source_sha:
                raise ValueError("CSV changed during ingestion; retry with a stable file.")
            unique = db.execute("SELECT COUNT(DISTINCT text_sha256) FROM reviews WHERE empty=0").fetchone()[0]
            report = {
                "schema": "internal-store-with-a5-audit-v1-hash", "file_sha256": source_sha,
                "file_bytes": Path(csv_path).stat().st_size, "source_rows": total,
                "nonempty_rows": total - empty_count, "empty_rows": empty_count,
                "unique_nonempty_texts": unique, "exact_text_reuse_rows": total - empty_count - unique,
                "duplicate_review_ids": 0, "ratings": dict(ratings), "missing_values": dict(missing),
                "timestamp_min_lexical": first_date, "timestamp_max_lexical": last_date,
                "timestamp_note": "Source strings preserved; timezone unspecified. Lexical bounds require ISO-like source format.",
                "internal_hash_algorithm": "sha256(UTF-8 JSON object, sorted keys, compact separators, ensure_ascii=False)",
                "source_headers": fields,
                "official_row_hash": "Unmodified course/check_submission.py::row_sha",
            }
            db.execute("INSERT INTO meta VALUES ('ingestion',?)", (canonical(report),))
        return report
    finally:
        db.close()


def validate_prediction(prediction, source_text, taxonomy):
    required = {"topic", "intent", "severity", "sentiment", "entities", "evidence_quote", "needs_review"}
    if set(prediction) != required:
        raise ValueError("Prediction must contain exactly: " + ", ".join(sorted(required)))
    for key in ("topic", "intent"):
        if not isinstance(prediction[key], str) or prediction[key] not in taxonomy[key]:
            raise ValueError("Invalid " + key)
    if type(prediction["severity"]) is not int or not 1 <= prediction["severity"] <= 5:
        raise ValueError("Severity must be an integer 1–5 (not a boolean).")
    score = prediction["sentiment"]
    if type(score) not in (int, float) or not math.isfinite(score) or not -1 <= score <= 1:
        raise ValueError("Sentiment must be finite and between -1 and 1.")
    if type(prediction["needs_review"]) is not bool:
        raise ValueError("needs_review must be a boolean.")
    quote = prediction["evidence_quote"]
    if not isinstance(quote, str) or not quote.strip() or quote not in source_text:
        raise ValueError("Evidence must be a nonempty exact source substring.")
    entities = prediction["entities"]
    if not isinstance(entities, list) or any(
        not isinstance(entity, str) or not entity.strip() or entity not in source_text for entity in entities
    ):
        raise ValueError("Internal entity representation requires verbatim source strings.")
    if len(entities) != len(set(entities)):
        raise ValueError("Duplicate entity strings.")


def import_predictions(db_path, config, results):
    """Import complete saved results atomically. Does not call any provider."""
    db = connect(db_path)
    inserted = 0
    try:
        with db:
            seen = set()
            for result in results:
                rid = result["review_id"]
                if rid in seen:
                    raise ValueError("Duplicate result ID: " + rid)
                seen.add(rid)
                if result["label_config"] != config["label_config"]:
                    raise ValueError("Result configuration mismatch.")
                row = db.execute("SELECT * FROM reviews WHERE review_id=?", (rid,)).fetchone()
                if not row or row["empty"]:
                    raise ValueError("Result has an unknown or empty-text source ID: " + rid)
                if result["internal_source_sha256"] != row["internal_source_sha256"]:
                    raise ValueError("Result source hash mismatch.")
                provenance = result["provenance"]
                if provenance.get("kind") not in ("provider_response", "synthetic_test"):
                    raise ValueError("Declare provider_response or synthetic_test provenance.")
                if not isinstance(provenance.get("reference"), str) or not provenance["reference"].strip():
                    raise ValueError("Provenance needs a saved response or synthetic fixture reference.")
                prediction = result["prediction"]
                validate_prediction(prediction, row["review_text"], config["taxonomy"])
                existing = db.execute("SELECT * FROM labels WHERE label_config=? AND text_sha256=?",
                                      (config["label_config"], row["text_sha256"])).fetchone()
                if existing:
                    if (existing["review_text"] != row["review_text"] or
                            existing["prediction_json"] != canonical(prediction) or
                            json.loads(existing["provenance_json"])["kind"] != provenance["kind"]):
                        raise ValueError("Conflicting cached result; create a new label configuration.")
                    continue
                db.execute("INSERT INTO labels VALUES (?,?,?,?,?,?)", (
                    config["label_config"], row["text_sha256"], row["review_text"], rid,
                    canonical(prediction), canonical(provenance)))
                inserted += 1
        return {"new_unique_results": inserted}
    finally:
        db.close()


def records(db_path, label_config):
    db = connect(db_path)
    try:
        query = """SELECT r.*, l.prediction_json, l.cache_source_id, l.provenance_json
                   FROM reviews r LEFT JOIN labels l ON r.text_sha256=l.text_sha256
                   AND r.review_text=l.review_text AND l.label_config=? ORDER BY r.ordinal"""
        for row in db.execute(query, (label_config,)):
            record = {
                "review_id": row["review_id"], "source": json.loads(row["source_json"]),
                "internal_source_sha256": row["internal_source_sha256"], "label_config": label_config,
                "source_sha256": row["source_sha256"],
                "status": "quarantined" if row["empty"] else "completed" if row["prediction_json"] else "pending",
                "reason": "empty_review_text" if row["empty"] else None,
                "cache_source_id": row["cache_source_id"] if row["cache_source_id"] != row["review_id"] else None,
                "prediction": json.loads(row["prediction_json"]) if row["prediction_json"] else None,
                "provenance": json.loads(row["provenance_json"]) if row["provenance_json"] else None,
            }
            yield record
    finally:
        db.close()


def pending(db_path, label_config, limit):
    if limit < 1:
        raise ValueError("Queue limit must be positive.")
    db = connect(db_path)
    try:
        query = """WITH representatives AS (
                       SELECT MIN(ordinal) AS ordinal FROM reviews WHERE empty=0
                       GROUP BY text_sha256, review_text
                   ) SELECT r.* FROM representatives p JOIN reviews r ON r.ordinal=p.ordinal
                   LEFT JOIN labels l ON r.text_sha256=l.text_sha256
                   AND r.review_text=l.review_text AND l.label_config=?
                   WHERE l.text_sha256 IS NULL ORDER BY r.ordinal LIMIT ?"""
        return [dict(row) for row in db.execute(query, (label_config, limit))]
    finally:
        db.close()


def status(db_path, label_config):
    counts = Counter()
    cache_hits = 0
    kinds = Counter()
    for record in records(db_path, label_config):
        counts[record["status"]] += 1
        cache_hits += int(record["cache_source_id"] is not None)
        if record["provenance"]:
            kinds[record["provenance"]["kind"]] += 1
    return {"statuses": dict(counts), "cache_reused_records": cache_hits,
            "completed_provenance": dict(kinds), "label_config": label_config,
            "official_contract_validated": False}
