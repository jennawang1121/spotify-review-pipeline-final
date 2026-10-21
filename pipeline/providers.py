"""Explicit paid transport with durable per-attempt evidence and bounded retries."""
import json
import socket
import http.client
import os
import random
import time
import threading
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .budget import BudgetLedger
from .common import ROOT, canonical, digest, read_json, write_json
from .costing import call_cost, load_rates


ENDPOINTS = {"typesafe": "https://api.typesafe.ai/v1/systemone", "openai": "https://api.openai.com/v1/responses"}


class InvalidModelOutput(ValueError):
    """Bounded attempts ended with a saved but invalid model response."""
    def __init__(self, request_id):
        super().__init__("Model output failed validation after bounded attempts: " + request_id)
        self.request_id = request_id


def credentials():
    values = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if separator and key.strip() in ("OPENAI_API_KEY", "TYPESAFE_API_KEY"):
                values[key.strip()] = value.strip().strip('"').strip("'")
    for key in ("OPENAI_API_KEY", "TYPESAFE_API_KEY"):
        values[key] = os.environ.get(key) or values.get(key, "")
    if any(not values.get(key) for key in ("OPENAI_API_KEY", "TYPESAFE_API_KEY")):
        raise ValueError("Configure OPENAI_API_KEY and TYPESAFE_API_KEY locally in spotify-pipeline/.env. Never paste keys into chat.")
    return {"openai": values["OPENAI_API_KEY"], "typesafe": values["TYPESAFE_API_KEY"]}


def billing_tokens(provider, usage):
    if not isinstance(usage, dict):
        return None
    total, output = usage.get("input_tokens"), usage.get("output_tokens")
    if type(total) is not int or type(output) is not int:
        return None
    cached = written = 0
    if provider == "openai":
        details = usage.get("input_tokens_details", {})
        cached, written = details.get("cached_tokens"), details.get("cache_write_tokens")
        # Missing categories are unresolved billing, not assumed free cache writes.
        if type(cached) is not int or type(written) is not int:
            return None
    result = {"input": total - cached - written, "cached_input": cached, "cache_write": written, "output": output}
    return result if all(value >= 0 for value in result.values()) else None


def response_json(response):
    if response.get("status") != "completed":
        raise ValueError("OpenAI response incomplete or refused.")
    parts = [part["text"] for item in response.get("output", []) if item.get("type") == "message"
             for part in item.get("content", []) if part.get("type") == "output_text"]
    if len(parts) != 1:
        raise ValueError("Expected one structured OpenAI output.")
    return json.loads(parts[0])


