
import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path

AUTH_DB = Path(__file__).resolve().parent.parent / "realcheck_users.db"


def get_connection():
    connection = sqlite3.connect(AUTH_DB, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_auth_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        600000
    ).hex()
    return salt, hashed


def register_user(full_name, username, email, password):
    full_name = full_name.strip()
    username = username.strip()
    email = email.strip().lower()

    if not all([full_name, username, email, password]):
        return False, "Please fill in every field."

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return False, "Enter a valid email address."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    salt, password_hash = hash_password(password)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users
                    (full_name, username, email, salt, password_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, username, email, salt, password_hash)
            )
        return True, "Account created successfully. Please log in."

    except sqlite3.IntegrityError:
        return False, "That username or email is already registered."


def authenticate_user(identifier, password):
    identifier = identifier.strip()

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, full_name, username, email, salt, password_hash
            FROM users
            WHERE username = ? COLLATE NOCASE
               OR email = ? COLLATE NOCASE
            """,
            (identifier, identifier)
        ).fetchone()

    if user is None:
        return None

    _, candidate_hash = hash_password(password, user["salt"])

    if not hmac.compare_digest(candidate_hash, user["password_hash"]):
        return None

    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "username": user["username"],
        "email": user["email"]
    }
