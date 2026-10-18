"""
Professional buttons + text behaviours for the RealCheck AI Streamlit app.

Usage (in app.py, right after apply_advanced_theme()):

    from src.ui_effects import apply_ui_effects
    apply_ui_effects()

BUTTONS  (a proper design system, not just effects)
  * three roles, detected automatically from the label:
      - Primary   "Start ... Analysis"          solid cyan gradient, dark text
      - Secondary "Download ... Report"         quiet outline
      - Danger    "Clear Analysis History"      red outline
  * hover lift, press-down, keyboard focus ring, subtle click ripple
  * loading state: the clicked button shows a spinner and is locked while
    Streamlit is working, so users cannot double-submit
TEXT
  * refined title / subtitle / description entrance (CSS, see theme.py)
  * DETECT / ANALYZE / VERIFY / EXPLAIN steps with a moving underline
  * metric numbers count up smoothly, tabular figures
  * floating Aa control (S / M / L / XL) that rescales all text, remembered between visits
  * result alerts get a verdict chip (FLAGGED / NO FLAGS RAISED) and a
    restrained colored glow
  * toast notifications with icon, message, countdown bar, click to dismiss

Same launcher trick as src/background.py: Streamlit does not run <script>
tags in st.html, so a tiny components.html iframe injects the styles and
behaviours into the main page. It only sets attributes/styles and text
nodes; it never removes Streamlit's own elements.
"""

import streamlit.components.v1 as components


_UI_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
/* =====================================================================
   CSS (injected into the main page <head>)
   ===================================================================== */
