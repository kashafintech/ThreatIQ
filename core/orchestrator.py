
"""
ThreatIQ Pipeline Orchestrator

This file controls the order in which the eight ThreatIQ agents run.

Agent order:
1. Intake
2. Evidence
3. Threat
4. Investigation
5. Correlation
6. Risk
7. Response
8. Report

It also provides a separate function for adaptive reassessment after
the user answers investigation questions.

No agent framework is used.
No classes are used.
"""

from agents.intake_agent import intake_agent
from agents.evidence_agent import evidence_agent
from agents.threat_agent import threat_agent
from agents.investigation_agent import investigation_agent
from agents.investigation_agent import apply_user_answers
from agents.correlation_agent import correlation_agent
from agents.risk_agent import risk_agent
from agents.response_agent import response_agent
from agents.report_agent import report_agent


def run_pipeline(evidence, incident_id):
    """
    Run the complete initial ThreatIQ pipeline.

    The initial pipeline runs all eight agents in the required order.
    Investigation questions are generated during this run, but no
    user answers are assumed yet.
    """

    # 1. Intake Agent
    state = intake_agent(
        evidence,
        incident_id,
    )

    # 2. Evidence Agent
    state = evidence_agent(state)

    # 3. Threat Agent
    state = threat_agent(state)

    # 4. Investigation Agent
    state = investigation_agent(state)

    # 5. Correlation Agent
    state = correlation_agent(state)

    # 6. Risk Agent
    state = risk_agent(state)

    # 7. Response Agent
    state = response_agent(state)

    # 8. Report Agent
    state = report_agent(state)

    # Return the complete incident state.
    return state


def reassess_after_investigation(state, answers):
    """
    Reassess an existing incident after the user answers
    investigation questions.

    The updated flow is:

    User answers
        ↓
    Apply answers
        ↓
    Recalculate risk
        ↓
    Risk Agent
        ↓
    Response Agent
        ↓
    Report Agent

    This makes the investigation genuinely adaptive.
    """

    # ---------------------------------------------------------------
    # 1. APPLY USER ANSWERS
    # ---------------------------------------------------------------
    state = apply_user_answers(
        state,
        answers,
    )

    # ---------------------------------------------------------------
    # 2. RUN RISK AGENT AGAIN
    # ---------------------------------------------------------------
    # The Risk Agent reads the updated user_actions and calculates
    # the new risk score.
    state = risk_agent(state)

    # ---------------------------------------------------------------
    # 3. REGENERATE RESPONSE
    # ---------------------------------------------------------------
    # Recommendations now match the updated risk level.
    state = response_agent(state)

    # ---------------------------------------------------------------
    # 4. REGENERATE REPORT
    # ---------------------------------------------------------------
    # The report now contains the updated risk and user actions.
    state = report_agent(state)

    # Return the fully updated state.
    return state


if __name__ == "__main__":
    """
    Direct test for the complete adaptive ThreatIQ pipeline.
    """

    # Sample suspicious message.
    sample_evidence = """
    Microsoft Security Alert!

    Your account will be suspended immediately.
    Verify your password here:
    https://secure-microsoft-example.com/login
    """

    # ---------------------------------------------------------------
    # RUN INITIAL PIPELINE
    # ---------------------------------------------------------------
    initial_state = run_pipeline(
        sample_evidence,
        "TEST-ORCHESTRATOR-001",
    )

    # Save the initial risk.
    initial_score = initial_state["risk_score"]
    initial_level = initial_state["risk_level"]

    # Save the number of timeline events before reassessment.
    initial_timeline_count = len(initial_state["timeline"])

    # ---------------------------------------------------------------
    # ANSWER INVESTIGATION QUESTION
    # ---------------------------------------------------------------
    updated_state = reassess_after_investigation(
        initial_state,
        {
            "Did you click or open the suspicious link?": "Yes",
        },
    )

    # Read the updated risk.
    updated_score = updated_state["risk_score"]
    updated_level = updated_state["risk_level"]

    # ---------------------------------------------------------------
    # VERIFY RESULTS
    # ---------------------------------------------------------------

    # The report agent stores the generated report under the
    # "incident_report" key.
    #
    # We therefore check that key instead of state["report"].
    report_generated = bool(
        updated_state.get("incident_report")
    )

    # Verify that the timeline increased after reassessment.
    timeline_updated = (
        len(updated_state["timeline"]) > initial_timeline_count
    )

    print("Adaptive Orchestrator test successful.")
    print(
        f"Initial risk: "
        f"{initial_score} ({initial_level})"
    )
    print(
        f"Updated risk: "
        f"{updated_score} ({updated_level})"
    )
    print(
        f"Risk change: "
        f"{updated_score - initial_score:+d}"
    )
    print(
        "Answer applied:",
        updated_state["user_actions"][0]["answer"] == "Yes",
    )
    print(
        "Report regenerated:",
        report_generated,
    )
    print(
        "Timeline updated:",
        timeline_updated,
    )