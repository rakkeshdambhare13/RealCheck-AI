import hashlib
import logging
import os
import re
import tempfile
import time

import pandas as pd
import streamlit as st
from PIL import Image

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
from src.background import render_3d_background
from src.theme import apply_advanced_theme
from src.ui_effects import apply_ui_effects
from src.main_fx import (
    render_main_toggle,
    render_main_background,
    render_title_fx,
    show_verdict
)
from src.auth_fx import (
    render_fx_toggle,
    render_fx_background,
    queue_fx,
    pop_fx,
    announce,
    FX_SECONDS
)

from src.auth import (
    init_auth_db,
    register_user,
    authenticate,
    save_user_analysis,
    get_user_history,
    clear_user_history
)

log = logging.getLogger("realcheck")


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
# INITIALIZE ACCOUNTS DATABASE
# ==================================================

init_auth_db()


# ==================================================
# CUSTOM UI (base styles; theme.py and ui_effects.py layer on top)
# ==================================================

st.html(
    """
    <style>

    /* ---------- GLOBAL BACKGROUND ---------- */

    .stApp {
        background:
            radial-gradient(circle at 15% 15%, rgba(0, 220, 255, 0.13), transparent 28%),
            radial-gradient(circle at 85% 25%, rgba(120, 0, 255, 0.12), transparent 30%),
            radial-gradient(circle at 50% 90%, rgba(0, 255, 170, 0.08), transparent 28%),
            #050816;
        color: #f5f7ff;
        overflow-x: hidden;
    }

    /* ---------- FLOATING AURA ---------- */

    .stApp::after {
        content: "";
        position: fixed;
        width: 450px;
        height: 450px;
        left: 50%;
        top: 35%;
        transform: translate(-50%, -50%);
        background: radial-gradient(circle, rgba(0, 220, 255, 0.10), transparent 65%);
        filter: blur(20px);
        animation: auraMove 9s ease-in-out infinite alternate;
        pointer-events: none;
        z-index: 0;
    }

    @keyframes auraMove {
        0%   { transform: translate(-55%, -45%) scale(0.9); }
        50%  { transform: translate(-35%, -55%) scale(1.2); }
        100% { transform: translate(-65%, -35%) scale(1); }
    }

    /* ---------- MAIN CONTENT ---------- */

    .block-container {
        position: relative;
        z-index: 2;
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }

    /* ---------- HEADER ---------- */

    .rc-header { text-align: center; padding: 25px 10px 20px; }

    .rc-icon {
        display: inline-flex;
        width: 150px;
        height: 150px;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-size: 80px;
        background: radial-gradient(circle at 35% 30%, rgba(255,255,255,0.25), rgba(0,220,255,0.10));
        border: 1px solid rgba(255,255,255,0.20);
        box-shadow: 0 0 25px rgba(0,220,255,0.35), inset 0 0 30px rgba(255,255,255,0.05);
        animation: iconFloat 4s ease-in-out infinite, iconGlow 3s ease-in-out infinite alternate;
    }

    @keyframes iconFloat {
        0%, 100% { transform: translateY(0) rotateY(0deg); }
        50%      { transform: translateY(-12px) rotateY(15deg); }
    }

    @keyframes iconGlow {
        from { box-shadow: 0 0 20px rgba(0,220,255,0.25), inset 0 0 20px rgba(255,255,255,0.04); }
        to   { box-shadow: 0 0 45px rgba(0,220,255,0.60), inset 0 0 30px rgba(255,255,255,0.08); }
    }

    .rc-title {
        margin-top: 20px;
        font-size: clamp(42px, 7vw, 82px);
        font-weight: 900;
        letter-spacing: 5px;
        background: linear-gradient(90deg, #00eaff, #ffffff, #9b5cff, #00eaff);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: titleGradient 5s linear infinite;
    }

    @keyframes titleGradient {
        0%   { background-position: 0% 50%; }
        100% { background-position: 300% 50%; }
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
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.10);
        backdrop-filter: blur(16px);
        color: #cbd3ea;
        line-height: 1.7;
    }

    /* ---------- GLASS CARDS ---------- */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 22px;
        backdrop-filter: blur(18px);
        box-shadow: 0 15px 50px rgba(0,0,0,0.20);
    }

    /* ---------- RADIO ---------- */

    div[role="radiogroup"] {
        background: rgba(255,255,255,0.035);
        padding: 10px;
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.10);
        backdrop-filter: blur(15px);
    }

    /* ---------- UPLOADER ---------- */

    section[data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.045);
        border: 1px dashed rgba(0,220,255,0.45);
        border-radius: 20px;
        transition: all 0.3s ease;
    }

    section[data-testid="stFileUploaderDropzone"]:hover {
        transform: translateY(-3px);
        border-color: rgba(0,230,255,0.85);
        box-shadow: 0 0 30px rgba(0,220,255,0.18);
    }

    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 14px;
        border: 1px solid rgba(0,220,255,0.30);
        background: linear-gradient(135deg, rgba(0,220,255,0.15), rgba(120,0,255,0.15));
        color: white;
        font-weight: 700;
        transition: all 0.25s ease;
        min-height: 45px;
    }

    .stButton > button:hover {
        transform: translateY(-3px) scale(1.01);
        border-color: rgba(0,230,255,0.80);
        box-shadow: 0 10px 30px rgba(0,220,255,0.20);
    }

    /* ---------- METRICS ---------- */

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 16px;
        transition: transform 0.25s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px) perspective(500px) rotateX(2deg) rotateY(-2deg);
    }

    /* ---------- DATAFRAME ---------- */

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
    }

    /* ---------- FOOTER ---------- */

    .rc-footer {
        text-align: center;
        margin-top: 60px;
        padding: 30px 20px;
        color: #78829d;
        border-top: 1px solid rgba(255,255,255,0.08);
        font-size: 13px;
    }

    .rc-contact {
        margin: 20px auto;
        padding: 18px 25px;
        max-width: 520px;
        border-radius: 18px;
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(0,220,255,0.15);
        backdrop-filter: blur(14px);
        box-shadow: 0 10px 35px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }

    .rc-contact:hover {
        transform: translateY(-3px);
        border-color: rgba(0,220,255,0.45);
        box-shadow: 0 0 30px rgba(0,220,255,0.12);
    }

    .rc-contact-title { color: #00eaff; font-size: 16px; font-weight: 700; margin-bottom: 12px; }
    .rc-contact-item { margin: 8px 0; color: #cbd3ea; font-size: 14px; }
    .rc-contact-item a { color: #cbd3ea; text-decoration: none; transition: color 0.25s ease; }
    .rc-contact-item a:hover { color: #00eaff; }

    /* ---------- MOBILE ---------- */

    @media (max-width: 700px) {
        .rc-title { font-size: 42px; letter-spacing: 2px; }
        .rc-subtitle { font-size: 11px; letter-spacing: 2px; }
        .rc-icon { width: 85px; height: 85px; font-size: 42px; }
        .block-container { padding-left: 15px; padding-right: 15px; }
        .rc-contact { margin-left: 10px; margin-right: 10px; }
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
# 3D ANIMATED BACKGROUND
# ==================================================

render_3d_background()
apply_advanced_theme()
apply_ui_effects()


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def md_escape(text):
    """Stop user-supplied text (names, file names) from being read as markdown."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~$])", r"\\\1", str(text))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_key(uploaded_file):
    """Identity of an upload, used to hide results that belong to a different file."""
    return (uploaded_file.name, uploaded_file.size)


