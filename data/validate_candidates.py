#!/usr/bin/env python3
"""
Validation script for sample_candidates.csv

Checks:
1. Exactly 50 rows exist
2. All required columns exist
3. Emails are unique
4. Phone numbers are unique
"""

import sys
import pandas as pd


def validate_candidates(csv_path: str = "data/sample_candidates.csv") -> bool:
    """Validate the sample candidates CSV file."""
    errors = []
    warnings = []

    # 1. Load CSV with pandas
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"❌ Error: File not found at {csv_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False

    # 2. Check exactly 50 rows exist
    row_count = len(df)
    if row_count != 50:
        errors.append(f"Expected 50 rows, found {row_count}")

    # 3. Ensure all required columns exist
    required_columns = [
        "id",
        "name",
        "email",
        "phone",
        "location",
        "skills",
        "experience_years",
        "education",
        "profile_completeness",
        "last_active_days_ago"
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")

    # 4. Verify emails are unique
    if "email" in df.columns:
        duplicate_emails = df[df.duplicated(subset=["email"], keep=False)]
        if not duplicate_emails.empty:
            dup_list = duplicate_emails["email"].tolist()
            errors.append(f"Duplicate emails found: {dup_list}")

    # 5. Verify phone numbers are unique
    if "phone" in df.columns:
        duplicate_phones = df[df.duplicated(subset=["phone"], keep=False)]
        if not duplicate_phones.empty:
            dup_list = duplicate_phones["phone"].tolist()
            errors.append(f"Duplicate phone numbers found: {dup_list}")

    # Additional validations (warnings)
    # Check for null values in required columns
    if not missing_columns:
        null_counts = df[required_columns].isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                warnings.append(f"Column '{col}' has {count} null values")

    # Check experience_years range (0-10)
    if "experience_years" in df.columns:
        invalid_exp = df[(df["experience_years"] < 0) | (df["experience_years"] > 10)]
        if not invalid_exp.empty:
            warnings.append(f"Invalid experience_years (outside 0-10): {len(invalid_exp)} rows")

    # Check profile_completeness range (0-100)
    if "profile_completeness" in df.columns:
        invalid_completeness = df[(df["profile_completeness"] < 0) | (df["profile_completeness"] > 100)]
        if not invalid_completeness.empty:
            warnings.append(f"Invalid profile_completeness (outside 0-100): {len(invalid_completeness)} rows")

    # Check last_active_days_ago is positive
    if "last_active_days_ago" in df.columns:
        invalid_active = df[df["last_active_days_ago"] < 0]
        if not invalid_active.empty:
            warnings.append(f"Negative last_active_days_ago: {len(invalid_active)} rows")

    # Print results
    if errors:
        print("[FAIL] Validation Failed")
        for error in errors:
            print(f"  - {error}")
        return False

    print("[PASS] Validation Passed")
    print(f"  - Rows: {row_count}")
    print(f"  - Columns: {len(required_columns)} required columns present")
    print(f"  - Unique emails: {df['email'].nunique()}")
    print(f"  - Unique phones: {df['phone'].nunique()}")

    if warnings:
        print("\n[WARN] Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    return True


if __name__ == "__main__":
    success = validate_candidates()
    sys.exit(0 if success else 1)