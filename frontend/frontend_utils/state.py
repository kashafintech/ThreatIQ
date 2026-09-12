"""
ThreatIQ — Session State Helpers

Central place to read/write Streamlit session_state.
Every component uses these helpers so we never touch
st.session_state directly from random places.
"""

import streamlit as st


# ============================================================
# DEFAULT STATE
# ============================================================

_DEFAULTS = {
    "screen": "new_scan",       # new_scan | analysis | result | investigation | report
    "evidence": None,
    "incident": None,
    "question_id": None,
    "answers": {},
}


def init_state():
    """Ensure every expected key exists in session_state."""
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# READERS
# ============================================================

def get_screen() -> str:
    return st.session_state.get("screen", "new_scan")


def get_evidence():
    return st.session_state.get("evidence")


def get_incident():
    return st.session_state.get("incident")


def get_answers() -> dict:
    return st.session_state.get("answers", {})


# ============================================================
# WRITERS
# ============================================================

def set_screen(name: str):
    st.session_state["screen"] = name


def set_evidence(evidence: str):
    st.session_state["evidence"] = evidence


def set_incident(incident: dict):
    st.session_state["incident"] = incident


def record_answer(question_id: str, answer: str):
    answers = st.session_state.get("answers", {})
    answers[question_id] = answer
    st.session_state["answers"] = answers


def reset_investigation():
    """Start a fresh investigation."""
    st.session_state["screen"] = "new_scan"
    st.session_state["evidence"] = None
    st.session_state["incident"] = None
    st.session_state["question_id"] = None
    st.session_state["answers"] = {}