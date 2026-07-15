"""
utils/interview_generator.py — Interview Question Generator for RecruitX

This module provides the InterviewQuestionGenerator class that uses an LLM
(via OpenRouter) to generate 5-10 personalized interview questions for a
candidate based on their profile, the job description, the skill gap analysis,
and the orchestrator's explanation of why the candidate matched.

Questions target:
    - Missing skills (highest priority)
    - Experience verification (probe claimed experience)
    - Role-specific technical depth
    - Behavioral fit (where appropriate)

Usage:
    from utils.interview_generator import InterviewQuestionGenerator, InterviewQuestions

    generator = InterviewQuestionGenerator()
    result = generator.generate(
        candidate_info={"name": "Rahul Sharma", ...},
        job_description="We are looking for a Senior Python Developer...",
        skill_gap={"matched": ["Python"], "missing": ["Docker"], "bonus": ["SQL"]},
        explanation="Rank #1. Matched 3 skill(s), missing 1 skill(s)...",
    )
    # result == InterviewQuestions(questions=["...", "...", ...])
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Default configuration from environment
DEFAULT_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")


SYSTEM_PROMPT = """You are a senior technical interviewer conducting a real interview. Your job is to generate concise, grounded, personalized interview questions for a job candidate.

You will receive:
1. Candidate Profile — name, skills, experience, education, previous roles.
2. Job Description — the role the candidate applied for.
3. Skill Gap Analysis — skills the candidate matched, is missing, and bonus skills.
4. Ranking Explanation — why the recruiter's AI system recommended this candidate.

Generate between 5 and 10 questions. Every single question must be grounded in the candidate's resume, the job description, or an identified skill gap.

GROUNDING RULE
Never invent technologies, frameworks, companies, responsibilities, certifications, or projects that are not explicitly mentioned in the candidate profile or the job description.
Do not assume the candidate has hands-on experience with a technology just because it appears in the job description. Only treat skills listed in the candidate's resume as experience they have.
Do not combine unrelated skills into the same question (for example, asking about NLP and OpenCV in one project) unless the resume explicitly shows the candidate has used them together.

EXPERIENCE-ADAPTED QUESTIONS
If the candidate has 0-2 years of experience, prioritize academic projects, internships, hackathons, coursework, and leadership roles instead of professional work experience.
Match the wording to the candidate's seniority: use simpler terminology for freshers and industry-level language for experienced candidates.

If a missing skill has no overlap with anything on the resume, ask about learning ability instead of assuming experience.
Example:
"The role requires Docker, which is not on your resume. How would you approach learning Docker for deployment?"

If a missing skill is partially covered by a similar skill the candidate has, ask an adaptation question.
Example:
"You have experience with FastAPI. How would you adapt your knowledge to build the same API using Flask?"

QUESTION FORMAT
- Each question must be at most 2 sentences (roughly 35-45 words).
- Do not combine multiple unrelated questions into one.
- Questions should sound like a real technical interviewer speaking aloud.
- Prefer practical, conversational phrasing over academic or textbook wording. For example, ask "How would you build a feature that lets users search by date range?" instead of "Explain the implementation of parameterized query filtering in RESTful architectures."
- Avoid generic questions such as "Tell me about yourself" or "Where do you see yourself in 5 years?"

QUESTION MIX (target these proportions per interview)
- 4-5 technical questions covering core required skills from the JD and the candidate's strongest skills.
- 1-2 resume/project verification questions that probe claims on the resume.
- 1-2 behavioral or situational questions.

DIFFICULTY PROGRESSION
Questions should progress in difficulty: easy, medium, medium, hard, behavioral.

PRIORITY ORDER
When choosing topics, follow this priority:
1. Core required skills from the job description.
2. Candidate's strongest skills.
3. Important missing skills.
4. Projects that verify resume claims.
5. Behavioral questions.

SKILL REPETITION
Avoid testing the same skill across multiple questions unless the job description explicitly requires that skill at a deep level.

MISSING SKILL HANDLING
Missing skills should generate verification or adaptation questions, not open-ended deep dives. See the examples above.

