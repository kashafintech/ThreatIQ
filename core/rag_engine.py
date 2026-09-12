"""
ThreatIQ RAG engine.

This file loads ThreatIQ's JSON knowledge bases, creates embeddings
using Sentence Transformers, and searches the knowledge base using
FAISS.

The engine is intentionally kept as plain functions and dictionaries.
No classes or agent frameworks are used.
"""

# Import json so we can read the knowledge-base JSON files.
import json

# Import os so we can safely build file paths.
import os

# Import typing helpers for clearer function definitions.
from typing import Any, Dict, List

# Import FAISS for fast vector similarity search.
import faiss

# Import the Sentence Transformer model used to create embeddings.
from sentence_transformers import SentenceTransformer


# Get the directory containing this file.
CORE_DIR = os.path.dirname(os.path.abspath(__file__))

# Move one directory up to reach the ThreatIQ project root.
PROJECT_ROOT = os.path.dirname(CORE_DIR)

# Point to the knowledge-base directory.
KNOWLEDGE_BASE_DIR = os.path.join(
    PROJECT_ROOT,
    "data",
    "knowledge_base",
)


# Use the required lightweight embedding model.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


# Store the model after it is loaded so repeated searches
# do not unnecessarily load the model again.
_embedding_model = None


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load a JSON knowledge-base file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        A list containing knowledge-base records.
    """

    # Open the JSON file using UTF-8 encoding.
    with open(file_path, "r", encoding="utf-8") as file:

        # Convert the JSON content into Python data.
        data = json.load(file)

    # Make sure the knowledge base has the expected list format.
    if not isinstance(data, list):

        # Stop with a clear error if the JSON structure is incorrect.
        raise ValueError(
            f"Knowledge base must contain a JSON list: {file_path}"
        )

    # Return the loaded knowledge-base records.
    return data


def get_embedding_model() -> SentenceTransformer:
    """
    Load and return the Sentence Transformer model.

    The model is loaded only once during the application's lifetime.
    """

    # Tell Python that we want to update the module-level model variable.
    global _embedding_model

    # Load the model only if it has not already been loaded.
    if _embedding_model is None:

        # Create the required Sentence Transformer model.
        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

    # Return the loaded model.
    return _embedding_model


def build_knowledge_base(
    file_name: str,
) -> Dict[str, Any]:
    """
    Load a knowledge base and build its FAISS index.

    Args:
        file_name: Name of the JSON knowledge-base file.

    Returns:
        A dictionary containing records, embeddings, and the FAISS index.
    """

    # Build the complete path to the requested JSON file.
    file_path = os.path.join(
        KNOWLEDGE_BASE_DIR,
        file_name,
    )

    # Load the knowledge records from the JSON file.
    records = load_json_file(file_path)

    # Extract the text field from every knowledge-base record.
    texts = [
        record.get("text", "")
        for record in records
    ]

    # Get the embedding model.
    model = get_embedding_model()

    # Convert every knowledge-base text into a vector.
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    # Convert the vector dimension into a regular integer.
    dimension = embeddings.shape[1]

    # Create a FAISS inner-product index.
    # Because embeddings are normalized, inner product represents
    # cosine similarity.
    index = faiss.IndexFlatIP(dimension)

    # Add all knowledge-base vectors to the FAISS index.
    index.add(embeddings.astype("float32"))

    # Return everything required for later searches.
    return {
        "file_name": file_name,
        "records": records,
        "embeddings": embeddings,
        "index": index,
    }


def search_knowledge_base(
    knowledge_base: Dict[str, Any],
    query: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Search a loaded knowledge base for the most relevant records.

    Args:
        knowledge_base: Knowledge base returned by build_knowledge_base.
        query: Text to search for.
        top_k: Maximum number of results to return.

    Returns:
        A list of matching records with similarity scores.
    """

    # Remove unnecessary whitespace from the query.
    query = str(query).strip()

    # Return no results for an empty query.
    if not query:
        return []

    # Get the embedding model.
    model = get_embedding_model()

    # Convert the query into an embedding vector.
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    # Convert the requested result count into a safe integer.
    top_k = max(1, int(top_k))

    # Never request more results than exist in the index.
    top_k = min(
        top_k,
        knowledge_base["index"].ntotal,
    )

    # Search the FAISS index for the closest vectors.
    scores, indexes = knowledge_base["index"].search(
        query_embedding.astype("float32"),
        top_k,
    )

    # Create a list for the final search results.
    results = []

    # Process every returned result.
    for score, index_position in zip(
        scores[0],
        indexes[0],
    ):

        # Ignore invalid FAISS indexes.
        if index_position < 0:
            continue

        # Retrieve the original knowledge-base record.
        record = knowledge_base["records"][index_position]

        # Copy the record so we do not modify the original data.
        result = dict(record)

        # Add the similarity score to the returned result.
        result["score"] = float(score)

        # Add the result to the final list.
        results.append(result)

    # Return the most relevant results.
    return results


def load_all_knowledge_bases() -> Dict[str, Dict[str, Any]]:
    """
    Load all ThreatIQ knowledge bases.

    Returns:
        A dictionary containing all four indexed knowledge bases.
    """

    # Load the phishing knowledge base.
    phishing = build_knowledge_base(
        "phishing_patterns.json"
    )

    # Load the scam knowledge base.
    scams = build_knowledge_base(
        "scam_examples.json"
    )

    # Load the brand impersonation knowledge base.
    brand_impersonation = build_knowledge_base(
        "brand_impersonation.json"
    )

    # Load the response playbooks.
    response_playbooks = build_knowledge_base(
        "response_playbooks.json"
    )

    # Return all loaded knowledge bases.
    return {
        "phishing_patterns": phishing,
        "scam_examples": scams,
        "brand_impersonation": brand_impersonation,
        "response_playbooks": response_playbooks,
    }


def search_all_knowledge_bases(
    query: str,
    top_k: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search all ThreatIQ knowledge bases using one query.

    Args:
        query: Text that should be investigated.
        top_k: Maximum results per knowledge base.

    Returns:
        Search results grouped by knowledge-base name.
    """

    # Load all knowledge bases.
    knowledge_bases = load_all_knowledge_bases()

    # Create a dictionary for the final results.
    results = {}

    # Search each knowledge base separately.
    for name, knowledge_base in knowledge_bases.items():

        # Store the matching records under the knowledge-base name.
        results[name] = search_knowledge_base(
            knowledge_base,
            query,
            top_k,
        )

    # Return all grouped search results.
    return results


if __name__ == "__main__":
    """
    Run a small direct test when this file is executed directly.
    """

    # Use a simple phishing-related query for testing.
    test_query = (
        "urgent account verification asking for password "
        "through a suspicious login link"
    )

    # Search the phishing knowledge base.
    test_knowledge_base = build_knowledge_base(
        "phishing_patterns.json"
    )

    # Retrieve the three most relevant records.
    test_results = search_knowledge_base(
        test_knowledge_base,
        test_query,
        top_k=3,
    )

    # Print a clear test heading.
    print("RAG engine test successful.")

    # Print the number of returned results.
    print(f"Results returned: {len(test_results)}")

    # Print each result in a compact format.
    for result in test_results:
        print(
            f"{result['id']} | "
            f"score={result['score']:.4f}"
        )