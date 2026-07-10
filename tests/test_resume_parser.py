"""
tests/test_resume_parser.py — Tests for the Resume Parser (Phase 13)

Tests cover:
    - PDF text extraction
    - DOCX text extraction
    - Text cleaning
    - MD5 hashing
    - Duplicate detection
    - Mocked LLM parsing with ResumeParseResult validation
    - Unsupported file type handling
    - Integration: database + FAISS updates (mocked)

Run with:
    pytest tests/test_resume_parser.py -v
"""

import hashlib
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from utils.resume_parser import ResumeParseResult, ResumeParser


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def parser() -> ResumeParser:
    """Return a fresh ResumeParser instance for each test."""
    return ResumeParser()


@pytest.fixture
def sample_pdf_path() -> str:
    """Create a temporary PDF-like file for extraction tests."""
    # This is NOT a valid PDF — just binary content. For true PDF extraction
    # tests we use mocking. This file is for hash/extraction-error tests.
    fd, path = tempfile.mkstemp(suffix=".pdf", prefix="test_resume_")
    with os.fdopen(fd, "wb") as f:
        f.write(b"Fake PDF content for testing")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_docx_path() -> str:
    """Create a temporary .docx-like file for extraction tests."""
    fd, path = tempfile.mkstemp(suffix=".docx", prefix="test_resume_")
    with os.fdopen(fd, "wb") as f:
        f.write(b"Fake DOCX content for testing")
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_txt_path() -> str:
    """Create a temporary .txt file for unsupported-type tests."""
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="test_resume_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("This is a plain text file")
    yield path
    if os.path.exists(path):
        os.remove(path)


# ===================================================================
# ResumeParseResult Model Tests
# ===================================================================


class TestResumeParseResultModel:
    """Verify the Pydantic model for structured LLM output."""

    def test_valid_result(self):
        """Test creation with all fields."""
        result = ResumeParseResult(
            name="Rahul Sharma",
            email="rahul@example.com",
            phone="9876543210",
            location="Bangalore",
            skills=["Python", "SQL", "FastAPI"],
            experience_years=5.0,
            education="B.Tech Computer Science",
            previous_roles=["Data Analyst at TCS", "Backend Dev at Infosys"],
        )
        assert result.name == "Rahul Sharma"
        assert result.email == "rahul@example.com"
        assert result.phone == "9876543210"
        assert result.location == "Bangalore"
        assert result.skills == ["Python", "SQL", "FastAPI"]
        assert result.experience_years == 5.0
        assert result.education == "B.Tech Computer Science"
        assert result.previous_roles == ["Data Analyst at TCS", "Backend Dev at Infosys"]

    def test_minimal_result(self):
        """Test creation with only required fields."""
        result = ResumeParseResult(
            name="Priya Singh",
            email="priya@example.com",
            skills=["Java"],
            experience_years=3.0,
        )
        assert result.name == "Priya Singh"
        assert result.email == "priya@example.com"
        assert result.skills == ["Java"]
        assert result.experience_years == 3.0
        assert result.phone is None
        assert result.location is None
        assert result.education is None
        assert result.previous_roles is None

    def test_model_validation_from_dict(self):
        """Test validation from a dict (simulating LLM JSON output)."""
        data = {
            "name": "Amit Kumar",
            "email": "amit@example.com",
            "skills": ["Python", "Django"],
            "experience_years": 2.5,
        }
        result = ResumeParseResult.model_validate(data)
        assert result.name == "Amit Kumar"
        assert result.experience_years == 2.5

    def test_invalid_missing_required_name(self):
        """Test that name is required."""
        with pytest.raises(Exception):
            ResumeParseResult(
                email="test@test.com",
                skills=["Python"],
                experience_years=1.0,
            )

    def test_invalid_missing_required_email(self):
        """Test that email is required."""
        with pytest.raises(Exception):
            ResumeParseResult(
                name="Test User",
                skills=["Python"],
                experience_years=1.0,
            )


# ===================================================================
# PDF Text Extraction
# ===================================================================