const RC_FX_CSS = `
/* ===================== BUTTON SYSTEM ===================== */
.stApp .stButton > button,
.stApp .stDownloadButton > button {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  min-height: 60px;
  padding: 0 30px;
  border-radius: 10px;
  font: 700 calc(var(--rc-u, 1.35px) * 14)/1 Inter, system-ui, -apple-system, 'Segoe UI', sans-serif;
  letter-spacing: .01em;
  text-transform: none;
  color: #e8eefc;
  background: rgba(255,255,255,.045);
  border: 1px solid rgba(148,163,184,.32);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.06), 0 1px 2px rgba(0,0,0,.35);
  transform: none;
  transition: transform .16s ease, box-shadow .2s ease, background .2s ease, border-color .2s ease, filter .2s ease;
}
.stApp .stButton > button p,
.stApp .stDownloadButton > button p {
  margin: 0;
  color: inherit !important;
  font: inherit !important;
  letter-spacing: inherit;
}
.stApp .stButton > button > *,
.stApp .stDownloadButton > button > * { position: relative; z-index: 1; }

/* ---- Secondary (default) ---- */
.stApp .stButton > button:hover,
.stApp .stDownloadButton > button:hover {
  transform: translateY(-1px);
  border-color: rgba(0,234,255,.6);
  background: rgba(0,234,255,.08);
  box-shadow: 0 8px 22px rgba(0,0,0,.35), 0 0 0 1px rgba(0,234,255,.16);
}
.stApp .stButton > button:active,
.stApp .stDownloadButton > button:active {
  transform: translateY(0) scale(.985);
  box-shadow: inset 0 2px 6px rgba(0,0,0,.35);
}

/* ---- Primary ---- */
.stApp .stButton > button[data-rc-variant="primary"],
.stApp .stDownloadButton > button[data-rc-variant="primary"] {
  min-width: 250px;
  color: #03141f;
  border: 1px solid rgba(125,243,255,.7);
  background: linear-gradient(180deg, #3aeaff 0%, #12b6ef 55%, #0b8fd6 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.55), 0 10px 28px rgba(14,165,233,.36), 0 1px 2px rgba(0,0,0,.4);
  text-shadow: 0 1px 0 rgba(255,255,255,.25);
}
.stApp .stButton > button[data-rc-variant="primary"]:hover,
.stApp .stDownloadButton > button[data-rc-variant="primary"]:hover {
  border-color: rgba(190,250,255,.9);
  background: linear-gradient(180deg, #3aeaff 0%, #12b6ef 55%, #0b8fd6 100%);
  filter: brightness(1.07) saturate(1.05);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.6), 0 14px 36px rgba(14,165,233,.5), 0 1px 2px rgba(0,0,0,.4);
}
.stApp .stButton > button[data-rc-variant="primary"]::before {
  content: "";
  position: absolute;
  top: 0; left: -60%;
  width: 40%; height: 100%;
  background: linear-gradient(100deg, transparent, rgba(255,255,255,.5), transparent);
  transform: skewX(-20deg);
  transition: left .65s ease;
  pointer-events: none;
  z-index: 2;
}
.stApp .stButton > button[data-rc-variant="primary"]:hover::before { left: 130%; }

/* ---- Danger ---- */
.stApp .stButton > button[data-rc-variant="danger"] {
  color: #ff9aab;
  border-color: rgba(255,93,115,.5);
  background: rgba(255,59,92,.06);
}
.stApp .stButton > button[data-rc-variant="danger"]:hover {
  color: #ffd2da;
  border-color: rgba(255,93,115,.9);
  background: rgba(255,59,92,.16);
  box-shadow: 0 8px 22px rgba(0,0,0,.35), 0 0 0 1px rgba(255,93,115,.25);
}

/* ---- Focus + disabled ---- */
.stApp .stButton > button:focus-visible,
.stApp .stDownloadButton > button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(45,226,255,.4), 0 0 0 1px rgba(45,226,255,.9);
}
.stApp .stButton > button:disabled,
.stApp .stDownloadButton > button:disabled { opacity: .45; filter: saturate(.4); cursor: not-allowed; }

/* ---- Loading ---- */
.stApp .stButton > button[data-rc-busy],
.stApp .stDownloadButton > button[data-rc-busy] { pointer-events: none; cursor: progress; padding-right: 48px; }
.stApp .stButton > button[data-rc-busy] > *,
.stApp .stDownloadButton > button[data-rc-busy] > * { opacity: .6; }
.stApp .stButton > button[data-rc-busy]::after,
.stApp .stDownloadButton > button[data-rc-busy]::after {
  content: "";
  position: absolute;
  right: 14px; top: 50%;
  width: 14px; height: 14px;
  margin-top: -7px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-right-color: transparent;
  animation: rcBtnSpin .7s linear infinite;
  z-index: 3;
}
@keyframes rcBtnSpin { to { transform: rotate(360deg); } }

/* ---- Ripple ---- */
.rc-ripple {
  position: absolute;
  width: 20px; height: 20px;
  margin: -10px 0 0 -10px;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  background: radial-gradient(circle, rgba(255,255,255,.55), rgba(255,255,255,.18) 50%, transparent 70%);
  transform: scale(0);
  animation: rcRipple .7s ease-out forwards;
}
@keyframes rcRipple { to { transform: scale(var(--rs, 18)); opacity: 0; } }


/* ===================== TEXT ===================== */
.rc-description b {
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px 2px;
  font: 800 calc(var(--rc-u, 1.35px) * 12)/1 Inter, system-ui, -apple-system, 'Segoe UI', sans-serif;
  letter-spacing: .16em;
}
.rc-tag {
  position: relative;
  padding: 7px 10px;
  color: #8a98bd;
  transition: color .35s ease;
}
.rc-tag::after {
  content: "";
  position: absolute;
  left: 10px; right: 10px; bottom: 0;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, #00eaff, #9b5cff);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform .55s ease;
}
.rc-tag.on { color: #eafcff; }
.rc-tag.on::after { transform: scaleX(1); }
.rc-sep { color: #3b4a73; padding: 0 2px; }

/* ---- result alerts ---- */
.stApp div[data-testid="stAlert"] { position: relative; animation: rcPop .5s cubic-bezier(.2,1.2,.4,1) backwards; }
@keyframes rcPop { from { opacity: 0; transform: translateY(12px) scale(.985); } }

.stApp div[data-testid="stAlert"][data-rc-kind] { padding-right: 200px; }
.stApp div[data-testid="stAlert"][data-rc-kind]::after {
  position: absolute;
  top: 50%; right: 14px;
  transform: translateY(-50%);
  padding: 6px 9px;
  border-radius: 6px;
  font: 700 calc(var(--rc-u, 1.35px) * 10.5)/1 'JetBrains Mono', ui-monospace, monospace;
  letter-spacing: .14em;
}
.stApp div[data-testid="stAlert"][data-rc-kind="fake"] {
  border-left: 3px solid #ff3b5c;
  animation: rcPop .5s cubic-bezier(.2,1.2,.4,1) backwards, rcGlowRed 3s ease-in-out .6s infinite;
}
.stApp div[data-testid="stAlert"][data-rc-kind="fake"]::after {
  content: "FLAGGED";
  color: #ffb3bf; background: rgba(255,59,92,.16); border: 1px solid rgba(255,93,115,.5);
}
.stApp div[data-testid="stAlert"][data-rc-kind="real"] {
  border-left: 3px solid #00e59f;
  animation: rcPop .5s cubic-bezier(.2,1.2,.4,1) backwards, rcGlowGreen 3s ease-in-out .6s infinite;
}
.stApp div[data-testid="stAlert"][data-rc-kind="real"]::after {
  content: "NO FLAGS RAISED";
  color: #a8ffe0; background: rgba(0,229,159,.12); border: 1px solid rgba(0,229,159,.45);
}
@keyframes rcGlowRed   { 0%,100% { box-shadow: 0 0 0 rgba(255,59,92,0); }  50% { box-shadow: 0 0 34px rgba(255,59,92,.3); } }
@keyframes rcGlowGreen { 0%,100% { box-shadow: 0 0 0 rgba(0,229,159,0); }  50% { box-shadow: 0 0 30px rgba(0,229,159,.26); } }

/* ---- sections and results rise in ---- */
.stApp div[data-testid="stElementContainer"],
.stApp .element-container { animation: rcRise .45s ease backwards; }
@keyframes rcRise { from { opacity: 0; transform: translateY(8px); } }


/* ===================== TOASTS ===================== */
#rc-toasts {
  position: fixed; top: 20px; right: 20px; z-index: 2147483000;
  display: flex; flex-direction: column; gap: 10px; pointer-events: none;
}
.rc-toast {
  position: relative;
  width: min(420px, calc(100vw - 40px));
  box-sizing: border-box;
  padding: 16px 18px 18px 16px;
  display: flex; gap: 12px; align-items: flex-start;
  border-radius: 12px;
  border: 1px solid rgba(148,163,184,.22);
  border-left: 3px solid var(--tc, #00eaff);
  background: rgba(8,14,34,.95);
  box-shadow: 0 18px 44px rgba(0,0,0,.5);
  backdrop-filter: blur(12px);
  font-family: Inter, system-ui, -apple-system, 'Segoe UI', sans-serif;
  pointer-events: auto;
  cursor: pointer;
  overflow: hidden;
  animation: rcToastIn .4s cubic-bezier(.2,1.1,.4,1) both;
}
.rc-toast.out { animation: rcToastOut .3s ease forwards; }
.rc-toast .ic {
  flex: none; width: 36px; height: 36px; border-radius: 9px;
  display: grid; place-items: center;
  font: 800 18px/1 Inter, sans-serif;
  color: var(--tc); background: var(--tb, rgba(0,234,255,.14));
}
.rc-toast .tt { font: 700 calc(var(--rc-u, 1.35px) * 13.5)/1.3 Inter, sans-serif; color: #f1f5ff; }
.rc-toast .tm { font: 600 calc(var(--rc-u, 1.35px) * 12.5)/1.45 Inter, sans-serif; color: #b4c0de; margin-top: 3px; }
.rc-toast .bar {
  position: absolute; left: 0; bottom: 0; height: 2px; width: 100%;
  background: var(--tc); opacity: .75;
  transform-origin: left;
  animation: rcBar 4.4s linear forwards;
}
@keyframes rcBar { to { transform: scaleX(0); } }
@keyframes rcToastIn  { from { opacity: 0; transform: translateX(32px); } }
@keyframes rcToastOut { to   { opacity: 0; transform: translateX(32px); } }

/* ===================== TABS (mode switch) ===================== */
/* one glowing pill slides between the options with a spring; JS (updateTabs) feeds it
   the position of the selected option through --ti-x / --ti-y / --ti-w / --ti-h */
.stApp div[role="radiogroup"][data-rc-tabs]::before {
  content: "";
  position: absolute; left: 0; top: 0; z-index: 0;
  box-sizing: border-box;
  width: var(--ti-w); height: var(--ti-h);
  transform: translate(var(--ti-x), var(--ti-y));
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(0,234,255,.30), rgba(155,92,255,.34));
  border: 1px solid rgba(0,234,255,.8);
  box-shadow: 0 0 24px rgba(0,234,255,.32), inset 0 0 14px rgba(0,234,255,.14);
  pointer-events: none;
}
.stApp div[role="radiogroup"][data-rc-tabs-ready]::before {
  transition: transform .55s cubic-bezier(.34,1.45,.5,1), width .55s cubic-bezier(.34,1.45,.5,1), height .3s ease;
}
.stApp div[role="radiogroup"].rc-pulse::before { animation: rcTabBurst .7s ease-out; }
@keyframes rcTabBurst {
  0%   { box-shadow: 0 0 0 0 rgba(0,234,255,.7),  0 0 24px rgba(0,234,255,.32), inset 0 0 14px rgba(0,234,255,.14); }
  100% { box-shadow: 0 0 0 18px rgba(0,234,255,0), 0 0 24px rgba(0,234,255,.32), inset 0 0 14px rgba(0,234,255,.14); }
}
.stApp div[role="radiogroup"][data-rc-tabs] > label:has(input:checked) {
  background: transparent; border-color: transparent; box-shadow: none;
  color: #fff; text-shadow: 0 0 12px rgba(0,234,255,.6);
}
.stApp div[role="radiogroup"] > label:active { transform: scale(.97); }
.stApp div[role="radiogroup"] > label .rc-ripple { opacity: .5; }

/* ===================== BACKGROUND BLUR ===================== */
/* the full-screen 3D background layer gets a light blur (set --rc-bg-blur in theme.py);
   scale hides the soft edge a blur would otherwise leave at the screen border */
[data-rc-bg] { filter: blur(var(--rc-bg-blur, 0px)); }

/* ===================== VERDICT TEXT ===================== */
/* the verdict line tracks in out of a blur and carries a faint glow in its own colour */
.stApp div[data-testid="stAlert"][data-rc-kind] p {
  animation: rcVerdict .9s cubic-bezier(.2,.7,.2,1) .15s backwards;
  font-weight: 800;
}
.stApp div[data-testid="stAlert"][data-rc-kind="fake"] p { text-shadow: 0 0 18px rgba(255,59,92,.45); }
.stApp div[data-testid="stAlert"][data-rc-kind="real"] p { text-shadow: 0 0 18px rgba(0,229,159,.4); }
@keyframes rcVerdict { from { opacity: 0; letter-spacing: .14em; filter: blur(6px); } }

/* ===================== TEXT SIZE CONTROL ===================== */
#rc-size {
  position: fixed; right: 18px; bottom: 18px; z-index: 2147482000;
  display: flex; align-items: center; gap: 2px;
  padding: 5px;
  border-radius: 999px;
  background: rgba(8,14,34,.88);
  border: 1px solid rgba(148,163,184,.28);
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 30px rgba(0,0,0,.45);
  font-family: Inter, system-ui, -apple-system, 'Segoe UI', sans-serif;
}
#rc-size span { padding: 0 8px 0 11px; font: 700 13px/1 Inter, sans-serif; color: #8fe3f5; letter-spacing: .04em; }
#rc-size button {
  appearance: none; border: 0; cursor: pointer;
  padding: 8px 11px; border-radius: 999px;
  background: transparent; color: #b4c0de;
  font: 700 12px/1 Inter, sans-serif; letter-spacing: .03em;
  transition: background .2s ease, color .2s ease, transform .15s ease;
}
#rc-size button:hover { color: #fff; background: rgba(255,255,255,.08); }
#rc-size button:active { transform: scale(.94); }
#rc-size button[aria-pressed="true"] {
  color: #03141f;
  background: linear-gradient(180deg, #3aeaff, #12b6ef);
}
#rc-size button:focus-visible { outline: none; box-shadow: 0 0 0 2px rgba(45,226,255,.9); }
@media (max-width: 700px) { #rc-size { right: 10px; bottom: 10px; } #rc-size span { display: none; } }
@media print { #rc-size { display: none; } }
`;

