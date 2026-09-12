"""
ThreatIQ Correlation Agent.

The Correlation Agent connects the indicators and investigation results
already collected in the incident state.

It looks for relationships such as:

- Suspicious URL + credential request
- Brand mention + suspicious URL
- Urgent language + credential request
- Payment request + impersonated brand
- Multiple suspicious indicators appearing together

This agent does not calculate the final risk score.
The Risk Agent handles scoring later.
"""

# Import typing helpers for the incident-state dictionary.
from typing import Any, Dict, List


def correlate_indicators(
    state: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Find relationships between extracted indicators.

    Args:
        state: Shared ThreatIQ incident state.

    Returns:
        A list of correlated security findings.
    """

    # Get the indicators extracted by the Evidence Agent.
    indicators = state.get("indicators", {})

    # Create a list for correlated findings.
    correlations: List[Dict[str, Any]] = []

    # Check whether the evidence contains both a URL and a
    # credential request.
    if (
        indicators.get("has_suspicious_url")
        and indicators.get("has_credential_request")
    ):
        correlations.append(
            {
                "type": "url_credential_correlation",
                "description": (
                    "A suspicious URL is combined with a request "
                    "for credentials."
                ),
            }
        )

    # Check whether a known brand was mentioned together with
    # a suspicious URL.
    if (
        indicators.get("has_brand_mention")
        and indicators.get("has_suspicious_url")
    ):
        correlations.append(
            {
                "type": "brand_url_correlation",
                "description": (
                    "A known brand is mentioned while the evidence "
                    "contains a suspicious URL."
                ),
            }
        )

    # Check whether urgent language is combined with a credential
    # request.
    if (
        indicators.get("has_urgent_language")
        and indicators.get("has_credential_request")
    ):
        correlations.append(
            {
                "type": "urgency_credential_correlation",
                "description": (
                    "Urgent language is combined with a request "
                    "for credentials."
                ),
            }
        )

    # Check whether urgent language is combined with a payment
    # request.
    if (
        indicators.get("has_urgent_language")
        and indicators.get("has_payment_request")
    ):
        correlations.append(
            {
                "type": "urgency_payment_correlation",
                "description": (
                    "Urgent language is combined with a request "
                    "for payment or financial information."
                ),
            }
        )

    # Check whether a brand is mentioned together with a payment
    # request.
    if (
        indicators.get("has_brand_mention")
        and indicators.get("has_payment_request")
    ):
        correlations.append(
            {
                "type": "brand_payment_correlation",
                "description": (
                    "A known brand is associated with a request "
                    "for payment or financial information."
                ),
            }
        )

    # Check whether the user actually interacted with the evidence.
    user_actions = state.get("user_actions", [])

    # Count answered actions that indicate potentially risky interaction.
    interaction_count = 0

    # Process every investigation answer.
    for action in user_actions:

        # Get the user's answer.
        answer = action.get("answer")

        # Convert the answer to lowercase text.
        answer_text = str(answer).strip().lower()

        # Count clearly affirmative answers.
        if answer_text in {
            "yes",
            "y",
            "true",
            "clicked",
            "opened",
        }:
            interaction_count += 1

    # Add a correlation when the user interacted with the evidence.
    if interaction_count > 0:
        correlations.append(
            {
                "type": "user_interaction_correlation",
                "description": (
                    "The user reported interacting with the "
                    "suspicious content."
                ),
            }
        )

    # Return all discovered relationships.
    return correlations


def correlation_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Correlate evidence and investigation results.

    Args:
        state: Shared ThreatIQ incident state.

    Returns:
        Updated incident state.
    """

    # Find relationships between the available indicators.
    correlations = correlate_indicators(state)

    # Store correlations inside the indicators dictionary.
    #
    # The shared state keeps indicators as a flexible dictionary,
    # so this does not require adding another top-level state key.
    state.setdefault("indicators", {})[
        "correlations"
    ] = correlations

    # Record the correlation step in the timeline.
    state.setdefault("timeline", []).append(
        {
            "agent": "correlation",
            "event": (
                f"Found {len(correlations)} indicator correlations."
            ),
        }
    )

    # Return the updated incident state.
    return state


if __name__ == "__main__":
    """
    Run a direct test when this file is executed as a module.
    """

    # Import the previous agents required to build a realistic state.
    from agents.intake_agent import intake_agent
    from agents.evidence_agent import evidence_agent
    from agents.threat_agent import threat_agent
    from agents.investigation_agent import investigation_agent
    from agents.investigation_agent import apply_user_answers

    # Create realistic suspicious evidence.
    test_evidence = (
        "URGENT! Your Microsoft account will be suspended today. "
        "Verify your password immediately at "
        "https://secure-microsoft-example.com/login."
    )

    # Run the Intake Agent.
    test_state = intake_agent(
        evidence=test_evidence,
        incident_id="TEST-CORRELATION-001",
    )

    # Extract indicators.
    test_state = evidence_agent(test_state)

    # Classify the threat.
    test_state = threat_agent(test_state)

    # Generate investigation questions.
    test_state = investigation_agent(test_state)

    # Simulate the user confirming that they clicked the link.
    test_state = apply_user_answers(
        test_state,
        {
            "Did you click or open the suspicious link?": "yes",
        },
    )

    # Run the Correlation Agent.
    test_state = correlation_agent(test_state)

    # Get the resulting correlations.
    correlations = test_state["indicators"]["correlations"]

    # Confirm successful execution.
    print("Correlation Agent test successful.")

    # Display the number of correlations found.
    print(
        f"Correlations found: "
        f"{len(correlations)}"
    )

    # Display each correlation.
    for correlation in correlations:
        print(
            f"- {correlation['type']}: "
            f"{correlation['description']}"
        )