class TestPdfExtraction:
    """Tests for _extract_pdf method."""

    def test_extract_pdf_success(self, parser, tmp_path):
        """Test successful text extraction from a PDF."""
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        mock_text = "Rahul Sharma\nPython Developer\nSkills: Python, SQL"
        mock_page = MagicMock()
        mock_page.extract_text.return_value = mock_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("pypdf.PdfReader", return_value=mock_reader):
            text = parser._extract_pdf(str(pdf_file))
            assert "Rahul Sharma" in text
            assert "Python" in text
            assert "SQL" in text

    def test_extract_pdf_multiple_pages(self, parser, tmp_path):
        """Test extraction from a multi-page PDF."""
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        mock_pages = []
        for i in range(3):
            page = MagicMock()
            page.extract_text.return_value = f"Page {i + 1} content."
            mock_pages.append(page)

        mock_reader = MagicMock()
        mock_reader.pages = mock_pages

        with patch("pypdf.PdfReader", return_value=mock_reader):
            text = parser._extract_pdf(str(pdf_file))
            assert "Page 1" in text
            assert "Page 2" in text
            assert "Page 3" in text

    def test_extract_pdf_empty_page(self, parser, tmp_path):
        """Test that empty pages are handled gracefully."""
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("pypdf.PdfReader", return_value=mock_reader):
            text = parser._extract_pdf(str(pdf_file))
            assert text == ""

    def test_extract_pdf_file_not_found(self, parser):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            parser.extract_text("nonexistent_file.pdf")

    def test_extract_pdf_runtime_error(self, parser, tmp_path):
        """Test that PyPDF2 errors are wrapped in RuntimeError."""
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        mock_page = MagicMock()
        mock_page.extract_text.side_effect = Exception("Corrupt PDF")
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("pypdf.PdfReader", return_value=mock_reader):
            with pytest.raises(RuntimeError, match="PDF extraction failed"):
                parser._extract_pdf(str(pdf_file))


# ===================================================================
# DOCX Text Extraction
# ===================================================================


class TestDocxExtraction:
    """Tests for _extract_docx method."""

    def test_extract_docx_success(self, parser):
        """Test successful text extraction from a DOCX."""
        mock_paragraphs = []
        for text in ["Rahul Sharma", "Python Developer", "Skills: Python, SQL"]:
            para = MagicMock()
            para.text = text
            para.strip.return_value = text.strip()
            mock_paragraphs.append(para)

        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paragraphs

        with patch("docx.Document", return_value=mock_doc):
            text = parser._extract_docx("dummy.docx")
            assert "Rahul Sharma" in text
            assert "Python Developer" in text
            assert "Skills: Python, SQL" in text

    def test_extract_docx_skip_empty(self, parser):
        """Test that empty paragraphs are skipped."""
        para_empty = MagicMock()
        para_empty.text = ""
        para_empty.strip.return_value = ""
        para_valid = MagicMock()
        para_valid.text = "Valid content"
        para_valid.strip.return_value = "Valid content"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [para_empty, para_valid]

        with patch("docx.Document", return_value=mock_doc):
            text = parser._extract_docx("dummy.docx")
            assert "Valid content" in text
            assert "" not in text.split("\n")

    def test_extract_docx_runtime_error(self, parser):
        """Test that python-docx errors are wrapped in RuntimeError."""
        with patch("docx.Document", side_effect=Exception("Corrupt DOCX")):
            with pytest.raises(RuntimeError, match="DOCX extraction failed"):
                parser._extract_docx("dummy.docx")


# ===================================================================
# Text Cleaning
# ===================================================================


class TestTextCleaning:
    """Tests for clean_text method."""

    def test_clean_extra_spaces(self, parser):
        """Test collapsing multiple spaces."""
        raw = "Rahul    Sharma   \n\nSkills:   Python, SQL"
        cleaned = parser.clean_text(raw)
        assert "  " not in cleaned

    def test_clean_carriage_returns(self, parser):
        """Test normalising \\r\\n to \\n."""
        raw = "Name: Rahul\r\nSkills: Python\r\nLocation: Mumbai\r"
        cleaned = parser.clean_text(raw)
        assert "\r" not in cleaned

    def test_clean_tabs(self, parser):
        """Test replacing tabs with spaces."""
        raw = "Name:\tRahul\tSharma"
        cleaned = parser.clean_text(raw)
        assert "\t" not in cleaned

    def test_clean_null_bytes(self, parser):
        """Test removing null bytes."""
        raw = "Rahul\x00Sharma\x00"
        cleaned = parser.clean_text(raw)
        assert "\x00" not in cleaned

    def test_clean_multiple_newlines(self, parser):
        """Test collapsing 3+ newlines into 2."""
        raw = "Line 1\n\n\n\n\nLine 2"
        cleaned = parser.clean_text(raw)
        assert "\n\n\n" not in cleaned

    def test_clean_strip_whitespace(self, parser):
        """Test leading/trailing whitespace removal."""
        raw = "  \n  Rahul Sharma  \n  "
        cleaned = parser.clean_text(raw)
        assert cleaned == "Rahul Sharma"

    def test_clean_empty_string(self, parser):
        """Test cleaning an empty string."""
        assert parser.clean_text("") == ""
        assert parser.clean_text(None) == ""

    def test_clean_preserves_content(self, parser):
        """Test that meaningful content is preserved after cleaning."""
        raw = "  Rahul   Sharma\nSkills:  Python,  SQL  "
        cleaned = parser.clean_text(raw)
        assert "Rahul" in cleaned
        assert "Sharma" in cleaned
        assert "Python" in cleaned
        assert "SQL" in cleaned


