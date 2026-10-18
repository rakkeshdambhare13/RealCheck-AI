"""
Advanced cyber-HUD theme for the RealCheck AI Streamlit app.

Usage (in app.py, right after render_3d_background()):

    from src.theme import apply_advanced_theme
    apply_advanced_theme()

It layers on top of the CSS already in app.py (it only overrides / adds), and
is designed to sit on the 3D background from src/background.py:

  * the whole content area becomes a frosted-glass HUD panel with an animated
    neon border and corner brackets
  * glowing section headings, neon metric cards, shimmer buttons
  * radio pills, scanning file-uploader, styled alerts / code / progress bars
  * a status strip under the header

TYPOGRAPHY
  * Inter for all readable text (titles, headings, body, buttons)
  * JetBrains Mono only for numbers, code and hashes
  * fluid type: --rc-u scales smoothly with the viewport (clamp), --rc-boost is the user knob
  * advanced text: aurora title, wipe/tracking reveals, text-wrap balance/pretty,
    scroll-driven reveals (animation-timeline: view()), variable Inter with optical sizing
"""

import streamlit as st


_THEME_HTML = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,100..900&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --rc-cyan:   #00eaff;
    --rc-violet: #9b5cff;
    --rc-green:  #00ffb0;
    --rc-red:    #ff3b5c;
    --rc-amber:  #ffc857;
    --rc-panel:  rgba(5, 10, 32, 0.62);
    --rc-boost:  1;      /* USER KNOB: 1 = normal, 1.15 = larger, 1.3 = largest (the Aa control sets this too) */
    /* FLUID TYPE UNIT: every size below is calc(var(--rc-u) * N), so "1px of design size"
       grows smoothly with the screen between 1.2px (phones) and 1.75px (large monitors).
       Edit the clamp() to retune. */
    --rc-u:      calc(clamp(1.2px, 0.95px + 0.04vw, 1.75px) * var(--rc-boost));
    --rc-bg-blur:   0px;   /* BACKGROUND BLUR: the 3D layer behind everything (0 = sharp, 1px = very light) */
    --rc-glass-blur: 0px;  /* GLASS BLUR: panel, cards, alerts (0 = fully clear; the old look was 10-18px) */
    --rc-w-body:   700;    /* TEXT WEIGHT: 400 = regular, 600 = semi-bold, 700 = bold, 800 = extra bold */
    --rc-w-head:   800;    /* HEADING WEIGHT */
    --rc-bg-speed: 0.45;   /* BACKGROUND SPEED: multiplies animation time, so LOWER = FASTER (1 = original) */
}

@property --rc-ang {
    syntax: '<angle>';
    initial-value: 0deg;
    inherits: false;
}

html, body, .stApp {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
    font-optical-sizing: auto;                       /* Inter picks its optical size automatically */
    font-feature-settings: "cv11", "ss03", "calt";   /* single-storey a, round quotes, contextual alternates */
}


/* ==================================================
   MAIN HUD PANEL (glass + animated neon border)
   ================================================== */

.block-container {
    background: var(--rc-panel);
    backdrop-filter: blur(var(--rc-glass-blur)) saturate(140%);
    -webkit-backdrop-filter: blur(var(--rc-glass-blur)) saturate(140%);
    border-radius: 28px;
    margin-top: 1.2rem;
    margin-bottom: 2rem;
    padding: 2rem 2.4rem 3rem !important;
    box-shadow:
        0 30px 90px rgba(0, 0, 0, 0.55),
        0 0 60px rgba(0, 234, 255, 0.07),
        inset 0 0 60px rgba(0, 234, 255, 0.025);
}

/* rotating neon border */
.block-container::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    padding: 1.5px;
    background: conic-gradient(
        from var(--rc-ang),
        rgba(0, 234, 255, 0.08) 0%,
        rgba(0, 234, 255, 0.08) 55%,
        var(--rc-cyan) 75%,
        var(--rc-violet) 90%,
        rgba(0, 234, 255, 0.08) 100%
    );
    -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
            mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0);
    animation: rcBorderSpin calc(7s * var(--rc-bg-speed)) linear infinite;
    pointer-events: none;
}

/* renamed from rcSpin so it can never clash with the button spinner */
@keyframes rcBorderSpin {
    to { --rc-ang: 360deg; }
}

