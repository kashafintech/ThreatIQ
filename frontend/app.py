"""
ThreatIQ — Streamlit Frontend

Run with:
    streamlit run frontend/app.py
"""

import sys
from pathlib import Path

import streamlit as st
from frontend.components.analysis_progress import render_analysis_progress

# Make project root importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.styles.theme import load_css
from frontend.frontend_utils.state import (
    init_state,
    get_screen,
    set_screen,
    set_evidence,
    get_evidence,
)
from frontend.components.input_panel import render_input_panel


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ThreatIQ — From Suspicion to Action",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# BOOTSTRAP
# ============================================================

load_css()
init_state()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="tq-header">
        <div>
            <div class="tq-logo"><span class="tq-logo-mark">◆</span>THREATIQ</div>
            <div class="tq-tagline">From Suspicion to Action</div>
        </div>
        <div class="tq-status">
            <span class="status-dot"></span>
            SYSTEM OPERATIONAL
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SCREEN ROUTER
# ============================================================

screen = get_screen()

if screen == "new_scan":
    evidence = render_input_panel()

    if evidence is not None:
        if evidence == "":
            st.warning("Please paste a message, email, or URL before analyzing.")
        else:
            set_evidence(evidence)
            set_screen("analysis")
            st.rerun()

elif screen == "analysis":
    render_analysis_progress()

    evidence = get_evidence()
    st.markdown('<div class="tq-card">', unsafe_allow_html=True)
    st.markdown('<div class="tq-label">Evidence Received</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-family:JetBrains Mono,monospace;font-size:13px;color:#22D3EE;word-break:break-all;">'
        f'{evidence[:300]}{"..." if evidence and len(evidence) > 300 else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.info("Backend pipeline hook-up coming next.")

    if st.button("← Start Over"):
        set_screen("new_scan")
        set_evidence(None)
        st.rerun()