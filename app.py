
import streamlit as st
from PIL import Image
import tempfile
import os

# ==================================================
# REALCHECK AI MODULES
# ==================================================

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
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="RealCheck AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# INITIALIZE DATABASE
# ==================================================

initialize_database()


# ==================================================
# CUSTOM UI
# ==================================================

st.html(
    """
    <style>

    /* ==============================================
       GLOBAL BACKGROUND
       ============================================== */

    .stApp {
        background:
            radial-gradient(
                circle at 15% 15%,
                rgba(0, 220, 255, 0.13),
                transparent 28%
            ),
            radial-gradient(
                circle at 85% 25%,
                rgba(120, 0, 255, 0.12),
                transparent 30%
            ),
            radial-gradient(
                circle at 50% 90%,
                rgba(0, 255, 170, 0.08),
                transparent 28%
            ),
            #050816;

        color: #f5f7ff;
        overflow-x: hidden;
    }


    /* ==============================================
       MOVING 3D GRID
       ============================================== */

    .stApp::before {
        content: "";
        position: fixed;
        left: -20%;
        right: -20%;
        bottom: -20%;
        height: 65%;

        background-image:
            linear-gradient(
                rgba(0, 210, 255, 0.12) 1px,
                transparent 1px
            ),
            linear-gradient(
                90deg,
                rgba(0, 210, 255, 0.12) 1px,
                transparent 1px
            );

        background-size: 70px 70px;

        transform:
            perspective(450px)
            rotateX(62deg)
            translateY(0);

        transform-origin: center bottom;

        animation: gridMove 8s linear infinite;

        pointer-events: none;
        z-index: 0;

        mask-image: linear-gradient(
            to top,
            rgba(0,0,0,1),
            rgba(0,0,0,0)
        );
    }

    @keyframes gridMove {
        from {
            background-position: 0 0;
        }

        to {
            background-position: 0 70px;
        }
    }


    /* ==============================================
       FLOATING AURA
       ============================================== */

    .stApp::after {
        content: "";
        position: fixed;

        width: 450px;
        height: 450px;

        left: 50%;
        top: 35%;

        transform: translate(-50%, -50%);

        background:
            radial-gradient(
                circle,
                rgba(0, 220, 255, 0.10),
                transparent 65%
            );

        filter: blur(20px);

        animation: auraMove 9s ease-in-out infinite alternate;

        pointer-events: none;
        z-index: 0;
    }

    @keyframes auraMove {

        0% {
            transform:
                translate(-55%, -45%)
                scale(0.9);
        }

        50% {
            transform:
                translate(-35%, -55%)
                scale(1.2);
        }

        100% {
            transform:
                translate(-65%, -35%)
                scale(1);
        }
    }


    /* ==============================================
       MAIN CONTENT
       ============================================== */

    .block-container {
        position: relative;
        z-index: 2;

        padding-top: 2rem;
        padding-bottom: 3rem;

        max-width: 1250px;
    }


    /* ==============================================
       HEADER
       ============================================== */

    .rc-header {
        text-align: center;
        padding: 25px 10px 20px;
    }

    .rc-icon {
        display: inline-flex;

        width: 150px;
        height: 150px;

        align-items: center;
        justify-content: center;

        border-radius: 50%;

        font-size: 80px;

        background:
            radial-gradient(
                circle at 35% 30%,
                rgba(255,255,255,0.25),
                rgba(0,220,255,0.10)
            );

        border: 1px solid rgba(255,255,255,0.20);

        box-shadow:
            0 0 25px rgba(0,220,255,0.35),
            inset 0 0 30px rgba(255,255,255,0.05);

        animation:
            iconFloat 4s ease-in-out infinite,
            iconGlow 3s ease-in-out infinite alternate;
    }

    @keyframes iconFloat {

        0%, 100% {
            transform:
                translateY(0)
                rotateY(0deg);
        }

        50% {
            transform:
                translateY(-12px)
                rotateY(15deg);
        }
    }

    @keyframes iconGlow {

        from {
            box-shadow:
                0 0 20px rgba(0,220,255,0.25),
                inset 0 0 20px rgba(255,255,255,0.04);
        }

        to {
            box-shadow:
                0 0 45px rgba(0,220,255,0.60),
                inset 0 0 30px rgba(255,255,255,0.08);
        }
    }


    .rc-title {

        margin-top: 20px;

        font-size: clamp(42px, 7vw, 82px);

        font-weight: 900;

        letter-spacing: 5px;

        background:
            linear-gradient(
                90deg,
                #00eaff,
                #ffffff,
                #9b5cff,
                #00eaff
            );

        background-size: 300% 100%;

        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;

        animation: titleGradient 5s linear infinite;
    }

    @keyframes titleGradient {

        0% {
            background-position: 0% 50%;
        }

        100% {
            background-position: 300% 50%;
        }
    }


    .rc-subtitle {

        margin-top: 8px;

        color: #aeb8d4;

        font-size: 16px;

        letter-spacing: 4px;

        text-transform: uppercase;
    }

    .rc-description {

        max-width: 850px;

        margin: 18px auto 0;

        padding: 18px 24px;

        border-radius: 20px;

        background:
            rgba(255,255,255,0.045);

        border:
            1px solid rgba(255,255,255,0.10);

        backdrop-filter: blur(16px);

        color: #cbd3ea;

        line-height: 1.7;
    }


    /* ==============================================
       GLASS CARDS
       ============================================== */

    div[data-testid="stVerticalBlockBorderWrapper"] {

        background:
            rgba(255,255,255,0.035);

        border:
            1px solid rgba(255,255,255,0.09);

        border-radius: 22px;

        backdrop-filter: blur(18px);

        box-shadow:
            0 15px 50px rgba(0,0,0,0.20);

    }


    /* ==============================================
       RADIO
       ============================================== */

    div[role="radiogroup"] {

        background:
            rgba(255,255,255,0.035);

        padding: 10px;

        border-radius: 18px;

        border:
            1px solid rgba(255,255,255,0.10);

        backdrop-filter: blur(15px);

    }


    /* ==============================================
       UPLOADER
       ============================================== */

    section[data-testid="stFileUploaderDropzone"] {

        background:
            rgba(255,255,255,0.045);

        border:
            1px dashed rgba(0,220,255,0.45);

        border-radius: 20px;

        transition:
            all 0.3s ease;

    }

    section[data-testid="stFileUploaderDropzone"]:hover {

        transform:
            translateY(-3px);

        border-color:
            rgba(0,230,255,0.85);

        box-shadow:
            0 0 30px rgba(0,220,255,0.18);

    }


    /* ==============================================
       BUTTONS
       ============================================== */

    .stButton > button {

        border-radius: 14px;

        border:
            1px solid rgba(0,220,255,0.30);

        background:
            linear-gradient(
                135deg,
                rgba(0,220,255,0.15),
                rgba(120,0,255,0.15)
            );

        color: white;

        font-weight: 700;

        transition:
            all 0.25s ease;

        min-height: 45px;
    }

    .stButton > button:hover {

        transform:
            translateY(-3px)
            scale(1.01);

        border-color:
            rgba(0,230,255,0.80);

        box-shadow:
            0 10px 30px rgba(0,220,255,0.20);
    }


    /* ==============================================
       METRICS
       ============================================== */

    div[data-testid="stMetric"] {

        background:
            rgba(255,255,255,0.035);

        border:
            1px solid rgba(255,255,255,0.08);

        border-radius: 18px;

        padding: 16px;

        transition:
            transform 0.25s ease;
    }

    div[data-testid="stMetric"]:hover {

        transform:
            translateY(-4px)
            perspective(500px)
            rotateX(2deg)
            rotateY(-2deg);

    }


    /* ==============================================
       DATAFRAME
       ============================================== */

    div[data-testid="stDataFrame"] {

        border-radius: 16px;

        overflow: hidden;

        border:
            1px solid rgba(255,255,255,0.08);
    }


    /* ==============================================
       FOOTER
       ============================================== */

    .rc-footer {

        text-align: center;

        margin-top: 60px;

        padding: 30px 20px;

        color: #78829d;

        border-top:
            1px solid rgba(255,255,255,0.08);

        font-size: 13px;
    }

    .rc-contact {

        margin: 20px auto;

        padding: 18px 25px;

        max-width: 520px;

        border-radius: 18px;

        background:
            rgba(255,255,255,0.035);

        border:
            1px solid rgba(0,220,255,0.15);

        backdrop-filter: blur(14px);

        box-shadow:
            0 10px 35px rgba(0,0,0,0.15);

        transition:
            all 0.3s ease;
    }

    .rc-contact:hover {

        transform:
            translateY(-3px);

        border-color:
            rgba(0,220,255,0.45);

        box-shadow:
            0 0 30px rgba(0,220,255,0.12);
    }

    .rc-contact-title {

        color: #00eaff;

        font-size: 16px;

        font-weight: 700;

        margin-bottom: 12px;
    }

    .rc-contact-item {

        margin: 8px 0;

        color: #cbd3ea;

        font-size: 14px;
    }

    .rc-contact-item a {

        color: #cbd3ea;

        text-decoration: none;

        transition:
            color 0.25s ease;
    }

    .rc-contact-item a:hover {

        color: #00eaff;
    }


    /* ==============================================
       MOBILE
       ============================================== */

    @media (max-width: 700px) {

        .rc-title {
            font-size: 42px;
            letter-spacing: 2px;
        }

        .rc-subtitle {
            font-size: 11px;
            letter-spacing: 2px;
        }

        .rc-icon {
            width: 85px;
            height: 85px;
            font-size: 42px;
        }

        .block-container {
            padding-left: 15px;
            padding-right: 15px;
        }

        .rc-contact {
            margin-left: 10px;
            margin-right: 10px;
        }
    }

    </style>

    <div class="rc-header">

        <div class="rc-icon">
            🔍
        </div>

        <div class="rc-title">
            REALCHECK AI
        </div>

        <div class="rc-subtitle">
            MULTIMODAL AI CONTENT FORENSICS
        </div>

        <div class="rc-description">

            Detect suspicious AI-generated and manipulated
            media using image analysis, video frame analysis,
            multimodal fusion, confidence estimation,
            digital evidence, and explainable AI.

            <br><br>

            <b>DETECT • ANALYZE • VERIFY • EXPLAIN</b>

        </div>

    </div>
    """
)


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def save_image_analysis_to_database(evidence, prediction, confidence):

    uncertainty = max(
        0.0,
        100.0 - float(confidence)
    )

    save_analysis(
        evidence_id=evidence["evidence_id"],
        file_name=evidence["file_name"],
        file_type=evidence["file_type"],
        analysis_type="Image Analysis",
        result=prediction,
        confidence=float(confidence),
        uncertainty=uncertainty,
        sha256=evidence["sha256"],
        analysis_time=evidence["analysis_time"]
    )