/* HUD corner brackets */
.block-container::after {
    content: "";
    position: absolute;
    inset: 12px;
    pointer-events: none;
    opacity: 0.85;
    background:
        linear-gradient(var(--rc-cyan), var(--rc-cyan)) top left     / 28px 2px no-repeat,
        linear-gradient(var(--rc-cyan), var(--rc-cyan)) top left     / 2px 28px no-repeat,
        linear-gradient(var(--rc-cyan), var(--rc-cyan)) top right    / 28px 2px no-repeat,
        linear-gradient(var(--rc-cyan), var(--rc-cyan)) top right    / 2px 28px no-repeat,
        linear-gradient(var(--rc-violet), var(--rc-violet)) bottom left  / 28px 2px no-repeat,
        linear-gradient(var(--rc-violet), var(--rc-violet)) bottom left  / 2px 28px no-repeat,
        linear-gradient(var(--rc-violet), var(--rc-violet)) bottom right / 28px 2px no-repeat,
        linear-gradient(var(--rc-violet), var(--rc-violet)) bottom right / 2px 28px no-repeat;
    filter: drop-shadow(0 0 6px rgba(0, 234, 255, 0.7));
}


/* ==================================================
   BACKGROUND MOTION
   ================================================== */

/* the floating aura defined in app.py moves faster (see --rc-bg-speed in :root) */
.stApp::after {
    animation-duration: calc(9s * var(--rc-bg-speed)) !important;
}


/* ==================================================
   GLASS BLUR (cards from app.py follow the same 5% knob)
   ================================================== */

.rc-header .rc-description,
.rc-contact,
div[role="radiogroup"],
div[data-testid="stVerticalBlockBorderWrapper"] {
    -webkit-backdrop-filter: blur(var(--rc-glass-blur));
            backdrop-filter: blur(var(--rc-glass-blur));
}


/* ==================================================
   HEADER
   ================================================== */

.rc-header .rc-icon {
    /* LOGO SIZE: circle = first clamp, magnifier emoji = second clamp (min, scales with screen, max) */
    width:  calc(clamp(120px, 15vw, 250px) * var(--rc-boost));
    height: calc(clamp(120px, 15vw, 250px) * var(--rc-boost));
    font-size: calc(clamp(60px, 8vw, 135px) * var(--rc-boost));
}

.rc-header .rc-title {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    font-weight: 900;
    font-size: calc(clamp(38px, 8vw, 124px) * var(--rc-boost));   /* TITLE SIZE: change 124px for a bigger/smaller maximum */
    letter-spacing: 0.08em;
    line-height: 1.1;
    /* two layers: (1) a soft spotlight that follows the mouse (--mx/--my are set by
       ui_effects.py), (2) the aurora gradient that drifts slowly across the letters */
    background:
        radial-gradient(circle 170px at var(--mx, -400px) var(--my, -400px), rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0) 70%) no-repeat,
        linear-gradient(90deg, #ffffff 0%, #8ff1ff 25%, #b9a2ff 50%, #8ff1ff 75%, #ffffff 100%);
    background-size: 100% 100%, 300% 100%;
    background-position: 0 0, 0 50%;
    -webkit-background-clip: text;
            background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 18px rgba(0, 234, 255, 0.25));
    animation:
        rcTitleIn 1.4s cubic-bezier(.2, .7, .2, 1) both,
        rcAurora 16s linear 1.4s infinite !important;
}

/* 150% of a 300%-wide tile = exactly one full tile, so the loop is seamless */
@keyframes rcAurora {
    to { background-position: 0 0, 150% 50%; }
}

/* cinematic reveal: left-to-right wipe + tracking tightens + blur clears.
   The negative clip-path insets keep the neon glow from being cut off. */
@keyframes rcTitleIn {
    from {
        opacity: 0;
        letter-spacing: 0.2em;
        filter: blur(8px) drop-shadow(0 0 18px rgba(0, 234, 255, 0.25));
        clip-path: inset(-60px 100% -60px -60px);
    }
    to {
        clip-path: inset(-60px -60px -60px -60px);
    }
}

@keyframes rcTrackIn {
    from { opacity: 0; letter-spacing: 0.5em; filter: blur(6px); }
}

@keyframes rcFadeUp {
    from { opacity: 0; transform: translateY(8px); }
}

