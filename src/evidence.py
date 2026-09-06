import hashlib
import os
from datetime import datetime


def calculate_sha256(file_path):
    """
    Calculate SHA-256 hash of a file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            data = file.read(1024 * 1024)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()


def get_file_size(file_path):
    """
    Return file size in bytes.
    """

    return os.path.getsize(file_path)


def format_file_size(size_bytes):
    """
    Convert bytes into human-readable size.
    """

    if size_bytes < 1024:

        return f"{size_bytes} B"

    elif size_bytes < 1024 ** 2:

        return f"{size_bytes / 1024:.2f} KB"

    elif size_bytes < 1024 ** 3:

        return f"{size_bytes / (1024 ** 2):.2f} MB"

    else:

        return f"{size_bytes / (1024 ** 3):.2f} GB"


def get_file_type(file_name):
    """
    Get file extension.
    """

    extension = os.path.splitext(file_name)[1]

    if extension:
        return extension.lower()

    return "Unknown"


def generate_evidence_id():
    """
    Generate unique evidence ID.
    """

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    return f"RC-{timestamp}"


def create_evidence_record(
    file_path,
    file_name,
    result=None,
    confidence=None
):
    """
    Create complete digital evidence record.
    """

    size_bytes = get_file_size(
        file_path
    )

    sha256_hash = calculate_sha256(
        file_path
    )

    evidence_id = generate_evidence_id()

    analysis_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return {

        "evidence_id": evidence_id,

        "file_name": file_name,

        "file_type": get_file_type(
            file_name
        ),

        "file_size_bytes": size_bytes,

        "file_size": format_file_size(
            size_bytes
        ),

        "sha256": sha256_hash,

        "analysis_time": analysis_time,

        "result": result,

        "confidence": confidence
    }