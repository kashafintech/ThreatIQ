# frontend/app.py
# ThreatIQ — single-file Streamlit frontend
# Run with: python -m streamlit run frontend/app.py (from project root)
#
# Screen flow:
#   scan → analysis → result → investigation → response → report
# ============================================================

import sys
import os
import uuid
import time
from datetime import datetime

import streamlit as st

# ---------------------------------------------------------------------------
# Path fix: allow imports from project root (agents/, core/, utils/)
# when Streamlit is launched from any working directory.
# ---------------------------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------------------------
# Backend imports — wrapped so a missing module gives a clear error message
# rather than a raw traceback.
# ---------------------------------------------------------------------------
try:
    from core.orchestrator import run_pipeline, reassess_after_investigation
    BACKEND_AVAILABLE = True
except Exception as _backend_import_err:
    BACKEND_AVAILABLE = False
    _BACKEND_ERR_MSG = str(_backend_import_err)


# ============================================================
# PAGE CONFIG  (must be the very first Streamlit call)
# ============================================================
st.set_page_config(
    page_title="ThreatIQ",
    page_icon="◆",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# THEME — injected once as a <style> block
# ============================================================
def apply_theme():

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #21262d;
    --border: #30363d;
    --border-accent: #1f6feb;
    --text: #c9d1d9;
    --text-muted: #8b949e;
    --accent: #58a6ff;
    --blue: #238636;
    --radius: 8px;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header, .stAppHeader { display: none !important; }

.block-container {
    max-width: 850px !important;
    padding: 2rem 1.5rem 4rem !important;
}

/* Glassmorphic Container Cards */
.stMarkdown div[style*="background:#fff"], 
.stMarkdown div[style*="background: #fff"],
.stMarkdown div[style*="background: white"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--border-accent) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
}

/* Fix text colors inside cards */
.stMarkdown div[style*="color:#6E7681"], 
.stMarkdown div[style*="color: #6E7681"] {
    color: var(--text-muted) !important;
}

.stMarkdown div[style*="color:#0F172A"], 
.stMarkdown div[style*="color: #0F172A"] {
    color: var(--text) !important;
}

/* Monospace text for logs and code */
code, pre, .stTextArea textarea, .stTextInput input {
    font-family: 'JetBrains Mono', monospace !important;
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}

/* Buttons Styling */
.stButton > button {
    background: #1f6feb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 0 10px rgba(31, 111, 235, 0.3) !important;
}

.stButton > button:hover {
    background: #388bfd !important;
    box-shadow: 0 0 15px rgba(56, 139, 253, 0.6) !important;
}

/* Status Indicator Dot Glow */
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.95); }
}

.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #3fb950;
    border-radius: 50%;
    box-shadow: 0 0 8px #3fb950;
    animation: pulse 2s infinite;
    margin-right: 6px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE INIT
