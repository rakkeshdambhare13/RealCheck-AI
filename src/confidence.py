def calculate_confidence(
    fake_score,
    image_fake_score=None,
    video_fake_score=None
):
    """
    Calculate confidence, uncertainty,
    reliability and evidence strength.
    """

    # Keep score between 0 and 100
    fake_score = max(
        0,
        min(100, fake_score)
    )

    # ---------------------------------
    # FINAL RESULT
    # ---------------------------------

    if fake_score >= 50:

        result = "FAKE"

        confidence = fake_score

    else:

        result = "REAL"

        confidence = 100 - fake_score


    # ---------------------------------
    # UNCERTAINTY
    # ---------------------------------

    uncertainty = 100 - confidence


    # ---------------------------------
    # RELIABILITY
    # ---------------------------------

    if confidence >= 80:

        reliability = "HIGH"

    elif confidence >= 65:

        reliability = "MEDIUM"

    else:

        reliability = "LOW"


    # ---------------------------------
    # EVIDENCE STRENGTH
    # ---------------------------------

    evidence_count = 0

    if image_fake_score is not None:
        evidence_count += 1

    if video_fake_score is not None:
        evidence_count += 1


    if evidence_count >= 2:

        evidence_strength = "STRONG"

    elif evidence_count == 1:

        evidence_strength = "MODERATE"

    else:

        evidence_strength = "WEAK"


    # ---------------------------------
    # MODEL AGREEMENT
    # ---------------------------------

    model_agreement = "N/A"

    if (
        image_fake_score is not None
        and video_fake_score is not None
    ):

        image_result = (
            "FAKE"
            if image_fake_score >= 50
            else "REAL"
        )

        video_result = (
            "FAKE"
            if video_fake_score >= 50
            else "REAL"
        )

        if image_result == video_result:

            model_agreement = "AGREE"

        else:

            model_agreement = "DISAGREE"


    # ---------------------------------
    # RETURN
    # ---------------------------------

    return {
        "result": result,
        "confidence": confidence,
        "uncertainty": uncertainty,
        "reliability": reliability,
        "evidence_strength": evidence_strength,
        "model_agreement": model_agreement
    }