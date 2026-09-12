"""
ThreatIQ LLM Utilities

This file provides the common Groq LLM functions used by ThreatIQ.

Required interface:
    ask_groq(system_prompt, user_prompt)
    ask_groq_json(system_prompt, user_prompt)

Model:
    llama-3.3-70b-versatile

API key:
    GROQ_API_KEY environment variable
"""

import json
import os
from typing import Any, Dict


# ---------------------------------------------------------------------------
# GROQ IMPORT
# ---------------------------------------------------------------------------
# Import the Groq client from the installed groq package.
from groq import Groq


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
# Read the API key from the environment.
# The key is intentionally NOT hard-coded into the source code.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Use the model specified for the ThreatIQ project.
GROQ_MODEL = "openai/gpt-oss-120b"


# ---------------------------------------------------------------------------
# GROQ CLIENT
# ---------------------------------------------------------------------------
def get_groq_client() -> Groq:
    """
    Create and return a Groq client.

    The API key must exist in the environment.
    """

    # Stop with a clear error if the API key is missing.
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set in the environment."
        )

    # Create the Groq API client.
    return Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# ASK GROQ
# ---------------------------------------------------------------------------
def ask_groq(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """
    Send a prompt to the Groq model and return plain text.

    Args:
        system_prompt: Instructions describing the model's role.
        user_prompt: The actual task or input.

    Returns:
        The model's response as a string.
    """

    # Create the Groq client.
    client = get_groq_client()

    # Send the request to the selected model.
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
    )

    # Extract the assistant's response.
    content = response.choices[0].message.content

    # Return an empty string if the model returned no content.
    return content.strip() if content else ""


# ---------------------------------------------------------------------------
# ASK GROQ FOR JSON
# ---------------------------------------------------------------------------
def ask_groq_json(
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, Any]:
    """
    Send a prompt to Groq and parse the response as JSON.

    The caller should instruct the model to return valid JSON.

    Returns:
        Parsed JSON as a Python dictionary.
    """

    # Create the Groq client.
    client = get_groq_client()

    # Add an explicit JSON instruction to the system prompt.
    json_system_prompt = (
        system_prompt
        + "\n\nReturn ONLY valid JSON. "
        "Do not include Markdown code fences."
    )

    # Send the request.
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": json_system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    # Extract the model response.
    content = response.choices[0].message.content

    # Make sure a response was returned.
    if not content:
        raise ValueError("Groq returned an empty JSON response.")

    # Parse the JSON string into a Python dictionary.
    parsed = json.loads(content)

    # Make sure the returned JSON has the expected dictionary form.
    if not isinstance(parsed, dict):
        raise ValueError(
            "Groq JSON response must be a JSON object."
        )

    # Return the parsed dictionary.
    return parsed


# ---------------------------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Simple connectivity test.

    WARNING:
    This test makes a real Groq API request and therefore requires
    GROQ_API_KEY to be configured.
    """

    # Check whether the API key is available before making the request.
    if not GROQ_API_KEY:
        print("LLM utility test skipped.")
        print("GROQ_API_KEY is not set.")
    else:
        # Send a tiny test request.
        result = ask_groq(
            system_prompt="You are a test assistant.",
            user_prompt="Reply with exactly: ThreatIQ LLM working.",
        )

        # Print the model response.
        print("LLM utility test successful.")
        print(f"Response: {result}")