def write_temp(uploaded_file, default_ext):
    """Write the ORIGINAL uploaded bytes to a temp file (so hashes match the real file)."""
    ext = os.path.splitext(uploaded_file.name)[1] or default_ext

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=ext
    ) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name


def remove_temp(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def show_error(message, exc):
    """Log the real exception, show the user a short friendly message."""
    log.exception(message)

    st.error(
        f"{message}. Please try another file or try again "
        f"({type(exc).__name__})."
    )


def show_table(data):
    try:
        st.dataframe(data, width="stretch", hide_index=True)
    except Exception:
        st.dataframe(data, use_container_width=True, hide_index=True)


def pct_weight(value, default):
    """Accept 0.4 or 40 and return a percentage string such as 40%."""
    try:
        w = float(value)
    except (TypeError, ValueError):
        w = default

    if w <= 1:
        w *= 100

    return f"{w:.0f}%"


def save_to_history(
    evidence,
    analysis_type,
    prediction,
    confidence,
    uncertainty
):

    save_user_analysis(
        user_id=st.session_state["user"]["id"],
        evidence_id=evidence["evidence_id"],
        file_name=evidence["file_name"],
        file_type=evidence["file_type"],
        analysis_type=analysis_type,
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


def normalize_image_result(result):
    """predict_image may return a dict or a tuple; return one shape."""

    if isinstance(result, dict):

        prediction = result["prediction"]
        confidence = float(result["confidence"]) * 100
        fake_score = float(result["fake_score"]) * 100
        real_score = float(result["real_score"]) * 100
        class_id = result["class_id"]

    else:

        prediction = result[0]
        confidence = float(result[1])
        class_id = result[2]
        fake_score = get_fake_score(prediction, confidence)
        real_score = 100.0 - fake_score

    return prediction, confidence, fake_score, real_score, class_id


def make_gradcam(image, class_id):
    """Returns (image, error_message); never raises."""

    try:
        model = load_model()

        return create_gradcam_image(
            model,
            image,
            transform,
            class_id,
            device
        ), None

    except Exception as e:
        log.exception("Grad-CAM generation failed")
        return None, f"{type(e).__name__}: {e}"


def display_evidence(evidence, title="🔐 Digital Evidence"):

    st.divider()

    if title:
        st.subheader(title)

    col1, col2 = st.columns(2)

    with col1:

        st.write(f"**Evidence ID:** {evidence['evidence_id']}")
        st.write(f"**File Name:** {md_escape(evidence['file_name'])}")
        st.write(f"**File Type:** {evidence['file_type']}")
        st.write(f"**File Size:** {evidence['file_size']}")

    with col2:

        st.write(f"**Analysis Time:** {evidence['analysis_time']}")
        st.write(f"**Result:** {evidence['result']}")
        st.write(f"**Confidence:** {float(evidence['confidence']):.2f}%")

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


def show_gradcam(gradcam, gradcam_error, caption, note):

    if gradcam is not None:

        st.image(
            gradcam,
            caption=caption,
            width=650
        )

        st.info(note)

    elif gradcam_error:

        st.error(
            f"Grad-CAM generation failed: {gradcam_error}"
        )


def show_frame_stats(result):

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Frames Analyzed", result["analyzed_frames"])

    with col2:
        st.metric("Fake Frames", result["fake_frames"])

    with col3:
        st.metric("Real Frames", result["real_frames"])

    st.write(
        f'**Fake Frame Ratio:** '
        f'{result["fake_ratio"]:.2f}%'
    )


def show_suspicious_frames(result, empty_message):

    suspicious = result["suspicious_frames"]

    if len(suspicious) > 0:

        for item in suspicious[:20]:

            st.write(
                f'🔴 Frame {item["frame"]} | '
                f'Time: {item["time"]:.2f}s | '
                f'Fake probability: '
                f'{item["fake_probability"]:.2f}%'
            )

    else:

        st.success(empty_message)


def render_footer():

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


# ==================================================
# LOGIN / REGISTRATION
# ==================================================

WORK_KEYS = (
    "res_image",
    "res_video",
    "res_fusion",
    "confirm_clear",
    "flash"
)


def start_session(user):
    """Sign a user in with a clean slate (no leftovers from anyone else)."""

    for key in WORK_KEYS:
        st.session_state.pop(key, None)

    st.session_state["user"] = user

    st.rerun()


def logout():
    """Forget the user and everything they analyzed in this session."""

    st.session_state.clear()

    st.rerun()


def show_problems(problems):

    st.error(
        "**Please fix the following:**\n\n"
        + "\n".join(f"- {p}" for p in problems)
    )


def render_auth_gate():

    # after a new account is created: go back to the Sign In tab, email pre-filled
    if st.session_state.pop("_to_login", False):
        st.session_state["auth_mode"] = "🔑 Sign In"
        st.session_state["login_email"] = st.session_state.pop("_new_email", "")

    st.markdown("## 🔐 Secure Access")

    st.write(
        "Sign in to your RealCheck AI account or create one. "
        "Every account keeps its own private analysis history."
    )

    # Enable / Disable switch (visible on the login AND registration views)
    fx_on = render_fx_toggle()

    # Zoom-out / fade-out background text. Emitted ONLY on this page, and
    # only while the switch is on; it sits behind the form and ignores clicks.
    if fx_on:
        render_fx_background()

    mode = st.radio(
        "Account",
        ["🔑 Sign In", "📝 Create Account"],
        horizontal=True,
        label_visibility="collapsed",
        key="auth_mode"
    )

    # One top-level slot for the event message (fixed-position overlay).
    message_slot = st.empty()

    # an event queued by the previous run (account created) shows once, now
    pending_fx = pop_fx()

    if pending_fx:

        with message_slot.container():
            announce(pending_fx, fx_on)

    _, centre, _ = st.columns([1, 2, 1])

    with centre:

        if mode == "🔑 Sign In":

            with st.form("login_form"):

                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    key="login_email"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password"
                )

                submitted = st.form_submit_button(
                    "Sign In",
                    type="primary"
                )

            if submitted:

                user, error = authenticate(email, password)

                if user:

                    with message_slot.container():
                        announce("login_ok", fx_on)

                    time.sleep(FX_SECONDS if fx_on else 1.0)

                    start_session(user)

                else:

                    with message_slot.container():
                        announce("login_fail", fx_on)

                    st.error(error)

        else:

            with st.form("register_form"):

                name = st.text_input(
                    "Full name",
                    key="reg_name"
                )

                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    key="reg_email"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    key="reg_password"
                )

                confirm = st.text_input(
                    "Confirm password",
                    type="password",
                    key="reg_confirm"
                )

                st.caption(
                    "At least 8 characters with an uppercase letter, "
                    "a lowercase letter and a number."
                )

                submitted = st.form_submit_button(
                    "Create Account",
                    type="primary"
                )

            if submitted:

                user, problems = register_user(
                    name,
                    email,
                    password,
                    confirm
                )

                if user:
                    queue_fx("account_created")
                    st.session_state["_to_login"] = True
                    st.session_state["_new_email"] = user["email"]
                    st.rerun()
                else:
                    show_problems(problems)

        st.caption(
            "Passwords are never stored. Only a salted "
            "PBKDF2 hash is kept."
        )


