from app.services.ai_extraction.inconsistency_rules import check_claim_form, check_invoice


def test_claim_form_flags_incident_after_filing_date():
    findings = check_claim_form(
        {
            "incident_date": "2026-03-01",
            "filing_date": "2026-01-01",
            "claimed_amount": 500,
            "claim_number": "C-1",
        }
    )
    assert any(f["field"] == "incident_date" for f in findings)


def test_claim_form_clean_data_has_no_findings():
    findings = check_claim_form(
        {
            "incident_date": "2026-01-01",
            "filing_date": "2026-01-05",
            "claimed_amount": 500,
            "claim_number": "C-1",
        }
    )
    assert findings == []


def test_invoice_flags_negative_total():
    findings = check_invoice({"total_amount": -100, "invoice_number": "INV-1"})
    assert any(f["field"] == "total_amount" for f in findings)
