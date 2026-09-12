"""
ThreatIQ Risk Engine

This file calculates the incident risk score using deterministic Python rules.

Important:
- No LLM is used for risk scoring.
- The score is completely explainable.
- Initial evidence indicators contribute to the score.
- User investigation answers can increase the score.
- The final score is always capped at 100.
"""


# ---------------------------------------------------------------------------
# BASE RISK RULES
# ---------------------------------------------------------------------------
# These are the original ThreatIQ scoring rules.
#
# Each detected indicator contributes a fixed number of points.
BASE_RISK_RULES = {
    "suspicious_url": 20,
    "credential_request": 20,
    "brand_impersonation": 15,
    "urgent_language": 10,
    "payment_request": 20,
    "external_reputation_warning": 25,
}


# ---------------------------------------------------------------------------
# INVESTIGATION RISK RULES
# ---------------------------------------------------------------------------
# These rules are applied after the user answers investigation questions.
#
# The purpose is to make the risk dynamic based on what actually happened.
#
# Example:
#   User clicked the suspicious URL
#       -> +10
#
#   User entered credentials
#       -> +30
#
#   User provided financial information or made a payment
#       -> +25
#
# These points are separate from the initial evidence score.
INVESTIGATION_RISK_RULES = {
    "clicked_link": 10,
    "entered_credentials": 30,
    "provided_financial_information": 25,
    "opened_attachment": 10,
    "provided_sensitive_information": 15,
}


# ---------------------------------------------------------------------------
# VALID RISK LEVELS
# ---------------------------------------------------------------------------
# Risk levels are determined entirely from the final numeric score.
RISK_LEVELS = {
    "LOW": (0, 29),
    "MEDIUM": (30, 59),
    "HIGH": (60, 79),
    "CRITICAL": (80, 100),
}


def get_risk_level(score):
    """
    Convert a numeric risk score into a ThreatIQ risk level.

    Score ranges:
        0-29   -> LOW
        30-59  -> MEDIUM
        60-79  -> HIGH
        80-100 -> CRITICAL
    """

    # Make sure the score stays inside the valid range.
    score = max(0, min(int(score), 100))

    # Check the score against every defined risk range.
    for level, (minimum, maximum) in RISK_LEVELS.items():
        if minimum <= score <= maximum:
            return level

    # This should never be reached because the score is clamped.
    return "LOW"


def _answer_is_yes(answer):
    """
    Check whether an investigation answer represents a positive response.

    Supports common answer formats:
        yes
        y
        true
        1
    """

    # Handle an actual boolean value.
    if isinstance(answer, bool):
        return answer

    # Missing answers are not treated as positive.
    if answer is None:
        return False

    # Normalize the answer.
    normalized = str(answer).strip().lower()

    # Return True for recognized positive answers.
    return normalized in {"yes", "y", "true", "1"}


def _get_investigation_answers(state):
    """
    Convert investigation answers into simple action flags.

    Returns a dictionary such as:

        {
            "clicked_link": True,
            "entered_credentials": False,
            "provided_financial_information": False,
            "opened_attachment": False,
            "provided_sensitive_information": False
        }
    """

    # Start with every action set to False.
    answers = {
        "clicked_link": False,
        "entered_credentials": False,
        "provided_financial_information": False,
        "opened_attachment": False,
        "provided_sensitive_information": False,
    }

    # Get the investigation questions/answers from the incident state.
    user_actions = state.get("user_actions", [])

    # Make sure user_actions has the expected list structure.
    if not isinstance(user_actions, list):
        return answers

    # Inspect every investigation question.
    for action in user_actions:

        # Each action should be a dictionary.
        if not isinstance(action, dict):
            continue

        # Get the question and answer safely.
        question = str(action.get("question", "")).lower()
        answer = action.get("answer")

        # Only a positive answer changes the risk.
        if not _answer_is_yes(answer):
            continue

        # Detect a clicked/opened suspicious link.
        if (
            "click" in question
            or "open the suspicious link" in question
            or "opened the suspicious link" in question
        ):
            answers["clicked_link"] = True

        # Detect credential submission.
        if (
            "password" in question
            or "credential" in question
            or "otp" in question
            or "verification code" in question
        ):
            answers["entered_credentials"] = True

        # Detect financial/payment interaction.
        if (
            "payment" in question
            or "financial information" in question
            or "transfer money" in question
            or "money" in question
        ):
            answers["provided_financial_information"] = True

        # Detect attachment interaction.
        if (
            "attachment" in question
            or "attached file" in question
        ):
            answers["opened_attachment"] = True

        # Detect sensitive-information submission.
        if (
            "sensitive information" in question
            or "personal information" in question
            or "other sensitive" in question
        ):
            answers["provided_sensitive_information"] = True

    return answers


