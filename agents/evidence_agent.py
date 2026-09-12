"""
ThreatIQ Evidence Agent.

The Evidence Agent examines the user's submitted evidence and extracts
useful security indicators such as:

- URLs
- Domains
- Email addresses
- Urgency indicators
- Credential requests
- Payment requests
- Possible brand names

This agent does not calculate the final risk score.
That is handled later by the Risk Agent.
"""

# Import regular expressions for extracting patterns from text.
import re

# Import typing helpers for the incident-state dictionary.
from typing import Any, Dict, List


# Regular expression used to find HTTP and HTTPS URLs.
URL_PATTERN = re.compile(
    r"https?://[^\s<>\"]+",
    re.IGNORECASE,
)


# Regular expression used to find email addresses.
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


# Words and phrases commonly associated with urgent social engineering.
URGENCY_TERMS = [
    "urgent",
    "immediately",
    "immediate action",
    "act now",
    "verify now",
    "expires today",
    "account suspended",
    "account will be suspended",
    "final warning",
    "last warning",
    "within 24 hours",
    "as soon as possible",
]


# Words and phrases commonly associated with credential requests.
CREDENTIAL_TERMS = [
    "password",
    "passcode",
    "login",
    "log in",
    "sign in",
    "username",
    "verification code",
    "security code",
    "otp",
    "one-time password",
    "authentication code",
    "recovery code",
]


# Words and phrases commonly associated with financial requests.
PAYMENT_TERMS = [
    "payment",
    "pay now",
    "pay",
    "bank account",
    "credit card",
    "debit card",
    "card number",
    "transfer money",
    "wire transfer",
    "gift card",
    "cryptocurrency",
    "crypto",
]


# Common brands and services that attackers may impersonate.
KNOWN_BRANDS = [
    "microsoft",
    "google",
    "apple",
    "paypal",
    "amazon",
    "netflix",
    "facebook",
    "instagram",
    "linkedin",
    "whatsapp",
    "docusign",
    "dropbox",
    "icloud",
    "outlook",
    "gmail",
]


def extract_urls(text: str) -> List[str]:
    """
    Extract HTTP and HTTPS URLs from text.

    Args:
        text: Text to inspect.

    Returns:
        A list of discovered URLs.
    """

    # Find all URL matches in the supplied text.
    matches = URL_PATTERN.findall(text)

    # Remove common punctuation that may appear immediately after a URL.
    cleaned_urls = [
        url.rstrip(".,!?;:)]}")
        for url in matches
    ]

    # Remove duplicates while preserving their original order.
    return list(dict.fromkeys(cleaned_urls))


def extract_domains(urls: List[str]) -> List[str]:
    """
    Extract domain names from discovered URLs.

    Args:
        urls: List of URLs.

    Returns:
        A list of domain names.
    """

    # Create a list to store extracted domains.
    domains = []

    # Process every discovered URL.
    for url in urls:

        # Remove the protocol from the URL.
        domain = re.sub(
            r"^https?://",
            "",
            url,
            flags=re.IGNORECASE,
        )

        # Remove everything after the domain name.
        domain = domain.split("/")[0]

        # Remove a possible port number.
        domain = domain.split(":")[0]

        # Remove a leading www.
        domain = re.sub(
            r"^www\.",
            "",
            domain,
            flags=re.IGNORECASE,
        )

        # Add the domain if it is not already present.
        if domain and domain not in domains:
            domains.append(domain)

    # Return all discovered domains.
    return domains


def find_matching_terms(
    text: str,
    terms: List[str],
) -> List[str]:
    """
    Find security-related terms appearing in the submitted text.

    Args:
        text: Text to inspect.
        terms: Terms to search for.

    Returns:
        Matching terms found in the text.
    """

    # Convert the text to lowercase for case-insensitive matching.
    lowered_text = text.lower()

    # Create a list for matching terms.
    matches = []

    # Check every term.
    for term in terms:

        # Add the term when it appears in the text.
        if term.lower() in lowered_text:
            matches.append(term)

    # Return unique matches.
    return list(dict.fromkeys(matches))


