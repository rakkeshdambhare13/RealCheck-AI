"""
Accounts and per-user analysis history for RealCheck AI.

Standard library only (sqlite3 + hashlib). Put this file in src/auth.py.

WHAT IT DOES
  * register_user()      create an account (validates name, email, password)
  * authenticate()       sign in (generic errors, temporary lock after repeated failures)
  * save_user_analysis() / get_user_history() / clear_user_history()
                         every analysis record belongs to exactly one user, and every
                         query is filtered by that user's id

SECURITY NOTES
  * Passwords are never stored. Only a salted PBKDF2-HMAC-SHA256 hash is (600,000 rounds,
    random 16-byte salt per user) and it is compared in constant time.
  * Sign-in errors are deliberately generic ("Invalid email or password") so the form does
    not reveal which emails have accounts.
  * After 5 wrong passwords an account is locked for 5 minutes.
  * All SQL uses bound parameters (no string-built queries).

STORAGE
  The database is a single SQLite file: <project>/data/realcheck_users.db
  (override with the REALCHECK_DB environment variable). Back this file up, and note that
  hosts with an ephemeral disk (for example Streamlit Community Cloud) lose it on restart.
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(
    os.environ.get(
        "REALCHECK_DB",
        Path(__file__).resolve().parent.parent / "data" / "realcheck_users.db"
    )
)

PBKDF2_ROUNDS = 600_000
MAX_FAILED_ATTEMPTS = 5
LOCK_SECONDS = 5 * 60

MIN_PASSWORD = 8
MAX_PASSWORD = 128

EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$"
)

COMMON_PASSWORDS = {
    "password", "password1", "password123", "passw0rd", "12345678", "123456789",
    "1234567890", "qwertyui", "qwerty123", "qwertyuiop", "11111111", "iloveyou",
    "admin123", "welcome1", "letmein1", "abc12345", "realcheck", "realcheck1",
    "realcheck123", "changeme", "football1", "monkey123", "dragon123", "sunshine1",
}


# ==================================================
# DATABASE
# ==================================================

@contextmanager
def _db():
    """One short-lived connection per call (safe with Streamlit's threads)."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        with conn:          # commit on success, roll back on error
            yield conn
    finally:
        conn.close()


def init_auth_db():
    """Create the tables if they do not exist yet (safe to call on every run)."""

    with _db() as c:

        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                email           TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                name            TEXT    NOT NULL,
                password_hash   TEXT    NOT NULL,
                created_at      INTEGER NOT NULL,
                last_login      INTEGER,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until    INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS analysis_history (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL
                              REFERENCES users(id) ON DELETE CASCADE,
                evidence_id   TEXT,
                file_name     TEXT,
                file_type     TEXT,
                analysis_type TEXT,
                result        TEXT,
                confidence    REAL,
                uncertainty   REAL,
                sha256        TEXT,
                analysis_time TEXT,
                created_at    INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_history_user
                ON analysis_history (user_id, id DESC);
            """
        )


# ==================================================
# PASSWORD HASHING
# ==================================================

def hash_password(password):

    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ROUNDS
    )

    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):

    try:

        algo, rounds, salt_hex, hash_hex = stored.split("$")

        if algo != "pbkdf2_sha256":
            return False

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(rounds)
        )

        return hmac.compare_digest(digest.hex(), hash_hex)

    except Exception:
        return False


_dummy_hash = None


def _burn_time():
    """Spend the same time as a real check, so timing does not reveal unknown emails."""

    global _dummy_hash

    if _dummy_hash is None:
        _dummy_hash = hash_password("not-a-real-password")

    verify_password("wrong-password", _dummy_hash)


# ==================================================
# VALIDATION
# ==================================================

def validate_email(email):
    """Returns (ok, normalized_email, error_message)."""

    value = (email or "").strip().lower()

    if not value:
        return False, "", "Enter your email address."

    bad = (
        len(value) > 254
        or not EMAIL_RE.match(value)
        or ".." in value
    )

    if not bad:

        local = value.split("@", 1)[0]

        bad = (
            len(local) > 64
            or local.startswith(".")
            or local.endswith(".")
        )

    if bad:
        return (
            False,
            "",
            "Enter a valid email address (for example name@example.com)."
        )

    return True, value, ""


def validate_password(password, email="", name=""):
    """Returns a list of problems (an empty list means the password is acceptable)."""

    problems = []

    password = password or ""

    if len(password) < MIN_PASSWORD:
        problems.append(f"Use at least {MIN_PASSWORD} characters.")

    if len(password) > MAX_PASSWORD:
        problems.append(f"Use at most {MAX_PASSWORD} characters.")

    if not re.search(r"[a-z]", password):
        problems.append("Add a lowercase letter.")

    if not re.search(r"[A-Z]", password):
        problems.append("Add an uppercase letter.")

    if not re.search(r"[0-9]", password):
        problems.append("Add a number.")

    lowered = password.lower()

    if lowered in COMMON_PASSWORDS:
        problems.append("That password is too common. Choose something less guessable.")

    local = (email or "").split("@", 1)[0].lower()

    if len(local) >= 3 and local in lowered:
        problems.append("Do not include your email name in the password.")

    return problems


# ==================================================
# ACCOUNTS
# ==================================================

def _public(row):
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"]
    }


def register_user(name, email, password, confirm):
    """Returns (user_dict, errors). user_dict is None when registration failed."""

    errors = []

    name = re.sub(r"[\x00-\x1f\x7f]", "", name or "")
    name = " ".join(name.split())

    if not 2 <= len(name) <= 60:
        errors.append("Enter your name (2 to 60 characters).")

    email_ok, normalized, email_error = validate_email(email)

    if not email_ok:
        errors.append(email_error)

    errors += validate_password(
        password,
        normalized if email_ok else "",
        name
    )

    if password != confirm:
        errors.append("Passwords do not match.")

    if errors:
        return None, errors

    now = int(time.time())

    try:

        password_hash = hash_password(password)

        with _db() as c:

            cursor = c.execute(
                """
                INSERT INTO users
                    (email, name, password_hash, created_at, last_login)
                VALUES (?, ?, ?, ?, ?)
                """,
                (normalized, name, password_hash, now, now)
            )

            user_id = cursor.lastrowid

    except sqlite3.IntegrityError:

        return None, [
            "An account with this email already exists. Try signing in."
        ]

    return {"id": user_id, "email": normalized, "name": name}, []


def authenticate(email, password):
    """Returns (user_dict, error_message). Exactly one of them is None."""

    generic = "Invalid email or password."

    email_ok, normalized, _ = validate_email(email)

    if (
        not email_ok
        or not password
        or len(password) > MAX_PASSWORD
    ):
        _burn_time()
        return None, generic

    with _db() as c:

        row = c.execute(
            "SELECT * FROM users WHERE email = ?",
            (normalized,)
        ).fetchone()

    if row is None:
        _burn_time()
        return None, generic

    now = int(time.time())

    if row["locked_until"] > now:

        minutes = max(1, -(-(row["locked_until"] - now) // 60))

        return None, (
            f"Too many failed attempts. "
            f"Try again in {minutes} minute(s)."
        )

    # the slow hash runs outside any database transaction
    password_ok = verify_password(password, row["password_hash"])

    with _db() as c:

        if password_ok:

            c.execute(
                """
                UPDATE users
                SET failed_attempts = 0, locked_until = 0, last_login = ?
                WHERE id = ?
                """,
                (now, row["id"])
            )

            return _public(row), None

        failed = row["failed_attempts"] + 1

        if failed >= MAX_FAILED_ATTEMPTS:

            c.execute(
                """
                UPDATE users
                SET failed_attempts = 0, locked_until = ?
                WHERE id = ?
                """,
                (now + LOCK_SECONDS, row["id"])
            )

            return None, (
                "Too many failed attempts. "
                "This account is locked for 5 minutes."
            )

        c.execute(
            "UPDATE users SET failed_attempts = ? WHERE id = ?",
            (failed, row["id"])
        )

    return None, generic


# ==================================================
# PER-USER ANALYSIS HISTORY
# ==================================================

def save_user_analysis(
    user_id,
    evidence_id,
    file_name,
    file_type,
    analysis_type,
    result,
    confidence,
    uncertainty,
    sha256,
    analysis_time
):

    with _db() as c:

        c.execute(
            """
            INSERT INTO analysis_history
                (user_id, evidence_id, file_name, file_type, analysis_type,
                 result, confidence, uncertainty, sha256, analysis_time,
                 created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(evidence_id),
                str(file_name),
                str(file_type),
                str(analysis_type),
                str(result),
                float(confidence),
                float(uncertainty),
                str(sha256),
                str(analysis_time),
                int(time.time())
            )
        )


def get_user_history(user_id):
    """This user's records only, newest first, as plain dicts."""

    with _db() as c:

        rows = c.execute(
            """
            SELECT id, evidence_id, file_name, file_type, analysis_type,
                   result, confidence, uncertainty, sha256, analysis_time
            FROM analysis_history
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (int(user_id),)
        ).fetchall()

    return [dict(row) for row in rows]


def clear_user_history(user_id):
    """Delete this user's records only."""

    with _db() as c:

        c.execute(
            "DELETE FROM analysis_history WHERE user_id = ?",
            (int(user_id),)
        )