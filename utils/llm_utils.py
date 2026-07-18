"""
utils/llm_utils.py — Shared LLM Utilities for RecruitX

Common helper functions used by LLM-calling modules (JD Analyst,
Chat Agent, Resume Parser, Interview Generator) to avoid code duplication.
"""

import json
import re


def clean_json_response(raw_response: str) -> str:
    """
    Strip markdown code block wrappers from an LLM JSON response.

    LLMs sometimes wrap JSON output in ```json ... ``` markers.
    This function extracts the raw JSON from between those markers,
    or removes the markers if no JSON block is found.

    Args:
        raw_response: The raw string returned by the LLM.

    Returns:
        The cleaned string ready for json.loads().
    """
    cleaned = raw_response.strip()
    if "```" in cleaned:
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()
        else:
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return cleaned
