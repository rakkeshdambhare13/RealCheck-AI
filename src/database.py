import sqlite3
from pathlib import Path
from datetime import datetime


# ==========================================
# DATABASE LOCATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = BASE_DIR / "realcheck.db"


# ==========================================
# CONNECT TO DATABASE
# ==========================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# CREATE DATABASE TABLE
# ==========================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            evidence_id TEXT,

            file_name TEXT,

            file_type TEXT,

            analysis_type TEXT,

            result TEXT,

            confidence REAL,

            uncertainty REAL,

            sha256 TEXT,

            analysis_time TEXT

        )
        """
    )

    connection.commit()

    connection.close()


# ==========================================
# SAVE ANALYSIS
# ==========================================

def save_analysis(
    evidence_id,
    file_name,
    file_type,
    analysis_type,
    result,
    confidence,
    uncertainty,
    sha256,
    analysis_time=None
):

    if analysis_time is None:

        analysis_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO analysis_history
        (
            evidence_id,
            file_name,
            file_type,
            analysis_type,
            result,
            confidence,
            uncertainty,
            sha256,
            analysis_time
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            evidence_id,
            file_name,
            file_type,
            analysis_type,
            result,
            confidence,
            uncertainty,
            sha256,
            analysis_time
        )
    )

    connection.commit()

    connection.close()


# ==========================================
# GET ANALYSIS HISTORY
# ==========================================

def get_analysis_history():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            evidence_id,
            file_name,
            file_type,
            analysis_type,
            result,
            confidence,
            uncertainty,
            sha256,
            analysis_time

        FROM analysis_history

        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ==========================================
# DELETE ALL HISTORY
# ==========================================

def clear_analysis_history():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM analysis_history"
    )

    connection.commit()

    connection.close()