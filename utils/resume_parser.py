"""
utils/resume_parser.py — AI Resume Parser for RecruitX

This module provides the ResumeParser class that extracts text from PDF and DOCX
resume files, cleans the text, and uses an LLM to parse it into a structured
candidate profile. It handles duplicate detection via MD5 file hashing,
persists new candidates to the SQLite database, and updates the FAISS vector
index so newly added candidates appear in future recruitment searches.

Usage:
    from utils.resume_parser import ResumeParser, ResumeParseResult

    parser = ResumeParser()
    result = parser.process_resume("uploads/resume_abc123.pdf", "rahul_resume.pdf")
    # result == {"candidate": {...}, "message": "...", "is_new": True}
"""

import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from database.crud import add_candidate, add_resume, get_resume_by_hash, update_candidate
from database.db_setup import get_db_connection
from embeddings.embedder import CandidateEmbedder
from embeddings.vector_store import CandidateVectorStore

logger = logging.getLogger(__name__)

# Default configuration from environment
DEFAULT_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index.bin")
FAISS_ID_MAP_PATH = os.getenv("FAISS_ID_MAP_PATH", "data/faiss_id_map.pkl")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))


class ResumeParseResult(BaseModel):
    """
    Structured output from the LLM after parsing a resume.

    Contains all fields needed to create a candidate profile in the database.
    """
    name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address of the candidate")
    phone: Optional[str] = Field(None, description="Phone number of the candidate")
    location: Optional[str] = Field(None, description="City or location of the candidate")
    skills: List[str] = Field(description="List of technical and professional skills")
    experience_years: float = Field(description="Total years of professional experience")
    education: Optional[str] = Field(None, description="Highest education qualification")
    previous_roles: Optional[List[str]] = Field(None, description="List of previous job roles")


SYSTEM_PROMPT = """You are an expert resume parser. Your job is to extract structured information from resume text.

Extract the following from the resume:
1. name: Full name of the candidate
2. email: Email address
3. phone: Phone number (if available)
4. location: City or location (if available)
5. skills: List of technical and professional skills mentioned
6. experience_years: Total years of professional experience as a number
7. education: Highest education qualification (if available)
8. previous_roles: List of previous job roles (if available)

Return your response as a valid JSON object with exactly these field names and types.
Do NOT include any markdown formatting or code blocks around the JSON."""


