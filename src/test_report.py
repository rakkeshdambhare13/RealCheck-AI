from report import generate_forensic_report


output_file = "reports/test_forensic_report.pdf"


generate_forensic_report(
    output_path=output_file,

    final_result="FAKE",

    final_confidence=94.36,

    uncertainty=5.64,

    reliability="HIGH",

    evidence_strength="STRONG",

    model_agreement="AGREE",

    image_fake_score=90.24,

    video_fake_score=97.11
)


print("================================")
print("REALCHECK AI PDF REPORT TEST")
print("================================")

print(
    f"PDF generated successfully:"
)

print(
    output_file
)