def save_video_analysis_to_database(evidence, prediction, confidence):

    uncertainty = max(
        0.0,
        100.0 - float(confidence)
    )

    save_analysis(
        evidence_id=evidence["evidence_id"],
        file_name=evidence["file_name"],
        file_type=evidence["file_type"],
        analysis_type="Video Analysis",
        result=prediction,
        confidence=float(confidence),
        uncertainty=uncertainty,
        sha256=evidence["sha256"],
        analysis_time=evidence["analysis_time"]
    )


def save_fusion_analysis_to_database(
    evidence,
    prediction,
    confidence,
    uncertainty
):

    save_analysis(
        evidence_id=evidence["evidence_id"],
        file_name=evidence["file_name"],
        file_type=evidence["file_type"],
        analysis_type="Multimodal Fusion",
        result=prediction,
        confidence=float(confidence),
        uncertainty=float(uncertainty),
        sha256=evidence["sha256"],
        analysis_time=evidence["analysis_time"]
    )


def get_reliability(confidence):

    confidence = float(confidence)

    if confidence >= 80:
        return "HIGH"

    elif confidence >= 65:
        return "MEDIUM"

    return "LOW"


def get_fake_score(label, confidence):

    confidence = float(confidence)

    if label == "FAKE":
        return confidence

    return 100.0 - confidence