def extract_brands(text: str) -> List[str]:
    """
    Identify known brands mentioned in the evidence.

    Args:
        text: Text to inspect.

    Returns:
        A list of detected brand names.
    """

    # Convert the text to lowercase for matching.
    lowered_text = text.lower()

    # Create a list for detected brands.
    brands = []

    # Check every known brand.
    for brand in KNOWN_BRANDS:

        # Add the brand if it appears in the evidence.
        if brand in lowered_text:
            brands.append(brand)

    # Return the detected brands.
    return brands


def get_submission_text(state: Dict[str, Any]) -> str:
    """
    Safely retrieve the original submitted text from the incident state.

    Args:
        state: ThreatIQ incident state.

    Returns:
        The submitted evidence as text.
    """

    # Get the evidence list from the state.
    evidence = state.get("evidence", [])

    # Return an empty string if there is no evidence.
    if not evidence:
        return ""

    # Get the first evidence item.
    first_evidence = evidence[0]

    # Handle the standard evidence dictionary created by Intake Agent.
    if isinstance(first_evidence, dict):

        # Retrieve the original content field.
        content = first_evidence.get("content", "")

    # Handle evidence that may already be plain text.
    else:
        content = first_evidence

    # Convert the content to text.
    return str(content)


def evidence_agent(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract indicators from the incident evidence.

    Args:
        state: Shared ThreatIQ incident state.

    Returns:
        Updated incident state containing extracted indicators.
    """

    # Retrieve the original submission.
    text = get_submission_text(state)

    # Extract URLs from the submission.
    urls = extract_urls(text)

    # Extract domains from the discovered URLs.
    domains = extract_domains(urls)

    # Find urgency-related terms.
    urgency = find_matching_terms(
        text,
        URGENCY_TERMS,
    )

    # Find credential-related terms.
    credential_requests = find_matching_terms(
        text,
        CREDENTIAL_TERMS,
    )

    # Find payment-related terms.
    payment_requests = find_matching_terms(
        text,
        PAYMENT_TERMS,
    )

    # Find recognizable brands.
    brands = extract_brands(text)

    # Store all extracted indicators in the shared state.
    state["indicators"] = {
        "urls": urls,
        "domains": domains,
        "emails": EMAIL_PATTERN.findall(text),
        "urgency_terms": urgency,
        "credential_requests": credential_requests,
        "payment_requests": payment_requests,
        "brands": brands,
        "has_suspicious_url": len(urls) > 0,
        "has_credential_request": len(credential_requests) > 0,
        "has_payment_request": len(payment_requests) > 0,
        "has_urgent_language": len(urgency) > 0,
        "has_brand_mention": len(brands) > 0,
    }

    # Add a timeline event showing that evidence analysis completed.
    state.setdefault("timeline", []).append(
        {
            "agent": "evidence",
            "event": "Evidence analyzed and indicators extracted.",
        }
    )

    # Return the updated state for the next agent.
    return state


if __name__ == "__main__":
    """
    Run a direct test when this file is executed as a module.
    """

    # Import the Intake Agent only for this test.
    from agents.intake_agent import intake_agent

    # Create realistic test evidence.
    test_evidence = (
        "URGENT! Your Microsoft account will be suspended today. "
        "Verify your password immediately at "
        "https://secure-microsoft-example.com/login "
        "or your account will be locked."
    )

    # Run the Intake Agent first to create the shared state.
    test_state = intake_agent(
        evidence=test_evidence,
        incident_id="TEST-EVIDENCE-001",
    )

    # Run the Evidence Agent on the initialized state.
    test_state = evidence_agent(test_state)

    # Confirm successful execution.
    print("Evidence Agent test successful.")

    # Display discovered URLs.
    print(f"URLs: {test_state['indicators']['urls']}")

    # Display discovered domains.
    print(f"Domains: {test_state['indicators']['domains']}")

    # Display detected urgency terms.
    print(
        f"Urgency detected: "
        f"{test_state['indicators']['has_urgent_language']}"
    )

    # Display detected credential request.
    print(
        f"Credential request detected: "
        f"{test_state['indicators']['has_credential_request']}"
    )

    # Display detected brands.
    print(
        f"Brands: "
        f"{test_state['indicators']['brands']}"
    )