# ============================================================
def initialize_session_state():
    defaults = {
        "screen":          "scan",       # current screen
        "incident_state":  None,         # full backend state dict
        "incident_id":     None,         # e.g. TQ-0001
        "evidence_text":   "",           # raw evidence submitted
        "answers":         {},           # {question_text: answer}
        "questions":       [],           # list of question strings
        "q_index":         0,            # which question we're on
        "prev_risk_score": None,         # score before last reassessment
        "prev_risk_level": None,
        "reassess_done":   False,        # have we called reassess yet?
        "error_msg":       None,         # surface-level error to display
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_scan():
    """Clear all incident data and return to scan screen."""
    keys_to_clear = [
        "screen", "incident_state", "incident_id",
        "evidence_text", "answers", "questions",
        "q_index", "prev_risk_score", "prev_risk_level",
        "reassess_done", "error_msg",
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()


def go_to(screen: str):
    st.session_state["screen"] = screen
    st.rerun()


# ============================================================
# SHARED HELPERS
# ============================================================
def risk_color(level: str) -> str:
    return {
        "LOW": "#238636",
        "MEDIUM": "#d29922",
        "HIGH": "#db6d28",
        "CRITICAL": "#f85149",
    }.get(str(level).upper(), "#8b949e")

def risk_bg(level: str) -> str:
    return {
        "LOW": "rgba(35, 134, 54, 0.15)",
        "MEDIUM": "rgba(210, 153, 34, 0.15)",
        "HIGH": "rgba(219, 109, 40, 0.15)",
        "CRITICAL": "rgba(248, 81, 73, 0.15)",
    }.get(str(level).upper(), "rgba(139, 148, 158, 0.15)")

def render_risk_badge(level: str):
    color = risk_color(level)
    bg = risk_bg(level)
    st.markdown(
        f'<span style="display:inline-block;padding:6px 14px;border-radius:20px;'
        f'background:{bg};color:{color};font-size:12px;font-weight:700;'
        f'border:1px solid {color};letter-spacing:0.08em;box-shadow:0 0 10px {bg};">{level.upper()}</span>',
        unsafe_allow_html=True,
    )

def render_risk_bar(score: int, level: str):
    color = risk_color(level)
    pct = min(max(int(score), 0), 100)
    st.markdown(
        f"""
        <div style="background:#21262d;border-radius:8px;height:10px;overflow:hidden;margin:12px 0;">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:8px;box-shadow:0 0 8px {color};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_start():
    """Open a white card container."""
    st.markdown(
        '<div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;'
        'padding:24px;box-shadow:0 1px 3px rgba(15,23,42,0.06);margin-bottom:16px;">',
        unsafe_allow_html=True,
    )


def card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def render_header(show_new_scan=True):
    """Persistent top header."""
    col_logo, col_right = st.columns([1, 1])
    with col_logo:
        st.markdown(
            '<p style="font-size:15px;font-weight:700;letter-spacing:-0.01em;'
            'color:#0F172A;margin:0;">◆ THREATIQ</p>',
            unsafe_allow_html=True,
        )
    with col_right:
        if show_new_scan:
            if st.button("← New Scan", key="hdr_new_scan"):
                reset_scan()
        else:
            st.markdown(
                '<p style="text-align:right;font-size:12px;color:#94A3B8;margin:0;">'
                '<span class="status-dot"></span>SYSTEM OPERATIONAL</p>',
                unsafe_allow_html=True,
            )
    st.markdown('<hr style="margin:12px 0 24px;">', unsafe_allow_html=True)


# ============================================================
# SCREEN 1 — NEW SCAN
# ============================================================
def render_scan_screen():
    render_header(show_new_scan=False)

    # Hero
    st.markdown(
        '<h1 style="font-size:36px;font-weight:700;letter-spacing:-0.03em;'
        'color:#0F172A;margin-bottom:6px;">Investigate suspicious evidence.</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-size:15px;color:#64748B;max-width:540px;line-height:1.6;">'
        'AI-powered cybersecurity investigation that extracts indicators, classifies threats, '
        'correlates evidence, calculates a transparent risk score, and tells you exactly what to do next.'
        '</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    # Evidence type tabs
    tab_msg, tab_url, tab_img = st.tabs(["Message / Email", "URL", "Screenshot"])

    evidence_to_submit = None
    submit_label = "Analyze Threat"

    with tab_msg:
        msg_input = st.text_area(
            "Paste the suspicious message or email",
            height=180,
            placeholder="Paste the full message or email body here…",
            key="input_msg",
            label_visibility="collapsed",
        )
        st.write("")
        if st.button(submit_label, key="btn_analyze_msg"):
            evidence_to_submit = msg_input.strip()

    with tab_url:
        url_input = st.text_input(
            "Enter the suspicious URL",
            placeholder="https://suspicious-example.com/login",
            key="input_url",
            label_visibility="collapsed",
        )
        st.write("")
        if st.button(submit_label, key="btn_analyze_url"):
            evidence_to_submit = url_input.strip()

    with tab_img:
        st.caption("Upload a screenshot of the suspicious content.")
        uploaded = st.file_uploader(
            "Screenshot",
            type=["png", "jpg", "jpeg", "webp"],
            key="input_img",
            label_visibility="collapsed",
        )
        st.write("")
        if st.button(submit_label, key="btn_analyze_img"):
            if uploaded is not None:
                # Extract filename and any readable text from file name as evidence hint
                # The backend works with text evidence; we surface the filename as context.
                evidence_to_submit = (
                    f"[Screenshot submitted: {uploaded.name}] "
                    "User uploaded a screenshot for analysis. "
                    "Please analyze any visible threat indicators."
                )
            else:
                st.warning("Please upload a screenshot first.")

    # ── Validation & transition ───────────────────────────────
    if evidence_to_submit is not None:
        if len(evidence_to_submit) < 4:
            st.warning("Please provide more detail so we can analyze the evidence.")
        else:
            st.session_state["evidence_text"] = evidence_to_submit
            st.session_state["incident_id"]   = generate_incident_id()
            st.session_state["screen"]        = "analysis"
            st.rerun()

    # Footer note
    st.write("")
    st.markdown(
        '<p style="font-size:12px;color:#94A3B8;margin-top:24px;">'
        '🔒 Evidence is analyzed locally. Nothing is stored or transmitted externally.'
        '</p>',
        unsafe_allow_html=True,
    )


# ============================================================
# SCREEN 2 — LIVE ANALYSIS
# ============================================================
_STAGES = [
    ("Intake",         "Evidence received"),
    ("Evidence",       "Indicators extracted"),
    ("Threat",         "Threat classification complete"),
    ("Investigation",  "Investigating evidence patterns"),
    ("Correlation",    "Correlating indicators"),
    ("Risk",           "Calculating risk score"),
    ("Response",       "Preparing response actions"),
    ("Report",         "Generating incident report"),
]


def render_analysis_screen():
    render_header(show_new_scan=True)

    incident_id = st.session_state.get("incident_id", "TQ-??????")
    evidence    = st.session_state.get("evidence_text", "")

    st.markdown(
        f'<h2 style="font-size:22px;font-weight:700;color:#0F172A;">Analyzing evidence</h2>'
        f'<p style="font-size:13px;color:#94A3B8;font-family:\'JetBrains Mono\',monospace;">'
        f'Incident {incident_id}</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    # Show backend unavailable error immediately
    if not BACKEND_AVAILABLE:
        st.error(
            f"Backend could not be loaded. Please check your installation.\n\n"
            f"Error: {_BACKEND_ERR_MSG}"
        )
        if st.button("← Return to Scan"):
            reset_scan()
        return

    # ── Progress display + real backend call ─────────────────
    progress_placeholder = st.empty()
    status_placeholder   = st.empty()

    def render_progress(done_count: int, active_idx: int):
        """Render the checklist of stages with done/active/pending states."""
        html = '<div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:24px;">'
        for i, (agent, label) in enumerate(_STAGES):
            if i < done_count:
                icon  = "✓"
                color = "#059669"
                weight = "500"
            elif i == active_idx:
                icon  = "●"
                color = "#2563EB"
                weight = "600"
            else:
                icon  = "○"
                color = "#94A3B8"
                weight = "400"
            html += (
                f'<div style="display:flex;align-items:center;gap:12px;'
                f'padding:9px 0;border-bottom:1px solid #F1F5F9;">'
                f'<span style="color:{color};font-size:15px;width:18px;">{icon}</span>'
                f'<span style="font-size:14px;font-weight:{weight};color:{color};">{label}</span>'
                f'<span style="margin-left:auto;font-size:11px;color:#CBD5E1;'
                f'font-family:\'JetBrains Mono\',monospace;">{agent.upper()}</span>'
                f'</div>'
            )
        html += "</div>"
        progress_placeholder.markdown(html, unsafe_allow_html=True)

    # Animate stages while backend runs in background
    # We tick through stages quickly and let the real call finish
    render_progress(0, 0)

    try:
        # Show animated stages while the backend processes.
        # We use a short delay per stage for UX — backend runs synchronously.
        # The progress animation is cosmetic; results are real.
        for i in range(len(_STAGES)):
            render_progress(i, i)
            status_placeholder.caption(f"Running {_STAGES[i][0]} agent…")
            time.sleep(0.25)   # cosmetic delay — real work happens in run_pipeline below

        # ── REAL BACKEND CALL ─────────────────────────────────
        state = run_pipeline(evidence, incident_id)

        # Mark all done
        render_progress(len(_STAGES), -1)
        status_placeholder.empty()

        # Validate returned state
        required_keys = ["risk_score", "risk_level", "threat_type"]
        for key in required_keys:
            if key not in state:
                raise ValueError(f"Backend returned incomplete state — missing '{key}'")

 st.session_state["incident_state"] = state

        # Extract questions for Screen 4
        user_actions = state.get("user_actions", [])
        if isinstance(user_actions, list):
            questions = [
                q if isinstance(q, str) else q.get("question", str(q))
                for q in user_actions
            ]
        else:
            questions = []
        st.session_state["questions"] = questions
        st.session_state["q_index"]   = 0
        st.session_state["answers"]   = {}

        time.sleep(0.5)  # brief pause so user sees "all done"
        go_to("result")

    except Exception as err:
        progress_placeholder.empty()
        status_placeholder.empty()
        print(f"[ThreatIQ] Backend error: {err}")   # log to terminal
        st.session_state["error_msg"] = str(err)
        go_to("error")


# ============================================================
# SCREEN — ERROR
# ============================================================
def render_error_screen():
    render_header(show_new_scan=True)
    st.error("Analysis failed — the backend returned an error.")
    err = st.session_state.get("error_msg", "Unknown error.")
    with st.expander("Error details (for debugging)"):
        st.code(err, language="text")
    st.write("")
    if st.button("← Start a New Scan"):
        reset_scan()


# ============================================================
# SCREEN 3 — THREAT RESULT
# ============================================================
# ============================================================
# SCREEN 3 — THREAT RESULT
# ============================================================
def render_result_screen():
    render_header(show_new_scan=True)

    state = st.session_state.get("incident_state")
    if not state:
        st.warning("No analysis results found. Please run a new scan.")
        if st.button("← New Scan"):
            reset_scan()
        return

    score = int(state.get("risk_score", 0))
    level = str(state.get("risk_level", "UNKNOWN")).upper()
    threat_type = state.get("threat_type", "Unknown Threat")
    color = risk_color(level)

    # ── Top SOC Metrics (3 Columns Layout) ──────────────────────
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;">Risk Score</div>
                <div style="font-size:32px;font-weight:700;color:{color};">{score}<span style="font-size:14px;color:#8b949e;font-weight:400;"> / 100</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">Severity</div>
                <span style="display:inline-block;padding:4px 12px;border-radius:20px;background:{risk_bg(level)};color:{color};font-size:12px;font-weight:700;border:1px solid {color};">{level}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:11px;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;">Threat Category</div>
                <div style="font-size:14px;font-weight:700;color:#c9d1d9;margin-top:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{threat_type}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_risk_bar(score, level)
    st.write("")

    # ── Why we detected this (Indicators Section) ───────────────
    indicators = state.get("indicators", {})
    risk_reasons = indicators.get("risk_reasons", []) if isinstance(indicators, dict) else []

    if risk_reasons:
        st.markdown(
            '<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px 24px;margin-bottom:16px;">'
            '<p style="font-size:11px;font-weight:600;color:#8b949e;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:14px;">Why we detected this</p>',
            unsafe_allow_html=True,
        )
        for reason in risk_reasons:
            if isinstance(reason, dict):
                pts = reason.get("score", "")
                label = reason.get("reason", "")
                value = reason.get("value", "")
            elif isinstance(reason, str):
                pts, label, value = "", reason, ""
            else:
                continue

            pts_str = f"+{pts}" if pts else ""
            val_html = (
                f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:12px;'
                f'color:#58a6ff;background:#21262d;padding:3px 8px;border-radius:4px;border:1px solid #30363d;">'
                f'{value}</span>'
            ) if value else ""

            st.markdown(
                f"""
                <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #21262d;">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:600;color:#d29922;min-width:40px;">{pts_str}</span>
                    <span style="font-size:13px;color:#c9d1d9;flex:1;">{label}</span>
                    {val_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    elif indicators:
        with st.expander("Detected Indicators"):
            if isinstance(indicators, dict):
                for k, v in indicators.items():
                    if v and k != "risk_reasons":
                        st.text(f"{k}: {v}")
            else:
                st.text(str(indicators))

    # ── Potential Impact Section ────────────────────────────────
    potential_impact = state.get("potential_impact", [])
    if potential_impact:
        st.markdown(
            '<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px 24px;margin-bottom:16px;">'
            '<p style="font-size:11px;font-weight:600;color:#8b949e;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:12px;">Potential Impact</p>',
            unsafe_allow_html=True,
        )
        if isinstance(potential_impact, list):
            for item in potential_impact:
                st.markdown(
                    f"""
                    <div style="display:flex;gap:10px;align-items:flex-start;padding:6px 0;font-size:13px;color:#c9d1d9;">
                        <span style="color:#f85149;margin-top:1px;">▸</span>
                        <span>{item}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.write(str(potential_impact))
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # ── Navigation Buttons ──────────────────────────────────────
    questions = st.session_state.get("questions", [])
    if questions:
        if st.button("Continue Investigation →", key="btn_continue_investigation"):
            go_to("investigation")
    else:
        if st.button("View Response Plan →", key="btn_skip_to_response"):
            go_to("response")
      # Store state and move to result
        st.se

# ============================================================
# SCREEN 4 — ADAPTIVE INVESTIGATION
# ============================================================
def render_investigation_screen():
    render_header(show_new_scan=True)

    state     = st.session_state.get("incident_state")
    questions = st.session_state.get("questions", [])
    answers   = st.session_state.get("answers", {})
    q_index   = st.session_state.get("q_index", 0)

    if not state:
        st.warning("Session expired. Please start a new scan.")
        reset_scan()
        return

    score = int(state.get("risk_score", 0))
    level = str(state.get("risk_level", "UNKNOWN")).upper()
    color = risk_color(level)

    # ── Header: current risk ──────────────────────────────────
    st.markdown(
        '<p style="font-size:11px;font-weight:600;color:#94A3B8;'
        'letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">'
        'Current Risk</p>',
        unsafe_allow_html=True,
    )
    col_score, col_badge = st.columns([3, 1])
    with col_score:
        st.markdown(
            f'<span style="font-size:40px;font-weight:700;color:{color};'
            f'letter-spacing:-0.03em;">{score}</span>'
            f'<span style="font-size:20px;color:#94A3B8;font-weight:400;"> / 100</span>',
            unsafe_allow_html=True,
        )
    with col_badge:
        st.write("")
        render_risk_badge(level)

    render_risk_bar(score, level)
    st.write("")

    # ── Question history timeline ─────────────────────────────
    if answers:
        st.markdown(
            '<p style="font-size:11px;font-weight:600;color:#94A3B8;'
            'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;">'
            'Investigation History</p>',
            unsafe_allow_html=True,
        )
        for q_text, ans in answers.items():
            ans_color = {
                "YES": "#DC2626", "NO": "#059669", "NOT SURE": "#D97706"
            }.get(ans.upper(), "#64748B")
            st.markdown(
                f'<div style="display:flex;align-items:flex-start;gap:10px;'
                f'padding:7px 0;border-bottom:1px solid #F1F5F9;font-size:13px;">'
                f'<span style="color:#CBD5E1;margin-top:4px;">●</span>'
                f'<span style="flex:1;color:#64748B;">{q_text}</span>'
                f'<span style="font-weight:700;color:{ans_color};">{ans}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.write("")

    # ── All questions done ────────────────────────────────────
    if q_index >= len(questions):
        # Run reassessment if not yet done
        if not st.session_state.get("reassess_done") and answers:
            try:
                updated_state = reassess_after_investigation(state, answers)
                prev_score = score
                prev_level = level
                st.session_state["incident_state"]  = updated_state
                st.session_state["prev_risk_score"] = prev_score
                st.session_state["prev_risk_level"] = prev_level
                st.session_state["reassess_done"]   = True
                st.rerun()
            except Exception as err:
                print(f"[ThreatIQ] Reassessment error: {err}")
                st.session_state["reassess_done"] = True
                st.rerun()
        else:
            # Show final risk transition
            prev_score = st.session_state.get("prev_risk_score")
            prev_level = st.session_state.get("prev_risk_level")
            new_state  = st.session_state.get("incident_state", state)
            new_score  = int(new_state.get("risk_score", score))
            new_level  = str(new_state.get("risk_level", level)).upper()

            if prev_score is not None and prev_score != new_score:
                delta      = new_score - prev_score
                delta_sign = "↑" if delta > 0 else "↓"
                delta_col  = "#DC2626" if delta > 0 else "#059669"
                st.markdown(
                    f'<div style="background:#fff;border:1px solid #E2E8F0;'
                    f'border-left:3px solid {risk_color(new_level)};'
                    f'border-radius:10px;padding:20px 24px;margin-bottom:16px;">'
                    f'<p style="font-size:12px;font-weight:700;color:#94A3B8;'
                    f'letter-spacing:0.08em;margin-bottom:12px;">RISK UPDATED</p>'
                    f'<div style="display:flex;align-items:center;gap:24px;">'
                    f'<div><div style="font-size:11px;color:#94A3B8;">Previous</div>'
                    f'<div style="font-size:22px;font-weight:700;color:{risk_color(prev_level)};">'
                    f'{prev_score} <span style="font-size:13px;">{prev_level}</span></div></div>'
                    f'<div style="font-size:20px;color:#CBD5E1;">→</div>'
                    f'<div><div style="font-size:11px;color:#94A3B8;">Updated</div>'
                    f'<div style="font-size:22px;font-weight:700;color:{risk_color(new_level)};">'
                    f'{new_score} <span style="font-size:13px;">{new_level}</span></div></div>'
                    f'<div style="margin-left:auto;">'
                    f'<span style="font-size:18px;font-weight:700;color:{delta_col};">'
                    f'{delta_sign} {abs(delta)}</span></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("Risk score unchanged based on your answers.")

            st.write("")
            if st.button("View Response Plan →", key="btn_to_response"):
                go_to("response")
        return

    # ── Current question ──────────────────────────────────────
    question = questions[q_index]

    st.markdown(
        f'<div style="background:#fff;border:1px solid #E2E8F0;'
        f'border-left:3px solid #2563EB;border-radius:10px;padding:24px;margin-bottom:20px;">'
        f'<p style="font-size:11px;font-weight:600;color:#94A3B8;'
        f'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">'
        f'Question {q_index + 1} of {len(questions)}</p>'
        f'<p style="font-size:17px;font-weight:600;color:#0F172A;line-height:1.5;margin:0;">'
        f'{question}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_yes, col_no, col_ns = st.columns(3)

    def record_answer(ans: str):
        st.session_state["answers"][question] = ans
        st.session_state["q_index"] = q_index + 1
        st.rerun()

    with col_yes:
        if st.button("YES", key=f"yes_{q_index}"):
            record_answer("YES")
    with col_no:
        if st.button("NO", key=f"no_{q_index}"):
            record_answer("NO")
    with col_ns:
        if st.button("NOT SURE", key=f"ns_{q_index}"):
            record_answer("NOT SURE")


# ============================================================
# SCREEN 5 — RESPONSE ACTIONS
# ============================================================
def render_response_screen():
    render_header(show_new_scan=True)

    state = st.session_state.get("incident_state")
    if not state:
        st.warning("No analysis results found.")
        reset_scan()
        return

    score   = int(state.get("risk_score", 0))
    level   = str(state.get("risk_level", "UNKNOWN")).upper()
    threat  = state.get("threat_type", "Unknown Threat")
    color   = risk_color(level)

    # Summary bar
    st.markdown(
        f'<div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;'
        f'padding:16px 20px;margin-bottom:20px;display:flex;gap:32px;align-items:center;">'
        f'<div><span style="font-size:11px;color:#94A3B8;">Risk Score</span><br>'
        f'<span style="font-size:22px;font-weight:700;color:{color};">{score}/100</span></div>'
        f'<div><span style="font-size:11px;color:#94A3B8;">Level</span><br>'
        f'<span style="font-size:14px;font-weight:700;color:{color};">{level}</span></div>'
        f'<div><span style="font-size:11px;color:#94A3B8;">Threat</span><br>'
        f'<span style="font-size:14px;font-weight:600;color:#0F172A;">{threat}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<h2 style="font-size:20px;font-weight:700;color:#0F172A;margin-bottom:4px;">'
        'What you should do now</h2>'
        '<p style="font-size:14px;color:#64748B;margin-bottom:20px;">'
        'These actions are personalized to this incident. Follow them in order.</p>',
        unsafe_allow_html=True,
    )

    recommendations = state.get("recommendations", [])

    if not recommendations:
        st.info("No specific recommendations were returned for this incident.")
    else:
        # Open card container
        st.markdown(
            '<div style="background:#fff;border:1px solid #E2E8F0;'
            'border-radius:10px;padding:8px 24px;margin-bottom:16px;">',
            unsafe_allow_html=True,
        )
        for i, rec in enumerate(recommendations, 1):
            rec_text = rec if isinstance(rec, str) else rec.get("action", str(rec))
            rec_meta = rec.get("priority", "") if isinstance(rec, dict) else ""
            meta_html = (
                f'<div style="font-size:11px;color:#94A3B8;margin-top:3px;">{rec_meta}</div>'
            ) if rec_meta else ""

            st.markdown(
                f'<div style="display:flex;gap:16px;align-items:flex-start;'
                f'padding:14px 0;border-bottom:1px solid #F8FAFC;">'
                f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:12px;'
                f'font-weight:700;color:#2563EB;background:#EFF6FF;min-width:30px;'
                f'height:30px;border-radius:6px;display:flex;align-items:center;'
                f'justify-content:center;flex-shrink:0;">{i:02d}</div>'
                f'<div style="font-size:14px;color:#0F172A;line-height:1.55;">'
                f'{rec_text}{meta_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    if st.button("Generate Incident Report →", key="btn_gen_report"):
        go_to("report")


# ============================================================
# SCREEN 6 — INCIDENT REPORT
# ============================================================
def render_report_screen():
    render_header(show_new_scan=True)

    state = st.session_state.get("incident_state")
    if not state:
        st.warning("No analysis results found.")
        reset_scan()
        return

    incident_id = state.get("incident_id", st.session_state.get("incident_id", "N/A"))
    score       = int(state.get("risk_score", 0))
    level       = str(state.get("risk_level", "UNKNOWN")).upper()
    threat      = state.get("threat_type", "Unknown")
    color       = risk_color(level)
    now         = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    st.markdown(
        '<h2 style="font-size:22px;font-weight:700;color:#0F172A;margin-bottom:4px;">'
        'Incident Report</h2>'
        f'<p style="font-size:13px;color:#94A3B8;font-family:\'JetBrains Mono\',monospace;">'
        f'Generated {now}</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    # ── Meta block ────────────────────────────────────────────
    meta_rows = [
        ("Incident ID",  incident_id),
        ("Threat Type",  threat),
        ("Risk Score",   f"{score} / 100"),
        ("Risk Level",   level),
        ("Generated",    now),
    ]
    st.markdown(
        '<div style="background:#fff;border:1px solid #E2E8F0;border-radius:10px;'
        'padding:8px 24px;margin-bottom:12px;">',
        unsafe_allow_html=True,
    )
    for key, val in meta_rows:
        val_color = color if key == "Risk Level" else "#0F172A"
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:10px 0;border-bottom:1px solid #F8FAFC;">'
            f'<span style="font-size:13px;color:#64748B;">{key}</span>'
            f'<span style="font-size:13px;font-weight:600;color:{val_color};'
            f'font-family:\'JetBrains Mono\',monospace;">{val}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Sections ──────────────────────────────────────────────
    def report_section(title, content):
        if not content:
            return
        with st.expander(title, expanded=True):
            if isinstance(content, list):
                for item in content:
                    st.markdown(f"• {item}")
            elif isinstance(content, dict):
                for k, v in content.items():
                    st.markdown(f"**{k}:** {v}")
            else:
                st.write(str(content))

    indicators = state.get("indicators", {})
    if isinstance(indicators, dict):
        ind_display = {k: v for k, v in indicators.items() if v and k != "risk_reasons"}
    else:
        ind_display = indicators

    report_section("Detected Indicators",   ind_display)
    report_section("User Actions",          state.get("user_actions", []))
    report_section("Potential Impact",      state.get("potential_impact", []))
    report_section("Recommendations",       state.get("recommendations", []))
    report_section("Investigation Timeline", state.get("timeline", []))

    # ── Full generated report ─────────────────────────────────
    incident_report = state.get("incident_report", "")
    if incident_report:
        with st.expander("Full AI-Generated Report", expanded=False):
            st.markdown(str(incident_report))

        st.write("")
        # Download as plain text
        st.download_button(
            label="Download Report (.txt)",
            data=str(incident_report),
            file_name=f"ThreatIQ_{incident_id}_report.txt",
            mime="text/plain",
            key="btn_download_report",
        )
    else:
        # Fallback: build a minimal text report from state
        fallback_text = _build_fallback_report(state, incident_id, now)
        st.download_button(
            label="Download Report (.txt)",
            data=fallback_text,
            file_name=f"ThreatIQ_{incident_id}_report.txt",
            mime="text/plain",
            key="btn_download_fallback",
        )

    st.write("")
    if st.button("Start New Investigation", key="btn_new_investigation"):
        reset_scan()


def _build_fallback_report(state: dict, incident_id: str, timestamp: str) -> str:
    """Build a plain-text report from state fields when incident_report is absent."""
    lines = [
        "=" * 60,
        "THREATIQ INCIDENT REPORT",
        "=" * 60,
        f"Incident ID:  {incident_id}",
        f"Generated:    {timestamp}",
        f"Threat Type:  {state.get('threat_type', 'N/A')}",
        f"Risk Score:   {state.get('risk_score', 'N/A')} / 100",
        f"Risk Level:   {state.get('risk_level', 'N/A')}",
        "",
        "INDICATORS",
        "-" * 40,
    ]
    indicators = state.get("indicators", {})
    if isinstance(indicators, dict):
        for k, v in indicators.items():
            if v:
                lines.append(f"  {k}: {v}")
    lines += [
        "",
        "POTENTIAL IMPACT",
        "-" * 40,
    ]
    for item in (state.get("potential_impact", []) or []):
        lines.append(f"  • {item}")
    lines += [
        "",
        "RECOMMENDATIONS",
        "-" * 40,
    ]
    for rec in (state.get("recommendations", []) or []):
        lines.append(f"  • {rec if isinstance(rec, str) else rec.get('action', str(rec))}")
    lines += [
        "",
        "TIMELINE",
        "-" * 40,
    ]
    for event in (state.get("timeline", []) or []):
        lines.append(f"  {event}")
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


# ============================================================
# MAIN ROUTER
# ============================================================
def main():
    apply_theme()
    initialize_session_state()

    screen = st.session_state.get("screen", "scan")

    if screen == "scan":
        render_scan_screen()
    elif screen == "analysis":
        render_analysis_screen()
    elif screen == "result":
        render_result_screen()
    elif screen == "investigation":
        render_investigation_screen()
    elif screen == "response":
        render_response_screen()
    elif screen == "report":
        render_report_screen()
    elif screen == "error":
        render_error_screen()
    else:
        render_scan_screen()


if __name__ == "__main__" or True:
    main()
