"""Prepare Jev requests OFFLINE; no HTTP client or API key is loaded here."""
import math


def build_request(review_text, config):
    if not review_text.strip():
        raise ValueError("Empty reviews are quarantined, not sent to a model.")
    if len(review_text.encode("utf-8")) > config["max_input_bytes"]:
        raise ValueError("Review exceeds the draft input byte cap; route explicitly, never silently truncate.")
    taxonomy = config["taxonomy"]
    shared = config["prompts"]["enrichment"]
    questions = {}
    for field, instruction in (
        ("topic", "Choose the highest-impact specific problem; first mentioned on a tie. For praise choose the first specific praised feature, or other for general praise. Premium-only controls are billing; paying customers' playback failures remain playback."),
        ("intent", "Select by precedence: cancellation > complaint > request > praise > unclear. Leaving, uninstalling or threats to leave are cancellation. Mixed praise/criticism is complaint. A bare boycott slogan is unclear without product criticism or personal departure."),
        ("severity", "Select supported impact, not anger or cancellation intent. Missing context does not justify inventing blocked function. A costly plan alone is not serious financial harm."),
    ):
        # Jev question IDs are not visible to its model, so name the field in instructions.
        questions[field] = {"type": "choice", "instructions": shared + " " + instruction,
                            "criteria": taxonomy[field]}
    questions["sentiment"] = {
        "type": "score", "instructions": shared + " Rate the sentiment expressed in the review.",
        "criteria": taxonomy["sentiment"],
    }
    questions["needs_review"] = {
        "type": "choice", "instructions": shared + " Does missing context, ambiguity or unsupported language prevent a reliable interpretation?",
        "criteria": {"yes": "Interpretation needs review because evidence or language is unclear.",
                     "no": "The text provides a clear supported interpretation."},
    }
    return {"model": config["classifier_model"], "state": {"review_text": review_text},
            "questions": questions}


def parse_labels(response, config):
    """Partial labels only: never mark complete before evidence/entity extraction."""
    if response["model"] != config["classifier_model"]:
        raise ValueError("Unexpected Jev model version.")
    answers = response["answers"]
    if set(answers) != {"topic", "intent", "severity", "sentiment", "needs_review"}:
        raise ValueError("Missing or unexpected Jev question IDs.")
    result = {}
    for field in ("topic", "intent", "severity", "sentiment", "needs_review"):
        answer = answers[field]
        expected_type = "score" if field == "sentiment" else "choice"
        if answer.get("type") != expected_type:
            raise ValueError("Unexpected Jev answer type.")
        confidence = answer.get("confidence")
        if type(confidence) not in (int, float) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Invalid confidence.")
        probabilities = answer.get("probabilities", {})
        expected = set(str(i) for i in range(5)) if field == "sentiment" else {"yes", "no"} if field == "needs_review" else set(config["taxonomy"][field])
        if set(probabilities) != expected or any(
            type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1
            for p in probabilities.values()
        ):
            raise ValueError("Invalid probability distribution.")
        # Live Jev responses round each probability to two decimal places.
        # Permit only the corresponding accumulated rounding error; retain raw
        # values unchanged and continue rejecting materially unnormalized output.
        rounded = all(abs(p - round(p, 2)) < 1e-10 for p in probabilities.values())
        tolerance = 0.005 * len(probabilities) + 1e-9 if rounded else 0.001
        if abs(sum(probabilities.values()) - 1) > tolerance:
            raise ValueError("Invalid probability distribution.")
        if field == "sentiment":
            score = answer.get("score")
            if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 4:
                raise ValueError("Invalid sentiment score.")
            result[field] = score / 2 - 1
        else:
            choice = answer.get("choice")
            if choice not in expected:
                raise ValueError("Invalid choice.")
            result[field] = int(choice) if field == "severity" else choice == "yes" if field == "needs_review" else choice
    return {"labels": result, "raw_answers": answers, "usage": response.get("usage"),
            "status": "awaiting_evidence_and_entities"}
