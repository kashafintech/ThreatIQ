
"""
ThreatIQ Risk Agent

This agent is responsible for:
- Calculating the incident risk score.
- Determining the risk level.
- Storing transparent risk reasons.
- Updating the incident timeline.

The actual scoring logic lives in core/risk_engine.py.
The Risk Agent only coordinates that logic and stores the result.
"""

from datetime import datetime, timezone

from core.incident_state import update_risk, add_timeline_event
from core.risk_engine import calculate_risk


def risk_agent(state):
    """
    Calculate and store the current incident risk.

    This function can be called:
    1. During the initial pipeline.
    2. Again after investigation answers are submitted.

    Because calculate_risk() reads the current user_actions,
    calling this function after user answers automatically
    produces the updated risk score.
    """

    # Calculate the current risk using the pure-Python risk engine.
    risk_result = calculate_risk(state)

    # Extract the calculated score.
    risk_score = risk_result["risk_score"]

    # Extract the calculated risk level.
    risk_level = risk_result["risk_level"]

    # Update the main incident-state risk fields.
    update_risk(
        state,
        risk_score,
        risk_level,
    )

    # Get the current indicators dictionary.
    indicators = state.get("indicators", {})

    # Make sure indicators is always a dictionary.
    if not isinstance(indicators, dict):
        indicators = {}

    # Store the exact reasons used by the risk engine.
    # The frontend can display these to make the score transparent.
    indicators["risk_reasons"] = risk_result["reasons"]

    # Save the updated indicators.
    state["indicators"] = indicators

    # Record the risk calculation in the timeline.
    add_timeline_event(
        state,
        {
            "agent": "risk",
            "event": "Risk score calculated.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_score": risk_score,
            "risk_level": risk_level,
        },
    )

    # Return the updated incident state.
    return state


if __name__ == "__main__":
    """
    Direct test for the Risk Agent.
    """

    # Import the incident-state initializer.
    from core.incident_state import init_incident

    # Create a sample incident.
    state = init_incident("TEST-RISK-001")

    # Simulate evidence indicators.
    state["indicators"] = {
        "has_suspicious_url": True,
        "has_credential_request": True,
        "has_payment_request": True,
        "has_urgent_language": True,
        "has_brand_mention": True,
    }

    # Simulate a classified threat.
    state["threat_type"] = "PHISHING"

    # Run the Risk Agent.
    risk_agent(state)

    # Verify the results.
    print("Risk Agent test successful.")
    print(f"Risk score: {state['risk_score']}")
    print(f"Risk level: {state['risk_level']}")
    print(f"Risk reasons: {len(state['indicators']['risk_reasons'])}")
    print(f"Timeline events: {len(state['timeline'])}")