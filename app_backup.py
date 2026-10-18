
import os
import time
import hashlib
import tempfile
from datetime import datetime

import streamlit as st

from src.predict_image import predict_image, load_model, transform, device
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
    clear_analysis_history,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="RealCheck AI",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ANIMATED UI / CSS
# ============================================================
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --rc-cyan: #00e5ff;
    --rc-purple: #a855f7;
    --rc-blue: #3b82f6;
    --rc-text: #edf7ff;
    --rc-muted: #a6b8d0;
    --rc-panel: rgba(9, 20, 43, 0.78);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse at 10% 15%,
            rgba(0, 225, 255, 0.22), transparent 38%),
        radial-gradient(ellipse at 90% 25%,
            rgba(145, 65, 255, 0.24), transparent 40%),
        radial-gradient(ellipse at 50% 95%,
            rgba(0, 100, 255, 0.18), transparent 42%),
        linear-gradient(125deg, #050817, #09162b, #160b2d, #06192b) !important;
    background-size: 200% 200% !important;
    animation: rc-color-flow 6s ease-in-out infinite;
    color: var(--rc-text);
    position: relative;
    isolation: isolate;
    overflow-x: hidden;
}

/* Animated perspective grid */
.stApp::before {
    content: "";
    position: fixed;
    inset: -30% -50%;
    width: 200%;
    height: 160%;
    pointer-events: none;
    z-index: -1;
    background-image:
        linear-gradient(rgba(65, 220, 255, 0.20) 1px, transparent 1px),
        linear-gradient(90deg, rgba(65, 220, 255, 0.20) 1px, transparent 1px);
    background-size: 48px 48px;
    transform: perspective(600px) rotateX(60deg);
    transform-origin: center center;
    mask-image: linear-gradient(
        to bottom, transparent, black 20%, black 80%, transparent
    );
    animation: rc-background-motion 2.5s linear infinite;
}

/* Moving colored glow */
.stApp::after {
    content: "";
    position: fixed;
    width: 650px;
    height: 650px;
    top: 10%;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 50%;
    pointer-events: none;
    z-index: -1;
    background: conic-gradient(
        from 0deg,
        rgba(0, 225, 255, 0.18),
        rgba(130, 70, 255, 0.20),
        rgba(0, 130, 255, 0.18),
        rgba(0, 255, 200, 0.12),
        rgba(0, 225, 255, 0.18)
    );
    filter: blur(75px);
    animation: rc-glow-motion 5s linear infinite;
}

@keyframes rc-background-motion {
    from { background-position: 0 0, 0 0; }
    to { background-position: 0 96px, 96px 0; }
}

@keyframes rc-color-flow {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

@keyframes rc-glow-motion {
    0% { rotate: 0deg; scale: 0.9; opacity: 0.55; }
    50% { rotate: 180deg; scale: 1.12; opacity: 0.9; }
    100% { rotate: 360deg; scale: 0.9; opacity: 0.55; }
}

.rc-hero {
    text-align: center;
    padding: 30px 10px 24px;
    border: 1px solid rgba(0, 229, 255, 0.25);
    border-radius: 22px;
    background: linear-gradient(
        135deg, rgba(5, 20, 43, 0.85), rgba(40, 15, 72, 0.72)
    );
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.08);
    margin-bottom: 24px;
}

.rc-icon {
    font-size: 48px;
    display: inline-block;
    animation: rc-icon-float 3s ease-in-out infinite;
}

.rc-title {
    font-size: clamp(30px, 5vw, 48px);
    font-weight: 800;
    letter-spacing: -1px;
    margin: 6px 0;
    color: #fff;
    text-shadow: 0 0 24px rgba(0, 229, 255, 0.45);
}

.rc-title span {
    color: var(--rc-cyan);
}

.rc-subtitle {
    color: var(--rc-muted);
    font-size: 14px;
}

@keyframes rc-icon-float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-7px); }
}

