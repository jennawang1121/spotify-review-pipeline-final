import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FIELDS = (
    "review_id", "review_text", "review_rating", "review_likes",
    "app_version", "review_timestamp",
)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".writing-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def write_jsonl(path, rows):
    # Stream large exports rather than placing the full corpus in RAM.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".writing-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            for row in rows:
                handle.write(canonical(row) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_csv(path, rows, fields):
    import io
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    atomic_text(path, buffer.getvalue())


def configuration(path=None):
    config = read_json(path or ROOT / "config.json")
    # Cache identity includes prompt contents, schema version, model, effort and extraction policy.
    config["prompts"] = {
        name: (ROOT / "prompts" / (name + ".txt")).read_text(encoding="utf-8")
        for name in ("enrichment", "verification", "grouping", "memo")
    }
    config["taxonomy"] = read_json(ROOT / "taxonomy.json")
    identity = {k: config[k] for k in ("schema_version", "classifier_model", "language_model",
                "reasoning_effort", "max_output_tokens", "extraction_policy", "prompts", "taxonomy")}
    config["label_config"] = digest(canonical(identity))
    return config