def display_evidence(evidence, title="🔐 Digital Evidence"):

    st.divider()

    if title:
        st.subheader(title)

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
            f"{float(evidence['confidence']):.2f}%"
        )

    st.write("**SHA-256 File Hash:**")

    st.code(
        evidence["sha256"],
        language="text"
    )

    st.info(
        "The SHA-256 hash acts as a digital fingerprint "
        "of the analyzed file. If the file changes, "
        "its SHA-256 hash will also change."
    )


# ==================================================
# ANALYSIS MODE
# ==================================================

media_type = st.radio(
    "Analysis Mode",
    [
        "🖼️ Image",
        "🎥 Video",
        "🔗 Multimodal Fusion"
    ],
    horizontal=True,
    label_visibility="collapsed"
)


# ==================================================
# IMAGE ANALYSIS
# ==================================================

if media_type == "🖼️ Image":

    st.markdown("## 🖼️ Image Forensics")

    st.write(
        "Upload an image to determine whether it is "
        "likely real or AI-generated."
    )

    uploaded_image = st.file_uploader(
        "Upload Image",
        type=[
            "jpg",
            "jpeg",
            "png"
        ],
        key="image_upload"
    )

    if uploaded_image is not None:

        image = Image.open(
            uploaded_image
        ).convert("RGB")

        st.image(
            image,
            caption="Uploaded Image",
            width=600
        )

        if st.button(
            "🔎 Start Image Analysis",
            key="start_image_analysis"
        ):

            image_temp_path = None

            try:

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".png"
                ) as temp_image:

                    image.save(
                        temp_image,
                        format="PNG"
                    )

                    image_temp_path = temp_image.name

                with st.spinner(
                    "AI is analyzing the image..."
                ):

                    result = predict_image(
                        image
                    )

                if isinstance(result, dict):

                    prediction = result["prediction"]

                    confidence = (
                        float(result["confidence"]) * 100
                    )

                    fake_score = (
                        float(result["fake_score"]) * 100
                    )

                    real_score = (
                        float(result["real_score"]) * 100
                    )

                    class_id = result["class_id"]

                else:

                    prediction = result[0]

                    confidence = float(result[1])

                    class_id = result[2]

                    fake_score = get_fake_score(
                        prediction,
                        confidence
                    )

                    real_score = (
                        100.0 - fake_score
                    )

                st.divider()

                st.subheader(
                    "🎯 Analysis Result"
                )

                if prediction == "FAKE":

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

                st.subheader(
                    "📊 Prediction Scores"
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "🔴 Fake Score",
                        f"{fake_score:.2f}%"
                    )

                with col2:

                    st.metric(
                        "🟢 Real Score",
                        f"{real_score:.2f}%"
                    )

                uncertainty = (
                    100.0 - confidence
                )

                reliability = get_reliability(
                    confidence
                )

                evidence = create_evidence_record(
                    file_path=image_temp_path,
                    file_name=uploaded_image.name,
                    result=prediction,
                    confidence=confidence
                )

                display_evidence(
                    evidence
                )

                save_image_analysis_to_database(
                    evidence=evidence,
                    prediction=prediction,
                    confidence=confidence
                )

                st.success(
                    "✅ Analysis saved to history."
                )

                st.divider()

                st.subheader(
                    "📄 Forensic Report"
                )

                pdf_data = create_pdf_report(
                    evidence_records=[
                        evidence
                    ],
                    final_result=prediction,
                    final_confidence=confidence,
                    uncertainty=uncertainty,
                    reliability=reliability,
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

                        gradcam_model = load_model()

                        gradcam_image = create_gradcam_image(
                            gradcam_model,
                            image,
                            transform,
                            class_id,
                            device
                        )

                        st.image(
                            gradcam_image,
                            caption=(
                                "Grad-CAM: Important Regions "
                                "Influencing the Prediction"
                            ),
                            width=650
                        )

                        st.info(
                            "Grad-CAM shows regions that "
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

                if (
                    image_temp_path is not None
                    and os.path.exists(image_temp_path)
                ):

                    try:
                        os.remove(image_temp_path)

                    except Exception:
                        pass


# ==================================================
# VIDEO ANALYSIS
# ==================================================

elif media_type == "🎥 Video":

    st.markdown("## 🎥 Video Forensics")

    st.write(
        "Upload a video and RealCheck AI will analyze "
        "sampled frames for suspicious AI-generated patterns."
    )

    uploaded_video = st.file_uploader(
        "Upload Video",
        type=[
            "mp4",
            "avi",
            "mov"
        ],
        key="video_upload"
    )

    if uploaded_video is not None:

        st.video(
            uploaded_video
        )

        if st.button(
            "🔎 Start Video Analysis",
            key="start_video_analysis"
        ):

            video_path = None

            try:

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

                with st.spinner(
                    "AI is analyzing video frames..."
                ):

                    result = analyze_video(
                        video_path,
                        frame_interval=15
                    )

                st.divider()

                st.subheader(
                    "🎯 Video Analysis Result"
                )

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

                st.subheader(
                    "🎞️ Frame Analysis"
                )

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

                video_evidence = create_evidence_record(
                    file_path=video_path,
                    file_name=uploaded_video.name,
                    result=result["result"],
                    confidence=result["confidence"]
                )

                display_evidence(
                    video_evidence
                )

                save_video_analysis_to_database(
                    evidence=video_evidence,
                    prediction=result["result"],
                    confidence=result["confidence"]
                )

                st.success(
                    "✅ Video analysis saved to history."
                )

                video_confidence = float(
                    result["confidence"]
                )

                video_uncertainty = (
                    100.0 - video_confidence
                )

                video_reliability = get_reliability(
                    video_confidence
                )

                video_fake_score = (
                    video_confidence
                    if result["result"] == "FAKE"
                    else
                    100.0 - video_confidence
                )

                st.divider()

                st.subheader(
                    "📄 Forensic Report"
                )

                video_pdf = create_pdf_report(
                    evidence_records=[
                        video_evidence
                    ],
                    final_result=result["result"],
                    final_confidence=video_confidence,
                    uncertainty=video_uncertainty,
                    reliability=video_reliability,
                    evidence_strength="MODERATE",
                    model_agreement="N/A",
                    video_fake_score=video_fake_score,
                    video_result=result
                )

                st.download_button(
                    label="📄 Download Video Forensic PDF Report",
                    data=video_pdf,
                    file_name=(
                        f"RealCheck_AI_Video_Report_"
                        f"{video_evidence['evidence_id']}.pdf"
                    ),
                    mime="application/pdf"
                )

                st.divider()

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

                if (
                    video_path is not None
                    and os.path.exists(video_path)
                ):

                    try:
                        os.remove(video_path)

                    except Exception:
                        pass


# ==================================================
# MULTIMODAL FUSION
# ==================================================

else:

    st.markdown(
        "## 🔗 Multimodal Image + Video Analysis"
    )

    st.write(
        "Upload both an image and a video. "
        "RealCheck AI analyzes both modalities and "
        "combines their evidence into a final prediction."
    )

    fusion_image_file = st.file_uploader(
        "🖼️ Upload Image",
        type=[
            "jpg",
            "jpeg",
            "png"
        ],
        key="fusion_image"
    )

    fusion_video_file = st.file_uploader(
        "🎥 Upload Video",
        type=[
            "mp4",
            "avi",
            "mov"
        ],
        key="fusion_video"
    )

    fusion_image = None

    if fusion_image_file is not None:

        fusion_image = Image.open(
            fusion_image_file
        ).convert("RGB")

        st.image(
            fusion_image,
            caption="Fusion Image",
            width=500
        )

    if fusion_video_file is not None:

        st.video(
            fusion_video_file
        )

    if (
        fusion_image_file is not None
        and fusion_video_file is not None
    ):

        if st.button(
            "🚀 Start Multimodal Analysis",
            key="start_fusion_analysis"
        ):

            image_path = None
            video_path = None

            try:

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

                with st.spinner(
                    "Analyzing image..."
                ):

                    image_result = predict_image(
                        fusion_image
                    )

                if isinstance(image_result, dict):

                    image_label = image_result[
                        "prediction"
                    ]

                    image_confidence = (
                        float(
                            image_result["confidence"]
                        ) * 100
                    )

                    image_prediction = image_result[
                        "class_id"
                    ]

                else:

                    image_label = image_result[0]

                    image_confidence = float(
                        image_result[1]
                    )

                    image_prediction = image_result[2]

                image_fake_score = get_fake_score(
                    image_label,
                    image_confidence
                )

                video_extension = os.path.splitext(
                    fusion_video_file.name
                )[1]

                if video_extension == "":
                    video_extension = ".mp4"

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=video_extension
                ) as temp_file:

                    temp_file.write(
                        fusion_video_file.getvalue()
                    )

                    video_path = temp_file.name

                with st.spinner(
                    "Analyzing video frames..."
                ):

                    video_result = analyze_video(
                        video_path,
                        frame_interval=15
                    )

                if video_result["result"] == "FAKE":

                    video_fake_score = (
                        float(
                            video_result["confidence"]
                        )
                    )

                else:

                    video_fake_score = (
                        100.0
                        -
                        float(
                            video_result["confidence"]
                        )
                    )

                with st.spinner(
                    "Combining image and video evidence..."
                ):

                    fusion_result = multimodal_fusion(
                        image_fake_score=image_fake_score,
                        video_fake_score=video_fake_score
                    )

                confidence_result = calculate_confidence(
                    fake_score=fusion_result["fake_score"],
                    image_fake_score=image_fake_score,
                    video_fake_score=video_fake_score
                )

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

                st.info(
                    "⚠️ RealCheck AI provides an AI-assisted "
                    "assessment. The result should not be treated "
                    "as absolute proof of authenticity or manipulation."
                )

                st.subheader(
                    "📊 Fusion Analysis"
                )

                st.write(
                    "Image contribution: **40%**"
                )

                st.write(
                    "Video contribution: **60%**"
                )

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

                st.divider()

                st.subheader(
                    "🔐 Digital Evidence"
                )

                st.markdown(
                    "### 🖼️ Image Evidence"
                )

                display_evidence(
                    image_evidence,
                    title=""
                )

                st.markdown(
                    "### 🎥 Video Evidence"
                )

                display_evidence(
                    video_evidence,
                    title=""
                )

                save_analysis(
                    evidence_id=image_evidence[
                        "evidence_id"
                    ],
                    file_name=image_evidence[
                        "file_name"
                    ],
                    file_type=image_evidence[
                        "file_type"
                    ],
                    analysis_type="Multimodal Image",
                    result=image_label,
                    confidence=float(
                        image_confidence
                    ),
                    uncertainty=(
                        100.0 -
                        float(image_confidence)
                    ),
                    sha256=image_evidence[
                        "sha256"
                    ],
                    analysis_time=image_evidence[
                        "analysis_time"
                    ]
                )

                save_fusion_analysis_to_database(
                    evidence=video_evidence,
                    prediction=final_result,
                    confidence=final_confidence,
                    uncertainty=uncertainty
                )

                st.success(
                    "✅ Multimodal analysis saved to history."
                )

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

                st.divider()

                st.subheader(
                    "🔍 Explainable AI — Image Grad-CAM"
                )

                with st.spinner(
                    "Generating AI explanation..."
                ):

                    try:

                        gradcam_model = load_model()

                        gradcam_image = create_gradcam_image(
                            gradcam_model,
                            fusion_image,
                            transform,
                            image_prediction,
                            device
                        )

                        st.image(
                            gradcam_image,
                            caption=(
                                "Grad-CAM: Important Regions "
                                "Influencing Image Prediction"
                            ),
                            width=650
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

                if (
                    image_path is not None
                    and os.path.exists(image_path)
                ):

                    try:
                        os.remove(image_path)

                    except Exception:
                        pass

                if (
                    video_path is not None
                    and os.path.exists(video_path)
                ):

                    try:
                        os.remove(video_path)

                    except Exception:
                        pass

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

st.markdown(
    "## 📚 Analysis History"
)

history = get_analysis_history()

if history:

    history_data = []

    for row in history:

        history_data.append(
            {
                "ID": row["id"],
                "Evidence ID": row["evidence_id"],
                "File Name": row["file_name"],
                "File Type": row["file_type"],
                "Analysis Type": row["analysis_type"],
                "Result": row["result"],
                "Confidence": (
                    f'{float(row["confidence"]):.2f}%'
                ),
                "Uncertainty": (
                    f'{float(row["uncertainty"]):.2f}%'
                ),
                "SHA-256": row["sha256"],
                "Analysis Time": row["analysis_time"]
            }
        )

    st.dataframe(
        history_data,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Total analyses recorded: {len(history)}"
    )

    if st.button(
        "🗑️ Clear Analysis History",
        key="clear_history"
    ):

        clear_analysis_history()

        st.success(
            "Analysis history cleared successfully."
        )

        st.rerun()

else:

    st.info(
        "No analysis history available yet."
    )


# ==================================================
# FOOTER + CONTACT
# ==================================================

st.html(
    """
    <div class="rc-footer">

        <b style="
            color:#00eaff;
            font-size:18px;
        ">
            REALCHECK AI
        </b>

        <br><br>

        Multimodal AI Content Forensics System

        <br>

        Detect • Analyze • Verify • Explain

        <br><br>

        <div class="rc-contact">

            <div class="rc-contact-title">
                📞 Contact
            </div>

            <div class="rc-contact-item">
                📱
                <a href="tel:7498153139">
                    <b>7498153139</b>
                </a>
            </div>

            <div class="rc-contact-item">
                📧
                <a href="mailto:rakkeshdambhare13@gmail.com">
                    <b>rakkeshdambhare13@gmail.com</b>
                </a>
            </div>

        </div>

        AI-assisted media authenticity assessment.

        <br>

        Results should not be treated as absolute proof.

        <br><br>

        © 2026 RealCheck AI. All Rights Reserved.

    </div>
    """
)
