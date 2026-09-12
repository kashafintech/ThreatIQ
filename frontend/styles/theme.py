"""
ThreatIQ — Theme

Central design tokens for the entire frontend.

Import this in every component so colors stay consistent.

Usage:
    from frontend.styles.theme import COLORS, load_css
    load_css()
"""

import streamlit as st


# ============================================================
# DESIGN TOKENS
# ============================================================

COLORS = {
    # Backgrounds
    "bg_primary":     "#070B14",
    "bg_secondary":   "#0D1424",
    "bg_tertiary":    "#131B2E",
    "bg_input":       "#0A0F1C",

    # Borders
    "border_subtle":  "#1A2332",
    "border_medium":  "#2A3444",
    "border_active":  "#3B82F6",

    # Text
    "text_primary":   "#E5E7EB",
    "text_secondary": "#9CA3AF",
    "text_muted":     "#6B7280",

    # Accents
    "accent_cyan":    "#22D3EE",
    "accent_blue":    "#3B82F6",
    "accent_blue_hover": "#2563EB",

    # Risk levels
    "risk_low":       "#10B981",
    "risk_medium":    "#6366F1",
    "risk_high":      "#F59E0B",
    "risk_critical":  "#EF4444",
}


RISK_COLORS = {
    "LOW":      COLORS["risk_low"],
    "MEDIUM":   COLORS["risk_medium"],
    "HIGH":     COLORS["risk_high"],
    "CRITICAL": COLORS["risk_critical"],
}


# ============================================================
# GLOBAL CSS
# ============================================================

_CSS = f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>

/* ---------- Global ---------- */
.stApp {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: 'Inter', -apple-system, sans-serif;
}}

.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1150px;
}}

#MainMenu, footer, header {{visibility: hidden;}}

/* ---------- Header ---------- */
.tq-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0 24px 0;
    border-bottom: 1px solid {COLORS['border_subtle']};
    margin-bottom: 40px;
}}

.tq-logo {{
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: {COLORS['text_primary']};
}}

.tq-logo-mark {{
    color: {COLORS['accent_cyan']};
    margin-right: 8px;
}}

.tq-tagline {{
    font-size: 12px;
    color: {COLORS['text_muted']};
    margin-top: 2px;
}}

.tq-status {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'JetBrains Mono', monospace;
}}

.status-dot {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {COLORS['risk_low']};
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.7);
    animation: pulse 2s infinite;
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.4; }}
}}

/* ---------- Hero ---------- */
.tq-hero {{
    text-align: center;
    margin: 32px 0 48px 0;
}}

.tq-hero h1 {{
    font-size: 40px;
    font-weight: 700;
    color: {COLORS['text_primary']};
    letter-spacing: -0.02em;
    margin-bottom: 8px;
}}

.tq-hero p {{
    font-size: 15px;
    color: {COLORS['text_secondary']};
    margin-bottom: 0;
}}

/* ---------- Card ---------- */
.tq-card {{
    background: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border_subtle']};
    border-radius: 12px;
    padding: 28px;
    margin-bottom: 24px;
}}

.tq-label {{
    font-size: 12px;
    font-weight: 600;
    color: {COLORS['text_muted']};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
}}

/* ---------- Inputs ---------- */
.stTextArea textarea,
.stTextInput input {{
    background-color: {COLORS['bg_input']} !important;
    border: 1px solid {COLORS['border_medium']} !important;
    border-radius: 8px !important;
    color: {COLORS['text_primary']} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}}

.stTextArea textarea:focus,
.stTextInput input:focus {{
    border-color: {COLORS['border_active']} !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}}

/* ---------- Button ---------- */
.stButton > button {{
    background-color: {COLORS['accent_blue']} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 28px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 150ms ease !important;
    width: 100%;
}}

.stButton > button:hover {{
    background-color: {COLORS['accent_blue_hover']} !important;
    box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.4),
                0 0 24px rgba(59, 130, 246, 0.25) !important;
}}

/* ---------- Risk badges ---------- */
.risk-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.risk-low      {{ background: rgba(16,185,129,0.12);  color:{COLORS['risk_low']};      border:1px solid rgba(16,185,129,0.3); }}
.risk-medium   {{ background: rgba(99,102,241,0.12);  color:{COLORS['risk_medium']};   border:1px solid rgba(99,102,241,0.3); }}
.risk-high     {{ background: rgba(245,158,11,0.12);  color:{COLORS['risk_high']};     border:1px solid rgba(245,158,11,0.3); }}
.risk-critical {{ background: rgba(239,68,68,0.12);   color:{COLORS['risk_critical']}; border:1px solid rgba(239,68,68,0.3); }}

</style>
"""


def load_css():
    """Inject the ThreatIQ global stylesheet."""
    st.markdown(_CSS, unsafe_allow_html=True)


def risk_badge_html(level: str) -> str:
    """Return HTML for a risk-level badge."""
    level = (level or "").upper()
    cls = f"risk-{level.lower()}" if level else "risk-low"
    return f'<span class="risk-badge {cls}">{level}</span>'