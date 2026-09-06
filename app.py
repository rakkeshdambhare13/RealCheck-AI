import streamlit as st
from PIL import Image
import tempfile
import os

from src.predict_image import (
    predict_image,
    load_model,
    transform,
    device
)

from src.predict_video import analyze_video
from src.gradcam import create_gradcam_image
from src.fusion import multimodal_fusion
from src.confidence import calculate_confidence
from src.evidence import create_evidence_record
from src.report import create_pdf_report
from src.database import (
    initialize_database,
    save_analysis,
    get_analysis_history,
    clear_analysis_history
)


# ==================================================
# INITIALIZE DATABASE
# ==================================================

initialize_database()


# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="RealCheck AI",
    page_icon="🔍",
    layout="wide"
)


# ==================================================
# TITLE
# ==================================================

st.title("🔍 RealCheck AI")

st.subheader(
    "Multimodal AI-Based Fake Media Detection and Prediction System"
)

st.write(
    "Upload image, video, or both to determine whether "
    "the media is likely real or AI-generated."
)


# ==================================================
# MEDIA TYPE
# ==================================================

media_type = st.radio(
    "Select Analysis Mode",
    [
        "🖼️ Image",
        "🎥 Video",
        "🔗 Multimodal Fusion"
    ],
    horizontal=True
)


# ==================================================
# IMAGE ANALYSIS
# ==================================================

