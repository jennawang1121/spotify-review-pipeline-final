"""Offline billing arithmetic. All Decimal amounts are USD, never inferred usage."""
import csv
from collections import defaultdict
from decimal import Decimal


CATEGORIES = ("input", "cached_input", "cache_write", "output")


def number(value):
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        raise ValueError("Costs, rates and durations must be finite and nonnegative.")
    return result


def load_rates(path):
    rates = {}
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["currency"] != "USD" or row["category"] not in CATEGORIES:
                raise ValueError("Expected USD rates in supported billing categories.")
            if row["unit_tokens"] != "1000000" or not row["source_url"] or not row["checked_on"]:
                raise ValueError("Rates need per-million units, a source URL and a checked date.")
            key = (row["provider"], row["model"], row["tier"], row["category"])
            if key in rates:
                raise ValueError("Duplicate price key.")
            rates[key] = number(row["usd_per_unit"]) / Decimal(1000000)
    return rates


def call_cost(call, rates):
    """billing_tokens partitions input; output INCLUDES any billed reasoning tokens.

    Raw provider usage must also be retained by the future live runner. Unknown
    usage or missing rates returns None, never a fabricated zero charge.
    """
    units = call.get("billing_tokens")
    if units is None:
        return None
    if set(units) != set(CATEGORIES) or any(type(v) is not int or v < 0 for v in units.values()):
        raise ValueError("Provide all four mutually exclusive, nonnegative integer billing categories.")
    total = Decimal(0)
    for category in CATEGORIES:
        key = (call["provider"], call["model"], call["tier"], category)
        if units[category] and key not in rates:
            return None
        total += units[category] * rates.get(key, Decimal(0))
    return total


def replay(calls, rates, measurement):
    stages = defaultdict(lambda: {"known_usd": Decimal(0), "unknown_attempts": 0,
                                  "attempts": 0, "summed_call_seconds": Decimal(0),
                                  "billing_tokens": {key: 0 for key in CATEGORIES}})
    seen = set()
    for call in calls:
        if call["call_id"] in seen:
            raise ValueError("Duplicate attempted call ID: " + call["call_id"])
        seen.add(call["call_id"])
        stage = stages[call["stage"]]
        stage["attempts"] += 1
        stage["summed_call_seconds"] += number(call["duration_seconds"])
        cost = call_cost(call, rates)
        if cost is None:
            stage["unknown_attempts"] += 1
        else:
            stage["known_usd"] += cost
        if call.get("billing_tokens") is not None:
            for key in CATEGORIES:
                stage["billing_tokens"][key] += call["billing_tokens"][key]
    known = sum((row["known_usd"] for row in stages.values()), Decimal(0))
    unknown = sum(row["unknown_attempts"] for row in stages.values())
    inputs, completed = measurement["input_records"], measurement["completed_records"]
    if type(inputs) is not int or inputs < 0 or type(completed) is not int or not 0 <= completed <= inputs:
        raise ValueError("Invalid pilot counts.")
    wall = number(measurement["wall_seconds"])
    for row in stages.values():
        row["known_usd"] = str(row["known_usd"])
        row["summed_call_seconds"] = str(row["summed_call_seconds"])
    return {
        "evidence_kind": measurement["evidence_kind"], "measurement": measurement,
        "known_api_usd": str(known), "unknown_charge_attempts": unknown,
        "total_api_usd": None if unknown else str(known), "stages": dict(stages),
        "api_usd_per_1000_inputs": str(known * 1000 / inputs) if inputs and not unknown else None,
        "api_usd_per_completed": str(known / completed) if completed and not unknown else None,
        "completed_per_second": str(Decimal(completed) / wall) if wall else None,
        "local_compute_usd": measurement.get("local_compute_usd"),
        "notes": ["Summed call durations are not end-to-end wall time.",
                  "Reasoning already billed in output must not be added again.",
                  "Incomplete charge coverage makes total API spend unknown."]}


def project(report, scenario):
    """Explicit stage denominators; fixed overhead counted once. One-worker time model.

    Stage costs include the pilot's attempts; attempts_multiplier is a RELATIVE
    stress factor, not a second charge for pilot retries. Unmeasured stages fail
    closed when their projected work is nonzero.
    """
    total = Decimal(0)
    serial = Decimal(0)
    unknown = []
    details = {}
    for stage, policy in scenario["stages"].items():
        units = number(policy["projected_units"])
        denominator = number(policy["pilot_units"])
        multiplier = number(policy.get("attempts_multiplier", 1))
        measured = report["stages"].get(stage)
        if units == 0:
            details[stage] = {"projected_usd": "0", "projected_units": "0"}
            continue
        if not denominator or not measured or measured["unknown_attempts"]:
            unknown.append(stage)
            details[stage] = {"projected_usd": None, "reason": "No fully priced pilot measurement for this stage"}
            continue
        factor = units / denominator * multiplier
        cost = number(measured["known_usd"]) * factor
        seconds = number(measured["summed_call_seconds"]) * factor
        total += cost
        serial += seconds
        details[stage] = {"projected_usd": str(cost), "projected_units": str(units),
                          "factor": str(factor), "modeled_serial_call_seconds": str(seconds)}
    # Refuse silently dropping a paid pilot stage from a full-run scenario.
    unknown.extend(stage for stage in report["stages"] if stage not in scenario["stages"])
    budget = number(scenario["budget_usd"])
    return {"name": scenario["name"], "source_rows": scenario["source_rows"],
            "stages": details, "known_projected_api_usd": str(total),
            "projected_api_usd": None if unknown else str(total), "unmodeled_stages": sorted(set(unknown)),
            "budget_usd": str(budget), "exceeds_budget": True if total > budget else None if unknown else False,
            "modeled_serial_call_seconds": None if unknown else str(serial),
            "time_note": "Model of summed API durations for ONE worker only; excludes queueing/local overhead. Not measured full-run wall time.",
            "evidence_kind": report["evidence_kind"]}

