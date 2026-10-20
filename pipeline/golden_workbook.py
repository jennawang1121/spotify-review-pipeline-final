"""Read the student's workbook offline; validate before exporting human labels."""
import argparse
import csv
import json
import posixpath
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from .common import ROOT, configuration, file_sha, read_json, write_csv
from .store import validate_prediction


NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
LABEL_COLUMNS = dict(zip("CDEFGHI", ("topic", "intent", "severity", "sentiment", "needs_review", "entities", "evidence_quote")))


def read_cells(path):
    with zipfile.ZipFile(path) as archive:
        if sum(i.file_size for i in archive.infolist()) > 20000000:
            raise ValueError("Workbook exceeds the bounded golden-label file size.")
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(node.itertext()) for node in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", NS)]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet = next((s for s in workbook.findall("s:sheets/s:sheet", NS) if s.get("name") == "标注"), None)
        if sheet is None:
            raise ValueError("Missing 标注 worksheet.")
        rid = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels if r.get("Id") == rid)
        target = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
        cells = {}
        for node in ET.fromstring(archive.read(target)).findall("s:sheetData/s:row/s:c", NS):
            address, kind = node.get("r"), node.get("t")
            if node.find("s:f", NS) is not None:
                cells[address] = {"formula": True}
                continue
            value = node.find("s:v", NS)
            value = value.text if value is not None else ""
            if kind == "s":
                value = shared[int(value)]
            elif kind == "inlineStr":
                value = "".join(node.find("s:is", NS).itertext())
            elif kind == "b":
                value = "true" if value == "1" else "false"
            cells[address] = value or ""
        return cells


def validate_cells(cells, originals, config):
    expected = {row["review_id"]: row for row in originals}
    for col, field in dict(LABEL_COLUMNS, B="review_text", L="review_id").items():
        if cells.get(col + "5") != field:
            raise ValueError("Keep the original workbook column headers.")
    seen, completed, output = set(), 0, {}
    for index in range(6, 56):
        rid = cells.get("L" + str(index))
        if not isinstance(rid, str) or rid not in expected or rid in seen:
            raise ValueError("Missing, duplicate or changed original review ID.")
        seen.add(rid)
        if cells.get("B" + str(index)) != expected[rid]["review_text"]:
            raise ValueError("Original review text changed; restore it before importing.")
        labels = {field: cells.get(col + str(index), "") for col, field in LABEL_COLUMNS.items()}
        if any(isinstance(v, dict) for v in labels.values()):
            raise ValueError("Human label cells must contain values, not formulas.")
        if not all(str(v).strip() for v in labels.values()):
            continue
        severity = float(labels["severity"])
        if not severity.is_integer():
            raise ValueError("Severity must be an integer.")
        flag = str(labels["needs_review"]).strip().lower()
        if flag not in ("true", "false"):
            raise ValueError("needs_review must be true or false.")
        prediction = dict(labels, severity=int(severity), sentiment=float(labels["sentiment"]),
                          needs_review=flag == "true", entities=json.loads(labels["entities"]))
        validate_prediction(prediction, expected[rid]["review_text"], config["taxonomy"])
        row = dict(expected[rid], **labels)
        row.update(severity=str(prediction["severity"]), sentiment=str(prediction["sentiment"]), needs_review=flag)
        output[rid] = row
        completed += 1
    if seen != set(expected):
        raise ValueError("Workbook must retain all 50 original IDs.")
    return completed, [output[r["review_id"]] for r in originals if r["review_id"] in output]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook")
    parser.add_argument("--out", help="Write CSV only when all 50 human labels are complete and valid.")
    args = parser.parse_args()
    source = ROOT / "data/course/golden_50_to_label.csv"
    if file_sha(source) != read_json(ROOT / "course/manifest.json")["files"][source.name]["sha256"]:
        raise ValueError("Original golden CSV differs from the course manifest.")
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        originals, headers = list(reader), reader.fieldnames
    completed, rows = validate_cells(read_cells(args.workbook), originals, configuration())
    if args.out:
        if completed != 50:
            raise ValueError("Student labels are incomplete: %d/50. No CSV written." % completed)
        if Path(args.out).resolve() == source.resolve():
            raise ValueError("Do not overwrite the original course template.")
        write_csv(args.out, rows, headers)
    print(json.dumps({"human_labels_complete_and_valid": completed, "total": 50,
                      "api_calls": 0, "exported": args.out if args.out else None}))


if __name__ == "__main__":
    main()