# ==================================================
# ACCESS CONTROL: nothing below runs unless a user is signed in
# ==================================================

if "user" not in st.session_state:

    render_auth_gate()
    render_footer()
    st.stop()

USER = st.session_state["user"]

bar_left, bar_right = st.columns([5, 1])

with bar_left:

    st.write(
        f"👤 **{md_escape(USER['name'])}** · "
        f"{md_escape(USER['email'])}"
    )

with bar_right:

    if st.button("🚪 Sign Out", key="logout"):
        logout()


# ==================================================
# ANALYSIS MODE
# ==================================================

media_type = st.radio(
    "Analysis Mode",
    [
        "🖼️ Image",
        "🎥 Video",
        "🔗 Multimodal Fusion",
        "🔐 Verify Evidence"
    ],
    horizontal=True,
    label_visibility="collapsed"
)


# ==================================================
# MAIN PAGE BACKGROUND ANIMATION  (runs only after login)
# ==================================================

main_fx_on = render_main_toggle()

# one slot: shows the plain background now, and is refilled with the
# REAL / FAKE verdict only after a prediction has finished
fx_slot = st.empty()

if main_fx_on:

    render_title_fx()

    with fx_slot.container():
        render_main_background()


# ==================================================
# IMAGE ANALYSIS
# ==================================================

