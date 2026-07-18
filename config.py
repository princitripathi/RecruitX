"""
config.py — Centralized Configuration for RecruitX

Single source of truth for all shared environment variables and defaults.
Every module that needs these values should import from here instead of
re-reading os.getenv() with duplicated fallback strings.

Usage:
    from config import DATABASE_PATH, EMBEDDING_DIMENSION, OPENROUTER_MODEL
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ── Database ────────────────────────────────────────────────────────
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/recruitx.db")

# ── FAISS Vector Store ──────────────────────────────────────────────
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index.bin")
FAISS_ID_MAP_PATH = os.getenv("FAISS_ID_MAP_PATH", "data/faiss_id_map.pkl")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── OpenRouter / LLM ───────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# ── Search ──────────────────────────────────────────────────────────
MAX_CANDIDATES_PER_SEARCH = int(os.getenv("MAX_CANDIDATES_PER_SEARCH", "20"))

# ── Logging ─────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Application ─────────────────────────────────────────────────────
APP_NAME = os.getenv("APP_NAME", "RecruitX")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