if media_type == "🖼️ Image":

    uploaded_file = st.file_uploader(
        "Upload Image",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if uploaded_file is not None:

        image = Image.open(
            uploaded_file
        ).convert("RGB")

        st.image(
            image,
            caption="Uploaded Image",
            width=500
        )

        if st.button(
            "🔎 Start Image Analysis"
        ):

            image_path = None

            try:

                # ==========================================
                # SAVE ORIGINAL IMAGE TEMPORARILY
                # ==========================================

                file_extension = os.path.splitext(
                    uploaded_file.name
                )[1]

                if file_extension == "":
                    file_extension = ".jpg"

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=file_extension
                ) as temp_file:

                    temp_file.write(
                        uploaded_file.getvalue()
                    )

                    image_path = temp_file.name


                # ==========================================
                # IMAGE ANALYSIS
                # ==========================================

                with st.spinner(
                    "AI is analyzing the image..."
                ):

                    (
                        label,
                        confidence,
                        prediction
                    ) = predict_image(
                        image
                    )


                st.divider()


                # ==========================================
                # IMAGE RESULT
                # ==========================================

                if label == "FAKE":

                    st.error(
                        "🔴 AI-GENERATED / FAKE"
                    )

                    st.metric(
                        "Confidence",
                        f"{confidence:.2f}%"
                    )

                    st.warning(
                        "The AI model detected patterns "
                        "associated with AI-generated or "
                        "manipulated images."
                    )

                else:

                    st.warning(
                        "🟡 LIKELY REAL"
                    )

                    st.metric(
                        "Confidence",
                        f"{confidence:.2f}%"
                    )

                    st.info(
                        "The AI model found the image more "
                        "consistent with real images."
                    )


                # ==========================================
                # CONFIDENCE INFORMATION
                # ==========================================

                image_uncertainty = 100 - confidence

                if confidence >= 80:

                    image_reliability = "HIGH"

                elif confidence >= 65:

                    image_reliability = "MEDIUM"

                else:

                    image_reliability = "LOW"


                # ==========================================
                # DIGITAL EVIDENCE
                # ==========================================

                evidence = create_evidence_record(
                    file_path=image_path,
                    file_name=uploaded_file.name,
                    result=label,
                    confidence=confidence
                )


                # ==========================================
                # SAVE IMAGE ANALYSIS TO DATABASE
                # ==========================================

                save_analysis(
                    evidence_id=evidence["evidence_id"],
                    file_name=evidence["file_name"],
                    file_type=evidence["file_type"],
                    analysis_type="Image",
                    result=evidence["result"],
                    confidence=evidence["confidence"],
                    uncertainty=100 - evidence["confidence"],
                    sha256=evidence["sha256"],
                    analysis_time=evidence["analysis_time"]
                )


                st.divider()

                st.subheader(
                    "🔐 Digital Evidence"
                )


                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**Evidence ID:** "
                        f"{evidence['evidence_id']}"
                    )

                    st.write(
                        f"**File Name:** "
                        f"{evidence['file_name']}"
                    )

                    st.write(
                        f"**File Type:** "
                        f"{evidence['file_type']}"
                    )

                    st.write(
                        f"**File Size:** "
                        f"{evidence['file_size']}"
                    )

                with col2:

                    st.write(
                        f"**Analysis Time:** "
                        f"{evidence['analysis_time']}"
                    )

                    st.write(
                        f"**Result:** "
                        f"{evidence['result']}"
                    )

                    st.write(
                        f"**Confidence:** "
                        f"{evidence['confidence']:.2f}%"
                    )


                st.write(
                    "**SHA-256 File Hash:**"
                )

                st.code(
                    evidence["sha256"],
                    language="text"
                )

                st.info(
                    "The SHA-256 hash acts as a digital fingerprint "
                    "of the analyzed file. If the file changes, "
                    "its SHA-256 hash will also change."
                )


                # ==========================================
                # STEP 13 — PDF FORENSIC REPORT
                # ==========================================

                st.divider()

                st.subheader(
                    "📄 Forensic Report"
                )

                pdf_data = create_pdf_report(
                    evidence_records=[
                        evidence
                    ],

                    final_result=label,

                    final_confidence=confidence,

                    uncertainty=image_uncertainty,

                    reliability=image_reliability,

                    evidence_strength="MODERATE",

                    model_agreement="N/A"
                )

                st.download_button(
                    label="📄 Download Forensic PDF Report",

                    data=pdf_data,

                    file_name=(
                        f"RealCheck_AI_Report_"
                        f"{evidence['evidence_id']}.pdf"
                    ),

                    mime="application/pdf"
                )


                # ==========================================
                # GRAD-CAM
                # ==========================================

                st.divider()

                st.subheader(
                    "🔍 Explainable AI — Grad-CAM"
                )

                st.write(
                    "The heatmap highlights image regions "
                    "that influenced the AI model's prediction."
                )

                with st.spinner(
                    "Generating AI explanation..."
                ):

                    try:

                        model = load_model()

                        gradcam_image = create_gradcam_image(
                            model=model,
                            image=image,
                            transform=transform,
                            target_class=prediction,
                            device=device
                        )

                        st.image(
                            gradcam_image,
                            caption=(
                                "Grad-CAM: Important Regions "
                                "Influencing the Prediction"
                            ),
                            width=600
                        )

                        st.info(
                            "Note: Grad-CAM shows regions that "
                            "influenced the model's decision. "
                            "It does not prove that a highlighted "
                            "region is fake."
                        )

                    except Exception as e:

                        st.error(
                            f"Grad-CAM generation failed: {e}"
                        )


            except Exception as e:

                st.error(
                    f"Image analysis failed: {e}"
                )

            finally:

                # ==========================================
                # DELETE TEMP IMAGE
                # ==========================================

                if (
                    image_path is not None
                    and os.path.exists(image_path)
                ):

                    os.remove(image_path)


# ==================================================
# VIDEO ANALYSIS
# ==================================================