def analyze_single_image(uploaded_image, image):
    """Run everything once and return a result dict that survives reruns."""

    temp_path = None

    try:

        temp_path = write_temp(uploaded_image, ".png")

        with st.spinner("AI is analyzing the image..."):
            result = predict_image(image)

        (
            prediction,
            confidence,
            fake_score,
            real_score,
            class_id
        ) = normalize_image_result(result)

        uncertainty = max(0.0, 100.0 - confidence)
        reliability = get_reliability(confidence)

        evidence = create_evidence_record(
            file_path=temp_path,
            file_name=uploaded_image.name,
            result=prediction,
            confidence=confidence
        )

        save_to_history(
            evidence,
            "Image Analysis",
            prediction,
            confidence,
            uncertainty
        )

        pdf = create_pdf_report(
            evidence_records=[evidence],
            final_result=prediction,
            final_confidence=confidence,
            uncertainty=uncertainty,
            reliability=reliability,
            evidence_strength="MODERATE",
            model_agreement="N/A"
        )

        with st.spinner("Generating AI explanation..."):
            gradcam, gradcam_error = make_gradcam(image, class_id)

        return {
            "key": file_key(uploaded_image),
            "prediction": prediction,
            "confidence": confidence,
            "fake_score": fake_score,
            "real_score": real_score,
            "evidence": evidence,
            "pdf": pdf,
            "gradcam": gradcam,
            "gradcam_error": gradcam_error
        }

    finally:
        remove_temp(temp_path)


def render_image_result(res):

    st.divider()

    st.subheader("🎯 Analysis Result")

    if res["prediction"] == "FAKE":

        st.error("🔴 AI-GENERATED / FAKE")

        st.metric("Confidence", f"{res['confidence']:.2f}%")

        st.warning(
            "The AI model detected patterns "
            "associated with AI-generated or "
            "manipulated images."
        )

    else:

        st.success("🟢 LIKELY REAL")

        st.metric("Confidence", f"{res['confidence']:.2f}%")

        st.info(
            "The AI model found the image more "
            "consistent with real images."
        )

    st.subheader("📊 Prediction Scores")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("🔴 Fake Score", f"{res['fake_score']:.2f}%")

    with col2:
        st.metric("🟢 Real Score", f"{res['real_score']:.2f}%")

    display_evidence(res["evidence"])

    st.success("✅ Analysis saved to history.")

    st.divider()

    st.subheader("📄 Forensic Report")

    st.download_button(
        label="📄 Download Forensic PDF Report",
        data=res["pdf"],
        file_name=(
            f"RealCheck_AI_Report_"
            f"{res['evidence']['evidence_id']}.pdf"
        ),
        mime="application/pdf",
        key="dl_image_pdf"
    )

    st.divider()

    st.subheader("🔍 Explainable AI — Grad-CAM")

    st.write(
        "The heatmap highlights image regions "
        "that influenced the AI model's prediction."
    )

    show_gradcam(
        res["gradcam"],
        res["gradcam_error"],
        "Grad-CAM: Important Regions Influencing the Prediction",
        "Grad-CAM shows regions that influenced the model's "
        "decision. It does not prove that a highlighted "
        "region is fake."
    )