# ===================================================================
# MD5 Hashing
# ===================================================================


class TestMD5Hashing:
    """Tests for compute_file_hash method."""

    def test_hash_consistency(self, parser):
        """Test that the same file produces the same hash."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd, "wb") as f:
            f.write(b"consistent content")
        try:
            hash1 = parser.compute_file_hash(path)
            hash2 = parser.compute_file_hash(path)
            assert hash1 == hash2
        finally:
            os.remove(path)

    def test_hash_different_files(self, parser):
        """Test that different files produce different hashes."""
        fd1, path1 = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd1, "wb") as f:
            f.write(b"content A")
        fd2, path2 = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd2, "wb") as f:
            f.write(b"content B")
        try:
            hash1 = parser.compute_file_hash(path1)
            hash2 = parser.compute_file_hash(path2)
            assert hash1 != hash2
        finally:
            os.remove(path1)
            os.remove(path2)

    def test_hash_matches_expected(self, parser):
        """Test that hash matches a known MD5 value."""
        content = b"Hello Resume"
        fd, path = tempfile.mkstemp(suffix=".pdf")
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        try:
            expected = hashlib.md5(content).hexdigest()
            actual = parser.compute_file_hash(path)
            assert actual == expected
        finally:
            os.remove(path)

    def test_hash_missing_file(self, parser):
        """Test that hashing a missing file raises."""
        with pytest.raises(RuntimeError, match="Failed to compute file hash"):
            parser.compute_file_hash("nonexistent_file.pdf")


# ===================================================================
# Duplicate Detection
# ===================================================================


class TestDuplicateDetection:
    """Tests for check_duplicate method."""

    def test_duplicate_exists(self, parser):
        """Test that an existing hash returns the resume record."""
        mock_conn = MagicMock()
        mock_resume = {"id": 1, "file_hash": "abc123", "candidate_id": 5}

        with patch("utils.resume_parser.get_resume_by_hash", return_value=mock_resume):
            result = parser.check_duplicate(mock_conn, "abc123")
            assert result is not None
            assert result["file_hash"] == "abc123"
            assert result["candidate_id"] == 5

    def test_no_duplicate(self, parser):
        """Test that a new hash returns None."""
        mock_conn = MagicMock()

        with patch("utils.resume_parser.get_resume_by_hash", return_value=None):
            result = parser.check_duplicate(mock_conn, "new_hash")
            assert result is None


# ===================================================================
# LLM Parsing
# ===================================================================


class TestLLMParsing:
    """Tests for parse_with_llm method."""

    VALID_RESUME_TEXT = "Rahul Sharma\nemail: rahul@test.com\nPython, SQL expert"
    MOCK_JSON = json.dumps({
        "name": "Rahul Sharma",
        "email": "rahul@test.com",
        "phone": "9876543210",
        "location": "Bangalore",
        "skills": ["Python", "SQL"],
        "experience_years": 5.0,
        "education": "B.Tech Computer Science",
        "previous_roles": ["Data Analyst", "Backend Developer"],
    })

    def test_parse_success(self, parser):
        """Test successful LLM parsing returns a valid ResumeParseResult."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = self.MOCK_JSON

        with patch.object(parser, "_create_parse_chain", return_value=mock_chain):
            result = parser.parse_with_llm(self.VALID_RESUME_TEXT)

        assert isinstance(result, ResumeParseResult)
        assert result.name == "Rahul Sharma"
        assert result.email == "rahul@test.com"
        assert result.phone == "9876543210"
        assert result.location == "Bangalore"
        assert result.skills == ["Python", "SQL"]
        assert result.experience_years == 5.0
        assert result.education == "B.Tech Computer Science"
        assert result.previous_roles == ["Data Analyst", "Backend Developer"]

    def test_parse_handles_markdown_code_blocks(self, parser):
        """Test LLM response wrapped in ```json ... ``` blocks."""
        markdown_response = f"```json\n{self.MOCK_JSON}\n```"
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = markdown_response

        with patch.object(parser, "_create_parse_chain", return_value=mock_chain):
            result = parser.parse_with_llm(self.VALID_RESUME_TEXT)

        assert result.name == "Rahul Sharma"
        assert result.email == "rahul@test.com"

    def test_parse_handles_plain_code_blocks(self, parser):
        """Test LLM response wrapped in ``` (without json) blocks."""
        markdown_response = f"```\n{self.MOCK_JSON}\n```"
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = markdown_response

        with patch.object(parser, "_create_parse_chain", return_value=mock_chain):
            result = parser.parse_with_llm(self.VALID_RESUME_TEXT)

        assert result.name == "Rahul Sharma"
        assert result.email == "rahul@test.com"

    def test_parse_retry_then_succeed(self, parser):
        """Test retry logic: first 2 attempts fail, 3rd succeeds."""
        side_effects = [
            json.JSONDecodeError("Invalid JSON", "", 0),
            json.JSONDecodeError("Invalid JSON", "", 0),
            self.MOCK_JSON,
        ]
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = side_effects

        with patch.object(parser, "_create_parse_chain", return_value=mock_chain):
            result = parser.parse_with_llm(self.VALID_RESUME_TEXT)

        assert isinstance(result, ResumeParseResult)
        assert result.name == "Rahul Sharma"

    def test_parse_all_retries_fail(self, parser):
        """Test that RuntimeError is raised when all retries fail."""
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = Exception("API error")

        with patch.object(parser, "_create_parse_chain", return_value=mock_chain):
            with pytest.raises(RuntimeError, match="Failed to parse resume"):
                parser.parse_with_llm(self.VALID_RESUME_TEXT)


