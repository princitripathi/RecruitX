"""
agents/jd_analyst.py — JD Analyst Agent for RecruitX

This agent analyzes raw job descriptions using OpenRouter LLM and returns
a structured JDAnalysis object with required skills, preferred skills,
experience requirements, and other role metadata.

The orchestrator agent calls this agent first during the recruitment pipeline.
"""

import json
import logging
import os
from typing import List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import LLM_MAX_RETRIES, LLM_TEMPERATURE, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from utils.llm_utils import clean_json_response

logger = logging.getLogger(__name__)


class JDAnalysis(BaseModel):
    """
    Structured output from the JD Analyst Agent.

    Contains all fields extracted from a job description analysis.
    The orchestrator uses this to drive the recruitment pipeline.
    """
    required_skills: List[str] = Field(
        description="Skills that are explicitly marked as required or mandatory"
    )
    preferred_skills: List[str] = Field(
        description="Skills mentioned as preferred, nice-to-have, or plus points"
    )
    min_experience_years: float = Field(
        description="Minimum years of experience required for the role"
    )
    education_required: str = Field(
        description="Minimum education qualification required"
    )
    seniority_level: str = Field(
        description="Seniority level: Junior, Mid, Senior, or Lead"
    )
    role_summary: str = Field(
        description="A concise 2-3 sentence summary of the role"
    )
    search_query: str = Field(
        description="Optimized search query string for FAISS semantic search"
    )


SYSTEM_PROMPT = """You are an expert recruitment analyst. Your job is to analyze job descriptions and extract structured information about the role.

Extract the following from the job description:
1. required_skills: Skills that are explicitly marked as required or mandatory
2. preferred_skills: Skills mentioned as preferred, nice-to-have, or plus points
3. min_experience_years: Minimum years of experience required (as a number)
4. education_required: Minimum education qualification required
5. seniority_level: One of: Junior, Mid, Senior, or Lead
6. role_summary: A concise 2-3 sentence summary of the role
7. search_query: An optimized search string combining role, key skills, and context for FAISS semantic search

Return your response as a valid JSON object with exactly these field names and types.
Do NOT include any markdown formatting or code blocks around the JSON."""


class JDAnalystAgent:
    """
    Agent that analyzes job descriptions using OpenRouter LLM and returns structured requirements.

    Uses LangChain with OpenRouter (OpenAI-compatible API) to extract:
    - Required and preferred skills
    - Experience and education requirements
    - Seniority level and role summary
    - Optimized search query for FAISS vector search

    Has built-in retry logic (default: 3 attempts) for resilience against transient API failures.
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
        Initialize the JD Analyst Agent.

        All parameters are optional — values default to .env configuration.
        Override any parameter by passing it directly (useful for testing).

        Args:
            api_key: OpenRouter API key (default: from OPENROUTER_API_KEY env var)
            base_url: OpenRouter base URL (default: from OPENROUTER_BASE_URL env var)
            model: LLM model name (default: from OPENROUTER_MODEL env var)
            temperature: LLM temperature (default: 0.1)
            max_retries: Retry attempts on failure (default: 3)
        """
        self.api_key = api_key or OPENROUTER_API_KEY
        self.base_url = base_url or OPENROUTER_BASE_URL
        self.model = model or OPENROUTER_MODEL
        self.temperature = temperature if temperature is not None else LLM_TEMPERATURE
        self.max_retries = max_retries if max_retries is not None else LLM_MAX_RETRIES

        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            logger.warning(
                "OPENROUTER_API_KEY is not set. "
                "Set it in .env file or pass api_key parameter."
            )

        self.chain = self._create_chain()

    def _create_chain(self):
        """
        Build the LangChain processing pipeline.

        Pipeline: ChatPromptTemplate -> ChatOpenAI (via OpenRouter) -> StrOutputParser

        Returns:
            LangChain Runnable that accepts {"jd_text": str} and returns a JSON string.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{jd_text}"),
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

    def analyze(self, jd_text: str) -> JDAnalysis:
        """
        Analyze a job description and return a structured JDAnalysis object.

        Implements retry logic:
        - On failure (JSON parse error, API error, validation error), retries up to max_retries times.
        - Only raises after all attempts are exhausted.

        Args:
            jd_text: Raw job description text from the recruiter.

        Returns:
            JDAnalysis object with all extracted fields.

        Raises:
            ValueError: If jd_text is empty or not a string.
            RuntimeError: If LLM analysis fails after all retry attempts.
        """
        if not jd_text or not isinstance(jd_text, str) or not jd_text.strip():
            logger.warning("Empty or invalid job description text provided")
            raise ValueError("Job description text must be a non-empty string")

        jd_text = jd_text.strip()

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "Analyzing job description (attempt %d/%d)",
                    attempt + 1, self.max_retries
                )

                raw_response = self.chain.invoke({"jd_text": jd_text})

                cleaned = clean_json_response(raw_response)

                parsed_json = json.loads(cleaned)
                result = JDAnalysis.model_validate(parsed_json)

                summary_preview = result.role_summary
                if len(summary_preview) > 60:
                    summary_preview = summary_preview[:57] + "..."

                logger.info(
                    "Successfully analyzed job description: %s",
                    summary_preview
                )
                return result

            except (json.JSONDecodeError, Exception) as e:
                last_error = e
                logger.warning(
                    "Analysis attempt %d/%d failed",
                    attempt + 1,
                    self.max_retries,
                )

                if attempt < self.max_retries - 1:
                    logger.debug("Retrying...")

        # All attempts exhausted
        error_msg = (
            f"Failed to analyze job description after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
