"""
agents/chat_agent.py — Chat Agent for RecruitX

This agent enables natural language interaction with the candidate database.
It uses a two-step LLM pipeline:
    1. Intent Parser: Classifies the recruiter message into a structured intent
    2. Response Generator: Converts database results into a conversational reply

Intents supported:
    - search_candidates: Find candidates matching skills, location, experience
    - get_candidate_details: Get details about a specific candidate
    - count_candidates: Get counts of candidates matching criteria
    - general_question: General questions about the system

If the LLM is unavailable, the agent falls back to keyword extraction
and deterministic response templates.
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import sqlite3
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from database.crud import (
    get_all_candidates,
    get_candidate_by_id,
    get_candidate_count,
    search_candidates,
)

load_dotenv()

logger = logging.getLogger(__name__)

# Default configuration loaded from .env (with sensible fallbacks)
DEFAULT_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
DEFAULT_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# Common tech skills for fallback keyword matching
COMMON_SKILLS: List[str] = [
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "rust",
    "swift", "kotlin", "php", "scala", "r", "matlab",
    "react", "angular", "vue", "django", "flask", "fastapi", "spring", "express",
    "node", "nodejs", "node.js",
    "sql", "mysql", "postgresql", "mongodb", "redis", "cassandra", "oracle",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
    "machine learning", "ml", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "git", "linux", "agile", "scrum", "rest api", "graphql",
    "html", "css", "sass", "less", "webpack", "babel",
    "tableau", "power bi", "excel", "spark", "hadoop",
    "devops", "ci/cd", "testing", "pytest", "junit",
]

# Common Indian cities for fallback location matching
INDIAN_CITIES: List[str] = [
    "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "pune", "chennai",
    "kolkata", "ahmedabad", "jaipur", "lucknow", "noida", "gurgaon", "indore",
    "bhopal", "surat", "chandigarh", "kochi", "coimbatore", "vizag", "nagpur",
]

# ============================================================
# Prompt Templates
# ============================================================

INTENT_SYSTEM_PROMPT = """You are an AI assistant for RecruitX, a recruitment database system. Your job is to analyze recruiter messages and classify their intent into exactly one of four types.

Return ONLY a valid JSON object with exactly these fields (no markdown, no code blocks, no extra text):
{{
    "intent": "...",
    "parameters": {{
        "skills": "... or null",
        "location": "... or null",
        "min_experience": number or null,
        "max_experience": number or null,
        "candidate_name": "... or null",
        "candidate_id": number or null
    }},
    "explanation": "..."
}}

INTENT TYPES:
1. "search_candidates" — Recruiter wants to FIND candidates matching criteria (skills, location, experience).
2. "get_candidate_details" — Recruiter asks about a SPECIFIC candidate by name or ID.
3. "count_candidates" — Recruiter asks HOW MANY candidates match criteria.
4. "general_question" — Anything else: greetings, thanks, system questions, chit-chat.

EXAMPLES:
User: Show Python developers in Mumbai with 3+ years
Response: {{"intent": "search_candidates", "parameters": {{"skills": "Python", "location": "Mumbai", "min_experience": 3, "max_experience": null, "candidate_name": null, "candidate_id": null}}, "explanation": "Recruiter wants Python developers in Mumbai with 3+ years experience"}}

User: Tell me about candidate 5
Response: {{"intent": "get_candidate_details", "parameters": {{"skills": null, "location": null, "min_experience": null, "max_experience": null, "candidate_name": null, "candidate_id": 5}}, "explanation": "Recruiter wants details on candidate ID 5"}}

User: Who is Rahul Sharma?
Response: {{"intent": "get_candidate_details", "parameters": {{"skills": null, "location": null, "min_experience": null, "max_experience": null, "candidate_name": "Rahul Sharma", "candidate_id": null}}, "explanation": "Recruiter wants details on Rahul Sharma"}}

User: How many Python developers are there?
Response: {{"intent": "count_candidates", "parameters": {{"skills": "Python", "location": null, "min_experience": null, "max_experience": null, "candidate_name": null, "candidate_id": null}}, "explanation": "Recruiter wants count of Python developers"}}

User: Hello
Response: {{"intent": "general_question", "parameters": {{"skills": null, "location": null, "min_experience": null, "max_experience": null, "candidate_name": null, "candidate_id": null}}, "explanation": "General greeting"}}

