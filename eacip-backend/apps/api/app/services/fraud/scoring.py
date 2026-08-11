SEVERITY_WEIGHTS = {"low": 0.05, "medium": 0.2, "high": 0.4}
FLAG_THRESHOLD = 0.4
# A single "high" finding, or two "medium" findings, is
# enough to cross the threshold —
# tuned conservatively toward false positives (a human
# reviews it either way) rather than false negatives (a
# real issue silently not flagged).


def compute_fraud_score(findings: list[dict[str, str]]) -> float:
    raw_score = sum(SEVERITY_WEIGHTS.get(f.get("severity", "low"), 0.05) for f in findings)
    return round(min(raw_score, 1.0), 2)


def should_flag(score: float) -> bool:
    return score >= FLAG_THRESHOLD
