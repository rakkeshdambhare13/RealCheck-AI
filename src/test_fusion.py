from fusion import multimodal_fusion


result = multimodal_fusion(
    image_fake_score=90.24,
    video_fake_score=82.50
)

print("================================")
print("REALCHECK AI MULTIMODAL FUSION")
print("================================")

print(
    f"Final Result : {result['result']}"
)

print(
    f"Fake Score   : "
    f"{result['fake_score']:.2f}%"
)

print(
    f"Confidence   : "
    f"{result['confidence']:.2f}%"
)