Rules:
- For search_candidates, always extract skills, location, and experience if mentioned.
- For get_candidate_details, use candidate_id if a number follows "candidate", or candidate_name if a person name is given.
- For count_candidates, extract any filters just like search_candidates.
- Set parameters to null if not mentioned."""

RESPONSE_SYSTEM_PROMPT = """You are a friendly and professional AI recruitment assistant for RecruitX. Given the recruiter's query, the intent, and the database results, generate a helpful conversational response.

RULES:
1. Be concise — maximum 4 sentences.
2. Be professional and helpful.
3. If candidates were found, briefly summarize: mention their names, key skills, and experience.
4. List at most 3 candidates by name. If there are more, say how many total were found.
5. If no candidates were found, suggest broadening the search criteria.
6. For count_candidates, state the number clearly.
7. For general_question, answer briefly about what RecruitX can do.
8. For get_candidate_details, show the candidate's name, skills, experience, location, and education.
9. Do NOT mention internal IDs, database queries, or technical details.
10. Use a natural, conversational tone — like a helpful assistant."""


class ChatAgent:
    """
    Agent that processes natural language recruiter queries using a two-step LLM pipeline.

    Step 1: Intent Parser — classifies the message and extracts structured search parameters.
    Step 2: Response Generator — converts database results into a conversational reply.

    If the LLM is unavailable, falls back to keyword extraction from the message
    and template-based responses.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize the Chat Agent.

        All parameters are optional — values default to .env configuration.
        Override any parameter by passing it directly (useful for testing).

        Args:
            api_key: OpenRouter API key (default: from OPENROUTER_API_KEY env var)
            base_url: OpenRouter base URL (default: from OPENROUTER_BASE_URL env var)
            model: LLM model name (default: from OPENROUTER_MODEL env var)
            temperature: LLM temperature (default: 0.1)
            max_retries: Retry attempts on failure (default: 3)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = base_url or DEFAULT_BASE_URL
        self.model = model or DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
        self.max_retries = max_retries if max_retries is not None else DEFAULT_MAX_RETRIES

        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            logger.warning(
                "OPENROUTER_API_KEY is not set. "
                "Chat Agent will use keyword fallback for intent parsing."
            )

        logger.info(
            "Initializing ChatAgent with model=%s, temperature=%.1f, max_retries=%d",
            self.model, self.temperature, self.max_retries,
        )

        self._intent_chain = self._build_intent_chain()
        self._response_chain = self._build_response_chain()

    def _build_intent_chain(self):
        """
        Build the LangChain pipeline for intent parsing.
        Pipeline: ChatPromptTemplate -> ChatOpenAI (via OpenRouter) -> StrOutputParser
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_SYSTEM_PROMPT),
            ("human", "Previous conversation:\n{history}\n\nCurrent message: {message}"),
        ])
        llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
            request_timeout=30,
            max_retries=1,
        )
        return prompt | llm | StrOutputParser()

    def _build_response_chain(self):
        """
        Build the LangChain pipeline for response generation.
        Pipeline: ChatPromptTemplate -> ChatOpenAI (via OpenRouter) -> StrOutputParser
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", RESPONSE_SYSTEM_PROMPT),
            (
                "human",
                "Recruiter query: {message}\n"
                "Intent: {intent}\n"
                "Candidates found ({count} total):\n{candidates}\n\n"
                "Generate a conversational response.",
            ),
        ])
        llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
            request_timeout=30,
            max_retries=1,
        )
        return prompt | llm | StrOutputParser()

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def process_message(
        self,
        message: str,
        history: List[Dict[str, Any]],
        conn: sqlite3.Connection,
    ) -> Dict[str, Any]:
        """
        Process a recruiter message and return a structured response.

        Args:
            message: The recruiter's natural language message.
            history: Previous conversation messages (list of dicts with 'role' and 'message').
            conn: Active SQLite database connection for CRUD operations.

        Returns:
            Dict with keys:
                - response (str): Conversational reply.
                - candidates (list): Matching candidate records.
                - intent (str): The detected intent type.
        """
        if not message or not message.strip():
            return {
                "response": "Please type a message and I'll be happy to help you find candidates.",
                "candidates": [],
                "intent": "general_question",
            }

        # Step 1: Parse intent via LLM (with fallback)
        intent_data = self._parse_intent(message, history)

        # Step 2: Execute database query via CRUD
        candidates = self._execute_query(intent_data, conn)

        # Step 3: Generate conversational response
        response = self._generate_response(message, intent_data, candidates, history)

        return {
            "response": response,
            "candidates": candidates,
            "intent": intent_data["intent"],
        }

    # ---------------------------------------------------------------
    # Step 1: Intent Parsing
    # ---------------------------------------------------------------

    def _parse_intent(
        self,
        message: str,
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Parse the recruiter message to extract intent and search parameters.

        Tries the LLM first. Falls back to keyword extraction if:
        - No API key is configured
        - The LLM call fails
        - The response cannot be parsed as valid intent JSON

        Args:
            message: The recruiter's message.
            history: Conversation history for context.

        Returns:
            Dict with 'intent', 'parameters', and 'explanation' keys.
        """
        # If no API key, skip LLM and go straight to fallback
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            logger.info("No API key configured — using keyword fallback for intent parsing")
            return self._fallback_extract_intent(message)

        # Try LLM-based intent parsing with retries
        formatted_history = self._format_history(history)
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "Parsing intent (attempt %d/%d): %.60s...",
                    attempt + 1, self.max_retries, message,
                )
                raw = self._intent_chain.invoke({
                    "history": formatted_history,
                    "message": message,
                })
                cleaned = raw.strip()
                # Strip markdown code blocks if present
                if "```" in cleaned:
                    import re as _re
                    match = _re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
                    if match:
                        cleaned = match.group(1).strip()
                    else:
                        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

                parsed = json.loads(cleaned)
                intent = parsed.get("intent")
                valid_intents = {"search_candidates", "get_candidate_details", "count_candidates", "general_question"}

                if intent not in valid_intents:
                    logger.warning("Unknown intent '%s' from LLM, defaulting to general_question", intent)
                    intent = "general_question"

                logger.info("Intent parsed: %s — %s", intent, parsed.get("explanation", ""))
                return {
                    "intent": intent,
                    "parameters": parsed.get("parameters", {}),
                    "explanation": parsed.get("explanation", ""),
                }

            except (json.JSONDecodeError, Exception) as e:
                last_error = e
                logger.warning("Intent parsing attempt %d/%d failed: %s", attempt + 1, self.max_retries, e)
                if attempt < self.max_retries - 1:
                    logger.info("Retrying intent parsing...")

        logger.error("LLM intent parsing failed after %d attempts. Using fallback.", self.max_retries)
        return self._fallback_extract_intent(message)

    def _fallback_extract_intent(self, message: str) -> Dict[str, Any]:
        """
        Extract intent and search parameters using keyword matching,
        without any LLM call. Used when the LLM is unavailable.

        Args:
            message: The recruiter's message.

        Returns:
            Dict with 'intent', 'parameters', and 'explanation' keys.
        """
        message_lower = message.lower().strip()
        params: Dict[str, Any] = {
            "skills": None,
            "location": None,
            "min_experience": None,
            "max_experience": None,
            "candidate_name": None,
            "candidate_id": None,
        }

        # Determine intent type
        if re.search(r'\b(how many|total|count)\b', message_lower):
            # Count intent — still extract any filters
            extracted = self._extract_search_params(message_lower)
            params.update(extracted)
            return {"intent": "count_candidates", "parameters": params, "explanation": "Fallback: count query detected"}

        # Check for candidate details by ID
        id_match = re.search(r'candidate\s+(\d+)', message_lower)
        if id_match:
            params["candidate_id"] = int(id_match.group(1))
            return {
                "intent": "get_candidate_details",
                "parameters": params,
                "explanation": f"Fallback: candidate ID {params['candidate_id']} requested",
            }

        # Check for candidate details by name
        name_match = re.search(
            r'(?:who is|tell me about|details?\s+(?:on|for|about))\s+(.+?)(?:\?|\.|$)',
            message_lower,
        )
        if name_match:
            name = name_match.group(1).strip().title()
            # Remove leading articles
            name = re.sub(r'^(The|A|An)\s+', '', name).strip()
            if name and len(name) > 2:
                params["candidate_name"] = name
                return {
                    "intent": "get_candidate_details",
                    "parameters": params,
                    "explanation": f"Fallback: details requested for '{name}'",
                }

        # Check for search keywords
        extracted = self._extract_search_params(message_lower)
        if extracted.get("skills") or extracted.get("location") or extracted.get("min_experience") is not None:
            params.update(extracted)
            return {
                "intent": "search_candidates",
                "parameters": params,
                "explanation": "Fallback: search keywords detected",
            }

        # Check for greetings and simple messages
        greeting_patterns = [
            r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
            r'\b(thanks|thank you)\b',
            r'\b(help|what can you do|how does this work)\b',
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, message_lower):
                return {
                    "intent": "general_question",
                    "parameters": params,
                    "explanation": "Fallback: greeting or help request",
                }

        # Default — treat as general question
        return {
            "intent": "general_question",
            "parameters": params,
            "explanation": "Fallback: could not determine specific intent",
        }

    def _extract_search_params(self, message: str) -> Dict[str, Any]:
        """
        Extract search parameters (skills, location, experience) from a message
        using keyword matching. Used by the fallback intent parser.

        Args:
            message: Lowercase recruiter message.

        Returns:
            Dict with skills, location, min_experience, max_experience, candidate_name, candidate_id.
        """
        params: Dict[str, Any] = {
            "skills": None,
            "location": None,
            "min_experience": None,
            "max_experience": None,
            "candidate_name": None,
            "candidate_id": None,
        }

        # Extract skills
        found_skills: List[str] = []
        for skill in COMMON_SKILLS:
            if skill in message:
                found_skills.append(skill)
        if found_skills:
            params["skills"] = ", ".join(found_skills)

        # Extract location
        for city in INDIAN_CITIES:
            if city in message:
                params["location"] = city.title()
                break

        # Extract experience
        exp_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience',
            r'experience\s+(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*\+\s*(?:years?|yrs?)',
        ]
        for pattern in exp_patterns:
            match = re.search(pattern, message)
            if match:
                params["min_experience"] = float(match.group(1))
                break

        return params

    # ---------------------------------------------------------------
    # Step 2: Query Execution
    # ---------------------------------------------------------------

    def _execute_query(
        self,
        intent_data: Dict[str, Any],
        conn: sqlite3.Connection,
    ) -> List[Dict[str, Any]]:
        """
        Execute database queries using existing CRUD functions based on the
        parsed intent. Never executes raw SQL.

        Args:
            intent_data: Parsed intent dict with 'intent' and 'parameters' keys.
            conn: Active SQLite database connection.

        Returns:
            List of candidate dictionaries (may be empty).
        """
        intent = intent_data["intent"]
        params = intent_data.get("parameters", {})

        try:
            if intent == "search_candidates":
                return search_candidates(
                    conn,
                    skills=params.get("skills"),
                    location=params.get("location"),
                    min_experience=params.get("min_experience"),
                    max_experience=params.get("max_experience"),
                )

            elif intent == "get_candidate_details":
                candidate_id = params.get("candidate_id")
                candidate_name = params.get("candidate_name")

                if candidate_id is not None:
                    candidate = get_candidate_by_id(conn, candidate_id)
                    return [candidate] if candidate else []

                if candidate_name:
                    all_candidates = get_all_candidates(conn)
                    name_lower = candidate_name.lower()
                    return [
                        c for c in all_candidates
                        if c.get("name") and name_lower in c["name"].lower()
                    ]

                return []

            elif intent == "count_candidates":
                return search_candidates(
                    conn,
                    skills=params.get("skills"),
                    location=params.get("location"),
                    min_experience=params.get("min_experience"),
                    max_experience=params.get("max_experience"),
                )

            else:
                return []

        except Exception as e:
            logger.error("Query execution failed for intent '%s': %s", intent, e)
            return []

    # ---------------------------------------------------------------
    # Step 3: Response Generation
    # ---------------------------------------------------------------

    def _generate_response(
        self,
        message: str,
        intent_data: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        history: List[Dict[str, Any]],
    ) -> str:
        """
        Generate a natural-language response from the query results.

        Tries the LLM first. Falls back to a template-based response if:
        - No API key is configured
        - The LLM call fails

        Args:
            message: Original recruiter message.
            intent_data: Parsed intent dict.
            candidates: Candidate records from the database query.
            history: Conversation history.

        Returns:
            Conversational response string.
        """
        intent = intent_data["intent"]

        # If no API key, skip LLM and use templates
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return self._fallback_response(message, intent, candidates)

        # Format candidates for the LLM prompt
        candidates_text = self._format_candidates_for_llm(candidates, max_count=10)

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                logger.info("Generating response (attempt %d/%d)", attempt + 1, self.max_retries)
                response = self._response_chain.invoke({
                    "message": message,
                    "intent": intent,
                    "count": len(candidates),
                    "candidates": candidates_text,
                })
                if response and response.strip():
                    return response.strip()
            except Exception as e:
                last_error = e
                logger.warning("Response generation attempt %d/%d failed: %s", attempt + 1, self.max_retries, e)

        logger.error("LLM response generation failed after %d attempts. Using template.", self.max_retries)
        return self._fallback_response(message, intent, candidates)

    def _fallback_response(
        self,
        message: str,
        intent: str,
        candidates: List[Dict[str, Any]],
    ) -> str:
        """
        Generate a template-based response when the LLM is unavailable.
        Covers all four intents.

        Args:
            message: Original recruiter message (unused in templates but kept for signature consistency).
            intent: The detected intent type.
            candidates: Candidate records from the database query.

        Returns:
            Template-generated response string.
        """
        count = len(candidates)

        if intent == "count_candidates":
            if count == 0:
                return "No candidates match those criteria."
            return f"I found {count} candidate(s) matching your criteria."

        if intent == "get_candidate_details":
            if not candidates:
                return "I couldn't find a candidate matching that name or ID. Please check the details and try again."
            c = candidates[0]
            parts = [f"Here are the details for {c.get('name', 'Unknown')}:"]
            if c.get("skills"):
                parts.append(f"Skills: {c['skills']}")
            if c.get("experience_years") is not None:
                parts.append(f"Experience: {c['experience_years']} year(s)")
            if c.get("location"):
                parts.append(f"Location: {c['location']}")
            if c.get("education"):
                parts.append(f"Education: {c['education']}")
            return " | ".join(parts)

        if intent == "search_candidates":
            if count == 0:
                return "I couldn't find any candidates matching those criteria. Try broadening your search — for example, remove location or experience filters."
            names = [c.get("name", "Unknown") for c in candidates[:5]]
            names_str = ", ".join(names)
            if count <= 5:
                return f"I found {count} candidate(s): {names_str}."
            return f"I found {count} candidate(s). Here are the top ones: {names_str}."

        # general_question
        return (
            "I'm the RecruitX AI assistant! I can help you search for candidates, "
            "get details about specific candidates, or count how many candidates "
            "match certain criteria. Try asking something like "
            "\"Show Python developers in Mumbai\" or \"Who is Rahul Sharma?\""
        )

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------

    @staticmethod
    def _format_history(history: List[Dict[str, Any]]) -> str:
        """
        Format conversation history for inclusion in LLM prompts.

        Args:
            history: List of message dicts with 'role' and 'message' keys.

        Returns:
            Formatted string of recent conversation exchanges.
        """
        if not history:
            return "(No previous conversation)"

        # Take up to the last 6 messages (3 exchanges) for context
        recent = history[-6:]
        lines: List[str] = []
        for msg in recent:
            role_label = "User" if msg.get("role") == "user" else "Assistant"
            lines.append(f"{role_label}: {msg.get('message', '')}")
        return "\n".join(lines)

    @staticmethod
    def _format_candidates_for_llm(
        candidates: List[Dict[str, Any]],
        max_count: int = 10,
    ) -> str:
        """
        Format candidate records for inclusion in the LLM response generator prompt.

        Args:
            candidates: List of candidate dicts from CRUD operations.
            max_count: Maximum number of candidates to include.

        Returns:
            Formatted string representation.
        """
        if not candidates:
            return "(No candidates found)"

        lines: List[str] = []
        for c in candidates[:max_count]:
            name = c.get("name", "Unknown")
            skills = c.get("skills", "N/A")
            exp = c.get("experience_years", "N/A")
            location = c.get("location", "N/A")
            education = c.get("education", "N/A")
            lines.append(
                f"- {name}: Skills: {skills} | Experience: {exp} yrs | Location: {location} | Education: {education}"
            )

        if len(candidates) > max_count:
            lines.append(f"... and {len(candidates) - max_count} more.")

        return "\n".join(lines)