class ResumeParser:
    """
    Parses uploaded resume files (PDF/DOCX), extracts text, uses an LLM to
    produce a structured candidate profile, and persists the result to both
    the SQLite database and the FAISS vector index.

    The typical flow is:
        1. extract_text()       -> raw text from PDF or DOCX
        2. clean_text()         -> remove extra whitespace and special characters
        3. compute_file_hash()  -> MD5 hash for duplicate detection
        4. check_duplicate()    -> look up existing resume by hash
        5. parse_with_llm()     -> structured candidate profile via OpenRouter
        6. save_candidate()     -> add to candidates + resumes tables
        7. update_vector_store()-> add embedding to FAISS index
    """

    def __init__(self):
        logger.info("Initialized ResumeParser")

    # ---------------------------------------------------------------
    # Public orchestrator
    # ---------------------------------------------------------------

    def process_resume(
        self,
        file_path: str,
        original_filename: str,
    ) -> Dict[str, Any]:
        """
        Run the full resume processing pipeline.

        Steps:
            1. Extract text from the resume file
            2. Clean the extracted text
            3. Compute MD5 hash for duplicate detection
            4. Check if the same file was already uploaded
            5. Parse the cleaned text with LLM into a structured profile
            6. Save the candidate and resume record to the database
            7. Add the candidate to the FAISS vector index

        Args:
            file_path: Absolute or relative path to the saved resume file.
            original_filename: Original filename as uploaded by the user.

        Returns:
            Dictionary with:
                - candidate (dict): The created or existing candidate profile.
                - message (str): Human-readable status message.
                - is_new (bool): True if a new candidate was created, False if
                  a duplicate was detected and the existing record returned.
        """
        logger.info("Processing resume: %s (file: %s)", original_filename, file_path)

        # Step 1 & 2: Extract and clean text
        raw_text = self.extract_text(file_path)
        cleaned_text = self.clean_text(raw_text)

        # Step 3: Compute MD5 hash
        file_hash = self.compute_file_hash(file_path)

        # Step 4: Check for duplicates
        conn = get_db_connection()
        try:
            duplicate = self.check_duplicate(conn, file_hash)
            if duplicate is not None:
                logger.info(
                    "Duplicate resume detected (hash: %s) — returning existing candidate ID %s",
                    file_hash, duplicate.get("candidate_id"),
                )
                candidate_id = duplicate["candidate_id"]
                candidate = self._get_candidate_dict(conn, candidate_id)
                return {
                    "candidate": candidate,
                    "message": (
                        f"Duplicate resume detected — existing candidate "
                        f"'{candidate.get('name', 'Unknown')}' (ID {candidate_id}) returned."
                    ),
                    "is_new": False,
                }

            # Step 5: Parse with LLM
            profile = self.parse_with_llm(cleaned_text)

            # Step 6: Save candidate and resume record
            result = self.save_candidate(conn, profile, file_path, original_filename, file_hash, cleaned_text)
            candidate_id = result["candidate_id"]

            # Step 7: Update vector store
            self.update_vector_store(candidate_id)

            candidate = self._get_candidate_dict(conn, candidate_id)
            logger.info(
                "Successfully processed resume -> candidate ID %d (%s)",
                candidate_id, profile.name,
            )
            return {
                "candidate": candidate,
                "message": (
                    f"Resume parsed successfully — candidate "
                    f"'{profile.name}' (ID {candidate_id}) created."
                ),
                "is_new": True,
            }

        except Exception as e:
            logger.error("Resume processing failed: %s", str(e), exc_info=True)
            raise
        finally:
            conn.close()

    # ---------------------------------------------------------------
    # Step 1: Text extraction
    # ---------------------------------------------------------------

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a resume file based on its extension.

        Args:
            file_path: Path to the resume file.

        Returns:
            Extracted raw text from the file.

        Raises:
            ValueError: If the file type is unsupported.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        _, ext = os.path.splitext(file_path.lower())

        if ext == ".pdf":
            return self._extract_pdf(file_path)
        elif ext == ".docx":
            return self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type '{ext}'. Only .pdf and .docx are supported.")

    def _extract_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using PyPDF2.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text from all pages.
        """
        try:
            import pypdf
        except ImportError:
            logger.error("pypdf is not installed. Install it with: pip install pypdf")
            raise RuntimeError("pypdf is required for PDF extraction")

        text_parts: List[str] = []
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            logger.error("Failed to extract text from PDF '%s': %s", file_path, str(e))
            raise RuntimeError(f"PDF extraction failed: {e}")

        full_text = "\n".join(text_parts)
        logger.info("Extracted %d characters from PDF '%s'", len(full_text), file_path)
        return full_text

    def _extract_docx(self, file_path: str) -> str:
        """
        Extract text from a DOCX file using python-docx.

        Args:
            file_path: Path to the DOCX file.

        Returns:
            Extracted text from all paragraphs.
        """
        try:
            from docx import Document
        except ImportError:
            logger.error("python-docx is not installed. Install it with: pip install python-docx")
            raise RuntimeError("python-docx is required for DOCX extraction")

        text_parts: List[str] = []
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
        except Exception as e:
            logger.error("Failed to extract text from DOCX '%s': %s", file_path, str(e))
            raise RuntimeError(f"DOCX extraction failed: {e}")

        full_text = "\n".join(text_parts)
        logger.info("Extracted %d characters from DOCX '%s'", len(full_text), file_path)
        return full_text

    # ---------------------------------------------------------------
    # Step 2: Text cleaning
    # ---------------------------------------------------------------

    def clean_text(self, raw_text: str) -> str:
        """
        Clean extracted resume text by normalizing whitespace and
        removing problematic characters.

        Cleaning steps:
            1. Replace carriage returns and tabs with newlines/spaces
            2. Collapse multiple consecutive newlines into one
            3. Collapse multiple consecutive spaces into one
            4. Remove null bytes and other non-printable characters
            5. Strip leading/trailing whitespace

        Args:
            raw_text: Raw text extracted from the resume file.

        Returns:
            Cleaned text string.
        """
        if not raw_text:
            return ""

        text = raw_text

        # Replace carriage returns and tabs
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")

        # Collapse multiple newlines into one
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Collapse multiple spaces into one (but keep single newlines)
        text = re.sub(r"[ ]{2,}", " ", text)

        # Remove null bytes and non-printable characters (except common whitespace)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

        # Strip leading and trailing whitespace
        text = text.strip()

        logger.debug("Cleaned text: %d characters -> %d characters", len(raw_text), len(text))
        return text

    # ---------------------------------------------------------------
    # Step 3: File hash computation
    # ---------------------------------------------------------------

    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute the MD5 hash of a file for duplicate detection.

        Args:
            file_path: Path to the file.

        Returns:
            MD5 hex digest string.
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
        except Exception as e:
            logger.error("Failed to compute hash for '%s': %s", file_path, str(e))
            raise RuntimeError(f"Failed to compute file hash: {e}")

        digest = hash_md5.hexdigest()
        logger.debug("Computed MD5 hash for '%s': %s", file_path, digest)
        return digest

    # ---------------------------------------------------------------
    # Step 4: Duplicate check
    # ---------------------------------------------------------------

    def check_duplicate(self, conn, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if a resume with the given MD5 hash already exists.

        Args:
            conn: Active SQLite connection.
            file_hash: MD5 hash of the uploaded file.

        Returns:
            Resume dict if a duplicate exists, None otherwise.
        """
        try:
            existing = get_resume_by_hash(conn, file_hash)
            if existing:
                logger.info("Duplicate resume found for hash: %s", file_hash)
                return dict(existing)
            return None
        except Exception as e:
            logger.error("Duplicate check failed for hash '%s': %s", file_hash, str(e))
            raise RuntimeError(f"Duplicate check failed: {e}")

    # ---------------------------------------------------------------
    # Step 5: LLM parsing
    # ---------------------------------------------------------------

    def _create_parse_chain(self) -> Any:
        """
        Build the LangChain processing pipeline for resume parsing.

        Pipeline: ChatPromptTemplate -> ChatOpenAI (via OpenRouter) -> StrOutputParser

        Separated into its own method to allow easy mocking in tests.

        Returns:
            LangChain Runnable that accepts {"resume_text": str} and returns a JSON string.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{resume_text}"),
        ])

        llm = ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            base_url=os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL),
            model=os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
            temperature=0.1,
        )

        return prompt | llm | StrOutputParser()

    def parse_with_llm(
        self,
        cleaned_text: str,
    ) -> ResumeParseResult:
        """
        Parse cleaned resume text using an LLM and return a structured profile.

        Uses OpenRouter (OpenAI-compatible) LLM with LangChain.

        Args:
            cleaned_text: The cleaned resume text.

        Returns:
            ResumeParseResult with structured candidate profile.

        Raises:
            RuntimeError: If LLM parsing fails after retries.
        """
        chain = self._create_parse_chain()

        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                logger.info(
                    "Parsing resume with LLM (attempt %d/%d)",
                    attempt + 1, max_retries,
                )

                raw_response = chain.invoke({"resume_text": cleaned_text})

                cleaned_response = raw_response.strip()
                if "```" in cleaned_response:
                    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned_response)
                    if json_match:
                        cleaned_response = json_match.group(1).strip()
                    else:
                        cleaned_response = cleaned_response.replace("```json", "").replace("```", "").strip()

                parsed_json = json.loads(cleaned_response)
                result = ResumeParseResult.model_validate(parsed_json)

                logger.info("Successfully parsed resume: %s", result.name)
                return result

            except (json.JSONDecodeError, Exception) as e:
                last_error = e
                logger.warning("LLM parsing attempt %d/%d failed: %s", attempt + 1, max_retries, str(e))

                if attempt < max_retries - 1:
                    logger.info("Retrying LLM parsing...")

        error_msg = (
            f"Failed to parse resume with LLM after {max_retries} attempts. "
            f"Last error: {last_error}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # ---------------------------------------------------------------
    # Step 6: Save candidate to database
    # ---------------------------------------------------------------

    def save_candidate(
        self,
        conn,
        profile: ResumeParseResult,
        file_path: str,
        original_filename: str,
        file_hash: str,
        parsed_text: str,
    ) -> Dict[str, Any]:
        """
        Save a parsed candidate profile to the database.

        Creates records in both the candidates and resumes tables.

        Args:
            conn: Active SQLite connection.
            profile: Structured candidate profile from LLM parsing.
            file_path: Path to the saved resume file.
            original_filename: Original filename from upload.
            file_hash: MD5 hash of the file.
            parsed_text: The raw extracted text (stored in resumes table).

        Returns:
            Dict with 'candidate_id' (int).

        Raises:
            ValueError: If a candidate with the same email already exists.
        """
        skills_str = ", ".join(profile.skills) if profile.skills else ""
        previous_roles_str = None
        if profile.previous_roles:
            previous_roles_str = "; ".join(profile.previous_roles)

        candidate_id = add_candidate(
            conn=conn,
            name=profile.name,
            email=profile.email,
            skills=skills_str,
            experience_years=profile.experience_years,
            phone=profile.phone,
            location=profile.location,
            education=profile.education,
            previous_roles=previous_roles_str,
            profile_completeness=80,
            last_active_days=0,
            resume_path=file_path,
        )

        resume_id = add_resume(
            conn=conn,
            file_name=original_filename,
            file_path=file_path,
            file_hash=file_hash,
            candidate_id=candidate_id,
            parsed_text=parsed_text,
        )

        logger.info(
            "Saved candidate ID %d and resume ID %d to database",
            candidate_id, resume_id,
        )

        return {"candidate_id": candidate_id, "resume_id": resume_id}

    # ---------------------------------------------------------------
    # Step 7: Update FAISS vector index
    # ---------------------------------------------------------------

    def update_vector_store(self, candidate_id: int) -> None:
        """
        Add a candidate's embedding to the FAISS vector index.

        Loads the existing index, generates an embedding for the new candidate,
        appends it, and saves the updated index to disk.

        Args:
            candidate_id: ID of the candidate to add to the index.
        """
        conn = get_db_connection()
        try:
            from database.crud import get_candidate_by_id

            candidate = get_candidate_by_id(conn, candidate_id)
            if candidate is None:
                logger.warning("Candidate ID %d not found — skipping vector store update", candidate_id)
                return

            candidate_text = self._generate_candidate_text(dict(candidate))

            embedder = CandidateEmbedder()
            embedding = embedder.embed_text(candidate_text)

            vector_store = CandidateVectorStore(dimension=EMBEDDING_DIMENSION)

            index_path = FAISS_INDEX_PATH
            map_path = FAISS_ID_MAP_PATH

            if os.path.exists(index_path) and os.path.exists(map_path):
                try:
                    vector_store.load(index_path, map_path)
                    logger.info("Loaded existing FAISS index with %d vectors", vector_store.index.ntotal)
                except Exception as e:
                    logger.warning("Could not load existing index, starting fresh: %s", str(e))

            vector_store.add_candidates([candidate_id], [embedding])
            vector_store.save(index_path, map_path)

            faiss_position = len(vector_store.id_map) - 1
            update_candidate(conn, candidate_id, embedding_id=faiss_position)

            logger.info(
                "Added candidate ID %d to FAISS index at position %d",
                candidate_id, faiss_position,
            )

        except Exception as e:
            logger.error("Failed to update vector store for candidate ID %d: %s", candidate_id, str(e))
            raise RuntimeError(f"Vector store update failed: {e}")
        finally:
            conn.close()

    def _generate_candidate_text(self, candidate: Dict[str, Any]) -> str:
        """
        Generate a text representation of a candidate for embedding.

        Mirrors the logic in embeddings/build_index.py.

        Args:
            candidate: Candidate dictionary from the database.

        Returns:
            A formatted string describing the candidate.
        """
        name = candidate.get("name", "").strip()
        location = candidate.get("location", "").strip()
        skills = candidate.get("skills", "").strip()
        experience = candidate.get("experience_years", 0)
        education = candidate.get("education", "").strip()
        previous_roles = candidate.get("previous_roles")

        text_parts = []
        if name:
            text_parts.append(f"Candidate: {name}.")
        if location:
            text_parts.append(f"Location: {location}.")
        if skills:
            text_parts.append(f"Skills: {skills}.")
        if experience is not None:
            text_parts.append(f"Experience: {experience} years.")
        if education:
            text_parts.append(f"Education: {education}.")
        if previous_roles:
            roles_clean = str(previous_roles).replace(";", ",").strip()
            text_parts.append(f"Previous Roles: {roles_clean}.")

        return " ".join(text_parts)

    # ---------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------

    def _get_candidate_dict(self, conn, candidate_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a full candidate dict from the database.

        Args:
            conn: Active SQLite connection.
            candidate_id: Candidate ID.

        Returns:
            Candidate dict or None.
        """
        from database.crud import get_candidate_by_id
        candidate = get_candidate_by_id(conn, candidate_id)
        return dict(candidate) if candidate else None