.rc-header .rc-subtitle {
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    font-size: calc(var(--rc-u) * 13);
    font-weight: 700;
    letter-spacing: 0.22em;
    color: #8fe3f5;
    text-shadow: none;
    animation: rcTrackIn 1.3s cubic-bezier(.2, .7, .2, 1) .5s both;
}

.rc-header .rc-description {
    max-width: 920px;
    font-size: calc(var(--rc-u) * 15);
    line-height: 1.7;
    color: #c9d4f2;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(148, 163, 184, 0.2);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    animation: rcFadeUp 0.8s ease 0.7s both;
}


/* ==================================================
   STATUS STRIP
   ================================================== */

.rc-hud {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin: 6px auto 22px;
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    font-weight: 700;
    font-size: calc(var(--rc-u) * 11.5);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.rc-hud span {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 13px;
    border-radius: 999px;
    color: #c9f8ff;
    background: rgba(0, 234, 255, 0.06);
    border: 1px solid rgba(0, 234, 255, 0.28);
}

.rc-hud span i {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--rc-green);
    box-shadow: 0 0 10px var(--rc-green);
    animation: rcBlink 1.4s ease-in-out infinite;
}

.rc-hud span:nth-child(2) i { background: var(--rc-cyan);   box-shadow: 0 0 10px var(--rc-cyan);   animation-delay: .2s; }
.rc-hud span:nth-child(3) i { background: var(--rc-violet); box-shadow: 0 0 10px var(--rc-violet); animation-delay: .4s; }
.rc-hud span:nth-child(4) i { background: var(--rc-amber);  box-shadow: 0 0 10px var(--rc-amber);  animation-delay: .6s; }
.rc-hud span:nth-child(5) i { background: var(--rc-red);    box-shadow: 0 0 10px var(--rc-red);    animation-delay: .8s; }

@keyframes rcBlink {
    50% { opacity: 0.25; transform: scale(0.8); }
}


/* ==================================================
   HEADINGS
   ================================================== */

div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3 {
    position: relative;
    padding-left: 16px;
    font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    font-weight: var(--rc-w-head);
    letter-spacing: -0.01em;
    text-shadow: none;
}

div[data-testid="stMarkdownContainer"] p {
    font-size: calc(var(--rc-u) * 16);
    line-height: 1.65;
    color: #dbe3f7;
}

div[data-testid="stMarkdownContainer"] h2::before,
div[data-testid="stMarkdownContainer"] h3::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0.22em;
    bottom: 0.22em;
    width: 4px;
    border-radius: 4px;
    background: linear-gradient(var(--rc-cyan), var(--rc-violet));
    box-shadow: 0 0 10px rgba(0, 234, 255, 0.55);
    transform-origin: top;
    animation: rcBarGrow .6s cubic-bezier(.2, .7, .2, 1) .15s backwards;
}

/* SECTION HEADINGS ("Image Forensics" ...): a focus pull. The text starts blurred and
   glowing, snaps into sharp focus, and the neon glow then fades out. The accent bar grows
   down and (h2 only) a gradient underline draws itself beneath. */
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3 {
    animation: rcHeadFocus 1.1s cubic-bezier(.2, .7, .2, 1) backwards;
}

@keyframes rcHeadFocus {
    0%   { opacity: 0; filter: blur(12px); transform: translateY(12px) scale(.985);
           text-shadow: 0 0 30px rgba(0, 234, 255, 0.9); }
    55%  { opacity: 1; filter: blur(0);    transform: none;
           text-shadow: 0 0 22px rgba(0, 234, 255, 0.75); }
    100% { opacity: 1; filter: blur(0);    transform: none;
           text-shadow: 0 0 0 rgba(0, 234, 255, 0); }
}

div[data-testid="stMarkdownContainer"] h2::after {
    content: "";
    position: absolute;
    left: 16px;
    bottom: 0.4rem;
    height: 2px;
    width: min(240px, 60%);
    border-radius: 2px;
    background: linear-gradient(90deg, var(--rc-cyan), var(--rc-violet) 60%, transparent);
    box-shadow: 0 0 10px rgba(0, 234, 255, 0.5);
    transform-origin: left;
    pointer-events: none;
    animation: rcUnderline .9s cubic-bezier(.2, .7, .2, 1) .3s backwards;
}

@keyframes rcUnderline {
    from { transform: scaleX(0); opacity: 0; }
}

@keyframes rcBarGrow {
    from { transform: scaleY(0); }
}