elif media_type == "🎥 Video":

    uploaded_video = st.file_uploader(
        "Upload Video",
        type=[
            "mp4",
            "avi",
            "mov"
        ]
    )

    if uploaded_video is not None:

        st.video(
            uploaded_video
        )

        if st.button(
            "🔎 Start Video Analysis"
        ):

            video_path = None

            try:

                # ==========================================
                # SAVE TEMPORARY VIDEO
                # ==========================================

                file_extension = os.path.splitext(
                    uploaded_video.name
                )[1]

                if file_extension == "":
                    file_extension = ".mp4"

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=file_extension
                ) as temp_file:

                    temp_file.write(
                        uploaded_video.getvalue()
                    )

                    video_path = temp_file.name


                # ==========================================
                # VIDEO ANALYSIS
                # ==========================================

                with st.spinner(
                    "AI is analyzing video frames..."
                ):

                    result = analyze_video(
                        video_path,
                        frame_interval=15
                    )


                st.divider()


                # ==========================================
                # VIDEO RESULT
                # ==========================================

                if result["result"] == "FAKE":

                    st.error(
                        "🔴 VIDEO LIKELY AI-GENERATED"
                    )

                else:

                    st.warning(
                        "🟡 VIDEO LIKELY REAL"
                    )

                st.metric(
                    "Confidence",
                    f'{result["confidence"]:.2f}%'
                )


                # ==========================================
                # FRAME INFORMATION
                # ==========================================

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Frames Analyzed",
                        result["analyzed_frames"]
                    )

                with col2:

                    st.metric(
                        "Fake Frames",
                        result["fake_frames"]
                    )

                with col3:

                    st.metric(
                        "Real Frames",
                        result["real_frames"]
                    )


                st.write(
                    f'**Fake Frame Ratio:** '
                    f'{result["fake_ratio"]:.2f}%'
                )


                # ==========================================
                # DIGITAL EVIDENCE
                # ==========================================

                video_evidence = create_evidence_record(
                    file_path=video_path,
                    file_name=uploaded_video.name,
                    result=result["result"],
                    confidence=result["confidence"]
                )


                # ==========================================
                # SAVE VIDEO ANALYSIS TO DATABASE
                # ==========================================

                save_analysis(
                    evidence_id=video_evidence["evidence_id"],
                    file_name=video_evidence["file_name"],
                    file_type=video_evidence["file_type"],
                    analysis_type="Video",
                    result=video_evidence["result"],
                    confidence=video_evidence["confidence"],
                    uncertainty=100 - video_evidence["confidence"],
                    sha256=video_evidence["sha256"],
                    analysis_time=video_evidence["analysis_time"]
                )


                st.divider()

                st.subheader(
                    "🔐 Digital Evidence"
                )


                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**Evidence ID:** "
                        f"{video_evidence['evidence_id']}"
                    )

                    st.write(
                        f"**File Name:** "
                        f"{video_evidence['file_name']}"
                    )

                    st.write(
                        f"**File Type:** "
                        f"{video_evidence['file_type']}"
                    )

                    st.write(
                        f"**File Size:** "
                        f"{video_evidence['file_size']}"
                    )

                with col2:

                    st.write(
                        f"**Analysis Time:** "
                        f"{video_evidence['analysis_time']}"
                    )

                    st.write(
                        f"**Result:** "
                        f"{video_evidence['result']}"
                    )

                    st.write(
                        f"**Confidence:** "
                        f"{video_evidence['confidence']:.2f}%"
                    )


                st.write(
                    "**SHA-256 File Hash:**"
                )

                st.code(
                    video_evidence["sha256"],
                    language="text"
                )

                st.info(
                    "The SHA-256 hash acts as a digital fingerprint "
                    "of the analyzed video."
                )


                # ==========================================
                # PDF FORENSIC REPORT
                # ==========================================

                video_uncertainty = (
                    100 - result["confidence"]
                )

                if result["confidence"] >= 80:

                    video_reliability = "HIGH"

                elif result["confidence"] >= 65:

                    video_reliability = "MEDIUM"

                else:

                    video_reliability = "LOW"


                st.divider()

                st.subheader(
                    "📄 Forensic Report"
                )


                video_fake_score = (
                    result["confidence"]
                    if result["result"] == "FAKE"
                    else 100 - result["confidence"]
                )


                video_pdf = create_pdf_report(
                    evidence_records=[
                        video_evidence
                    ],

                    final_result=result["result"],

                    final_confidence=result["confidence"],

                    uncertainty=video_uncertainty,

                    reliability=video_reliability,

                    evidence_strength="MODERATE",

                    model_agreement="N/A",

                    video_fake_score=video_fake_score,

                    video_result=result
                )


                st.download_button(
                    label="📄 Download Forensic PDF Report",

                    data=video_pdf,

                    file_name=(
                        f"RealCheck_AI_Video_Report_"
                        f"{video_evidence['evidence_id']}.pdf"
                    ),

                    mime="application/pdf"
                )


                # ==========================================
                # SUSPICIOUS FRAMES
                # ==========================================

                st.subheader(
                    "⚠️ Suspicious Frames"
                )

                suspicious = result[
                    "suspicious_frames"
                ]

                if len(suspicious) > 0:

                    for item in suspicious[:20]:

                        st.write(
                            f'🔴 Frame '
                            f'{item["frame"]} | '
                            f'Time: '
                            f'{item["time"]:.2f}s | '
                            f'Fake probability: '
                            f'{item["fake_probability"]:.2f}%'
                        )

                else:

                    st.success(
                        "No highly suspicious "
                        "frames detected."
                    )


            except Exception as e:

                st.error(
                    f"Video analysis failed: {e}"
                )

            finally:

                # ==========================================
                # DELETE TEMP VIDEO
                # ==========================================

                if (
                    video_path is not None
                    and os.path.exists(video_path)
                ):

                    os.remove(video_path)