Return your response as a JSON object with a single key "questions" containing a list of strings.
Example:
{{
    "questions": [
        "How would you design a REST API for a payment service? What considerations would you make regarding versioning and idempotency?",
        "You have experience with FastAPI. How would you adapt your knowledge to build the same API using Flask?"
    ]
}}
Do NOT include any markdown formatting or code blocks around the JSON."""


class InterviewQuestions(BaseModel):
    """
    Structured output from the LLM after generating interview questions.

    Contains a list of personalized interview question strings.
    """
    questions: List[str] = Field(
        ...,
        min_length=5,
        max_length=10,
        description="List of 5-10 personalized interview questions",
    )


class InterviewQuestionGenerator:
    """
    Generates personalized interview questions for a candidate using an LLM.

    The generator takes the full context of a candidate's profile, the job
    description, the skill gap analysis, and the ranking explanation to
    produce targeted questions that probe missing skills, verify experience,
    and assess role-specific technical depth.

    Typical flow:
        1. Build a context string from all inputs
        2. Call LLM with structured prompt
        3. Parse JSON response into InterviewQuestions model
        4. Return the list of questions
    """

    def __init__(self) -> None:
        """Initialize the Interview Question Generator."""
        self._generation_chain = None
        logger.info("Initialized InterviewQuestionGenerator")

    def _get_generation_chain(self):
        """Return a cached LangChain chain for question generation."""
        if self._generation_chain is None:
            self._generation_chain = self._create_generation_chain()
        return self._generation_chain

    # ---------------------------------------------------------------
    # Public interface
    # ---------------------------------------------------------------

    def generate(
        self,
        candidate_info: Dict[str, Any],
        job_description: str,
        skill_gap: Dict[str, List[str]],
        explanation: str,
    ) -> InterviewQuestions:
        """
        Generate personalized interview questions for a candidate.

        Args:
            candidate_info: Candidate profile dict with keys like name, skills,
                experience_years, education, previous_roles, location.
            job_description: Raw job description text from the recruiter.
            skill_gap: Dict with "matched", "missing", "bonus" lists of skills.
            explanation: Human-readable explanation from the orchestrator of
                why this candidate was ranked as they were.

        Returns:
            InterviewQuestions object with a list of 5-10 question strings.

        Raises:
            ValueError: If inputs are empty or invalid.
            RuntimeError: If LLM generation fails after all retries.
        """
        # Validate inputs
        if not job_description or not isinstance(job_description, str) or not job_description.strip():
            logger.error("Empty or invalid job description provided")
            raise ValueError("job_description must be a non-empty string")

        if not candidate_info or not isinstance(candidate_info, dict):
            logger.error("Empty or invalid candidate_info provided")
            raise ValueError("candidate_info must be a non-empty dict")

        # Build the context string for the LLM prompt
        context = self._build_context(candidate_info, job_description, skill_gap, explanation)

        # Call LLM with retry logic
        return self._generate_with_llm(context)

    # ---------------------------------------------------------------
    # Context builder
    # ---------------------------------------------------------------

    def _build_context(
        self,
        candidate_info: Dict[str, Any],
        job_description: str,
        skill_gap: Dict[str, List[str]],
        explanation: str,
    ) -> str:
        """
        Build a structured context string from all inputs for the LLM prompt.

        Args:
            candidate_info: Candidate profile dict.
            job_description: Raw job description text.
            skill_gap: Dict with matched/missing/bonus skill lists.
            explanation: Orchestrator's ranking explanation.

        Returns:
            A formatted string containing all context sections.
        """
        sections: List[str] = []

        # Section 1: Candidate Profile
        profile_lines: List[str] = []
        profile_lines.append(f"Name: {candidate_info.get('name', 'Unknown')}")
        profile_lines.append(f"Skills: {candidate_info.get('skills', 'N/A')}")
        profile_lines.append(f"Experience: {candidate_info.get('experience_years', 0)} years")
        education = candidate_info.get('education')
        if education:
            profile_lines.append(f"Education: {education}")
        location = candidate_info.get('location')
        if location:
            profile_lines.append(f"Location: {location}")
        previous_roles = candidate_info.get('previous_roles')
        if previous_roles:
            profile_lines.append(f"Previous Roles: {previous_roles}")
        sections.append("=== CANDIDATE PROFILE ===")
        sections.extend(profile_lines)
        sections.append("")

        # Section 2: Job Description
        sections.append("=== JOB DESCRIPTION ===")
        sections.append(job_description.strip())
        sections.append("")

        # Section 3: Skill Gap Analysis
        sections.append("=== SKILL GAP ANALYSIS ===")
        sections.append(f"Matched Skills: {', '.join(skill_gap.get('matched', [])) or 'None'}")
        sections.append(f"Missing Skills: {', '.join(skill_gap.get('missing', [])) or 'None'}")
        sections.append(f"Bonus Skills: {', '.join(skill_gap.get('bonus', [])) or 'None'}")
        sections.append("")

        # Section 4: Ranking Explanation
        sections.append("=== RANKING EXPLANATION ===")
        sections.append(explanation.strip())
        sections.append("")

        return "\n".join(sections)

    # ---------------------------------------------------------------
    # LLM interaction
    # ---------------------------------------------------------------

    def _create_generation_chain(self) -> Any:
        """
        Build the LangChain processing pipeline for question generation.

        Pipeline: ChatPromptTemplate -> ChatOpenAI (via OpenRouter) -> StrOutputParser

        Separated into its own method to allow easy mocking in tests.

        Returns:
            LangChain Runnable that accepts {"context": str} and returns a JSON string.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{context}"),
        ])

        llm = ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            base_url=os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL),
            model=os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
            temperature=0.3,
            request_timeout=30,
            max_retries=1,
        )

        return prompt | llm | StrOutputParser()

    def _generate_with_llm(self, context: str) -> InterviewQuestions:
        """
        Generate interview questions by calling the LLM with retry logic.

        Args:
            context: Formatted context string for the prompt.

        Returns:
            InterviewQuestions object with validated questions.

        Raises:
            RuntimeError: If LLM generation fails after all retries.
        """
        chain = self._get_generation_chain()

        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                logger.info(
                    "Generating interview questions with LLM (attempt %d/%d)",
                    attempt + 1, max_retries,
                )

                raw_response = chain.invoke({"context": context})

                cleaned_response = raw_response.strip()
                if "```" in cleaned_response:
                    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned_response)
                    if json_match:
                        cleaned_response = json_match.group(1).strip()
                    else:
                        cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()

                parsed_json = json.loads(cleaned_response)
                result = InterviewQuestions.model_validate(parsed_json)

                # Validate question count is within 5-10 range
                if len(result.questions) < 5:
                    logger.warning(
                        "Generated only %d questions (minimum 5 required), re-requesting",
                        len(result.questions),
                    )
                    raise ValueError(f"Only {len(result.questions)} questions generated, minimum is 5")

                logger.info(
                    "Successfully generated %d interview questions",
                    len(result.questions),
                )
                return result

            except (json.JSONDecodeError, ValueError, Exception) as e:
                last_error = e
                logger.warning(
                    "LLM generation attempt %d/%d failed: %s",
                    attempt + 1, max_retries, str(e),
                )

                if attempt < max_retries - 1:
                    logger.info("Retrying question generation...")

        error_msg = (
            f"Failed to generate interview questions after {max_retries} attempts. "
            f"Last error: {last_error}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
