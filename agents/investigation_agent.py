"""
ThreatIQ Investigation Agent

This agent:
- Generates investigation questions from the detected evidence.
- Stores questions and answers in the incident state.
- Allows the frontend to submit user answers.
- Recalculates risk after answers are applied.

No classes are used.
No LLM is required for the investigation logic.
"""

from datetime import datetime, timezone

from core.risk_engine import calculate_risk
from core.incident_state import add_timeline_event


def get_questions(state):
    """
    Generate investigation questions based on the current incident.

    Questions are adaptive:
    only questions relevant to the detected evidence are added.
    """

    # Get extracted indicators safely.
    indicators = state.get("indicators", {})

    if not isinstance(indicators, dict):
        indicators = {}

    # Store generated questions here.
    questions = []

    # Ask about suspicious URL interaction when a URL was detected.
    if indicators.get("has_suspicious_url", False):
        questions.append(
            "Did you click or open the suspicious link?"
        )

    # Ask about credential submission when credentials were requested.
    if indicators.get("has_credential_request", False):
        questions.append(
            "Did you enter a password, OTP, verification code, "
            "or other credentials?"
        )

    # Ask about payment/financial interaction when relevant.
    if indicators.get("has_payment_request", False):
        questions.append(
            "Did you make a payment, transfer money, "
            "or provide financial information?"
        )

    # Ask about attachments for threats where attachments may be involved.
    threat_type = str(state.get("threat_type", "")).upper()

    if threat_type in {
        "PHISHING",
        "SCAM",
        "BRAND_IMPERSONATION",
    }:
        questions.append(
            "Did you open or download an attachment from this message?"
        )

        questions.append(
            "Did you provide any other sensitive information?"
        )

    return questions


def investigation_agent(state):
    """
    Add adaptive investigation questions to the incident state.

    Existing answers are preserved if this function is called again.
    """

    # Generate questions based on the current evidence.
    questions = get_questions(state)

    # Existing user actions may already contain answers.
    existing_actions = state.get("user_actions", [])

    if not isinstance(existing_actions, list):
        existing_actions = []

    # Build a lookup of previously answered questions.
    existing_answers = {}

    for action in existing_actions:
        if isinstance(action, dict):
            question = action.get("question")

            if question:
                existing_answers[question] = action.get("answer")

    # Rebuild the action list while preserving existing answers.
    state["user_actions"] = []

    for question in questions:
        state["user_actions"].append(
            {
                "question": question,
                "answer": existing_answers.get(question),
            }
        )

    # Add a timeline event.
    add_timeline_event(
        state,
        {
            "agent": "investigation",
            "event": "Adaptive investigation questions generated.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question_count": len(questions),
        },
    )

    return state


def apply_user_answers(state, answers):
    """
    Apply answers submitted by the frontend.

    The answers argument can be either:

        {
            "Did you click or open the suspicious link?": "Yes"
        }

    or:

        {
            0: "Yes",
            1: "No"
        }

    After answers are applied, risk is recalculated immediately.
    """

    # Get the current investigation questions.
    user_actions = state.get("user_actions", [])

    if not isinstance(user_actions, list):
        user_actions = []

    # Make sure answers is a dictionary.
    if not isinstance(answers, dict):
        answers = {}

    # Apply each submitted answer.
    for index, action in enumerate(user_actions):

        # Ignore malformed investigation entries.
        if not isinstance(action, dict):
            continue

        question = action.get("question")

        # First support question text as the dictionary key.
        if question in answers:
            action["answer"] = answers[question]

        # Also support question index as the dictionary key.
        elif index in answers:
            action["answer"] = answers[index]

        # Support string indexes such as "0", "1", etc.
        elif str(index) in answers:
            action["answer"] = answers[str(index)]

    # Save the updated actions back into the state.
    state["user_actions"] = user_actions

    # Recalculate the risk using the newly submitted answers.
    risk_result = calculate_risk(state)

    # Store the new risk values directly in the incident state.
    state["risk_score"] = risk_result["risk_score"]
    state["risk_level"] = risk_result["risk_level"]

    # Store the new reasons for transparent frontend display.
    indicators = state.get("indicators", {})

    if not isinstance(indicators, dict):
        indicators = {}

    indicators["risk_reasons"] = risk_result["reasons"]
    state["indicators"] = indicators

    # Add a timeline event showing that reassessment occurred.
    add_timeline_event(
        state,
        {
            "agent": "investigation",
            "event": "User answers applied and risk reassessed.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
        },
    )

    return state


if __name__ == "__main__":
    """
    Direct test for the adaptive investigation agent.
    """

    # Import the incident-state initializer.
    from core.incident_state import init_incident

    # Create a sample phishing incident.
    state = init_incident("TEST-INVESTIGATION-001")

    # Simulate indicators produced by the evidence agent.
    state["indicators"] = {
        "has_suspicious_url": True,
        "has_credential_request": True,
        "has_payment_request": False,
        "has_urgent_language": True,
    }

    # Simulate threat classification.
    state["threat_type"] = "PHISHING"

    # Generate the investigation questions.
    investigation_agent(state)

    # Record the initial risk before the user answers.
    initial_risk = calculate_risk(state)

    # Answer YES to the suspicious-link question.
    apply_user_answers(
        state,
        {
            "Did you click or open the suspicious link?": "Yes",
        },
    )

    # Read the updated risk.
    updated_risk = {
        "risk_score": state["risk_score"],
        "risk_level": state["risk_level"],
    }

    # Print verification results.
    print("Investigation Agent test successful.")
    print(f"Questions: {len(state['user_actions'])}")
    print(
        f"Initial risk: "
        f"{initial_risk['risk_score']} "
        f"({initial_risk['risk_level']})"
    )
    print(
        f"Updated risk: "
        f"{updated_risk['risk_score']} "
        f"({updated_risk['risk_level']})"
    )
    print(
        f"Risk increase: "
        f"{updated_risk['risk_score'] - initial_risk['risk_score']}"
    )
    print(
        "Answer applied:",
        state["user_actions"][0]["answer"] == "Yes",
    )