if media_type == "🖼️ Image":

    st.markdown("## 🖼️ Image Forensics")

    st.write(
        "Upload an image to determine whether it is "
        "likely real or AI-generated."
    )

    uploaded_image = st.file_uploader(
        "Upload Image",
        type=["jpg", "jpeg", "png"],
        key="image_upload"
    )

    if uploaded_image is not None:

        image = Image.open(uploaded_image).convert("RGB")

        st.image(
            image,
            caption="Uploaded Image",
            width=600
        )

        if st.button(
            "🔎 Start Image Analysis",
            key="start_image_analysis"
        ):

            try:

                st.session_state["res_image"] = analyze_single_image(
                    uploaded_image,
                    image
                )

            except Exception as e:

                st.session_state.pop("res_image", None)
                show_error("Image analysis failed", e)

        res = st.session_state.get("res_image")

        if res and res["key"] == file_key(uploaded_image):
            render_image_result(res)

            # verdict comes from the stored predict_image() output
            show_verdict(
                fx_slot,
                main_fx_on,
                "IMAGE",
                res["prediction"] == "FAKE"
            )


# ==================================================
# VIDEO ANALYSIS
# ==================================================

def analyze_single_video(uploaded_video):

    video_path = None

    try:

        video_path = write_temp(uploaded_video, ".mp4")

        with st.spinner("AI is analyzing video frames..."):
            result = analyze_video(
                video_path,
                frame_interval=15
            )

        label = result["result"]
        confidence = float(result["confidence"])
        uncertainty = max(0.0, 100.0 - confidence)
        reliability = get_reliability(confidence)
        fake_score = get_fake_score(label, confidence)

        evidence = create_evidence_record(
            file_path=video_path,
            file_name=uploaded_video.name,
            result=label,
            confidence=result["confidence"]
        )

        save_to_history(
            evidence,
            "Video Analysis",
            label,
            confidence,
            uncertainty
        )

        pdf = create_pdf_report(
            evidence_records=[evidence],
            final_result=label,
            final_confidence=confidence,
            uncertainty=uncertainty,
            reliability=reliability,
            evidence_strength="MODERATE",
            model_agreement="N/A",
            video_fake_score=fake_score,
            video_result=result
        )

        return {
            "key": file_key(uploaded_video),
            "result": result,
            "evidence": evidence,
            "pdf": pdf
        }

    finally:
        remove_temp(video_path)


def render_video_result(res):

    result = res["result"]

    st.divider()

    st.subheader("🎯 Video Analysis Result")

    if result["result"] == "FAKE":
        st.error("🔴 VIDEO LIKELY AI-GENERATED")
    else:
        st.success("🟢 VIDEO LIKELY REAL")

    st.metric("Confidence", f'{result["confidence"]:.2f}%')

    st.subheader("🎞️ Frame Analysis")

    show_frame_stats(result)

    display_evidence(res["evidence"])

    st.success("✅ Video analysis saved to history.")

    st.divider()

    st.subheader("📄 Forensic Report")

    st.download_button(
        label="📄 Download Video Forensic PDF Report",
        data=res["pdf"],
        file_name=(
            f"RealCheck_AI_Video_Report_"
            f"{res['evidence']['evidence_id']}.pdf"
        ),
        mime="application/pdf",
        key="dl_video_pdf"
    )

    st.divider()

    st.subheader("⚠️ Suspicious Frames")

    show_suspicious_frames(
        result,
        "No highly suspicious frames detected."
    )


