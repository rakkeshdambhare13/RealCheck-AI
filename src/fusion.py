def multimodal_fusion(
    image_fake_score=None,
    video_fake_score=None
):
    """
    Combine image and video fake probabilities.

    Scores must be between 0 and 100.
    """

    scores = []

    if image_fake_score is not None:
        scores.append({
            "score": image_fake_score,
            "weight": 0.40
        })

    if video_fake_score is not None:
        scores.append({
            "score": video_fake_score,
            "weight": 0.60
        })

    if not scores:
        raise ValueError(
            "No modality scores available."
        )

    total_weight = sum(
        item["weight"]
        for item in scores
    )

    final_fake_score = sum(
        item["score"] * item["weight"]
        for item in scores
    ) / total_weight

    if final_fake_score >= 50:
        result = "FAKE"

        confidence = final_fake_score

    else:
        result = "REAL"

        confidence = 100 - final_fake_score

    return {
        "result": result,
        "fake_score": final_fake_score,
        "confidence": confidence
    }