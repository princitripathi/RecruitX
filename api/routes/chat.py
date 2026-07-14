"""
api/routes/chat.py — Chat Interface API Endpoint for RecruitX

Endpoint:
    POST /api/chat — Process a natural language query from the recruiter

Uses the ChatAgent (agents/chat_agent.py) with a two-step LLM pipeline:
    1. Intent Parser — classifies the recruiter message into search_candidates,
       get_candidate_details, count_candidates, or general_question.
    2. Response Generator — converts database results into a conversational reply.

The route:
    - Loads conversation history from the database via get_chat_history()
    - Passes history and the new message to the ChatAgent
    - Persists both user and assistant messages via add_chat_message()
    - Always returns HTTP 200 with {response, candidates, session_id, intent}
"""

import logging

from fastapi import APIRouter

from api.models import ChatRequest
from database.crud import add_chat_message, get_chat_history
from database.db_setup import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy singleton — ChatAgent is created on first use to avoid blocking FastAPI startup
_chat_agent = None


def _get_chat_agent():
    global _chat_agent
    if _chat_agent is None:
        from agents.chat_agent import ChatAgent
        _chat_agent = ChatAgent()
    return _chat_agent


@router.post("/api/chat")
def chat(request: ChatRequest):
    """
    Process a natural language chat query from the recruiter.

    Args:
        request: ChatRequest with message and session_id.

    Returns:
        Dict with:
            - response (str): Conversational reply from the Chat Agent.
            - candidates (list): Matching candidate records (may be empty).
            - session_id (str): Echoed session identifier.
            - intent (str): Detected intent type.
    """
    logger.info(
        "Chat query received (session: %s): %.60s...",
        request.session_id,
        request.message,
    )

    conn = get_db_connection()
    try:
        # Load previous conversation history for this session
        history = get_chat_history(conn, request.session_id)

        # Process the message through the Chat Agent
        agent = _get_chat_agent()
        result = agent.process_message(
            message=request.message,
            history=history,
            conn=conn,
        )

        # Persist user message
        add_chat_message(
            conn,
            session_id=request.session_id,
            role="user",
            message=request.message,
        )

        # Persist assistant reply
        add_chat_message(
            conn,
            session_id=request.session_id,
            role="assistant",
            message=result["response"],
        )

        logger.info(
            "Chat response (session: %s, intent: %s, candidates: %d)",
            request.session_id,
            result["intent"],
            len(result["candidates"]),
        )

        return {
            "response": result["response"],
            "candidates": result["candidates"],
            "session_id": request.session_id,
            "intent": result["intent"],
        }

    except Exception as e:
        logger.error("Chat processing failed (session: %s): %s", request.session_id, e)
        return {
            "response": (
                "I encountered a temporary issue while processing your request. "
                "Please try again in a moment."
            ),
            "candidates": [],
            "session_id": request.session_id,
            "intent": "error",
        }

    finally:
        conn.close()
