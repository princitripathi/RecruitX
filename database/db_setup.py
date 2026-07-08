"""
database/db_setup.py — Database Initialization for RecruitX

This script:
1. Creates the SQLite database file at the path from .env (DATABASE_PATH)
2. Creates all 5 tables (candidates, job_descriptions, shortlists, resumes, chat_history)
3. Creates all 6 performance indexes
4. Loads 50 sample candidates from data/sample_candidates.csv

Run this script once before starting the application:
    python database/db_setup.py

Re-running is safe — it uses CREATE TABLE IF NOT EXISTS and
skips CSV loading if candidates already exist.
"""

import csv
import logging
import os
import sqlite3
import sys
from pathlib import Path

# Add project root to Python path so imports work when running directly
# This is needed because we run: python database/db_setup.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from database.models import ALL_INDEXES, ALL_TABLES

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database path from .env (default: data/recruitx.db)
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/recruitx.db")

# Path to sample candidates CSV
SAMPLE_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "sample_candidates.csv")


def get_db_connection(db_path: str = DATABASE_PATH) -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        sqlite3.Connection object with row_factory set to sqlite3.Row
        so results can be accessed by column name.

    Note:
        The caller is responsible for closing the connection.
    """
    # Ensure the directory for the database file exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # Connect to SQLite (creates file if it doesn't exist)
    conn = sqlite3.connect(db_path)

    # Enable foreign key support (off by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON")

    # Return rows as dict-like objects (access by column name)
    conn.row_factory = sqlite3.Row

    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """
    Create all database tables defined in models.py.

    Uses CREATE TABLE IF NOT EXISTS, so it's safe to run multiple times.

    Args:
        conn: Active SQLite connection
    """
    cursor = conn.cursor()

    for table_name, create_sql in ALL_TABLES:
        try:
            cursor.execute(create_sql)
            logger.info("✅ Table '%s' created (or already exists)", table_name)
        except sqlite3.Error as e:
            logger.error("❌ Failed to create table '%s': %s", table_name, str(e))
            raise

    conn.commit()
    logger.info("All %d tables created successfully", len(ALL_TABLES))


def create_indexes(conn: sqlite3.Connection) -> None:
    """
    Create all performance indexes defined in models.py.

    Uses CREATE INDEX IF NOT EXISTS, so it's safe to run multiple times.

    Args:
        conn: Active SQLite connection
    """
    cursor = conn.cursor()

    for index_name, create_sql in ALL_INDEXES:
        try:
            cursor.execute(create_sql)
            logger.info("✅ Index '%s' created (or already exists)", index_name)
        except sqlite3.Error as e:
            logger.error("❌ Failed to create index '%s': %s", index_name, str(e))
            raise

    conn.commit()
    logger.info("All %d indexes created successfully", len(ALL_INDEXES))


def load_sample_data(conn: sqlite3.Connection, csv_path: str = SAMPLE_CSV_PATH) -> int:
    """
    Load sample candidates from CSV into the candidates table.

    Skips loading if candidates already exist in the database.
    Maps CSV columns to database columns:
        CSV 'last_active_days' → DB 'last_active_days'
        CSV 'previous_roles'   → DB 'previous_roles' (can be blank)

    Args:
        conn: Active SQLite connection
        csv_path: Path to the sample_candidates.csv file

    Returns:
        Number of candidates inserted (0 if skipped)
    """
    cursor = conn.cursor()

    # Check if candidates already exist (skip if re-running)
    cursor.execute("SELECT COUNT(*) FROM candidates")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        logger.info(
            "⏭️  Skipping CSV load — %d candidates already exist in database",
            existing_count
        )
        return 0

    # Read CSV file
    if not os.path.exists(csv_path):
        logger.error("❌ CSV file not found: %s", csv_path)
        raise FileNotFoundError(f"Sample CSV not found at: {csv_path}")

    inserted_count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Map CSV columns to database INSERT
                # Note: 'id' is auto-incremented, but we use the CSV id
                # to keep consistent numbering with the sample data.
                # 'resume_path' and 'embedding_id' are NULL initially —
                # they get populated when resumes are uploaded (Phase 13)
                # and when FAISS index is built (Phase 4).
                cursor.execute(
                    """
                    INSERT INTO candidates (
                        id, name, email, phone, location, skills,
                        experience_years, education, previous_roles,
                        profile_completeness, last_active_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(row["id"]),
                        row["name"].strip(),
                        row["email"].strip(),
                        row["phone"].strip(),
                        row["location"].strip(),
                        row["skills"].strip(),
                        float(row["experience_years"]),
                        row["education"].strip(),
                        # previous_roles can be empty for freshers
                        row["previous_roles"].strip() if row.get("previous_roles", "").strip() else None,
                        int(row["profile_completeness"]),
                        int(row["last_active_days"]),
                    )
                )
                inserted_count += 1

            except (KeyError, ValueError) as e:
                logger.error("❌ Error inserting row %s: %s", row.get("id", "?"), str(e))
                raise

    conn.commit()
    logger.info("✅ Loaded %d candidates from CSV into database", inserted_count)
    return inserted_count


def verify_database(conn: sqlite3.Connection) -> None:
    """
    Run quick checks to verify the database was set up correctly.

    Prints a summary of table row counts and a sample candidate.

    Args:
        conn: Active SQLite connection
    """
    cursor = conn.cursor()

    # Count rows in each table
    logger.info("--- Database Verification ---")

    for table_name, _ in ALL_TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        logger.info("  📊 Table '%s': %d rows", table_name, count)

    # Show a sample candidate to verify data integrity
    cursor.execute("SELECT * FROM candidates LIMIT 1")
    sample = cursor.fetchone()

    if sample:
        logger.info("--- Sample Candidate ---")
        logger.info("  Name: %s", sample["name"])
        logger.info("  Email: %s", sample["email"])
        logger.info("  Location: %s", sample["location"])
        logger.info("  Skills: %s", sample["skills"])
        logger.info("  Experience: %s years", sample["experience_years"])
        logger.info("  Previous Roles: %s", sample["previous_roles"])
        logger.info("  Profile Completeness: %s%%", sample["profile_completeness"])
        logger.info("  Last Active: %s days ago", sample["last_active_days"])


def setup_database() -> None:
    """
    Main function — runs the complete database setup pipeline.

    Steps:
        1. Connect to SQLite database
        2. Create all tables
        3. Create all indexes
        4. Load sample data from CSV
        5. Verify the setup
    """
    logger.info("=" * 60)
    logger.info("RecruitX Database Setup")
    logger.info("=" * 60)
    logger.info("Database path: %s", DATABASE_PATH)

    conn = None
    try:
        # Step 1: Connect
        conn = get_db_connection(DATABASE_PATH)
        logger.info("✅ Connected to database")

        # Step 2: Create tables
        create_tables(conn)

        # Step 3: Create indexes
        create_indexes(conn)

        # Step 4: Load sample data
        loaded = load_sample_data(conn)

        # Step 5: Verify
        verify_database(conn)

        logger.info("=" * 60)
        logger.info("✅ Database setup complete!")
        if loaded > 0:
            logger.info("   %d candidates loaded from CSV", loaded)
        logger.info("=" * 60)

    except Exception as e:
        logger.error("❌ Database setup failed: %s", str(e))
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


# ============================================================
# Run setup when executing this file directly:
#   python database/db_setup.py
# ============================================================
if __name__ == "__main__":
    setup_database()
