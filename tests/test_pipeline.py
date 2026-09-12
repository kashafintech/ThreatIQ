"""
ThreatIQ Pipeline Tests

This file verifies that the main ThreatIQ pipeline works correctly.

The tests cover:
1. Complete pipeline execution.
2. Required incident-state fields.
3. Threat classification.
4. Risk scoring.
5. Response recommendations.
6. Final incident report generation.

Run this file with:
    python -m tests.test_pipeline
"""


# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
from core.orchestrator import run_pipeline


# ---------------------------------------------------------------------------
# TEST EVIDENCE
# ---------------------------------------------------------------------------
# This example contains several indicators that should be detected:
# - suspicious URL
# - Microsoft brand
# - urgent language
# - credential request
TEST_EVIDENCE = (
    "URGENT! Your Microsoft account will be suspended immediately. "
    "Verify your account at "
    "https://secure-microsoft-example.com/login "
    "and enter your password and OTP."
)


# ---------------------------------------------------------------------------
# TEST 1: COMPLETE PIPELINE
# ---------------------------------------------------------------------------
def test_complete_pipeline():
    """
    Verify that all eight agents execute successfully.
    """

    # Run the complete ThreatIQ pipeline.
    state = run_pipeline(
        evidence=TEST_EVIDENCE,
        incident_id="TEST-FULL-001",
    )

    # Make sure the incident ID is preserved.
    assert state["incident_id"] == "TEST-FULL-001"

    # Make sure threat classification happened.
    assert state["threat_type"] == "PHISHING"

    # Make sure a risk score was calculated.
    assert isinstance(state["risk_score"], int)

    # Make sure the risk level is one of the valid levels.
    assert state["risk_level"] in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    # Make sure investigation questions were generated.
    assert len(state["user_actions"]) > 0

    # Make sure response recommendations were generated.
    assert len(state["recommendations"]) > 0

    # Make sure the final report exists.
    assert isinstance(state.get("incident_report"), str)
    assert len(state["incident_report"]) > 0

    # Make sure the pipeline recorded timeline events.
    assert len(state["timeline"]) >= 8


# ---------------------------------------------------------------------------
# TEST 2: REQUIRED STATE FIELDS
# ---------------------------------------------------------------------------
def test_required_state_fields():
    """
    Verify that all required top-level incident-state fields exist.
    """

    # Run the pipeline.
    state = run_pipeline(
        evidence=TEST_EVIDENCE,
        incident_id="TEST-STATE-001",
    )

    # These are the required ThreatIQ state fields.
    required_fields = {
        "incident_id",
        "evidence",
        "indicators",
        "threat_type",
        "risk_score",
        "risk_level",
        "user_actions",
        "potential_impact",
        "recommendations",
        "timeline",
    }

    # Make sure every required field exists.
    for field in required_fields:
        assert field in state, f"Missing required field: {field}"


# ---------------------------------------------------------------------------
# TEST 3: EVIDENCE EXTRACTION
# ---------------------------------------------------------------------------
def test_evidence_extraction():
    """
    Verify that important indicators are extracted from the evidence.
    """

    # Run the pipeline.
    state = run_pipeline(
        evidence=TEST_EVIDENCE,
        incident_id="TEST-EVIDENCE-001",
    )

    # Get extracted indicators.
    indicators = state["indicators"]

    # Verify the URL was detected.
    assert indicators["has_suspicious_url"] is True

    # Verify the credential request was detected.
    assert indicators["has_credential_request"] is True

    # Verify urgent language was detected.
    assert indicators["has_urgent_language"] is True

    # Verify the Microsoft brand was detected.
    assert "microsoft" in indicators["brands"]


# ---------------------------------------------------------------------------
# TEST 4: RISK SCORE
# ---------------------------------------------------------------------------
def test_risk_score():
    """
    Verify that the deterministic risk engine calculates the expected score.

    For this evidence:
        suspicious URL       = +20
        credential request   = +20
        urgent language      = +10

    Total:
        50

    Therefore:
        Risk level = MEDIUM
    """

    # Run the pipeline.
    state = run_pipeline(
        evidence=TEST_EVIDENCE,
        incident_id="TEST-RISK-001",
    )

    # Verify the exact score.
    assert state["risk_score"] == 50

    # Verify the corresponding risk level.
    assert state["risk_level"] == "MEDIUM"


# ---------------------------------------------------------------------------
# TEST 5: RESPONSE
# ---------------------------------------------------------------------------
def test_response():
    """
    Verify that the Response Agent provides recommendations.
    """

    # Run the pipeline.
    state = run_pipeline(
        evidence=TEST_EVIDENCE,
        incident_id="TEST-RESPONSE-001",
    )

    # Recommendations must be stored as a list.
    assert isinstance(state["recommendations"], list)

    # There must be at least one recommendation.
    assert len(state["recommendations"]) > 0

    # The selected playbook should also be recorded.
    assert state["indicators"].get("response_playbook") != ""


# ---------------------------------------------------------------------------
# TEST 6: REPORT
# ---------------------------------------------------------------------------
def test_report():
    """
    Verify that the Report Agent creates a readable incident report.
    """

    # Run the pipeline.
    state = run_pipeline(
        evidence=TEST_EVIDENCE,
        incident_id="TEST-REPORT-001",
    )

    # Get the generated report.
    report = state["incident_report"]

    # Verify that important report sections exist.
    assert "THREATIQ INCIDENT REPORT" in report
    assert "Incident ID: TEST-REPORT-001" in report
    assert "Threat Type: PHISHING" in report
    assert "Risk Score: 50/100" in report
    assert "Risk Level: MEDIUM" in report
    assert "RECOMMENDATIONS" in report
    assert "TIMELINE" in report


# ---------------------------------------------------------------------------
# RUN ALL TESTS
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Run every test manually.

    This avoids requiring pytest for the basic project verification.
    """

    # Run each test function.
    test_complete_pipeline()
    test_required_state_fields()
    test_evidence_extraction()
    test_risk_score()
    test_response()
    test_report()

    # If execution reaches this point, every test passed.
    print("All ThreatIQ pipeline tests passed successfully.")