.rc-panel {
    border: 1px solid rgba(0, 229, 255, 0.22);
    border-radius: 16px;
    background: var(--rc-panel);
    padding: 18px;
    margin: 8px 0 16px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.rc-label {
    color: var(--rc-cyan);
    font-weight: 700;
    letter-spacing: 1px;
    font-size: 12px;
    text-transform: uppercase;
}

.rc-result {
    border-radius: 14px;
    padding: 18px;
    margin: 12px 0;
    border: 1px solid rgba(255, 255, 255, 0.14);
    background: rgba(5, 15, 35, 0.7);
}

.rc-real { border-left: 5px solid #facc15; }
.rc-fake { border-left: 5px solid #ff4d6d; }
.rc-neutral { border-left: 5px solid var(--rc-cyan); }

div[data-testid="stFileUploader"] {
    border: 1px dashed rgba(0, 229, 255, 0.45);
    border-radius: 14px;
    padding: 8px;
    background: rgba(0, 229, 255, 0.035);
}

.stButton > button,
.stDownloadButton > button {
    border: 1px solid rgba(0, 229, 255, 0.45);
    border-radius: 10px;
    background: linear-gradient(100deg, #075985, #5b21b6);
    color: white;
    font-weight: 700;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.22);
    border-color: var(--rc-cyan);
}

[data-testid="stMetric"] {
    border: 1px solid rgba(0, 229, 255, 0.20);
    border-radius: 12px;
    padding: 12px;
    background: rgba(7, 20, 43, 0.7);
}

h1, h2, h3, p, label {
    color: var(--rc-text);
}

.rc-footer {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    padding: 25px 0 10px;
}

@media (prefers-reduced-motion: reduce) {
    .stApp,
    .stApp::before,
    .stApp::after,
    .rc-icon {
        animation: none !important;
    }
}
</style>

<div class="rc-hero">
    <div class="rc-icon">🔎</div>
    <div class="rc-title">RealCheck <span>AI</span></div>
    <div class="rc-subtitle">
        Multimodal AI-Based Fake Media Detection and Prediction System
    </div>
</div>
""")


# ============================================================
# DATABASE INITIALIZATION
# ============================================================
try:
    initialize_database()
except Exception as exc:
    st.error(f"Database initialization failed: {exc}")


# ============================================================
# HELPERS
# ============================================================
def file_sha256(file_bytes):
    """Return the SHA-256 hash of uploaded file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def save_uploaded_temp(uploaded_file):
    """Save an uploaded file temporarily and return its path."""
    suffix = os.path.splitext(uploaded_file.name)[1]
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp.write(uploaded_file.getvalue())
        return temp.name
    finally:
        temp.close()


def cleanup_temp(path):
    """Delete a temporary file if it exists."""
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def show_result(result, media_name, media_hash, media_type):
    """
    Display a prediction and save the analysis.

    Supports dictionary results and basic string results. Your prediction
    modules may use different dictionary keys, so inspect the returned
    result if the displayed label or confidence is missing.
    """
    st.subheader("Analysis Result")

    if isinstance(result, dict):
        label = (
            result.get("label")
            or result.get("prediction")
            or result.get("class")
            or result.get("result")
            or "Unknown"
        )
        confidence = result.get("confidence", result.get("probability", None))
        details = result
    else:
        label = str(result)
        confidence = None
        details = {"result": label}

    label_text = str(label)
    label_lower = label_text.lower()

    if "fake" in label_lower or "ai-generated" in label_lower:
        style_class = "rc-fake"
        icon = "🚨"
    elif "real" in label_lower or "authentic" in label_lower:
        style_class = "rc-real"
        icon = "🟡"
    else:
        style_class = "rc-neutral"
        icon = "🔎"

    st.html(
        f"""
        <div class="rc-result {style_class}">
            <div style="font-size:14px;color:#a6b8d0;">PREDICTION</div>
            <div style="font-size:28px;font-weight:800;">
                {icon} {label_text}
            </div>
        </div>
        """
    )

    if confidence is not None:
        try:
            confidence_value = float(confidence)
            # Accommodate either 0-1 or 0-100 confidence values.
            if 0 <= confidence_value <= 1:
                confidence_value *= 100
            confidence_value = max(0.0, min(100.0, confidence_value))
            st.metric("Confidence", f"{confidence_value:.2f}%")
            st.progress(confidence_value / 100)
        except (TypeError, ValueError):
            st.write("Confidence:", confidence)

    with st.expander("View technical details"):
        st.json(details, expanded=True)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "filename": media_name,
        "media_type": media_type,
        "sha256": media_hash,
        "prediction": label_text,
        "confidence": confidence,
        "details": details,
    }

    # Save through the project's existing evidence module.
    try:
        evidence = create_evidence_record(record)
        st.subheader("Evidence Record")
        st.json(evidence if evidence is not None else record)
    except Exception as exc:
        st.warning(f"Evidence record could not be created: {exc}")
        evidence = record

    # Save analysis history using the existing database module.
    try:
        save_analysis(record)
        st.success("Analysis saved to history.")
    except Exception as exc:
        st.warning(f"Could not save analysis history: {exc}")

    # Create downloadable PDF report using the existing report module.
    try:
        report_result = create_pdf_report(record)
        if isinstance(report_result, (bytes, bytearray)):
            st.download_button(
                "📄 Download PDF Report",
                data=bytes(report_result),
                file_name="realcheck_report.pdf",
                mime="application/pdf",
                key=f"report_{media_hash[:12]}",
            )
        elif isinstance(report_result, str) and os.path.isfile(report_result):
            with open(report_result, "rb") as report_file:
                st.download_button(
                    "📄 Download PDF Report",
                    data=report_file.read(),
                    file_name="realcheck_report.pdf",
                    mime="application/pdf",
                    key=f"report_{media_hash[:12]}",
                )
        elif report_result is not None:
            st.info("Your report module returned a result, but its format needs checking.")
    except Exception as exc:
        st.warning(f"PDF report could not be generated: {exc}")


def run_image_analysis(uploaded_image):
    """Run image prediction and optionally generate Grad-CAM."""
    image_bytes = uploaded_image.getvalue()
    image_hash = file_sha256(image_bytes)

    st.image(uploaded_image, caption="Uploaded image", use_container_width=True)

    if not st.button("🔍 Analyze Image", type="primary", key="analyze_image"):
        return

    with st.spinner("Analyzing image..."):
        temp_path = save_uploaded_temp(uploaded_image)
        try:
            # The prediction function in this project may expect a path
            # or an image object. This version passes the saved file path.
            prediction = predict_image(temp_path)
        finally:
            cleanup_temp(temp_path)

    show_result(prediction, uploaded_image.name, image_hash, "image")

    st.subheader("Grad-CAM Visual Explanation")
    try:
        with st.spinner("Generating visual explanation..."):
            gradcam_result = create_gradcam_image(uploaded_image)
        if gradcam_result is not None:
            if isinstance(gradcam_result, str) and os.path.isfile(gradcam_result):
                st.image(
                    gradcam_result,
                    caption="Grad-CAM heatmap",
                    use_container_width=True,
                )
            else:
                st.write(gradcam_result)
        else:
            st.info("Grad-CAM did not return an image.")
    except Exception as exc:
        st.warning(f"Grad-CAM could not be generated: {exc}")


def run_video_analysis(uploaded_video):
    """Run video analysis using the existing video module."""
    video_bytes = uploaded_video.getvalue()
    video_hash = file_sha256(video_bytes)

    st.video(video_bytes)

    if not st.button("🎞️ Analyze Video", type="primary", key="analyze_video"):
        return

    with st.spinner("Analyzing video frames..."):
        temp_path = save_uploaded_temp(uploaded_video)
        try:
            # This assumes analyze_video accepts a video file path.
            result = analyze_video(temp_path)
        finally:
            cleanup_temp(temp_path)

    show_result(result, uploaded_video.name, video_hash, "video")


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚙️ Control Center")
    st.caption("RealCheck AI")

    page = st.radio(
        "Choose a module",
        [
            "Image Detection",
            "Video Detection",
            "Multimodal Fusion",
            "Analysis History",
            "About Project",
        ],
    )

    st.divider()
    st.markdown("### Detection Indicators")
    st.markdown("🔴 **Red:** Possible fake / AI-generated media")
    st.markdown("🟡 **Yellow:** Possible real media")
    st.caption("Predictions are estimates, not proof of authenticity.")


# ============================================================
# IMAGE DETECTION
# ============================================================
if page == "Image Detection":
    st.header("🖼️ Image Fake-Media Detection")
    st.write("Upload a JPG, JPEG, PNG, or WEBP image for analysis.")

    image_file = st.file_uploader(
        "Choose an image",
        type=["jpg", "jpeg", "png", "webp"],
        key="image_upload",
    )

    if image_file is not None:
        run_image_analysis(image_file)


# ============================================================
# VIDEO DETECTION
# ============================================================
elif page == "Video Detection":
    st.header("🎬 Video Fake-Media Detection")
    st.write("Upload an MP4, AVI, or MOV video for frame-based analysis.")

    video_file = st.file_uploader(
        "Choose a video",
        type=["mp4", "avi", "mov"],
        key="video_upload",
    )

    if video_file is not None:
        max_size_mb = 200
        if video_file.size > max_size_mb * 1024 * 1024:
            st.error(f"Video exceeds the {max_size_mb} MB upload limit.")
        else:
            run_video_analysis(video_file)


# ============================================================
# MULTIMODAL FUSION
# ============================================================
elif page == "Multimodal Fusion":
    st.header("🔗 Multimodal Analysis")
    st.write(
        "Analyze an image and a video together. The fusion module combines "
        "the results returned by your image and video prediction modules."
    )

    fusion_image = st.file_uploader(
        "Upload image",
        type=["jpg", "jpeg", "png", "webp"],
        key="fusion_image",
    )

    fusion_video = st.file_uploader(
        "Upload video",
        type=["mp4", "avi", "mov"],
        key="fusion_video",
    )

    if st.button("🧠 Run Multimodal Fusion", type="primary"):
        if fusion_image is None or fusion_video is None:
            st.warning("Please upload both an image and a video.")
        else:
            image_temp = None
            video_temp = None

            try:
                with st.spinner("Analyzing both media files..."):
                    image_temp = save_uploaded_temp(fusion_image)
                    video_temp = save_uploaded_temp(fusion_video)

                    image_result = predict_image(image_temp)
                    video_result = analyze_video(video_temp)

                    fusion_result = multimodal_fusion(
                        image_result,
                        video_result,
                    )

                st.subheader("Fusion Result")
                st.json(fusion_result)

                fusion_record = {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "filename": f"{fusion_image.name} + {fusion_video.name}",
                    "media_type": "multimodal",
                    "sha256": hashlib.sha256(
                        fusion_image.getvalue() + fusion_video.getvalue()
                    ).hexdigest(),
                    "image_result": image_result,
                    "video_result": video_result,
                    "fusion_result": fusion_result,
                }

                try:
                    save_analysis(fusion_record)
                    st.success("Multimodal analysis saved to history.")
                except Exception as exc:
                    st.warning(f"Could not save fusion history: {exc}")

            except Exception as exc:
                st.error(f"Multimodal analysis failed: {exc}")

            finally:
                cleanup_temp(image_temp)
                cleanup_temp(video_temp)


# ============================================================
# ANALYSIS HISTORY
# ============================================================
elif page == "Analysis History":
    st.header("📚 Analysis History")
    st.write("View previous analyses stored in your local database.")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.caption("History is loaded from your existing database module.")

    with col2:
        confirm_clear = st.checkbox("Confirm clearing history")

        if st.button("🗑️ Clear History"):
            if confirm_clear:
                try:
                    clear_analysis_history()
                    st.success("Analysis history cleared.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not clear history: {exc}")
            else:
                st.warning("Tick the confirmation box first.")

    try:
        history = get_analysis_history()

        if history is None:
            st.info("No history was returned.")
        elif hasattr(history, "empty") and history.empty:
            st.info("No analysis records yet.")
        elif isinstance(history, (list, tuple)) and len(history) == 0:
            st.info("No analysis records yet.")
        elif hasattr(history, "to_dict"):
            st.dataframe(history, use_container_width=True)
        elif isinstance(history, (list, tuple)):
            st.dataframe(list(history), use_container_width=True)
        else:
            st.write(history)

    except Exception as exc:
        st.error(f"Could not load analysis history: {exc}")


# ============================================================
# ABOUT
# ============================================================
elif page == "About Project":
    st.header("ℹ️ About RealCheck AI")

    st.markdown("""
    **RealCheck AI** is a multimodal fake-media detection project designed
    to help users inspect potentially AI-generated or manipulated media.

    ### Main modules
    - Image classification
    - Video frame analysis
    - Multimodal result fusion
    - Grad-CAM visual explanation
    - Confidence scoring
    - SHA-256 evidence records
    - PDF report generation
    - Local analysis history

    ### Important limitation
    A model prediction is not definitive proof that a file is real or fake.
    Results can be wrong, particularly for unfamiliar generators, heavily
    compressed files, edited media, and inputs unlike the training data.
    """)


# ============================================================
# FOOTER
# ============================================================
st.html("""
<div class="rc-footer">
    RealCheck AI · Multimodal Fake Media Detection System
    <br>
    AI predictions are estimates and should be verified independently.
</div>
""")
