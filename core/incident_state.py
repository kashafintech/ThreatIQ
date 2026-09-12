"""
ThreatIQ incident state management.

This file contains the shared incident-state structure used by all
ThreatIQ agents.

The state intentionally uses only the required keys:

- incident_id
- evidence
- indicators
- threat_type
- risk_score
- risk_level
- user_actions
- potential_impact
- recommendations
- timeline
"""

# Import typing helpers so the functions are easier to understand
# and provide clear type information.
from typing import Any, Dict, List


def init_incident(incident_id: str) -> Dict[str, Any]:
    """
    Create and return a new ThreatIQ incident state.

    Args:
        incident_id: Unique identifier for the incident.

    Returns:
        A dictionary containing the complete initial incident state.
    """

    # Return the exact shared state structure required by ThreatIQ.
    return {
        "incident_id": incident_id,
        "evidence": [],
        "indicators": {},
        "threat_type": "",
        "risk_score": 0,
        "risk_level": "LOW",
        "user_actions": [],
        "potential_impact": "",
        "recommendations": [],
        "timeline": [],
    }


def safe_append(state: Dict[str, Any], key: str, value: Any) -> None:
    """
    Safely append a value to a list inside the incident state.

    If the requested key does not exist, it is created as an empty list.
    If the existing value is not a list, it is replaced with a list.

    Args:
        state: The shared incident state dictionary.
        key: The state key containing the list.
        value: The value to append.
    """

    # Check whether the requested key exists and contains a list.
    if not isinstance(state.get(key), list):

        # Create an empty list if the key is missing or has the wrong type.
        state[key] = []

    # Add the new value to the list.
    state[key].append(value)


def safe_extend(
    state: Dict[str, Any],
    key: str,
    values: List[Any],
) -> None:
    """
    Safely add multiple values to a list inside the incident state.

    Args:
        state: The shared incident state dictionary.
        key: The state key containing the list.
        values: Multiple values to add.
    """

    # Check whether the requested key exists and contains a list.
    if not isinstance(state.get(key), list):

        # Create an empty list if necessary.
        state[key] = []

    # Add all supplied values to the existing list.
    state[key].extend(values)


def add_evidence(
    state: Dict[str, Any],
    evidence: Any,
) -> None:
    """
    Add evidence to the incident.

    Args:
        state: The shared incident state dictionary.
        evidence: Evidence collected from the user submission.
    """

    # Safely append the evidence to the evidence list.
    safe_append(state, "evidence", evidence)


def add_timeline_event(
    state: Dict[str, Any],
    event: Any,
) -> None:
    """
    Add an event to the incident timeline.

    Args:
        state: The shared incident state dictionary.
        event: Timeline event information.
    """

    # Safely append the event to the timeline list.
    safe_append(state, "timeline", event)


def update_risk(
    state: Dict[str, Any],
    score: int,
    level: str,
) -> None:
    """
    Update the incident risk score and risk level.

    The score is always kept between 0 and 100.

    Args:
        state: The shared incident state dictionary.
        score: Calculated risk score.
        level: Risk level such as LOW, MEDIUM, HIGH, or CRITICAL.
    """

    # Convert the score to an integer.
    score = int(score)

    # Prevent the score from going below 0.
    if score < 0:
        score = 0

    # Prevent the score from going above 100.
    if score > 100:
        score = 100

    # Normalize the risk level so it is consistently uppercase.
    level = str(level).upper().strip()

    # Define the only valid ThreatIQ risk levels.
    valid_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    # If an invalid level is supplied, calculate the level from the score.
    if level not in valid_levels:

        # Scores from 0 to 29 are LOW.
        if score < 30:
            level = "LOW"

        # Scores from 30 to 59 are MEDIUM.
        elif score < 60:
            level = "MEDIUM"

        # Scores from 60 to 79 are HIGH.
        elif score < 80:
            level = "HIGH"

        # Scores from 80 to 100 are CRITICAL.
        else:
            level = "CRITICAL"

    # Store the final validated score.
    state["risk_score"] = score

    # Store the final validated risk level.
    state["risk_level"] = level