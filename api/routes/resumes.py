"""
api/routes/resumes.py — Resume Upload API Endpoint for RecruitX

Endpoint:
    POST /api/upload-resume — Upload a PDF or DOCX resume file

This endpoint accepts a resume file upload, runs it through the ResumeParser
(implemented in Phase 13), which:
    1. Validates file type and size
    2. Extracts text from PDF/DOCX
    3. Cleans the extracted text
    4. Detects duplicates via MD5 hash
    5. Parses the text with LLM into a structured candidate profile
    6. Saves the candidate to the database
    7. Adds the candidate to the FAISS vector index
"""

import logging
import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile

from utils.resume_parser import ResumeParser

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
# Max upload size in bytes (default: 10 MB)
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024
# Upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


@router.post("/api/upload-resume")
async def upload_resume(file: UploadFile):
    """
    Upload a resume file (PDF or DOCX) and parse it into a candidate profile.

    The pipeline extracts text, detects duplicates via MD5 hash, parses
    with LLM, saves to the database, and updates the FAISS vector index.

    Args:
        file: The uploaded resume file (multipart upload).

    Returns:
        Dict with the parsed or existing candidate, message, and dedup flag.

    Raises:
        HTTPException 400: If file type is invalid, file is too large,
                           or parsing fails.
        HTTPException 409: If a duplicate is detected.
        HTTPException 500: If file save or processing fails.
    """
    # Validate file extension
    file_ext: str = ""
    if file.filename:
        _, file_ext = os.path.splitext(file.filename.lower())

    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(
            "Invalid file type uploaded: %s (extension: %s)",
            file.filename, file_ext,
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file_ext}'. Only PDF (.pdf) and DOCX (.docx) files are allowed.",
        )

    # Read file content for size validation
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
        logger.warning(
            "File too large: %d bytes (max %d MB)",
            file_size, max_mb,
        )
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {max_mb} MB",
        )

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save file with unique name to prevent collisions
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(save_path, "wb") as f:
            f.write(content)

        logger.info(
            "Resume saved: %s -> %s (%d bytes)",
            file.filename, save_path, file_size,
        )

    except OSError as e:
        logger.error("Failed to save uploaded file: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {e}",
        )

    # Run through ResumeParser
    try:
        parser = ResumeParser()
        filename = file.filename or "unknown"
        result = parser.process_resume(save_path, filename)
        if result.get("duplicate_reason") == "email":
            raise HTTPException(status_code=409, detail=result["message"])
        return result
    except ValueError as e:
        logger.error("Resume parsing validation error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error("Resume parsing runtime error: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error during resume parsing: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal error during resume processing")
