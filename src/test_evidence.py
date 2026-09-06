from evidence import create_evidence_record


TEST_FILE = "test_evidence.txt"


with open(TEST_FILE, "w") as file:

    file.write(
        "RealCheck AI Digital Evidence Test"
    )


record = create_evidence_record(
    file_path=TEST_FILE,
    file_name=TEST_FILE,
    result="FAKE",
    confidence=94.36
)


print("================================")
print("REALCHECK AI DIGITAL EVIDENCE")
print("================================")

print(
    f"Evidence ID   : "
    f"{record['evidence_id']}"
)

print(
    f"File Name     : "
    f"{record['file_name']}"
)

print(
    f"File Type     : "
    f"{record['file_type']}"
)

print(
    f"File Size     : "
    f"{record['file_size']}"
)

print(
    f"SHA-256       : "
    f"{record['sha256']}"
)

print(
    f"Analysis Time : "
    f"{record['analysis_time']}"
)

print(
    f"Result        : "
    f"{record['result']}"
)

print(
    f"Confidence    : "
    f"{record['confidence']:.2f}%"
)