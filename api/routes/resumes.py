"""
api/routes/resumes.py — Resume Upload API Endpoint for RecruitX

Endpoint:
    POST /api/upload-resume — Upload a PDF or DOCX resume file

This is a lightweight placeholder implementation for Phase 11.
Full resume parsing with text extraction and candidate auto-creation
will be implemented in Phase 13 (Resume Parser).

Current behavior:
    1. Validates file type (PDF or DOCX)
    2. Validates file size (max 10 MB)
    3. Saves file to uploads/ directory with unique filename
    4. Returns placeholder response
"""

import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile

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
    Upload a resume file (PDF or DOCX).

    Placeholder implementation — validates and saves the file.
    Full parsing with candidate extraction comes in Phase 13.

    Args:
        file: The uploaded resume file (multipart upload).

    Returns:
        Dict with file info and a message indicating full parsing
        will be available in a future update.

    Raises:
        HTTPException 400: If file type is invalid or file is too large.
        HTTPException 500: If file save fails.
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

        return {
            "candidate": None,
            "message": (
                "Resume uploaded successfully. "
                "Full parsing with text extraction and candidate auto-creation "
                "will be available in Phase 13."
            ),
        }

    except OSError as e:
        logger.error("Failed to save uploaded file: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {e}",
        )
