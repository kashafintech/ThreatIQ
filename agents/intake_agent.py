"""
ThreatIQ Intake Agent.

The Intake Agent receives the user's original submission and creates
the initial incident state.

It accepts:
- A suspicious URL
- An email
- A message
- Other text-based evidence

The agent keeps the input in the shared incident state and records
when the incident entered the ThreatIQ pipeline.
"""

# Import datetime so we can record when the incident was created.
from datetime import datetime, timezone

# Import Any and Dict for flexible incident-state dictionaries.
from typing import Any, Dict

# Import the incident-state helper functions.
from core.incident_state import (
    add_evidence,
    add_timeline_event,
    init_incident,
)


def intake_agent(
    evidence: Any,
    incident_id: str,
) -> Dict[str, Any]:
    """
    Create the initial ThreatIQ incident state.

    Args:
        evidence: User-submitted suspicious content.
        incident_id: Unique identifier for this incident.

    Returns:
        The initialized incident state.
    """

    # Create a fresh incident state using the shared state structure.
    state = init_incident(incident_id)

    # Store the original user submission as evidence.
    add_evidence(
        state,
        {
            "source": "user_submission",
            "content": evidence,
        },
    )

    # Create a UTC timestamp for the incident timeline.
    timestamp = datetime.now(timezone.utc).isoformat()

    # Record that the evidence was received by the Intake Agent.
    add_timeline_event(
        state,
        {
            "timestamp": timestamp,
            "agent": "intake",
            "event": "Evidence received and incident initialized.",
        },
    )

    # Return the shared state for the next ThreatIQ agent.
    return state


if __name__ == "__main__":
    """
    Run a small direct test when this file is executed directly.
    """

    # Create sample suspicious evidence for testing.
    test_evidence = (
        "Your account will be suspended today. "
        "Verify your password immediately: "
        "https://example.com/login"
    )

    # Create an incident using the test evidence.
    test_state = intake_agent(
        evidence=test_evidence,
        incident_id="TEST-INTAKE-001",
    )

    # Confirm that the Intake Agent worked correctly.
    print("Intake Agent test successful.")

    # Print the generated incident ID.
    print(f"Incident ID: {test_state['incident_id']}")

    # Print the number of evidence items stored.
    print(f"Evidence items: {len(test_state['evidence'])}")

    # Print the number of timeline events recorded.
    print(f"Timeline events: {len(test_state['timeline'])}")