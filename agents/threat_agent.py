"""
ThreatIQ Threat Agent.

The Threat Agent determines the most likely threat category by using
the indicators extracted by the Evidence Agent and the ThreatIQ RAG
knowledge base.

Possible threat types include:
- PHISHING
- SCAM
- BRAND_IMPERSONATION
- SUSPICIOUS_ACTIVITY
- UNKNOWN
"""

# Import typing helpers for the incident-state dictionary.
from typing import Any, Dict, List

# Import the RAG functions used to search the knowledge base.
from core.rag_engine import (
    build_knowledge_base,
    search_knowledge_base,
)


# Define the similarity score above which a RAG result is considered
# relevant enough to contribute to threat classification.
RAG_RELEVANCE_THRESHOLD = 0.30


def get_evidence_text(state: Dict[str, Any]) -> str:
    """
    Convert the incident evidence and indicators into searchable text.

    Args:
        state: Shared ThreatIQ incident state.

    Returns:
        Text that can be searched against the knowledge bases.
    """

    # Create a list that will contain all useful evidence text.
    text_parts: List[str] = []

    # Get the original evidence list.
    evidence = state.get("evidence", [])

    # Process every evidence item.
    for item in evidence:

        # Handle evidence dictionaries.
        if isinstance(item, dict):

            # Extract the original content.
            content = item.get("content", "")

        # Handle plain-text evidence.
        else:
            content = item

        # Add non-empty content to the searchable text.
        if content:
            text_parts.append(str(content))

    # Get indicators extracted by the Evidence Agent.
    indicators = state.get("indicators", {})

    # Add detected urgency terms.
    text_parts.extend(
        indicators.get("urgency_terms", [])
    )

    # Add credential-related terms.
    text_parts.extend(
        indicators.get("credential_requests", [])
    )

    # Add payment-related terms.
    text_parts.extend(
        indicators.get("payment_requests", [])
    )

    # Add detected brands.
    text_parts.extend(
        indicators.get("brands", [])
    )

    # Combine everything into one searchable string.
    return " ".join(text_parts)


def calculate_category_scores(
    query: str,
) -> Dict[str, float]:
    """
    Search the relevant RAG knowledge bases and calculate category scores.

    Args:
        query: Evidence text to classify.

    Returns:
        A dictionary containing the best similarity score for each threat
        category.
    """

    # Create a dictionary for the final category scores.
    scores = {
        "PHISHING": 0.0,
        "SCAM": 0.0,
        "BRAND_IMPERSONATION": 0.0,
    }

    # Map threat categories to their corresponding knowledge bases.
    knowledge_base_files = {
        "PHISHING": "phishing_patterns.json",
        "SCAM": "scam_examples.json",
        "BRAND_IMPERSONATION": "brand_impersonation.json",
    }

    # Search each threat category separately.
    for category, file_name in knowledge_base_files.items():

        # Build the FAISS knowledge-base index.
        knowledge_base = build_knowledge_base(
            file_name
        )

        # Search for the most relevant knowledge-base records.
        results = search_knowledge_base(
            knowledge_base,
            query,
            top_k=3,
        )

        # Process returned RAG matches.
        for result in results:

            # Read the similarity score.
            similarity = float(
                result.get("score", 0.0)
            )

            # Ignore weak matches.
            if similarity < RAG_RELEVANCE_THRESHOLD:
                continue

            # Keep the strongest match for this category.
            if similarity > scores[category]:
                scores[category] = similarity

    # Return the category scores.
    return scores


def classify_threat(
    state: Dict[str, Any],
) -> str:
    """
    Determine the most likely threat type.

    Args:
        state: Shared ThreatIQ incident state.

    Returns:
        The selected threat type.
    """

    # Convert the available evidence into searchable text.
    query = get_evidence_text(state)

    # Return UNKNOWN if there is no evidence to analyze.
    if not query.strip():
        return "UNKNOWN"

    # Search the RAG knowledge bases.
    scores = calculate_category_scores(query)

    # Select the category with the strongest similarity score.
    best_category = max(
        scores,
        key=scores.get,
    )

    # Get the strongest similarity score.
    best_score = scores[best_category]

    # If no category has a meaningful match, classify it as suspicious
    # activity rather than forcing an unsupported threat category.
    if best_score < RAG_RELEVANCE_THRESHOLD:
        return "SUSPICIOUS_ACTIVITY"

    # Return the strongest supported category.
    return best_category


def threat_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Analyze the incident and assign a threat type.

    Args:
        state: Shared ThreatIQ incident state.

    Returns:
        Updated incident state.
    """

    # Classify the threat using the extracted evidence and RAG.
    threat_type = classify_threat(state)

    # Store the classification in the shared state.
    state["threat_type"] = threat_type

    # Record the classification in the incident timeline.
    state.setdefault("timeline", []).append(
        {
            "agent": "threat",
            "event": f"Threat classified as {threat_type}.",
        }
    )

    # Return the updated state.
    return state


if __name__ == "__main__":
    """
    Run a direct test when this file is executed as a module.
    """

    # Import the previous agents required to create a realistic state.
    from agents.intake_agent import intake_agent
    from agents.evidence_agent import evidence_agent

    # Create realistic phishing evidence.
    test_evidence = (
        "URGENT! Your Microsoft account will be suspended today. "
        "Verify your password immediately at "
        "https://secure-microsoft-example.com/login."
    )

    # Run the Intake Agent first.
    test_state = intake_agent(
        evidence=test_evidence,
        incident_id="TEST-THREAT-001",
    )

    # Extract indicators using the Evidence Agent.
    test_state = evidence_agent(test_state)

    # Classify the threat using the Threat Agent.
    test_state = threat_agent(test_state)

    # Confirm successful execution.
    print("Threat Agent test successful.")

    # Display the resulting threat category.
    print(
        f"Threat type: "
        f"{test_state['threat_type']}"
    )