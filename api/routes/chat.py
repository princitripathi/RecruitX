"""
api/routes/chat.py — Chat Interface API Endpoint for RecruitX

Endpoint:
    POST /api/chat — Process a natural language query from the recruiter

This is a lightweight placeholder implementation for Phase 11.
The full Chat Agent with LangChain-powered intent parsing, database
querying, and conversational memory will be implemented in Phase 14.

Current behavior:
    - Accepts a message and session_id
    - Returns a placeholder response indicating the feature is coming soon
"""

import logging

from fastapi import APIRouter

from api.models import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/chat")
def chat(request: ChatRequest):
    """
    Process a natural language chat query from the recruiter.

    Placeholder implementation — returns a static response.
    Full conversational AI agent with intent parsing and database
    querying comes in Phase 14.

    Args:
        request: ChatRequest with message and session_id.

    Returns:
        Dict with a placeholder response and empty candidates list.
    """
    logger.info(
        "Chat query received (session: %s): %.60s...",
        request.session_id,
        request.message,
    )

    return {
        "response": (
            "The RecruitX Chat Agent is under construction. "
            "In the full implementation (Phase 14), I will be able to "
            "answer natural language questions about your candidates, "
            "such as 'Show Python developers with 3+ years experience' "
            "or 'Who has the highest signal score?'."
        ),
        "candidates": [],
    }
