"""
RealCheck AI - login / registration page effects.

Everything here is used ONLY by the authentication page, so every CSS rule is
prefixed with "rcfx-" and is emitted only while that page is being rendered.
As soon as the user signs in, the page stops emitting these elements and the
dashboard is untouched.

Public API (unchanged names, so app.py keeps working):

    FX_SECONDS            how long the "login ok" message plays before the rerun
    render_fx_toggle()    Enable / Disable switch, returns True when enabled
    render_fx_background()  zoom-out + fade-out background text (behind the form)
    queue_fx(event)       remember an event for the NEXT run (account created)
    pop_fx()              fetch + clear the queued event
    show_fx(event)        animated message (green / red / cyan)
    show_static(event)    same message without animation (effects disabled)
    announce(event, fx_on)  picks show_fx or show_static
"""

import html

import streamlit as st

FX_SECONDS = 1.8

TOGGLE_KEY = "fx_enabled"
_QUEUE_KEY = "_fx_queue"
_NONCE_KEY = "_fx_nonce"

# event -> (text, hex colour, rgb triplet, seconds on screen)
EVENTS = {
    "login_ok": ("LOGIN SUCCESSFULLY", "#22e07a", "34,224,122", FX_SECONDS),
    "login_fail": ("LOGIN UNSUCCESSFULLY", "#ff4d5e", "255,77,94", 4.0),
    "account_created": ("ACCOUNT CREATED SUCCESSFULLY", "#00eaff", "0,234,255", 4.0),
}

BACKGROUND_WORDS = [
    "REALCHECK AI",
    "DETECT",
    "ANALYZE",
    "VERIFY",
    "EXPLAIN",
]

_CYCLE = 10          # seconds for one zoom-out / fade-out loop
_STEP = _CYCLE / len(BACKGROUND_WORDS)


# --------------------------------------------------------------------------
# Toggle
# --------------------------------------------------------------------------

def render_fx_toggle():
    """Visible Enable/Disable switch for the login page. True = effects on."""
    return bool(
        st.toggle(
            "✨ Background effects",
            value=True,
            key=TOGGLE_KEY,
            help="Turn the animated background text and the "
                 "login / registration messages on or off."
        )
    )


# --------------------------------------------------------------------------
# Event queue (survives exactly one st.rerun)
# --------------------------------------------------------------------------

def queue_fx(event):
    st.session_state[_QUEUE_KEY] = event


def pop_fx():
    return st.session_state.pop(_QUEUE_KEY, None)


# --------------------------------------------------------------------------
# Background: zoom-out + fade-out text, BEHIND the form
# --------------------------------------------------------------------------

def _background_css():
    rules = []

    for i in range(len(BACKGROUND_WORDS)):
        # negative delay -> the loop is already running when the page opens
        rules.append(
            f".rcfx-w{i}{{animation-delay:-{i * _STEP:.2f}s;}}"
        )

    return f"""
<style>
/* The form must stack ABOVE the background (z-index 0 below). */
.stApp .block-container {{
    position: relative !important;
    z-index: 2 !important;
}}

.rcfx-bg {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 0;
    overflow: hidden;
    pointer-events: none;      /* never intercepts clicks or typing */
}}

.rcfx-word {{
    position: absolute;
    left: 50%;
    top: 46%;
    white-space: nowrap;
    font-weight: 900;
    letter-spacing: 0.12em;
    font-size: clamp(40px, 9vw, 120px);
    color: rgba(0, 234, 255, 0.10);
    -webkit-text-stroke: 2px rgba(0, 234, 255, 0.55);
    text-shadow: 0 0 40px rgba(0, 234, 255, 0.35);
    opacity: 0;
    transform: translate(-50%, -50%) scale(1.9);
    animation: rcfxZoomOut {_CYCLE}s ease-in infinite;
    will-change: transform, opacity;
}}

.rcfx-w1, .rcfx-w3 {{
    color: rgba(155, 92, 255, 0.10);
    -webkit-text-stroke: 2px rgba(155, 92, 255, 0.55);
    text-shadow: 0 0 40px rgba(155, 92, 255, 0.35);
}}

@keyframes rcfxZoomOut {{
    0%   {{ opacity: 0;    transform: translate(-50%, -50%) scale(1.9); }}
    12%  {{ opacity: 0.55; }}
    100% {{ opacity: 0;    transform: translate(-50%, -50%) scale(0.35); }}
}}

{''.join(rules)}

@media (prefers-reduced-motion: reduce) {{
    .rcfx-word {{ animation: none; opacity: 0; }}
    .rcfx-w0   {{ opacity: 0.25; transform: translate(-50%, -50%) scale(1); }}
}}
</style>
"""


def render_fx_background():
    """Emit the animated background. Call only while the auth page is shown."""
    words = "".join(
        f'<span class="rcfx-word rcfx-w{i}">{html.escape(w)}</span>'
        for i, w in enumerate(BACKGROUND_WORDS)
    )

    st.html(
        _background_css()
        + f'<div class="rcfx-bg" aria-hidden="true">{words}</div>'
    )


# --------------------------------------------------------------------------
# Event messages
# --------------------------------------------------------------------------

_MSG_CSS = """
<style>
.rcfx-msg-wrap {
    position: fixed;
    top: 70px; left: 0; right: 0;
    display: flex;
    justify-content: center;
    z-index: 99999;
    pointer-events: none;      /* never blocks the form underneath */
}
.rcfx-msg {
    padding: 14px 34px;
    border-radius: 18px;
    font-weight: 900;
    letter-spacing: 3px;
    font-size: clamp(18px, 3.4vw, 40px);
    text-align: center;
    background: rgba(5, 8, 22, 0.78);
    backdrop-filter: blur(10px);
}
@keyframes rcfxMsg {
    0%   { opacity: 0; transform: scale(1.6); }
    14%  { opacity: 1; transform: scale(1); }
    75%  { opacity: 1; transform: scale(1); }
    100% { opacity: 0; transform: scale(0.9); }
}
.rcfx-static { animation: none !important; }
</style>
"""


def _banner(event, animated):
    text, colour, rgb, seconds = EVENTS[event]

    # a fresh nonce makes the browser replay the animation on every event
    nonce = int(st.session_state.get(_NONCE_KEY, 0)) + 1
    st.session_state[_NONCE_KEY] = nonce

    style = (
        f"color:{colour};"
        f"border:2px solid {colour};"
        f"text-shadow:0 0 18px rgba({rgb},0.9);"
        f"box-shadow:0 0 36px rgba({rgb},0.45);"
    )

    if animated:
        style += f"opacity:0;animation:rcfxMsg {seconds}s ease-out forwards;"
        extra = ""
    else:
        extra = " rcfx-static"

    st.html(
        _MSG_CSS
        + f'<div class="rcfx-msg-wrap" data-n="{nonce}">'
          f'<div class="rcfx-msg{extra}" role="status" style="{style}">'
          f'{html.escape(text)}</div></div>'
    )


def show_fx(event, detail=None):
    """Animated message: green login ok, red login fail, cyan account created."""
    if event in EVENTS:
        _banner(event, animated=True)


def show_static(event, detail=None):
    """Same message with no animation, for when effects are disabled."""
    if event in EVENTS:
        _banner(event, animated=False)


def announce(event, fx_on, detail=None):
    if fx_on:
        show_fx(event, detail)
    else:
        show_static(event, detail)