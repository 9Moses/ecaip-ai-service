from prometheus_client import Counter, Gauge, Histogram

document_extraction_total = Counter(
    "eacip_document_extraction_total",
    "Total document extraction attempts",
    ["method", "status"],
    # method: native_pdf|ocr, status: success|failure
)

ai_extraction_total = Counter(
    "eacip_ai_extraction_total",
    "Total AI structured extraction attempts",
    ["status"],
    # completed|needs_review|failed
)

fraud_flags_created_total = Counter(
    "eacip_fraud_flags_created_total",
    "Total fraud flags created",
)

llm_call_duration_seconds = Histogram(
    "eacip_llm_call_duration_seconds",
    "LLM Gateway call latency",
    ["provider", "purpose"],
    # purpose: extraction|summarization|chat|router|fraud_rationale
)

llm_call_total = Counter(
    "eacip_llm_call_total",
    "Total LLM Gateway calls",
    ["provider", "purpose", "status"],
)

queue_depth = Gauge(
    "eacip_queue_depth",
    "Approximate pending messages per queue, sampled periodically",
    ["queue_name"],
)