/* =====================================================================
   rcFx: behaviours. Serialized and injected into the MAIN page.
   ===================================================================== */
function rcFx() {
  const FX_ENABLED = true;
  if (!FX_ENABLED) return;

  if (window.__rcFxCleanup) { try { window.__rcFxCleanup(); } catch (e) {} }
  const ac = new AbortController();
  const sig = ac.signal;
  const timers = [];

  const BTN = ".stApp .stButton > button, .stApp .stDownloadButton > button";
  const TAB = 'div[role="radiogroup"] > label';
  const reduceMotion = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  /* ------------------------- button roles ------------------------- */
  function classify(b) {
    const tx = (b.textContent || "").toLowerCase();
    let v = "secondary";
    if (b.getAttribute("kind") === "primary" || b.getAttribute("data-testid") === "stBaseButton-primary") v = "primary";
    else if (/clear|delete|remove|reset/.test(tx)) v = "danger";
    else if (/download|export|report|save/.test(tx)) v = "secondary";
    else if (/start|analy|run|scan|detect|verify/.test(tx)) v = "primary";
    if (b.getAttribute("data-rc-variant") !== v) b.setAttribute("data-rc-variant", v);
  }

  /* --------------------------- ripple --------------------------- */
  document.addEventListener("pointerdown", function (e) {
    const b = e.target && e.target.closest ? e.target.closest(BTN + ", " + TAB) : null;
    if (!b || b.disabled) return;
    const r = b.getBoundingClientRect();
    const s = document.createElement("span");
    s.className = "rc-ripple";
    s.style.left = (e.clientX - r.left) + "px";
    s.style.top  = (e.clientY - r.top) + "px";
    s.style.setProperty("--rs", (Math.max(r.width, r.height) * 2.4 / 20).toFixed(1));
    b.appendChild(s);
    setTimeout(function () { if (s.parentNode) s.parentNode.removeChild(s); }, 750);
  }, { capture: true, passive: true, signal: sig });

  /* ------------------------- loading state ------------------------- */
  let busyBtn = null, busyAt = 0, busyTimer = null;
  function running() {
    return !!document.querySelector('[data-testid="stStatusWidget"], [data-testid="stSpinner"]');
  }
  function clearBusy() {
    if (busyBtn && busyBtn.isConnected) { busyBtn.removeAttribute("data-rc-busy"); busyBtn.removeAttribute("aria-busy"); }
    busyBtn = null;
    if (busyTimer) { clearInterval(busyTimer); busyTimer = null; }
  }
  document.addEventListener("click", function (e) {
    const b = e.target && e.target.closest ? e.target.closest(BTN) : null;
    if (!b || b.disabled) return;
    clearBusy();
    b.setAttribute("data-rc-busy", "1");
    b.setAttribute("aria-busy", "true");
    busyBtn = b; busyAt = performance.now();
    busyTimer = setInterval(function () {
      const age = performance.now() - busyAt;
      if (!busyBtn || !busyBtn.isConnected || age > 180000 || (age > 900 && !running())) clearBusy();
    }, 250);
    timers.push(busyTimer);
  }, { capture: true, signal: sig });

  /* ------------------------ header tag steps ------------------------ */
  function startTags() {
    const b = document.querySelector(".rc-description b:not([data-rc-fx])");
    if (!b || b.textContent.indexOf("•") < 0) return;
    b.setAttribute("data-rc-fx", "1");
    const words = b.textContent.split("•").map(function (w) { return w.trim(); }).filter(Boolean);
    b.textContent = "";
    const spans = [];
    words.forEach(function (w, i) {
      if (i) { const sep = document.createElement("span"); sep.className = "rc-sep"; sep.textContent = "/"; b.appendChild(sep); }
      const s = document.createElement("span"); s.className = "rc-tag"; s.textContent = w;
      b.appendChild(s); spans.push(s);
    });
    let idx = 0;
    const step = function () {
      if (!b.isConnected) return false;
      spans.forEach(function (s, i) { s.classList.toggle("on", i === idx); });
      idx = (idx + 1) % spans.length;
      return true;
    };
    step();
    const tm = setInterval(function () { if (!step()) clearInterval(tm); }, 1500);
    timers.push(tm);
  }

  /* ------------------ title spotlight: light follows the mouse ------------------ */
  let spotX = 0, spotY = 0, spotRaf = 0;
  function moveSpot() {
    spotRaf = 0;
    const t = document.querySelector(".rc-header .rc-title");
    if (!t) return;
    const r = t.getBoundingClientRect();
    t.style.setProperty("--mx", (spotX - r.left) + "px");
    t.style.setProperty("--my", (spotY - r.top) + "px");
  }
  if (!reduceMotion) {
    document.addEventListener("pointermove", function (e) {
      spotX = e.clientX; spotY = e.clientY;
      if (!spotRaf) spotRaf = requestAnimationFrame(moveSpot);
    }, { passive: true, signal: sig });
    document.documentElement.addEventListener("pointerleave", function () {
      const t = document.querySelector(".rc-header .rc-title");
      if (t) { t.style.setProperty("--mx", "-400px"); t.style.setProperty("--my", "-400px"); }
    }, { signal: sig });
  }

  /* ------------------------ tabs: sliding indicator ------------------------ */
  const tabSeen = new WeakSet();
  const tabRO = window.ResizeObserver ? new ResizeObserver(function () { updateTabs(true); }) : null;
  function updateTabs(fromResize) {
    const groups = document.querySelectorAll('div[role="radiogroup"]');
    for (let gi = 0; gi < groups.length; gi++) {
      const g = groups[gi];
      const labels = g.querySelectorAll(":scope > label");
      let on = null;
      for (let i = 0; i < labels.length; i++) {
        const inp = labels[i].querySelector("input");
        if (tabRO && !tabSeen.has(labels[i])) { tabSeen.add(labels[i]); tabRO.observe(labels[i]); }
        if (inp && inp.checked) on = labels[i];
      }
      if (tabRO && !tabSeen.has(g)) { tabSeen.add(g); tabRO.observe(g); }
      if (!on || !on.offsetWidth) continue;
      const x = on.offsetLeft + "px", y = on.offsetTop + "px";
      const w = on.offsetWidth + "px", h = on.offsetHeight + "px";
      if (g.style.getPropertyValue("--ti-x") === x && g.style.getPropertyValue("--ti-y") === y &&
          g.style.getPropertyValue("--ti-w") === w && g.style.getPropertyValue("--ti-h") === h) continue;
      const first = !g.hasAttribute("data-rc-tabs");
      g.style.setProperty("--ti-x", x);
      g.style.setProperty("--ti-y", y);
      g.style.setProperty("--ti-w", w);
      g.style.setProperty("--ti-h", h);
      if (first) {
        g.setAttribute("data-rc-tabs", "1");
        requestAnimationFrame(function () {
          requestAnimationFrame(function () { g.setAttribute("data-rc-tabs-ready", "1"); });
        });
      } else if (!fromResize) {
        g.classList.remove("rc-pulse");
        void g.offsetWidth;
        g.classList.add("rc-pulse");
        setTimeout(function () { g.classList.remove("rc-pulse"); }, 750);
      }
    }
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { updateTabs(true); });

  /* ------------------ background layer: find + tag it ------------------ */
  /* The 3D background is a full-screen fixed canvas/iframe. It is found by what it
     is (fixed, covers the screen) rather than by id, then tagged so CSS can blur it. */
  function tagBackground() {
    if (document.querySelector("[data-rc-bg]")) return;
    const els = document.querySelectorAll("canvas, iframe");
    const vw = window.innerWidth, vh = window.innerHeight;
    for (let i = 0; i < els.length; i++) {
      const el = els[i];
      const cs = getComputedStyle(el);
      if (cs.position !== "fixed" && cs.position !== "absolute") continue;
      const r = el.getBoundingClientRect();
      if (r.width >= vw * 0.9 && r.height >= vh * 0.9) { el.setAttribute("data-rc-bg", "1"); return; }
    }
  }

  /* ------------------------ text-size control ------------------------ */
  const SIZES = [
    { k: "S",  v: 0.9,  t: "Smaller text" },
    { k: "M",  v: 1,    t: "Default text size" },
    { k: "L",  v: 1.15, t: "Larger text" },
    { k: "XL", v: 1.3,  t: "Largest text" }
  ];
  function buildSizeControl() {
    if (document.getElementById("rc-size")) return;
    let saved = 1;
    try { saved = parseFloat(localStorage.getItem("rc-boost")) || 1; } catch (e) {}
    const box = document.createElement("div");
    box.id = "rc-size";
    box.setAttribute("role", "group");
    box.setAttribute("aria-label", "Text size");
    const lab = document.createElement("span");
    lab.textContent = "Aa";
    box.appendChild(lab);
    const btns = [];
    function apply(v) {
      document.documentElement.style.setProperty("--rc-boost", String(v));
      try { localStorage.setItem("rc-boost", String(v)); } catch (e) {}
      btns.forEach(function (b) { b.setAttribute("aria-pressed", String(parseFloat(b.dataset.v) === v)); });
    }
    SIZES.forEach(function (o) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = o.k;
      b.title = o.t;
      b.setAttribute("aria-label", o.t);
      b.dataset.v = String(o.v);
      b.addEventListener("click", function () { apply(o.v); });
      box.appendChild(b);
      btns.push(b);
    });
    document.body.appendChild(box);
    apply(SIZES.some(function (o) { return o.v === saved; }) ? saved : 1);
  }

  /* ------------------------ metrics: count-up ------------------------ */
  function firstTextNode(el) {
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
    let n;
    while ((n = w.nextNode())) { if (n.nodeValue.trim()) return n; }
    return null;
  }
  function animateMetric(el) {
    if (el.__rcBusy) return;                       // ignore our own text writes while animating
    const node = firstTextNode(el);
    if (!node) return;
    const orig = node.nodeValue;
    const txt = orig.trim();
    if (el.__rcLast === txt) return;
    el.__rcLast = txt;
    const m = /^(-?\\d+(?:\\.\\d+)?)(.*)$/.exec(txt);
    if (!m) return;                                // words (HIGH, MODERATE) just appear
    el.__rcBusy = true;
    let lastWritten = null;
    const target = parseFloat(m[1]), suffix = m[2];
    const dec = (m[1].split(".")[1] || "").length;
    const t0 = performance.now(), dur = 900;
    (function step(now) {
      if (!node.isConnected || (lastWritten !== null && node.nodeValue !== lastWritten)) {
        el.__rcLast = null; el.__rcBusy = false; return;     // someone else changed it: re-run next scan
      }
      const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      lastWritten = (p >= 1) ? orig : (target * e).toFixed(dec) + suffix;
      node.nodeValue = lastWritten;
      if (p < 1) requestAnimationFrame(step); else el.__rcBusy = false;
    })(t0);
  }

  /* ------------------------ alerts + toasts ------------------------ */
  let toastBox = null;
  const TOAST = {
    info:    { c: "#4cc9ff", bg: "rgba(76,201,255,.14)",  ic: "i" },
    danger:  { c: "#ff5d73", bg: "rgba(255,93,115,.14)",  ic: "!" },
    success: { c: "#00e59f", bg: "rgba(0,229,159,.14)",   ic: "✓" }
  };
  function toast(kind, title, msg) {
    if (!toastBox || !toastBox.isConnected) {
      toastBox = document.getElementById("rc-toasts");
      if (!toastBox) { toastBox = document.createElement("div"); toastBox.id = "rc-toasts"; document.body.appendChild(toastBox); }
    }
    const K = TOAST[kind];
    const t = document.createElement("div");
    t.className = "rc-toast";
    t.setAttribute("role", "status");
    t.style.setProperty("--tc", K.c);
    t.style.setProperty("--tb", K.bg);
    const ic = document.createElement("div"); ic.className = "ic"; ic.textContent = K.ic;
    const box = document.createElement("div");
    const tt = document.createElement("div"); tt.className = "tt"; tt.textContent = title;
    const tm = document.createElement("div"); tm.className = "tm"; tm.textContent = msg;
    box.appendChild(tt); box.appendChild(tm);
    const bar = document.createElement("div"); bar.className = "bar";
    t.appendChild(ic); t.appendChild(box); t.appendChild(bar);
    toastBox.appendChild(t);
    const kill = function () { t.classList.add("out"); setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 320); };
    t.addEventListener("click", kill);
    setTimeout(kill, 4400);
  }

  let lastState = 0, lastResult = 0;
  function scanAlerts() {
    let fake = false, real = false;
    const al = document.querySelectorAll('[data-testid="stAlert"]');
    for (let i = 0; i < al.length; i++) {
      /* Only look at the START of the alert, so explanatory paragraphs such as
         "The AI model detected patterns associated with AI-generated ..." do not
         get a verdict chip of their own. */
      const head = (al[i].textContent || "").toUpperCase().slice(0, 32);
      let kind = "";
      if (head.indexOf("AI-GENERATED") >= 0 || head.indexOf("LIKELY AI") >= 0) { kind = "fake"; fake = true; }
      else if (head.indexOf("LIKELY REAL") >= 0) { kind = "real"; real = true; }
      if (kind) { if (al[i].getAttribute("data-rc-kind") !== kind) al[i].setAttribute("data-rc-kind", kind); }
      else if (al[i].hasAttribute("data-rc-kind")) al[i].removeAttribute("data-rc-kind");
    }
    const spinning = !!document.querySelector('[data-testid="stSpinner"]');
    const state = spinning ? 1 : (fake ? 2 : (real ? 3 : 0));
    if (state === lastState) return;
    if (state === 0) lastResult = 0;
    if (state === 1 && lastState === 0) toast("info", "Analysis started", "Scanning the media for signs of manipulation.");
    if ((state === 2 || state === 3) && state !== lastResult) {
      lastResult = state;
      if (state === 2) toast("danger", "Analysis complete", "Likely AI-generated or manipulated. Review the evidence below.");
      else toast("success", "Analysis complete", "Likely authentic. No manipulation flagged; review the evidence below.");
    }
    lastState = state;
  }

  /* ----------------------------- scan loop ----------------------------- */
  function scan() {
    const bs = document.querySelectorAll(BTN);
    for (let i = 0; i < bs.length; i++) classify(bs[i]);
    startTags();
    buildSizeControl();
    tagBackground();
    updateTabs(false);
    const mv = document.querySelectorAll('[data-testid="stMetricValue"]');
    for (let i = 0; i < mv.length; i++) animateMetric(mv[i]);
    scanAlerts();
  }
  let queued = false;
  const obs = new MutationObserver(function () {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; scan(); });
  });
  obs.observe(document.body, { childList: true, subtree: true, characterData: true });
  scan();

  window.__rcFxCleanup = function () {
    ac.abort();
    obs.disconnect();
    if (tabRO) tabRO.disconnect();
    timers.forEach(function (t) { clearInterval(t); });
  };
}

/* =====================================================================
   Launcher
   ===================================================================== */
(function () {
  let doc = document;
  try { if (window.parent && window.parent !== window && window.parent.document) doc = window.parent.document; } catch (e) {}

  try {
    let st = doc.getElementById("rc-fx-style");
    if (!st) { st = doc.createElement("style"); st.id = "rc-fx-style"; doc.head.appendChild(st); }
    st.textContent = RC_FX_CSS;

    /* replace the previous script tag instead of piling up a new one per rerun */
    const old = doc.getElementById("rc-fx-script");
    if (old && old.parentNode) old.parentNode.removeChild(old);
    const s = doc.createElement("script");
    s.id = "rc-fx-script";
    s.textContent = "(" + rcFx.toString() + ")();";
    doc.head.appendChild(s);
  } catch (e) { console.warn("RealCheck UI effects failed:", e); }
})();
</script>
</body>
</html>
"""


def apply_ui_effects():
    """Activate the professional button system and text behaviours."""
    components.html(_UI_HTML, height=0)