if media_type == "🎥 Video":

    st.markdown("## 🎥 Video Forensics")

    st.write(
        "Upload a video and RealCheck AI will analyze "
        "sampled frames for suspicious AI-generated patterns."
    )

    uploaded_video = st.file_uploader(
        "Upload Video",
        type=["mp4", "avi", "mov"],
        key="video_upload"
    )

    if uploaded_video is not None:

        st.video(uploaded_video)

        if st.button(
            "🔎 Start Video Analysis",
            key="start_video_analysis"
        ):

            try:

                st.session_state["res_video"] = analyze_single_video(
                    uploaded_video
                )

            except Exception as e:

                st.session_state.pop("res_video", None)
                show_error("Video analysis failed", e)

        res = st.session_state.get("res_video")

        if res and res["key"] == file_key(uploaded_video):
            render_video_result(res)

            # verdict comes from the stored analyze_video() output
            show_verdict(
                fx_slot,
                main_fx_on,
                "VIDEO",
                res["result"]["result"] == "FAKE"
            )


# ==================================================
# MULTIMODAL FUSION
# ==================================================

def analyze_fusion(fusion_image_file, fusion_image, fusion_video_file):

    image_path = None
    video_path = None

    try:

        image_path = write_temp(fusion_image_file, ".jpg")

        with st.spinner("Analyzing image..."):
            image_result = predict_image(fusion_image)

        (
            image_label,
            image_confidence,
            _,
            _,
            image_class_id
        ) = normalize_image_result(image_result)

        image_fake_score = get_fake_score(
            image_label,
            image_confidence
        )

        video_path = write_temp(fusion_video_file, ".mp4")

        with st.spinner("Analyzing video frames..."):
            video_result = analyze_video(
                video_path,
                frame_interval=15
            )

        video_fake_score = get_fake_score(
            video_result["result"],
            video_result["confidence"]
        )

        with st.spinner("Combining image and video evidence..."):

            fusion_result = multimodal_fusion(
                image_fake_score=image_fake_score,
                video_fake_score=video_fake_score
            )

        confidence_result = calculate_confidence(
            fake_score=fusion_result["fake_score"],
            image_fake_score=image_fake_score,
            video_fake_score=video_fake_score
        )

        final_result = confidence_result["result"]
        final_confidence = confidence_result["confidence"]
        uncertainty = confidence_result["uncertainty"]
        reliability = confidence_result["reliability"]
        evidence_strength = confidence_result["evidence_strength"]
        model_agreement = confidence_result["model_agreement"]

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

        save_to_history(
            image_evidence,
            "Multimodal Image",
            image_label,
            image_confidence,
            100.0 - float(image_confidence)
        )

        save_to_history(
            video_evidence,
            "Multimodal Fusion",
            final_result,
            final_confidence,
            uncertainty
        )

        pdf = create_pdf_report(
            evidence_records=[image_evidence, video_evidence],
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

        with st.spinner("Generating AI explanation..."):
            gradcam, gradcam_error = make_gradcam(
                fusion_image,
                image_class_id
            )

        return {
            "key": (
                file_key(fusion_image_file),
                file_key(fusion_video_file)
            ),
            "image_fake_score": image_fake_score,
            "video_fake_score": video_fake_score,
            "video_result": video_result,
            "final_result": final_result,
            "final_confidence": final_confidence,
            "uncertainty": uncertainty,
            "reliability": reliability,
            "evidence_strength": evidence_strength,
            "model_agreement": model_agreement,
            "image_weight": pct_weight(
                fusion_result.get("image_weight"), 0.4
            ),
            "video_weight": pct_weight(
                fusion_result.get("video_weight"), 0.6
            ),
            "image_evidence": image_evidence,
            "video_evidence": video_evidence,
            "pdf": pdf,
            "gradcam": gradcam,
            "gradcam_error": gradcam_error
        }

    finally:
        remove_temp(image_path)
        remove_temp(video_path)


def render_fusion_result(res):

    st.divider()

    st.subheader("🧠 Multimodal Fusion Result")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("🖼️ Image Fake Score", f"{res['image_fake_score']:.2f}%")

    with col2:
        st.metric("🎥 Video Fake Score", f"{res['video_fake_score']:.2f}%")

    if res["final_result"] == "FAKE":

        st.error("🔴 AI-GENERATED / FAKE")

        st.metric("Final Confidence", f"{res['final_confidence']:.2f}%")

        st.warning(
            "Multimodal analysis detected patterns "
            "associated with AI-generated or "
            "manipulated media."
        )

    else:

        st.success("🟢 LIKELY REAL")

        st.metric("Final Confidence", f"{res['final_confidence']:.2f}%")

        st.info(
            "Multimodal analysis found the provided media "
            "more consistent with real content."
        )

    st.divider()

    st.subheader("📊 Confidence & Reliability Analysis")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Confidence", f"{res['final_confidence']:.2f}%")

    with col2:
        st.metric("Uncertainty", f"{res['uncertainty']:.2f}%")

    with col3:
        st.metric("Reliability", res["reliability"])

    with col4:
        st.metric("Evidence Strength", res["evidence_strength"])

    if res["model_agreement"] == "AGREE":

        st.success(
            "✓ Image and video models agree "
            "on the overall prediction."
        )

    elif res["model_agreement"] == "DISAGREE":

        st.warning(
            "⚠️ Image and video models disagree. "
            "The prediction should be interpreted "
            "cautiously."
        )

    st.write(f"**Uncertainty Level:** {res['uncertainty']:.2f}%")

    st.progress(
        min(max(int(res["uncertainty"]), 0), 100)
    )

    st.info(
        "⚠️ RealCheck AI provides an AI-assisted "
        "assessment. The result should not be treated "
        "as absolute proof of authenticity or manipulation."
    )

    st.subheader("📊 Fusion Analysis")

    st.write(f"Image contribution: **{res['image_weight']}**")
    st.write(f"Video contribution: **{res['video_weight']}**")

    st.subheader("🎥 Video Evidence")

    show_frame_stats(res["video_result"])

    st.subheader("⚠️ Suspicious Video Frames")

    show_suspicious_frames(
        res["video_result"],
        "No highly suspicious video frames detected."
    )

    st.divider()

    st.subheader("🔐 Digital Evidence")

    st.markdown("### 🖼️ Image Evidence")

    display_evidence(res["image_evidence"], title="")

    st.markdown("### 🎥 Video Evidence")

    display_evidence(res["video_evidence"], title="")

    st.success("✅ Multimodal analysis saved to history.")

    st.divider()

    st.subheader("📄 Forensic Report")

    st.download_button(
        label="📄 Download Multimodal Forensic PDF Report",
        data=res["pdf"],
        file_name=(
            f"RealCheck_AI_Multimodal_Report_"
            f"{res['image_evidence']['evidence_id']}.pdf"
        ),
        mime="application/pdf",
        key="dl_fusion_pdf"
    )

    st.divider()

    st.subheader("🔍 Explainable AI — Image Grad-CAM")

    show_gradcam(
        res["gradcam"],
        res["gradcam_error"],
        "Grad-CAM: Important Regions Influencing Image Prediction",
        "Grad-CAM highlights regions that influenced the image "
        "model's decision. It does not prove that a highlighted "
        "region is fake."
    )


if media_type == "🔗 Multimodal Fusion":

    st.markdown("## 🔗 Multimodal Image + Video Analysis")

    st.write(
        "Upload both an image and a video. "
        "RealCheck AI analyzes both modalities and "
        "combines their evidence into a final prediction."
    )

    fusion_image_file = st.file_uploader(
        "🖼️ Upload Image",
        type=["jpg", "jpeg", "png"],
        key="fusion_image"
    )

    fusion_video_file = st.file_uploader(
        "🎥 Upload Video",
        type=["mp4", "avi", "mov"],
        key="fusion_video"
    )

    fusion_image = None

    if fusion_image_file is not None:

        fusion_image = Image.open(fusion_image_file).convert("RGB")

        st.image(
            fusion_image,
            caption="Fusion Image",
            width=500
        )

    if fusion_video_file is not None:
        st.video(fusion_video_file)

    if (
        fusion_image_file is not None
        and fusion_video_file is not None
    ):

        if st.button(
            "🚀 Start Multimodal Analysis",
            key="start_fusion_analysis"
        ):

            try:

                st.session_state["res_fusion"] = analyze_fusion(
                    fusion_image_file,
                    fusion_image,
                    fusion_video_file
                )

            except Exception as e:

                st.session_state.pop("res_fusion", None)
                show_error("Multimodal analysis failed", e)

        res = st.session_state.get("res_fusion")

        if res and res["key"] == (
            file_key(fusion_image_file),
            file_key(fusion_video_file)
        ):
            render_fusion_result(res)

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
# VERIFY EVIDENCE  (new)
# ==================================================

if media_type == "🔐 Verify Evidence":

    st.markdown("## 🔐 Evidence Verification")

    st.write(
        "Upload a file to check whether it is byte-for-byte "
        "identical to a file RealCheck AI analyzed before. "
        "The file's SHA-256 fingerprint is compared with "
        "every record in your analysis history."
    )

    verify_file = st.file_uploader(
        "Upload File to Verify",
        type=["jpg", "jpeg", "png", "mp4", "avi", "mov"],
        key="verify_upload"
    )

    if verify_file is not None:

        digest = sha256_bytes(verify_file.getvalue())

        st.write("**SHA-256 of the uploaded file:**")

        st.code(digest, language="text")

        matches = [
            row for row in get_user_history(USER["id"])
            if row["sha256"] == digest
        ]

        if matches:

            st.success(
                f"✅ VERIFIED: this file matches "
                f"{len(matches)} recorded analysis "
                f"{'entry' if len(matches) == 1 else 'entries'}. "
                f"It has not been altered since it was analyzed."
            )

            show_table([
                {
                    "Evidence ID": row["evidence_id"],
                    "File Name": row["file_name"],
                    "Analysis Type": row["analysis_type"],
                    "Result": row["result"],
                    "Confidence": f'{float(row["confidence"]):.2f}%',
                    "Analysis Time": row["analysis_time"]
                }
                for row in matches
            ])

        else:

            st.warning(
                "⚠️ NO MATCH: no record with this fingerprint exists. "
                "Either the file was never analyzed here, or it has "
                "changed (even one byte) since it was analyzed."
            )

            st.caption(
                "Records created before this version were hashed from "
                "a re-saved copy of images and will not match the "
                "original upload."
            )


# ==================================================
# ANALYSIS HISTORY
# ==================================================

st.divider()

st.markdown("## 📚 Analysis History")

flash = st.session_state.pop("flash", None)

if flash:
    st.success(flash)

history = get_user_history(USER["id"])

if history:

    rows = []

    for position, row in enumerate(history):

        rows.append(
            {
                "ID": len(history) - position,
                "Evidence ID": row["evidence_id"],
                "File Name": row["file_name"],
                "File Type": row["file_type"],
                "Analysis Type": row["analysis_type"],
                "Result": row["result"],
                "Confidence": f'{float(row["confidence"]):.2f}%',
                "Uncertainty": f'{float(row["uncertainty"]):.2f}%',
                "SHA-256": row["sha256"],
                "Analysis Time": row["analysis_time"],
                "_conf": float(row["confidence"])
            }
        )

    df = pd.DataFrame(rows)

    # ---- summary ----

    total = len(df)
    fake_count = int((df["Result"] == "FAKE").sum())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Analyses", total)

    with col2:
        st.metric("Flagged Fake", fake_count)

    with col3:
        st.metric("Not Flagged", total - fake_count)

    with col4:
        st.metric("Avg Confidence", f'{df["_conf"].mean():.1f}%')

    # ---- search + filters ----

    f1, f2, f3 = st.columns([2, 1, 1])

    with f1:
        query = st.text_input(
            "Search history",
            placeholder="🔎 Search file name or evidence ID",
            label_visibility="collapsed",
            key="hist_query"
        )

    with f2:
        type_filter = st.selectbox(
            "Analysis type",
            ["All types"] + sorted(df["Analysis Type"].unique()),
            label_visibility="collapsed",
            key="hist_type"
        )

    with f3:
        result_filter = st.selectbox(
            "Result",
            ["All results"] + sorted(df["Result"].astype(str).unique()),
            label_visibility="collapsed",
            key="hist_result"
        )

    view = df

    if query:

        q = query.strip()

        view = view[
            view["File Name"].astype(str).str.contains(q, case=False, regex=False, na=False)
            | view["Evidence ID"].astype(str).str.contains(q, case=False, regex=False, na=False)
        ]

    if type_filter != "All types":
        view = view[view["Analysis Type"] == type_filter]

    if result_filter != "All results":
        view = view[view["Result"].astype(str) == result_filter]

    shown = view.drop(columns=["_conf"])

    show_table(shown)

    st.caption(
        f"Showing {len(shown)} of {total} recorded analyses"
    )

    st.download_button(
        label="⬇️ Download History (CSV)",
        data=shown.to_csv(index=False).encode("utf-8"),
        file_name="RealCheck_AI_History.csv",
        mime="text/csv",
        key="dl_history_csv"
    )

    # ---- clear history (two-step confirmation) ----

    if st.session_state.get("confirm_clear"):

        st.warning(
            "⚠️ This permanently deletes every analysis record, "
            "including the SHA-256 evidence history. "
            "This cannot be undone."
        )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "Yes, delete everything",
                key="confirm_clear_yes"
            ):

                clear_user_history(USER["id"])
                st.session_state["confirm_clear"] = False
                st.session_state["flash"] = (
                    "Analysis history cleared successfully."
                )
                st.rerun()

        with c2:

            if st.button(
                "Cancel",
                key="confirm_clear_no"
            ):

                st.session_state["confirm_clear"] = False
                st.rerun()

    else:

        if st.button(
            "🗑️ Clear Analysis History",
            key="clear_history"
        ):

            st.session_state["confirm_clear"] = True
            st.rerun()

else:

    st.info(
        "No analysis history available yet."
    )


# ==================================================
# FOOTER + CONTACT
# ==================================================

render_footer()