/* smart line breaking: balanced headings, no orphan words in paragraphs */
.rc-header .rc-title,
.rc-header .rc-description,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3 { text-wrap: balance; }

div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li { text-wrap: pretty; }

@keyframes rcTextRise {
    from { opacity: 0; transform: translateY(14px); filter: blur(3px); }
}

/* SCROLL-DRIVEN REVEAL: where the browser supports animation-timeline, headings and
   paragraphs animate as they scroll into view (instead of on a fixed timer). */
@supports (animation-timeline: view()) {
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3 {
        animation: rcHeadFocus linear both;
        animation-timeline: view();
        animation-range: entry 0% entry 60%;
    }
    div[data-testid="stMarkdownContainer"] h2::after {
        animation: rcUnderline linear both;
        animation-timeline: view();
        animation-range: entry 25% entry 90%;
    }
    div[data-testid="stMarkdownContainer"] p {
        animation: rcTextRise linear both;
        animation-timeline: view();
        animation-range: entry 0% entry 50%;
    }
}


/* ==================================================
   RADIO (mode switch) -> pills
   ================================================== */

div[role="radiogroup"] {
    position: relative;
    isolation: isolate;
    gap: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(0, 234, 255, 0.2);
    box-shadow: inset 0 0 24px rgba(0, 234, 255, 0.04);
}

div[role="radiogroup"] > label {
    position: relative;
    z-index: 1;
    overflow: hidden;
    cursor: pointer;
    padding: 8px 16px;
    border-radius: 12px;
    border: 1px solid transparent;
    transition: background 0.25s ease, color 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    font-weight: 700;
    font-size: calc(var(--rc-u) * 14);
    letter-spacing: 0.01em;
}

div[role="radiogroup"] > label:hover {
    background: rgba(0, 234, 255, 0.08);
}

div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(135deg, rgba(0, 234, 255, 0.22), rgba(155, 92, 255, 0.25));
    border-color: rgba(0, 234, 255, 0.7);
    box-shadow: 0 0 22px rgba(0, 234, 255, 0.28), inset 0 0 14px rgba(0, 234, 255, 0.12);
}


/* ==================================================
   FILE UPLOADER -> scanning dropzone
   ================================================== */

section[data-testid="stFileUploaderDropzone"] {
    position: relative;
    overflow: hidden;
    background: rgba(0, 234, 255, 0.035);
    border: 1px dashed rgba(0, 234, 255, 0.55);
}

section[data-testid="stFileUploaderDropzone"]::after {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--rc-cyan), transparent);
    box-shadow: 0 0 14px var(--rc-cyan);
    opacity: 0.8;
    animation: rcScan 3.4s ease-in-out infinite;
    pointer-events: none;
}

@keyframes rcScan {
    0%, 100% { top: 0; }
    50%      { top: calc(100% - 2px); }
}


/* ==================================================
   METRICS -> neon cards
   ================================================== */

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(0, 234, 255, 0.07), rgba(155, 92, 255, 0.06));
    border: 1px solid rgba(0, 234, 255, 0.2);
    border-left: 3px solid var(--rc-cyan);
    border-radius: 14px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}

div[data-testid="stMetricLabel"] {
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.1em;
    font-size: calc(var(--rc-u) * 11.5);
    opacity: 0.9;
}

div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: calc(var(--rc-u) * 28);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    text-shadow: 0 0 14px rgba(0, 234, 255, 0.35);
    animation: rcValueIn .8s cubic-bezier(.2, .7, .2, 1) .1s backwards;
}

@keyframes rcValueIn {
    from { opacity: 0; filter: blur(6px); transform: translateY(6px); }
}


/* ==================================================
   ALERTS, CODE, PROGRESS, DIVIDERS
   ================================================== */

div[data-testid="stAlert"] {
    border-radius: 14px;
    backdrop-filter: blur(var(--rc-glass-blur));
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.25);
}

div[data-testid="stCode"],
div[data-testid="stCode"] pre {
    border-radius: 12px;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
}

div[data-testid="stCode"] {
    border: 1px solid rgba(0, 234, 255, 0.22);
    box-shadow: 0 0 22px rgba(0, 234, 255, 0.06);
}

div[data-testid="stProgress"] div[role="progressbar"] > div {
    background: linear-gradient(90deg, var(--rc-cyan), var(--rc-violet)) !important;
    box-shadow: 0 0 14px rgba(0, 234, 255, 0.6);
}