# ===================================================================
# Unsupported File Type
# ===================================================================


class TestUnsupportedFileType:
    """Tests for handling unsupported file types."""

    def test_unsupported_extension(self, parser, sample_txt_path):
        """Test that .txt files raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            parser.extract_text(sample_txt_path)

    def test_unsupported_no_extension(self, parser):
        """Test that files without extension raise ValueError."""
        fd, path = tempfile.mkstemp(suffix="")
        os.close(fd)
        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                parser.extract_text(path)
        finally:
            os.remove(path)


# ===================================================================
# Extract Text Dispatch
# ===================================================================


class TestExtractTextDispatch:
    """Tests for the extract_text method dispatching to correct extractor."""

    def test_dispatch_to_pdf(self, parser, tmp_path):
        """Test that .pdf files go to _extract_pdf."""
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"fake")
        with patch.object(parser, "_extract_pdf", return_value="PDF text") as mock_pdf:
            result = parser.extract_text(str(pdf_file))
            assert result == "PDF text"
            mock_pdf.assert_called_once()

    def test_dispatch_to_docx(self, parser, tmp_path):
        """Test that .docx files go to _extract_docx."""
        docx_file = tmp_path / "resume.docx"
        docx_file.write_bytes(b"fake")
        with patch.object(parser, "_extract_docx", return_value="DOCX text") as mock_docx:
            result = parser.extract_text(str(docx_file))
            assert result == "DOCX text"
            mock_docx.assert_called_once()

    def test_dispatch_case_insensitive(self, parser, tmp_path):
        """Test that .PDF (uppercase) is handled."""
        pdf_file = tmp_path / "resume.PDF"
        pdf_file.write_bytes(b"fake")
        with patch.object(parser, "_extract_pdf", return_value="PDF text") as mock_pdf:
            result = parser.extract_text(str(pdf_file))
            assert result == "PDF text"
            mock_pdf.assert_called_once()

    def test_extract_text_file_not_found(self, parser):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parser.extract_text("nonexistent.pdf")


# ===================================================================
# Full Pipeline Integration (mocked)
# ===================================================================


class TestProcessResumeIntegration:
    """Integration tests for process_resume with all dependencies mocked."""

    SAMPLE_PROFILE_JSON = json.dumps({
        "name": "Test Candidate",
        "email": "test.candidate@example.com",
        "phone": "1234567890",
        "location": "Mumbai",
        "skills": ["Python", "FastAPI"],
        "experience_years": 4.0,
        "education": "B.Tech",
        "previous_roles": ["Engineer"],
    })

    @patch("database.crud.get_candidate_by_id")
    @patch("utils.resume_parser.get_db_connection")
    @patch("utils.resume_parser.get_resume_by_hash")
    @patch("utils.resume_parser.add_candidate")
    @patch("utils.resume_parser.add_resume")
    @patch("utils.resume_parser.update_candidate")
    @patch("utils.resume_parser.CandidateEmbedder")
    @patch("utils.resume_parser.CandidateVectorStore")
    def test_process_resume_new_candidate(
        self,
        mock_vector_store_cls,
        mock_embedder_cls,
        mock_update_candidate,
        mock_add_resume,
        mock_add_candidate,
        mock_get_resume_by_hash,
        mock_get_db,
        mock_get_candidate,
    ):
        """Test that a new resume creates a candidate and updates FAISS."""
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_get_resume_by_hash.return_value = None
        mock_add_candidate.return_value = 42
        mock_add_resume.return_value = 99
        mock_get_candidate.return_value = {
            "id": 42, "name": "Test Candidate", "email": "test.candidate@example.com",
        }

        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed_text.return_value = [0.1] * 384
        mock_embedder_cls.return_value = mock_embedder_instance

        mock_vector_store_instance = MagicMock()
        mock_vector_store_instance.index.ntotal = 50
        mock_vector_store_instance.id_map = {i: i for i in range(50)}
        mock_vector_store_cls.return_value = mock_vector_store_instance

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = self.SAMPLE_PROFILE_JSON

        parser = ResumeParser()
        with patch.object(parser, "_create_parse_chain", return_value=mock_chain):
            with patch.object(parser, "extract_text", return_value="Test Candidate\nemail: test.candidate@example.com"):
                fd, path = tempfile.mkstemp(suffix=".pdf")
                with os.fdopen(fd, "wb") as f:
                    f.write(b"Fake resume content")
                try:
                    output = parser.process_resume(path, "test_resume.pdf")
                finally:
                    os.remove(path)

        assert output["is_new"] is True
        assert output["candidate"] is not None
        assert "Test Candidate" in output["message"]
        assert "42" in output["message"]

    @patch("database.crud.get_candidate_by_id")
    @patch("utils.resume_parser.get_db_connection")
    @patch("utils.resume_parser.get_resume_by_hash")
    def test_process_resume_duplicate(
        self,
        mock_get_resume_by_hash,
        mock_get_db,
        mock_get_candidate,
        parser,
    ):
        """Test that a duplicate hash returns existing candidate."""
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_get_resume_by_hash.return_value = {"id": 1, "candidate_id": 5}
        mock_get_candidate.return_value = {"id": 5, "name": "Existing User", "email": "existing@test.com"}

        with patch.object(parser, "extract_text", return_value="Some resume text"):
            fd, path = tempfile.mkstemp(suffix=".pdf")
            with os.fdopen(fd, "wb") as f:
                f.write(b"Duplicate content")
            try:
                output = parser.process_resume(path, "dup.pdf")
            finally:
                os.remove(path)

        assert output["is_new"] is False
        assert "duplicate" in output["message"].lower()
        assert output["candidate"] is not None
        assert output["candidate"]["id"] == 5


# ===================================================================
# Save Candidate
# ===================================================================


class TestSaveCandidate:
    """Tests for save_candidate method."""

    def test_save_candidate_success(self, parser):
        """Test that save_candidate creates both candidate and resume records."""
        mock_conn = MagicMock()
        profile = ResumeParseResult(
            name="Test User",
            email="test@example.com",
            phone="1234567890",
            location="Delhi",
            skills=["Python", "SQL"],
            experience_years=3.0,
            education="BCA",
            previous_roles=["Junior Dev"],
        )

        with patch("utils.resume_parser.add_candidate", return_value=101) as mock_add_c:
            with patch("utils.resume_parser.add_resume", return_value=201) as mock_add_r:
                result = parser.save_candidate(
                    conn=mock_conn,
                    profile=profile,
                    file_path="uploads/test.pdf",
                    original_filename="resume.pdf",
                    file_hash="abc123",
                    parsed_text="Some extracted text",
                )

        assert result["candidate_id"] == 101
        assert result["resume_id"] == 201
        mock_add_c.assert_called_once()
        mock_add_r.assert_called_once()
