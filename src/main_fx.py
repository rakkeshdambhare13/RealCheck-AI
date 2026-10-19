"""
RealCheck AI - main (post-login) page effects.

Used ONLY after a user is signed in. The login / registration page never
imports or calls anything from this file, and src/auth_fx.py is not modified:
the zoom-out / fade-out background is REUSED from it, and everything new
(verdict text, title glow) lives here under its own "rcmx-" CSS prefix.

Public API:

    render_main_toggle()                  Enable / Disable switch -> bool
    render_title_fx()                     neon glow + zoom-out for the REALCHECK AI title
    render_main_background(verdict=None)  animated background (+ optional verdict)
    show_verdict(slot, enabled, kind, is_fake)
                                          fill the slot with the verdict for a
                                          FINISHED prediction ("IMAGE" / "VIDEO")
"""

import html

import streamlit as st

from src.auth_fx import render_fx_background   # same animation as the login page

MAIN_TOGGLE_KEY = "main_fx_enabled"

NEON_GREEN = ("#39ff14", "57,255,20")
NEON_RED = ("#ff073a", "255,7,58")


def render_main_toggle():
    """Enable / Disable switch for the main page. True = effects on."""
    return bool(
        st.toggle(
            "✨ Background animation",
            value=True,
            key=MAIN_TOGGLE_KEY,
            help="Turn the animated background text, the animated title "
                 "and the REAL / FAKE result animation on or off."
        )
    )


def render_title_fx():
    """Zoom-out entrance + neon glow for the existing .rc-title element.

    The existing gradient animation (titleGradient) is kept; the zoom-out is
    added next to it. Only emitted on the main page, so the login page title
    is not affected.
    """
    st.html(
        """
<style>
.stApp .rc-title {
    animation:
        titleGradient 5s linear infinite,
        rcmxTitleZoom 1.6s cubic-bezier(.16,.84,.3,1) 1 both;
    filter:
        drop-shadow(0 0 12px rgba(0, 234, 255, 0.80))
        drop-shadow(0 0 32px rgba(155, 92, 255, 0.50));
    transform-origin: center;
}

.stApp .rc-header {
    position: relative;
}

/* dark futuristic glow plate behind the title only */
.stApp .rc-header::before {
    content: "";
    position: absolute;
    left: 50%; top: 55%;
    width: min(900px, 96%);
    height: 70%;
    transform: translate(-50%, -50%);
    background: radial-gradient(ellipse at center,
                rgba(0, 234, 255, 0.10), rgba(5, 8, 22, 0) 70%);
    pointer-events: none;
    z-index: -1;
}

@keyframes rcmxTitleZoom {
    0%   { opacity: 0; transform: scale(2.6); }
    60%  { opacity: 1; }
    100% { opacity: 1; transform: scale(1); }
}

@media (prefers-reduced-motion: reduce) {
    .stApp .rc-title { animation: titleGradient 5s linear infinite; }
}
</style>
"""
    )


def _verdict_html(text, colour, rgb):
    return f"""
<style>
.rcmx-verdict {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 1;                 /* above bg (0), below the interface (2) */
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;       /* never blocks uploads, buttons, video */
    overflow: hidden;
}}
.rcmx-verdict span {{
    font-weight: 900;
    white-space: nowrap;
    letter-spacing: 0.14em;
    font-size: clamp(40px, 10vw, 130px);
    color: {colour};
    text-shadow:
        0 0 12px rgba({rgb}, 0.95),
        0 0 36px rgba({rgb}, 0.75),
        0 0 80px rgba({rgb}, 0.45);
    opacity: 0;
    animation: rcmxVerdict 4.2s ease-out 1 forwards;
    will-change: transform, opacity;
}}
@keyframes rcmxVerdict {{
    0%   {{ opacity: 0;    transform: scale(2.4); }}
    22%  {{ opacity: 0.85; transform: scale(1.25); }}
    60%  {{ opacity: 0.70; transform: scale(1);    }}
    100% {{ opacity: 0;    transform: scale(0.55); }}
}}
@media (prefers-reduced-motion: reduce) {{
    .rcmx-verdict span {{ animation: none; opacity: 0.35; }}
}}
</style>
<div class="rcmx-verdict" aria-hidden="true"><span>{html.escape(text)}</span></div>
"""


def render_main_background(verdict=None):
    """Background animation, plus a verdict word when one is given.

    verdict: None, or (text, is_fake).
    """
    render_fx_background()

    if verdict:
        text, is_fake = verdict
        colour, rgb = NEON_RED if is_fake else NEON_GREEN
        st.html(_verdict_html(text, colour, rgb))


def show_verdict(slot, enabled, kind, is_fake):
    """Call ONLY after the model has finished and its output is stored.

    kind    "IMAGE" or "VIDEO"
    is_fake True when the real predict_image()/analyze_video() output said FAKE
    """
    if not enabled:
        return

    text = ("FAKE " if is_fake else "REAL ") + kind

    with slot.container():
        render_main_background((text, bool(is_fake)))