hr {
    border: 0 !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, rgba(0, 234, 255, 0.55), transparent) !important;
    margin: 1.6rem 0 !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid rgba(0, 234, 255, 0.22);
    box-shadow: 0 0 26px rgba(0, 234, 255, 0.06);
}

div[data-testid="stImage"] img {
    border-radius: 16px;
    border: 1px solid rgba(0, 234, 255, 0.25);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 234, 255, 0.08);
}

div[data-testid="stSpinner"] {
    color: var(--rc-cyan);
}


/* ==================================================
   TEXT SIZE (all driven by --rc-u at the top)
   ================================================== */

div[data-testid="stMarkdownContainer"] h2 { font-size: calc(var(--rc-u) * 30); }
div[data-testid="stMarkdownContainer"] h3 { font-size: calc(var(--rc-u) * 22); }

div[data-testid="stMarkdownContainer"] li,
div[data-testid="stWidgetLabel"] p,
label p {
    font-size: calc(var(--rc-u) * 16);
}

div[data-testid="stAlert"] p {
    font-size: calc(var(--rc-u) * 16);
    line-height: 1.55;
}

div[data-testid="stCaptionContainer"],
div[data-testid="stCaptionContainer"] p {
    font-size: calc(var(--rc-u) * 14);
}

section[data-testid="stFileUploaderDropzone"] span,
section[data-testid="stFileUploaderDropzone"] div {
    font-size: calc(var(--rc-u) * 14);
}

section[data-testid="stFileUploaderDropzone"] small {
    font-size: calc(var(--rc-u) * 12.5);
}

div[data-testid="stCode"] pre,
div[data-testid="stCode"] code {
    font-size: calc(var(--rc-u) * 14) !important;
}

.rc-footer { font-size: calc(var(--rc-u) * 13); }
.rc-contact-item { font-size: calc(var(--rc-u) * 14); }

/* ==================================================
   BOLD TYPOGRAPHY (one knob: --rc-w-body in :root)
   ================================================== */

.stApp div[data-testid="stMarkdownContainer"] p,
.stApp div[data-testid="stMarkdownContainer"] li,
.stApp div[data-testid="stWidgetLabel"] p,
.stApp label p,
.stApp div[data-testid="stCaptionContainer"],
.stApp div[data-testid="stCaptionContainer"] p,
.stApp div[data-testid="stAlert"] p,
.stApp section[data-testid="stFileUploaderDropzone"] span,
.stApp section[data-testid="stFileUploaderDropzone"] small,
.stApp section[data-testid="stFileUploaderDropzone"] div,
.stApp .rc-header .rc-description,
.stApp .rc-footer,
.stApp .rc-contact-item {
    font-weight: var(--rc-w-body);
}

.stApp div[data-testid="stMarkdownContainer"] strong,
.stApp div[data-testid="stMarkdownContainer"] b,
.stApp .rc-footer b {
    font-weight: 800;
}

.stApp div[role="radiogroup"] > label p,
.stApp div[data-testid="stMetricLabel"] p {
    font-weight: 700;
}


/* ==================================================
   SCROLLBAR + SELECTION
   ================================================== */

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.03); }
::-webkit-scrollbar-thumb {
    background: linear-gradient(var(--rc-cyan), var(--rc-violet));
    border-radius: 10px;
}

::selection {
    background: rgba(0, 234, 255, 0.35);
    color: #ffffff;
}


/* ==================================================
   MOBILE
   ================================================== */

@media (max-width: 700px) {
    .rc-header .rc-title { letter-spacing: 0.05em; }
    .block-container {
        padding: 1.2rem 1rem 2rem !important;
        border-radius: 20px;
    }
    .rc-hud { font-size: 10px; gap: 6px; }
    .rc-hud span { padding: 5px 9px; }
}


/* ==================================================
   REDUCED MOTION (accessibility + lighter on weak devices)
   ================================================== */

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation: none !important;
        transition: none !important;
    }
}
</style>

<div class="rc-hud">
    <span><i></i>System Online</span>
    <span><i></i>Image Model</span>
    <span><i></i>Video Analyzer</span>
    <span><i></i>SHA-256 Evidence</span>
    <span><i></i>Grad-CAM XAI</span>
</div>
"""


def apply_advanced_theme():
    """Apply the cyber-HUD theme and render the status strip."""
    st.html(_THEME_HTML)