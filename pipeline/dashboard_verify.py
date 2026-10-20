"""Check the deployed backend against saved evidence; no model calls."""
import argparse
import getpass
import json
import urllib.request

from .common import read_json, write_json


def verify(url, token, expected):
    if not url.startswith("https://"):
        raise ValueError("Use the successful HTTPS deployment URL.")
    def get(path):
        headers = {"OAI-Sites-Authorization": "Bearer " + token} if token else {}
        request = urllib.request.Request(url.rstrip("/") + path, headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    summary, issues, quality, memo = [get(path) for path in
        ("/api/summary", "/api/issues", "/api/quality", "/api/recommendation")]
    assert summary["coverage"]["completed"] == expected["completed"]
    assert summary["coverage"]["total"] == expected["source_rows"]
    assert len(issues) == len(expected["ranking"])
    for actual, wanted in zip(issues, expected["ranking"]):
        for key in ("issue_id", "complaint_count", "severity_sum", "priority_score", "mean_severity", "rank"):
            assert actual[key] == wanted[key], "Deployed ranking mismatch: " + key
    reviews = get("/api/reviews?topic=usability&intent=complaint")
    assert all(r["prediction"]["topic"] == "usability" and r["prediction"]["intent"] == "complaint" for r in reviews["rows"])
    review = get("/api/reviews/" + reviews["rows"][0]["review_id"])
    assert review["prediction"]["evidence_quote"] in review["source"]["review_text"]
    assert len(review["source_sha256"]) == 64
    assert len(quality["verification"]) == expected["quality"]["sample_size"]
    assert memo["structured"]["priority_issue_id"] == issues[0]["issue_id"]
    return {"status": "pass", "url": url, "coverage": summary["coverage"],
            "database": summary["database"], "issue_rankings_match_saved_results": len(issues),
            "filters_and_source_quote_valid": True, "independent_cases": len(quality["verification"]),
            "recommendation_priority_matches_ranking": True, "new_model_calls": 0,
            "method": "Deployed Worker API reads production D1; compares exact coverage, baseline figures and source evidence to saved checkpoint results."}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True)
    p.add_argument("--expected", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--private", action="store_true")
    args = p.parse_args()
    token = getpass.getpass("Private-site credential on hidden stdin: ") if args.private else ""
    result = verify(args.url, token, read_json(args.expected))
    write_json(args.out, result)
    print(json.dumps(result, indent=2))