def schema_object(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def openai_request(config, instructions, inputs, schema):
    return {"model": config["language_model"], "reasoning": {"effort": config["reasoning_effort"]},
            "max_output_tokens": config["max_output_tokens"], "store": False,
            "instructions": instructions, "input": canonical(inputs),
            "text": {"format": {"type": "json_schema", "name": "stage_result", "strict": True, "schema": schema}}}


class DispatchLimiter:
    """One shared dispatch clock across workers and retries (two calls/s)."""
    def __init__(self):
        self.lock = threading.Lock()
        self.last = 0.0

    def wait(self, deadline):
        with self.lock:
            delay = max(0, .5 - (time.monotonic() - self.last))
            if time.monotonic() + delay >= deadline:
                raise ValueError("Run time cap reached before dispatch; resume saved results.")
            time.sleep(delay)
            self.last = time.monotonic()


class Transport:
    def __init__(self, run_dir, config, budget, phase, invocation, keys, send=None):
        self.root = Path(run_dir)
        self.config, self.phase, self.invocation, self.keys = config, phase, invocation, keys
        self.rates = load_rates(ROOT / "cost" / "rates.csv")
        self.ledger = BudgetLedger(self.root / "budget.sqlite", budget)
        self.send = send or self._http
        self.evidence_kind = "synthetic_test" if send is not None else "real_pilot"
        self.deadline = time.monotonic() + config.get("max_runtime_seconds", 900)
        self.cache_hits = 0
        self.last_request_id = None
        self.last_dispatch = 0.0
        self.limiter = DispatchLimiter()

    def _http(self, provider, payload):
        encoded = canonical(payload).encode("utf-8")
        request = urllib.request.Request(ENDPOINTS[provider], data=encoded, method="POST", headers={
            "Authorization": "Bearer " + self.keys[provider], "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read()), response.headers.get("x-request-id")

    def _reservation(self, provider, payload):
        model = payload["model"]
        prefix = (provider, model, "standard")
        if provider == "typesafe":
            return self.rates[prefix + ("input",)] * 64000
        maximum_input_rate = max(self.rates[prefix + (category,)] for category in ("input", "cached_input", "cache_write"))
        # Conservative byte upper-bound plus overhead; not an absolute provider-billing guarantee.
        return maximum_input_rate * (len(canonical(payload).encode("utf-8")) + 8192) + self.rates[prefix + ("output",)] * payload["max_output_tokens"]

    def call(self, provider, role, stage, payload, ids, validator):
        if provider not in ENDPOINTS or payload["model"] not in ("jev-1.13.0", "gpt-6-luna"):
            raise ValueError("Model/provider not allowlisted.")
        if role == "enrich" and not 1 <= len(ids) <= 50:
            raise ValueError("Enrichment requests require 1–50 original review IDs.")
        if len(canonical(payload).encode("utf-8")) > 120000:
            raise ValueError("Request exceeds the bounded payload cap; reduce evidence before dispatch.")
        fingerprint = digest(canonical([provider, role, stage, payload, self.config["label_config"]]))
        cache = self.root / "response_cache" / (fingerprint + ".json")
        if cache.exists():
            saved = read_json(cache)
            value = validator(saved["response"])
            self.last_request_id = saved["request_id"]
            self.cache_hits += 1
            return value
        invalid_retries = transient_retries = 0
        while True:
            if time.monotonic() >= self.deadline:
                raise ValueError("Run time cap reached; saved results remain available for resume.")
            self.limiter.wait(self.deadline)
            attempt_id = uuid.uuid4().hex
            reservation = self._reservation(provider, payload)
            self.ledger.reserve(attempt_id, reservation)
            request_path = self.root / "requests" / (attempt_id + ".json")
            event_path = self.root / "attempts" / (attempt_id + ".json")
            write_json(request_path, payload)
            event = {"request_id": attempt_id, "call_id": attempt_id, "run_id": self.invocation,
                     "role": role, "stage": stage, "provider": provider, "model": payload["model"],
                     "tier": "standard", "review_ids": ids, "phase": self.phase,
                     "label_config": self.config["label_config"], "schema_version": self.config["schema_version"],
                     "effort": self.config["reasoning_effort"] if provider == "openai" else None,
                     "worker_count": self.config["workers"], "batch_size": len(ids), "outcome": "in_flight",
                     "input_tokens": None, "output_tokens": None, "billing_tokens": None,
                     "raw_usage": None, "duration_seconds": 0, "evidence_kind": self.evidence_kind,
                     "reserved_usd": str(reservation), "request_artifact": str(request_path.relative_to(self.root)),
                     "started_at": datetime.now(timezone.utc).isoformat()}
            write_json(event_path, event)
            response = None
            retry = False
            delay = 0
            self.last_dispatch = started = time.monotonic()
            try:
                response, provider_id = self.send(provider, payload)
                event["provider_request_id"] = provider_id
                event["returned_model"] = response.get("model")
                event["raw_usage"] = response.get("usage")
                event["billing_tokens"] = billing_tokens(provider, response.get("usage"))
                if isinstance(response.get("usage"), dict):
                    event["input_tokens"] = response["usage"].get("input_tokens")
                    event["output_tokens"] = response["usage"].get("output_tokens")
                write_json(self.root / "responses" / (attempt_id + ".json"), response)
                value = validator(response)
                event["outcome"] = "succeeded"
            except urllib.error.HTTPError as exc:
                event["outcome"] = "failed"
                event["error"] = "HTTP " + str(exc.code)
                # Keep only provider error identifiers, never request headers,
                # credential values, or arbitrary echoed response messages.
                try:
                    error = json.loads(exc.read()).get("error", {})
                    for key in ("code", "type"):
                        value = error.get(key)
                        if isinstance(value, str) and len(value) <= 100 and all(c.isalnum() or c in "_-" for c in value):
                            event["provider_error_" + key] = value
                except (ValueError, AttributeError, TypeError):
                    pass
                quota_blocked = (event.get("provider_error_code") in
                                 ("insufficient_quota", "billing_hard_limit_reached", "credit_balance_exhausted")
                                 or event.get("provider_error_type") == "insufficient_quota")
                if not quota_blocked and exc.code in (408, 429, 500, 502, 503, 504) and transient_retries < self.config["transient_error_retries"]:
                    transient_retries += 1
                    retry = True
                    try:
                        delay = min(30.0, max(0.0, float(exc.headers.get("retry-after", 0))))
                    except (ValueError, AttributeError):
                        delay = 0
            except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, http.client.HTTPException) as exc:
                event["outcome"] = "failed"
                event["error"] = type(exc).__name__ + ": charges may be unknown"
                if transient_retries < self.config["transient_error_retries"]:
                    transient_retries += 1
                    retry = True
            except (ValueError, KeyError, TypeError) as exc:
                event["outcome"] = "failed"
                event["error"] = "invalid_response: " + type(exc).__name__
                if invalid_retries < self.config["invalid_output_retries"]:
                    invalid_retries += 1
                    retry = True
            finally:
                event["duration_seconds"] = time.monotonic() - started
                cost = call_cost(event, self.rates)
                event["calculated_usd"] = str(cost) if cost is not None else None
                if cost is not None:
                    self.ledger.settle(attempt_id, cost, event["outcome"] if event["outcome"] in ("succeeded", "failed") else "failed")
                # Unknown usage leaves the original reservation in place.
                write_json(event_path, event)
            if event["outcome"] == "succeeded":
                write_json(cache, {"request_id": attempt_id, "response": response})
                self.last_request_id = attempt_id
                return value
            if not retry:
                if event.get("error", "").startswith("invalid_response:"):
                    raise InvalidModelOutput(attempt_id)
                raise ValueError("Model task failed after bounded attempts; inspect saved attempt IDs (no keys logged).")
            time.sleep(max(delay, min(10, 2 ** transient_retries)) + random.random() * 0.2)

    def close(self):
        self.ledger.close()
