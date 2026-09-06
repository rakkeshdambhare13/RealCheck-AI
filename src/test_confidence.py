from confidence import calculate_confidence


result = calculate_confidence(
    fake_score=85.60,
    image_fake_score=90.24,
    video_fake_score=82.50
)


print("================================")
print("REALCHECK AI CONFIDENCE ENGINE")
print("================================")

print(
    f"Result            : {result['result']}"
)

print(
    f"Confidence        : "
    f"{result['confidence']:.2f}%"
)

print(
    f"Uncertainty       : "
    f"{result['uncertainty']:.2f}%"
)

print(
    f"Reliability       : "
    f"{result['reliability']}"
)

print(
    f"Evidence Strength : "
    f"{result['evidence_strength']}"
)

print(
    f"Model Agreement   : "
    f"{result['model_agreement']}"
)