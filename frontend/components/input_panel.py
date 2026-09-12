"""
ThreatIQ — Input Panel

Screen 1: New Scan.

Renders the evidence input card (text/URL tabs) and
returns the submitted evidence string, or None.
"""

import streamlit as st


def render_input_panel():
    """Render the input UI. Returns the submitted evidence or None."""

    st.markdown(
        """
        <div class="tq-hero">
            <h1>Investigate suspicious evidence</h1>
            <p>Submit a URL, email, or message. ThreatIQ investigates, scores, and guides your response.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="tq-card">', unsafe_allow_html=True)
    st.markdown('<div class="tq-label">Evidence Input</div>', unsafe_allow_html=True)

    tab_text, tab_url = st.tabs(["Message / Email", "URL"])

    with tab_text:
        text_input = st.text_area(
            "Paste suspicious message or email",
            placeholder="e.g. Your PayPal account has been limited. Click https://paypa1-security.example and verify your password immediately.",
            height=160,
            label_visibility="collapsed",
            key="input_text",
        )

    with tab_url:
        url_input = st.text_input(
            "Suspicious URL",
            placeholder="https://paypa1-security.example/login",
            label_visibility="collapsed",
            key="input_url",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        clicked = st.button("Analyze Evidence", use_container_width=True)

    if clicked:
        if text_input and text_input.strip():
            return text_input.strip()
        if url_input and url_input.strip():
            return url_input.strip()
        return ""  # empty = user clicked but nothing entered

    return None