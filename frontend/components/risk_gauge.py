
"""
ThreatIQ - Risk Gauge Component

Displays the ThreatIQ risk score and risk level.

The backend is responsible for calculating:
    - risk_score
    - risk_level

This component only displays those values.
"""

# ============================================================
# IMPORTS
# ============================================================

import streamlit as st


# ============================================================
# RISK LEVEL CONFIGURATION
# ============================================================
# These colors are ONLY visual representations of the
# corresponding security states.

RISK_CONFIG = {
    "LOW": {
        "description": "Limited indicators detected",
        "color": "#10B981",
    },
    "MEDIUM": {
        "description": "Suspicious activity detected",
        "color": "#F59E0B",
    },
    "HIGH": {
        "description": "Significant threat indicators detected",
        "color": "#EF4444",
    },
    "CRITICAL": {
        "description": "Severe threat indicators detected",
        "color": "#EF4444",
    },
}


# ============================================================
# NORMALIZE SCORE
# ============================================================

def normalize_score(score) -> int:
    """
    Safely convert a score into an integer between 0 and 100.

    This does NOT calculate risk.
    """

    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0

    return max(0, min(100, score))


# ============================================================
# NORMALIZE RISK LEVEL
# ============================================================

def normalize_level(level: str) -> str:
    """
    Safely normalize the risk level.

    Supported levels:
        LOW
        MEDIUM
        HIGH
        CRITICAL
    """

    if not isinstance(level, str):
        return "LOW"

    level = level.strip().upper()

    if level in RISK_CONFIG:
        return level

    return "LOW"


# ============================================================
# SHOW RISK GAUGE
# ============================================================

def show_risk_gauge(
    risk_score: int,
    risk_level: str,
) -> None:
    """
    Render the ThreatIQ risk gauge.

    Parameters
    ----------
    risk_score:
        Risk score received from the backend.

    risk_level:
        Risk level received from the backend.
    """

    # --------------------------------------------------------
    # Prepare values.
    # --------------------------------------------------------

    score = normalize_score(risk_score)
    level = normalize_level(risk_level)

    config = RISK_CONFIG[level]

    color = config["color"]
    description = config["description"]


    # ========================================================
    # BUILD HTML
    # ========================================================
    # We use a normal HTML string.
    #
    # It will be rendered using st.html() below.
    # This avoids Streamlit Markdown interpreting the HTML
    # as a code block.

    html = f"""
<div style="
    background-color: #0D1424;
    border: 1px solid #1E293B;
    border-radius: 16px;
    padding: 24px;
    width: 100%;
    box-sizing: border-box;
    font-family: Arial, sans-serif;
">

    <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    ">

        <div style="
            color: #CBD5E1;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        ">
            Risk Assessment
        </div>

        <div style="
            color: {color};
            border: 1px solid {color};
            border-radius: 999px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
        ">
            {level}
        </div>

    </div>

    <div style="
        display: flex;
        align-items: baseline;
        gap: 7px;
        margin-bottom: 16px;
    ">

        <span style="
            color: #F8FAFC;
            font-size: 56px;
            font-weight: 700;
            line-height: 1;
        ">
            {score}
        </span>

        <span style="
            color: #64748B;
            font-size: 16px;
            font-weight: 500;
        ">
            / 100
        </span>

    </div>

    <div style="
        width: 100%;
        height: 10px;
        background-color: #1E293B;
        border-radius: 999px;
        overflow: hidden;
    ">

        <div style="
            width: {score}%;
            height: 100%;
            background-color: {color};
            border-radius: 999px;
        "></div>

    </div>

    <div style="
        color: #64748B;
        font-size: 13px;
        margin-top: 12px;
    ">
        {description}
    </div>

</div>
"""


    # ========================================================
    # RENDER HTML
    # ========================================================
    # IMPORTANT:
    #
    # st.html() renders HTML directly.
    # It does not interpret the HTML as Markdown code.
    #
    # This is why we are using st.html() instead of:
    #
    #     st.markdown(..., unsafe_allow_html=True)

    st.html(html)


# ============================================================
# DIRECT TEST
# ============================================================
# This section lets us test this component independently.

if __name__ == "__main__":

    # --------------------------------------------------------
    # Page configuration
    # --------------------------------------------------------

    st.set_page_config(
        page_title="ThreatIQ - Risk Gauge",
        page_icon="🛡️",
        layout="wide",
    )


    # --------------------------------------------------------
    # Page background
    # --------------------------------------------------------

    st.html(
        """
<style>
.stApp {
    background-color: #070B14;
    color: #F8FAFC;
}

.block-container {
    max-width: 800px;
    padding-top: 4rem;
}
</style>
"""
    )


    # --------------------------------------------------------
    # Test heading
    # --------------------------------------------------------

    st.html(
        """
<div style="
    text-align: center;
    color: #F8FAFC;
    font-size: 30px;
    font-weight: 700;
    margin-bottom: 32px;
    font-family: Arial, sans-serif;
">
    ThreatIQ Risk Gauge
</div>
"""
    )


    # --------------------------------------------------------
    # TEST DATA
    # --------------------------------------------------------
    # These values simulate what the backend will eventually
    # send to this component.

    show_risk_gauge(
        risk_score=72,
        risk_level="HIGH",
    )