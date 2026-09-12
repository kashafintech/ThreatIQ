"""
ThreatIQ Helper Functions

Small reusable utility functions used across the ThreatIQ project.

No classes are used.
No LLM is used.
"""


def clean_text(text):
    """
    Clean user-provided text by:
    - Converting it to a string
    - Removing leading/trailing whitespace
    - Replacing repeated whitespace with a single space

    Returns:
        Cleaned string.
    """

    # Return an empty string for None.
    if text is None:
        return ""

    # Convert the value to a string and split it into words.
    # Joining the words removes unnecessary repeated whitespace.
    return " ".join(str(text).strip().split())


def normalize_risk_level(level):
    """
    Normalize a risk level to uppercase.

    Example:
        "high" -> "HIGH"
        " Critical " -> "CRITICAL"
    """

    # Return an empty string when no level is provided.
    if level is None:
        return ""

    # Remove whitespace and convert the level to uppercase.
    return str(level).strip().upper()


def clamp_score(score, minimum=0, maximum=100):
    """
    Keep a numeric score inside a specified range.

    Example:
        clamp_score(120) -> 100
        clamp_score(-5) -> 0
    """

    # Convert the score to a number when possible.
    try:
        score = int(score)
    except (TypeError, ValueError):
        # Return the minimum value for invalid input.
        return minimum

    # Keep the score within the allowed range.
    return max(minimum, min(score, maximum))


def format_list(items, empty_text="None"):
    """
    Convert a list of values into readable numbered text.

    Example:
        ["Block URL", "Change password"]

    Becomes:
        "1. Block URL\n2. Change password"
    """

    # Handle missing or empty lists.
    if not items:
        return empty_text

    # Create one numbered line for every item.
    return "\n".join(
        f"{index}. {item}"
        for index, item in enumerate(items, start=1)
    )


def get_nested_value(data, *keys, default=None):
    """
    Safely retrieve a value from nested dictionaries.

    Example:
        get_nested_value(data, "indicators", "urls", default=[])

    prevents errors when a key does not exist.
    """

    # Start with the original dictionary.
    current = data

    # Follow each requested key.
    for key in keys:

        # Stop safely if the current value is not a dictionary.
        if not isinstance(current, dict):
            return default

        # Return the default when the key does not exist.
        if key not in current:
            return default

        # Move deeper into the dictionary.
        current = current[key]

    # Return the final value.
    return current


def bool_from_answer(answer):
    """
    Convert common user answers into True/False.

    Useful for investigation questions such as:
    "Did you click the link?"

    Recognized positive answers:
        yes, y, true, 1

    Recognized negative answers:
        no, n, false, 0

    Returns:
        True, False, or None when the answer is unclear.
    """

    # Handle boolean values directly.
    if isinstance(answer, bool):
        return answer

    # Return None for missing answers.
    if answer is None:
        return None

    # Normalize the answer.
    normalized = str(answer).strip().lower()

    # Recognized positive answers.
    if normalized in {"yes", "y", "true", "1"}:
        return True

    # Recognized negative answers.
    if normalized in {"no", "n", "false", "0"}:
        return False

    # The answer could not be confidently interpreted.
    return None


def generate_incident_id(prefix="INC"):
    """
    Generate a simple UTC-based incident ID.

    Example:
        INC-20260912-173045
    """

    # Import datetime only when this helper is called.
    from datetime import datetime, timezone

    # Get the current UTC time.
    now = datetime.now(timezone.utc)

    # Format the timestamp into a readable incident ID.
    timestamp = now.strftime("%Y%m%d-%H%M%S")

    return f"{prefix}-{timestamp}"


# Direct test for this file.
if __name__ == "__main__":

    # Test text cleaning.
    cleaned = clean_text("   Suspicious    login   link   ")

    # Test risk-level normalization.
    normalized_level = normalize_risk_level("  high ")

    # Test score clamping.
    high_score = clamp_score(125)
    low_score = clamp_score(-10)

    # Test list formatting.
    formatted = format_list(["Block the URL", "Change your password"])

    # Test nested dictionary lookup.
    sample_data = {
        "indicators": {
            "urls": ["https://example.com"]
        }
    }

    nested_value = get_nested_value(
        sample_data,
        "indicators",
        "urls",
        default=[]
    )

    # Test answer conversion.
    yes_answer = bool_from_answer("YES")
    no_answer = bool_from_answer("no")

    # Test incident ID generation.
    incident_id = generate_incident_id()

    # Display the results.
    print("Helpers test successful.")
    print(f"Cleaned text: {cleaned}")
    print(f"Normalized risk level: {normalized_level}")
    print(f"Clamped high score: {high_score}")
    print(f"Clamped low score: {low_score}")
    print(f"Formatted list lines: {len(formatted.splitlines())}")
    print(f"Nested value found: {nested_value == ['https://example.com']}")
    print(f"YES converted to: {yes_answer}")
    print(f"NO converted to: {no_answer}")
    print(f"Generated incident ID: {incident_id}")