# ==================================================
# MULTIMODAL FUSION
# ==================================================

else:

    st.subheader(
        "🔗 Multimodal Image + Video Analysis"
    )

    st.write(
        "Upload both an image and a video. "
        "RealCheck AI will analyze both modalities "
        "and combine their results into a final prediction."
    )


    # ==========================================
    # UPLOAD IMAGE
    # ==========================================

    fusion_image_file = st.file_uploader(
        "🖼️ Upload Image",
        type=[
            "jpg",
            "jpeg",
            "png"
        ],
        key="fusion_image"
    )


    # ==========================================
    # UPLOAD VIDEO
    # ==========================================

    fusion_video_file = st.file_uploader(
        "🎥 Upload Video",
        type=[
            "mp4",
            "avi",
            "mov"
        ],
        key="fusion_video"
    )


    # ==========================================
    # SHOW UPLOADED MEDIA
    # ==========================================

    fusion_image = None

    if fusion_image_file is not None:

        fusion_image = Image.open(
            fusion_image_file
        ).convert("RGB")

        st.image(
            fusion_image,
            caption="Fusion Image",
            width=450
        )


    if fusion_video_file is not None:

        st.video(
            fusion_video_file
        )


    # ==========================================
    # START FUSION ANALYSIS
    # ==========================================

    if (
        fusion_image_file is not None
        and fusion_video_file is not None
    ):

        if st.button(
            "🚀 Start Multimodal Analysis"
        ):

            image_path = None
            video_path = None

            try:

                # ==========================================
                # SAVE ORIGINAL IMAGE
                # ==========================================

                image_extension = os.path.splitext(
                    fusion_image_file.name
                )[1]

                if image_extension == "":
                    image_extension = ".jpg"

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=image_extension
                ) as temp_file:

                    temp_file.write(
                        fusion_image_file.getvalue()
                    )

                    image_path = temp_file.name


                # ==========================================
                # IMAGE ANALYSIS
                # ==========================================

                with st.spinner(
                    "Analyzing image..."
                ):

                    (
                        image_label,
                        image_confidence,
                        image_prediction
                    ) = predict_image(
                        fusion_image
                    )


                if image_label == "FAKE":

                    image_fake_score = image_confidence

                else:

                    image_fake_score = (
                        100 - image_confidence
                    )


                # ==========================================
                # SAVE VIDEO
                # ==========================================

                file_extension = os.path.splitext(
                    fusion_video_file.name
                )[1]

                if file_extension == "":
                    file_extension = ".mp4"

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=file_extension
                ) as temp_file:

                    temp_file.write(
                        fusion_video_file.getvalue()
                    )

                    video_path = temp_file.name


                # ==========================================
                # VIDEO ANALYSIS
                # ==========================================

                with st.spinner(
                    "Analyzing video frames..."
                ):

                    video_result = analyze_video(
                        video_path,
                        frame_interval=15
                    )


                if video_result["result"] == "FAKE":

                    video_fake_score = (
                        video_result["confidence"]
                    )

                else:

                    video_fake_score = (
                        100 - video_result["confidence"]
                    )


                # ==========================================
                # MULTIMODAL FUSION
                # ==========================================

                with st.spinner(
                    "Combining image and video evidence..."
                ):

                    fusion_result = multimodal_fusion(
                        image_fake_score=image_fake_score,
                        video_fake_score=video_fake_score
                    )


                # ==========================================
                # CONFIDENCE ENGINE
                # ==========================================

                confidence_result = calculate_confidence(
                    fake_score=fusion_result["fake_score"],
                    image_fake_score=image_fake_score,
                    video_fake_score=video_fake_score
                )


                # ==========================================
                # FINAL RESULT DATA
                # ==========================================

                final_result = confidence_result[
                    "result"
                ]

                final_confidence = confidence_result[
                    "confidence"
                ]

                uncertainty = confidence_result[
                    "uncertainty"
                ]

                reliability = confidence_result[
                    "reliability"
                ]

                evidence_strength = confidence_result[
                    "evidence_strength"
                ]

                model_agreement = confidence_result[
                    "model_agreement"
                ]


                st.divider()


                # ==========================================
                # MULTIMODAL FUSION RESULT
                # ==========================================

                st.subheader(
                    "🧠 Multimodal Fusion Result"
                )


                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "🖼️ Image Fake Score",
                        f"{image_fake_score:.2f}%"
                    )

                with col2:

                    st.metric(
                        "🎥 Video Fake Score",
                        f"{video_fake_score:.2f}%"
                    )


                st.divider()


                # ==========================================
                # FINAL RESULT
                # ==========================================

                if final_result == "FAKE":

                    st.error(
                        "🔴 AI-GENERATED / FAKE"
                    )

                    st.metric(
                        "Final Confidence",
                        f"{final_confidence:.2f}%"
                    )

                    st.warning(
                        "Multimodal analysis detected "
                        "patterns associated with "
                        "AI-generated or manipulated media."
                    )

                else:

                    st.warning(
                        "🟡 LIKELY REAL"
                    )

                    st.metric(
                        "Final Confidence",
                        f"{final_confidence:.2f}%"
                    )

                    st.info(
                        "Multimodal analysis found the "
                        "provided media more consistent "
                        "with real content."
                    )


                # ==========================================
                # CONFIDENCE & RELIABILITY
                # ==========================================

                st.divider()

                st.subheader(
                    "📊 Confidence & Reliability Analysis"
                )


                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric(
                        "Confidence",
                        f"{final_confidence:.2f}%"
                    )

                with col2:

                    st.metric(
                        "Uncertainty",
                        f"{uncertainty:.2f}%"
                    )

                with col3:

                    st.metric(
                        "Reliability",
                        reliability
                    )

                with col4:

                    st.metric(
                        "Evidence Strength",
                        evidence_strength
                    )


                # ==========================================
                # MODEL AGREEMENT
                # ==========================================

                if model_agreement == "AGREE":

                    st.success(
                        "✓ Image and video models agree "
                        "on the overall prediction."
                    )

                elif model_agreement == "DISAGREE":

                    st.warning(
                        "⚠️ Image and video models disagree. "
                        "The prediction should be interpreted "
                        "cautiously."
                    )


                # ==========================================
                # UNCERTAINTY
                # ==========================================

                st.write(
                    f"**Uncertainty Level:** "
                    f"{uncertainty:.2f}%"
                )

                st.progress(
                    min(
                        max(
                            int(uncertainty),
                            0
                        ),
                        100
                    )
                )


                # ==========================================
                # DISCLAIMER
                # ==========================================

                st.info(
                    "⚠️ RealCheck AI provides an AI-assisted "
                    "assessment. The result should not be treated "
                    "as absolute proof of authenticity or manipulation."
                )


                # ==========================================
                # FUSION DETAILS
                # ==========================================

                st.subheader(
                    "📊 Fusion Analysis"
                )

                st.write(
                    "Image contribution: **40%**"
                )

                st.write(
                    "Video contribution: **60%**"
                )


                # ==========================================
                # VIDEO EVIDENCE
                # ==========================================

                st.subheader(
                    "🎥 Video Evidence"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Frames Analyzed",
                        video_result[
                            "analyzed_frames"
                        ]
                    )

                with col2:

                    st.metric(
                        "Fake Frames",
                        video_result[
                            "fake_frames"
                        ]
                    )

                with col3:

                    st.metric(
                        "Real Frames",
                        video_result[
                            "real_frames"
                        ]
                    )


                st.write(
                    f'**Fake Frame Ratio:** '
                    f'{video_result["fake_ratio"]:.2f}%'
                )


                # ==========================================
                # SUSPICIOUS FRAMES
                # ==========================================

                st.subheader(
                    "⚠️ Suspicious Video Frames"
                )

                suspicious = video_result[
                    "suspicious_frames"
                ]

                if len(suspicious) > 0:

                    for item in suspicious[:20]:

                        st.write(
                            f'🔴 Frame '
                            f'{item["frame"]} | '
                            f'Time: '
                            f'{item["time"]:.2f}s | '
                            f'Fake probability: '
                            f'{item["fake_probability"]:.2f}%'
                        )

                else:

                    st.success(
                        "No highly suspicious "
                        "video frames detected."
                    )


                # ==========================================
                # DIGITAL EVIDENCE
                # ==========================================

                image_evidence = create_evidence_record(
                    file_path=image_path,
                    file_name=fusion_image_file.name,
                    result=image_label,
                    confidence=image_confidence
                )


                video_evidence = create_evidence_record(
                    file_path=video_path,
                    file_name=fusion_video_file.name,
                    result=final_result,
                    confidence=final_confidence
                )


                # ==========================================
                # SAVE MULTIMODAL ANALYSIS TO DATABASE
                # ==========================================

                save_analysis(
                    evidence_id=image_evidence["evidence_id"],
                    file_name=image_evidence["file_name"],
                    file_type=image_evidence["file_type"],
                    analysis_type="Multimodal - Image",
                    result=image_evidence["result"],
                    confidence=image_evidence["confidence"],
                    uncertainty=100 - image_evidence["confidence"],
                    sha256=image_evidence["sha256"],
                    analysis_time=image_evidence["analysis_time"]
                )

                save_analysis(
                    evidence_id=video_evidence["evidence_id"],
                    file_name=video_evidence["file_name"],
                    file_type=video_evidence["file_type"],
                    analysis_type="Multimodal - Video",
                    result=final_result,
                    confidence=final_confidence,
                    uncertainty=uncertainty,
                    sha256=video_evidence["sha256"],
                    analysis_time=video_evidence["analysis_time"]
                )


                st.divider()

                st.subheader(
                    "🔐 Digital Evidence"
                )


                # ==========================================
                # IMAGE EVIDENCE
                # ==========================================

                st.markdown(
                    "### 🖼️ Image Evidence"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**Evidence ID:** "
                        f"{image_evidence['evidence_id']}"
                    )

                    st.write(
                        f"**File Name:** "
                        f"{image_evidence['file_name']}"
                    )

                    st.write(
                        f"**File Type:** "
                        f"{image_evidence['file_type']}"
                    )

                    st.write(
                        f"**File Size:** "
                        f"{image_evidence['file_size']}"
                    )

                with col2:

                    st.write(
                        f"**Result:** "
                        f"{image_evidence['result']}"
                    )

                    st.write(
                        f"**Confidence:** "
                        f"{image_evidence['confidence']:.2f}%"
                    )

                    st.write(
                        f"**Analysis Time:** "
                        f"{image_evidence['analysis_time']}"
                    )


                st.write(
                    "**Image SHA-256 Hash:**"
                )

                st.code(
                    image_evidence["sha256"],
                    language="text"
                )


                # ==========================================
                # VIDEO EVIDENCE
                # ==========================================

                st.markdown(
                    "### 🎥 Video Evidence Record"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"**Evidence ID:** "
                        f"{video_evidence['evidence_id']}"
                    )

                    st.write(
                        f"**File Name:** "
                        f"{video_evidence['file_name']}"
                    )

                    st.write(
                        f"**File Type:** "
                        f"{video_evidence['file_type']}"
                    )

                    st.write(
                        f"**File Size:** "
                        f"{video_evidence['file_size']}"
                    )

                with col2:

                    st.write(
                        f"**Result:** "
                        f"{video_evidence['result']}"
                    )

                    st.write(
                        f"**Confidence:** "
                        f"{video_evidence['confidence']:.2f}%"
                    )

                    st.write(
                        f"**Analysis Time:** "
                        f"{video_evidence['analysis_time']}"
                    )


                st.write(
                    "**Video SHA-256 Hash:**"
                )

                st.code(
                    video_evidence["sha256"],
                    language="text"
                )


                st.info(
                    "SHA-256 hashes provide unique digital "
                    "fingerprints for the original analyzed "
                    "image and video files."
                )


                # ==========================================
                # STEP 13 — MULTIMODAL PDF REPORT
                # ==========================================

                st.divider()

                st.subheader(
                    "📄 Forensic Report"
                )


                multimodal_pdf = create_pdf_report(

                    evidence_records=[
                        image_evidence,
                        video_evidence
                    ],

                    final_result=final_result,

                    final_confidence=final_confidence,

                    uncertainty=uncertainty,

                    reliability=reliability,

                    evidence_strength=evidence_strength,

                    model_agreement=model_agreement,

                    image_fake_score=image_fake_score,

                    video_fake_score=video_fake_score,

                    video_result=video_result
                )


                st.download_button(

                    label=(
                        "📄 Download Multimodal "
                        "Forensic PDF Report"
                    ),

                    data=multimodal_pdf,

                    file_name=(
                        f"RealCheck_AI_Multimodal_Report_"
                        f"{image_evidence['evidence_id']}.pdf"
                    ),

                    mime="application/pdf"
                )


                # ==========================================
                # GRAD-CAM
                # ==========================================

                st.divider()

                st.subheader(
                    "🔍 Explainable AI — Image Grad-CAM"
                )

                with st.spinner(
                    "Generating AI explanation..."
                ):

                    try:

                        model = load_model()

                        gradcam_image = create_gradcam_image(
                            model=model,
                            image=fusion_image,
                            transform=transform,
                            target_class=image_prediction,
                            device=device
                        )

                        st.image(
                            gradcam_image,
                            caption=(
                                "Grad-CAM: Important Regions "
                                "Influencing Image Prediction"
                            ),
                            width=600
                        )

                        st.info(
                            "Grad-CAM highlights regions that "
                            "influenced the image model's decision. "
                            "It does not prove that a highlighted "
                            "region is fake."
                        )

                    except Exception as e:

                        st.error(
                            f"Grad-CAM generation failed: {e}"
                        )


            except Exception as e:

                st.error(
                    f"Multimodal analysis failed: {e}"
                )

            finally:

                # ==========================================
                # DELETE TEMP IMAGE
                # ==========================================

                if (
                    image_path is not None
                    and os.path.exists(image_path)
                ):

                    os.remove(image_path)


                # ==========================================
                # DELETE TEMP VIDEO
                # ==========================================

                if (
                    video_path is not None
                    and os.path.exists(video_path)
                ):

                    os.remove(video_path)


    elif (
        fusion_image_file is not None
        or fusion_video_file is not None
    ):

        st.info(
            "Please upload BOTH an image and a video "
            "to perform multimodal fusion."
        )

    else:

        st.info(
            "Upload an image and a video to begin "
            "multimodal analysis."
        )

# ==================================================
# ANALYSIS HISTORY
# ==================================================

st.divider()

st.header("📚 Analysis History")

history = get_analysis_history()

if history:

    history_data = []

    for row in history:

        history_data.append({
            "ID": row["id"],
            "Evidence ID": row["evidence_id"],
            "File Name": row["file_name"],
            "File Type": row["file_type"],
            "Analysis Type": row["analysis_type"],
            "Result": row["result"],
            "Confidence": f'{row["confidence"]:.2f}%',
            "Uncertainty": f'{row["uncertainty"]:.2f}%',
            "Analysis Time": row["analysis_time"]
        })

    st.dataframe(
        history_data,
        use_container_width=True,
        hide_index=True
    )

    if st.button("🗑️ Clear Analysis History"):

        clear_analysis_history()

        st.success(
            "Analysis history cleared successfully."
        )

        st.rerun()

else:

    st.info(
        "No analysis history available yet."
    )
