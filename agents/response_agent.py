
"""
ThreatIQ Response Agent

This agent:
1. Reads the final risk level.
2. Selects the appropriate response playbook.
3. Stores recommended actions in the incident state.
4. Adds a timeline event.

The response actions come from response_playbooks.json.
No LLM is required for this agent.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# FILE PATH
# ---------------------------------------------------------------------------
# Build the path to the response playbooks relative to the project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLAYBOOK_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "knowledge_base",
    "response_playbooks.json",
)


# ---------------------------------------------------------------------------
# LOAD RESPONSE PLAYBOOKS
# ---------------------------------------------------------------------------
def load_response_playbooks() -> List[Dict[str, Any]]:
    """
    Load all response playbooks from the JSON knowledge base.
    """

    # Open the JSON file using UTF-8 encoding.
    with open(PLAYBOOK_PATH, "r", encoding="utf-8") as file:
        playbooks = json.load(file)

    # Make sure the loaded data is a list.
    if not isinstance(playbooks, list):
        raise ValueError("Response playbooks must be stored as a list.")

    return playbooks


# ---------------------------------------------------------------------------
# FIND PLAYBOOK
# ---------------------------------------------------------------------------
def get_playbook_for_level(
    risk_level: str,
    playbooks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Find the playbook matching the incident's risk level.
    """

    # Normalize the requested risk level.
    normalized_level = str(risk_level).upper().strip()

    # Search through every available playbook.
    for playbook in playbooks:

        # Compare the playbook level with the incident level.
        if str(playbook.get("level", "")).upper().strip() == normalized_level:
            return playbook

    # Return an empty result if no matching playbook exists.
    return {}


# ---------------------------------------------------------------------------
# RESPONSE AGENT
# ---------------------------------------------------------------------------
def response_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Select response recommendations based on the current risk level.
    """

    # Get the current risk level from the incident state.
    risk_level = state.get("risk_level", "LOW")

    # Load the response playbooks.
    playbooks = load_response_playbooks()

    # Find the playbook matching the risk level.
    playbook = get_playbook_for_level(risk_level, playbooks)

    # Get recommended actions from the selected playbook.
    actions = playbook.get("actions", [])

    # Make sure actions are stored as a list.
    if not isinstance(actions, list):
        actions = [str(actions)]

    # Store the recommended actions in the required state field.
    state["recommendations"] = actions.copy()

    # Store the playbook explanation separately so the report agent
    # can use it when creating the incident report.
    state.setdefault("indicators", {})
    state["indicators"]["response_playbook"] = playbook.get("id", "")
    state["indicators"]["response_guidance"] = playbook.get("text", "")

    # Create a UTC timestamp for the timeline.
    timestamp = datetime.now(timezone.utc).isoformat()

    # Record the Response Agent activity.
    state.setdefault("timeline", [])
    state["timeline"].append(
        {
            "timestamp": timestamp,
            "agent": "response",
            "event": (
                f"Response playbook selected for {risk_level} risk."
            ),
        }
    )

    # Return the updated incident state.
    return state


# ---------------------------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Simple standalone test.

    A CRITICAL risk level should select the CRITICAL response playbook.
    """

    # Import the incident-state initializer.
    from core.incident_state import init_incident

    # Create a test incident.
    test_state = init_incident("TEST-RESPONSE-001")

    # Simulate a CRITICAL risk assessment.
    test_state["risk_score"] = 90
    test_state["risk_level"] = "CRITICAL"

    # Run the Response Agent.
    result = response_agent(test_state)

    # Print verification information.
    print("Response Agent test successful.")
    print(f"Risk level: {result['risk_level']}")
    print(f"Recommendations: {len(result['recommendations'])}")
    print(
        f"Playbook: "
        f"{result['indicators']['response_playbook']}"
    )
    print(f"Timeline events: {len(result['timeline'])}")

