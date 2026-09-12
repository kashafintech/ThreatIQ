"""
ThreatIQ Validators

This file contains simple validation functions used to check:
- Incident IDs
- Evidence
- Risk scores
- Risk levels
- Complete incident state dictionaries

No classes are used.
No LLM is used.
"""

# Required top-level fields for every ThreatIQ incident state.
REQUIRED_STATE_FIELDS = {
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

# Only these four risk levels are valid in ThreatIQ.
VALID_RISK_LEVELS = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}


def validate_incident_id(incident_id):
    """
    Check whether an incident ID is a non-empty string.
    """

    return isinstance(incident_id, str) and bool(incident_id.strip())


def validate_evidence(evidence):
    """
    Check whether submitted evidence is a non-empty string.
    """

    return isinstance(evidence, str) and bool(evidence.strip())


def validate_risk_score(score):
    """
    Check whether a risk score is an integer between 0 and 100.

    bool is explicitly rejected because Python treats True/False as integers.
    """

    return (
        isinstance(score, int)
        and not isinstance(score, bool)
        and 0 <= score <= 100
    )


def validate_risk_level(level):
    """
    Check whether the risk level is one of:
    LOW, MEDIUM, HIGH, or CRITICAL.
    """

    return (
        isinstance(level, str)
        and level.upper() in VALID_RISK_LEVELS
    )


def validate_required_state_fields(state):
    """
    Check whether the incident state contains every required top-level field.

    Returns:
        (True, []) when all fields exist.
        (False, [error messages]) when fields are missing.
    """

    # The state must first be a dictionary.
    if not isinstance(state, dict):
        return False, ["Incident state must be a dictionary."]

    # Find every required field that is missing.
    missing_fields = [
        field
        for field in REQUIRED_STATE_FIELDS
        if field not in state
    ]

    # Convert missing fields into readable error messages.
    errors = [
        f"Missing required field: {field}"
        for field in sorted(missing_fields)
    ]

    return len(errors) == 0, errors


def validate_incident_state(state):
    """
    Validate the complete ThreatIQ incident state.

    Returns:
        (True, []) when the state is valid.
        (False, [error messages]) when validation fails.
    """

    # Start with an empty list of validation errors.
    errors = []

    # First make sure the state itself is a dictionary.
    if not isinstance(state, dict):
        return False, ["Incident state must be a dictionary."]

    # Check that every required field exists.
    fields_valid, field_errors = validate_required_state_fields(state)
    errors.extend(field_errors)

    # If required fields are missing, do not try to validate
    # their individual values.
    if not fields_valid:
        return False, errors

    # Validate the incident ID.
    if not validate_incident_id(state["incident_id"]):
        errors.append("incident_id must be a non-empty string.")

    # Evidence inside the incident state is stored as a list
    # of evidence records.
    if not isinstance(state["evidence"], list):
        errors.append("evidence must be a list.")

    # Indicators are stored as a dictionary.
    if not isinstance(state["indicators"], dict):
        errors.append("indicators must be a dictionary.")

    # Threat type should always be a string.
    if not isinstance(state["threat_type"], str):
        errors.append("threat_type must be a string.")

    # Validate the calculated risk score.
    if not validate_risk_score(state["risk_score"]):
        errors.append("risk_score must be an integer between 0 and 100.")

    # Validate the calculated risk level.
    if not validate_risk_level(state["risk_level"]):
        errors.append(
            "risk_level must be LOW, MEDIUM, HIGH, or CRITICAL."
        )

    # User actions are stored as a list of questions and answers.
    if not isinstance(state["user_actions"], list):
        errors.append("user_actions must be a list.")

    # Potential impact is stored as text.
    if not isinstance(state["potential_impact"], str):
        errors.append("potential_impact must be a string.")

    # Recommendations are stored as a list of actions.
    if not isinstance(state["recommendations"], list):
        errors.append("recommendations must be a list.")

    # Timeline events are stored as a list.
    if not isinstance(state["timeline"], list):
        errors.append("timeline must be a list.")

    # The state is valid only when there are no errors.
    return len(errors) == 0, errors


# Direct test for this file.
if __name__ == "__main__":
    # Import the incident-state initializer.
    from core.incident_state import init_incident

    # Create a valid ThreatIQ incident state.
    valid_state = init_incident("TEST-VALIDATION-001")

    # Validate the state.
    is_valid, validation_errors = validate_incident_state(valid_state)

    # Test invalid evidence.
    invalid_evidence_result = validate_evidence("")

    # Test an invalid risk score.
    invalid_score_result = validate_risk_score(150)

    # Print the test results.
    print("Validators test successful.")
    print(f"Valid state: {is_valid}")
    print(f"Validation errors: {len(validation_errors)}")
    print(f"Invalid evidence accepted: {invalid_evidence_result}")
    print(f"Invalid risk score accepted: {invalid_score_result}")