def calculate_risk_score(state):
    """
    Calculate the complete risk score.

    Returns:
        (
            final_score,
            reasons
        )

    The reasons list explains exactly why points were added.
    """

    # Get indicators safely from the incident state.
    indicators = state.get("indicators", {})

    # Make sure indicators is a dictionary.
    if not isinstance(indicators, dict):
        indicators = {}

    # Start the score at zero.
    score = 0

    # Store every scoring reason for transparent reporting.
    reasons = []

    # -----------------------------------------------------------------------
    # BASE EVIDENCE SCORING
    # -----------------------------------------------------------------------

    # Suspicious URL: +20
    if indicators.get("has_suspicious_url", False):
        points = BASE_RISK_RULES["suspicious_url"]
        score += points

        reasons.append(
            f"Suspicious URL detected (+{points})"
        )

    # Credential request: +20
    if indicators.get("has_credential_request", False):
        points = BASE_RISK_RULES["credential_request"]
        score += points

        reasons.append(
            f"Credential request detected (+{points})"
        )

    # Brand impersonation: +15
    #
    # This is considered true when:
    # 1. The evidence agent explicitly marked it, OR
    # 2. The threat classifier identified BRAND_IMPERSONATION.
    if (
        indicators.get("has_brand_impersonation", False)
        or state.get("threat_type") == "BRAND_IMPERSONATION"
    ):
        points = BASE_RISK_RULES["brand_impersonation"]
        score += points

        reasons.append(
            f"Brand impersonation detected (+{points})"
        )

    # Urgent/threatening language: +10
    if indicators.get("has_urgent_language", False):
        points = BASE_RISK_RULES["urgent_language"]
        score += points

        reasons.append(
            f"Urgent/threatening language detected (+{points})"
        )

    # Payment request: +20
    if indicators.get("has_payment_request", False):
        points = BASE_RISK_RULES["payment_request"]
        score += points

        reasons.append(
            f"Payment request detected (+{points})"
        )

    # External reputation warning: +25
    if indicators.get("external_reputation_warning", False):
        points = BASE_RISK_RULES["external_reputation_warning"]
        score += points

        reasons.append(
            f"External reputation warning detected (+{points})"
        )

    # -----------------------------------------------------------------------
    # ADAPTIVE INVESTIGATION SCORING
    # -----------------------------------------------------------------------

    # Extract the user's investigation answers.
    investigation_answers = _get_investigation_answers(state)

    # User clicked/opened suspicious link: +10
    if investigation_answers["clicked_link"]:
        points = INVESTIGATION_RISK_RULES["clicked_link"]
        score += points

        reasons.append(
            f"User interacted with suspicious link (+{points})"
        )

    # User entered credentials: +30
    if investigation_answers["entered_credentials"]:
        points = INVESTIGATION_RISK_RULES["entered_credentials"]
        score += points

        reasons.append(
            f"User entered credentials (+{points})"
        )

    # User provided financial information or made a payment: +25
    if investigation_answers["provided_financial_information"]:
        points = INVESTIGATION_RISK_RULES[
            "provided_financial_information"
        ]
        score += points

        reasons.append(
            f"User provided financial information (+{points})"
        )

    # User opened an attachment: +10
    if investigation_answers["opened_attachment"]:
        points = INVESTIGATION_RISK_RULES["opened_attachment"]
        score += points

        reasons.append(
            f"User opened an attachment (+{points})"
        )

    # User provided sensitive information: +15
    if investigation_answers["provided_sensitive_information"]:
        points = INVESTIGATION_RISK_RULES[
            "provided_sensitive_information"
        ]
        score += points

        reasons.append(
            f"User provided sensitive information (+{points})"
        )

    # -----------------------------------------------------------------------
    # FINAL SCORE CAP
    # -----------------------------------------------------------------------

    # ThreatIQ never allows a score above 100.
    score = min(score, 100)

    return score, reasons


def calculate_risk(state):
    """
    Calculate the risk score and risk level together.

    Returns:

        {
            "risk_score": 50,
            "risk_level": "MEDIUM",
            "reasons": [...]
        }
    """

    # Calculate the deterministic score.
    score, reasons = calculate_risk_score(state)

    # Convert the score into a risk level.
    level = get_risk_level(score)

    # Return the complete risk result.
    return {
        "risk_score": score,
        "risk_level": level,
        "reasons": reasons,
    }


# ---------------------------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    # Create a sample incident containing:
    # - suspicious URL
    # - credential request
    # - urgent language
    #
    # Base score:
    # 20 + 20 + 10 = 50
    sample_state = {
        "indicators": {
            "has_suspicious_url": True,
            "has_credential_request": True,
            "has_urgent_language": True,
            "has_payment_request": False,
            "has_brand_impersonation": False,
            "external_reputation_warning": False,
        },
        "threat_type": "PHISHING",
        "user_actions": [],
    }

    # Calculate the initial risk.
    initial_result = calculate_risk(sample_state)

    # Simulate the user saying YES to:
    # "Did you click or open the suspicious link?"
    sample_state["user_actions"] = [
        {
            "question": "Did you click or open the suspicious link?",
            "answer": "Yes",
        }
    ]

    # Calculate the reassessed risk.
    updated_result = calculate_risk(sample_state)

    # Display the test results.
    print("Adaptive Risk Engine test successful.")

    print(
        f"Initial risk: "
        f"{initial_result['risk_score']} "
        f"({initial_result['risk_level']})"
    )

    print(
        f"Updated risk: "
        f"{updated_result['risk_score']} "
        f"({updated_result['risk_level']})"
    )

    print(
        f"Risk increase: "
        f"{updated_result['risk_score'] - initial_result['risk_score']}"
    )

    print(
        "User interaction detected:",
        any(
            "User interacted with suspicious link" in reason
            for reason in updated_result["reasons"]
        )
    )

