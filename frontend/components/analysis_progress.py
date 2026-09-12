"""
ThreatIQ — Analysis Progress

Screen 2: Live Analysis.

Renders a progressive checklist that plays while the
backend pipeline runs. Uses a placeholder technique so
each step appears one at a time.
"""

import time
import streamlit as st


STEPS = [
    ("✓", "Evidence received"),
    ("✓", "Indicators extracted"),
    ("✓", "Threat classification complete"),
    ("●", "Investigating evidence patterns"),
    ("●", "Correlating indicators"),
    ("●", "Calculating risk score"),
]


def render_analysis_progress():
    """Render animated progressive steps for 3 seconds."""
    placeholder = st.empty()

    lines = []
    for i, (icon, text) in enumerate(STEPS):
        color = "#10B981" if icon == "✓" else "#22D3EE"
        lines.append(
            f'<div style="font-family:JetBrains Mono,monospace;font-size:13px;'
            f'color:{color};padding:6px 0;">{icon}&nbsp;&nbsp;{text}</div>'
        )
        placeholder.markdown(
            '<div class="tq-card"><div class="tq-label">Analysis in Progress</div>'
            + "".join(lines)
            + "</div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.4)

    placeholder.markdown(
        '<div class="tq-card"><div class="tq-label">Analysis Complete</div>'
        + "".join(lines)
        + "</div>",
        unsafe_allow_html=True,
    )