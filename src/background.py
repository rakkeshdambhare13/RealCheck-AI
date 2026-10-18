"""
Advanced 3D cyber-forensics background for the RealCheck AI Streamlit app.

Usage (in app.py, once, after st.set_page_config / the CSS block):

    from src.background import render_3d_background
    render_3d_background()

What it draws (all on the GPU, no external libraries, works offline):
  * flowing aurora / nebula (domain-warped fractal noise) + twinkling stars
  * neon perspective grid floor rushing toward you, with horizon glow
  * shader-based falling code rain
  * a holographic AI-shield globe: lat/long mesh, glowing nodes, three
    gyroscope rings with comets, a red/cyan scan beam, pulsing red threat
    nodes and attack arcs with travelling data packets
  * 1400 depth-parallax particles, shooting stars, orbiting wireframe cubes
  * REACTS TO THE APP: analyzing -> amber warp speed, fake result -> red alert,
    likely-real result -> green shield (detected from Streamlit's own spinner
    and alert boxes), with a live status label
  * click shockwaves, scroll depth, mouse parallax, vignette, dithering,
    adaptive resolution for slow GPUs

How it is wired into Streamlit
------------------------------
Streamlit does not run <script> tags in st.markdown / st.html, so a tiny
components.html iframe is used only as a launcher. Its script reaches into
the MAIN page (window.parent) and draws the animation on a full-screen,
click-through canvas behind the app content. Nothing depends on the iframe
being visible. If the main page cannot be reached, it falls back to running
inside the iframe, which is then pinned to the whole window.
"""

import streamlit.components.v1 as components


_BACKGROUND_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  :root { color-scheme: normal; }
  html, body { margin: 0; padding: 0; background: transparent; }
</style>
</head>
<body>
<script>
/* =====================================================================
   rcMain: the whole animation. It is serialized and injected into the
   main Streamlit page, so it may only use window / document.
   ===================================================================== */
function rcMain() {
  // Set to true to freeze the animation when the OS "reduce motion" setting is on.
  const RESPECT_REDUCED_MOTION = false;
  const SHOW_STATUS_HUD = true;       // small live status label in the bottom-right corner
  const REACT_TO_APP    = true;       // background changes color/speed with the analysis state
  const reduce = RESPECT_REDUCED_MOTION && matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Replace any previous copy (Streamlit reruns) and stop its loop
  const old = document.getElementById("rc-bg-root");
  if (old) old.remove();
  window.__rcBgGen = (window.__rcBgGen || 0) + 1;
  const gen = window.__rcBgGen;
  const alive = () => gen === window.__rcBgGen;
  window.__rcBgFrames = 0;

  const root = document.createElement("div");
  root.id = "rc-bg-root";
  root.setAttribute("aria-hidden", "true");
  root.style.cssText =
    "position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;" +
    "pointer-events:none;overflow:hidden;" +
    "background:radial-gradient(ellipse at 50% 30%,#0b1a45 0%,#050816 60%,#02030a 100%);";
  const canvas = document.createElement("canvas");
  canvas.style.cssText = "position:absolute;top:0;left:0;width:100%;height:100%;display:block;";
  root.appendChild(canvas);
  document.body.appendChild(root);

  // Small status badge: shows briefly when running, stays visible on errors
  function badge(msg, ok, ttl) {
    let b = document.getElementById("rc-bg-badge");
    if (!b) {
      b = document.createElement("div");
      b.id = "rc-bg-badge";
      b.style.cssText = "position:fixed;left:14px;bottom:12px;z-index:2147483000;pointer-events:none;" +
        "font:600 11px/1 ui-monospace,Consolas,monospace;letter-spacing:.08em;padding:7px 10px;" +
        "border-radius:8px;background:rgba(2,8,24,.85);transition:opacity .8s;";
      document.body.appendChild(b);
    }
    b.style.opacity = "1";
    b.style.color = ok ? "#00ffb0" : "#ff6b81";
    b.style.border = "1px solid " + (ok ? "rgba(0,255,176,.45)" : "rgba(255,107,129,.65)");
    b.textContent = msg;
    if (ttl) setTimeout(function () { b.style.opacity = "0"; }, ttl);
  }

  const gl = canvas.getContext("webgl", { antialias: true, alpha: false, powerPreference: "high-performance" })
          || canvas.getContext("experimental-webgl");
  if (!gl) { console.warn("RealCheck background: WebGL not available"); badge("3D BACKGROUND OFF: WebGL is not available in this browser", false); return; }

  /* ------------------------- shader helpers ------------------------- */
  function sh(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.warn("RealCheck shader error:", gl.getShaderInfoLog(s));
      badge("3D BACKGROUND ERROR: shader failed (see console)", false);
      return null;
    }
    return s;
  }
  function makeProgram(vs, fs, attribs) {
    const v = sh(gl.VERTEX_SHADER, vs), f = sh(gl.FRAGMENT_SHADER, fs);
    if (!v || !f) return null;
    const p = gl.createProgram();
    gl.attachShader(p, v); gl.attachShader(p, f);
    attribs.forEach((a, i) => gl.bindAttribLocation(p, i, a));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      console.warn("RealCheck link error:", gl.getProgramInfoLog(p));
      return null;
    }
    const cache = {};
    return { p: p, u: function (n) { return n in cache ? cache[n] : (cache[n] = gl.getUniformLocation(p, n)); } };
  }
  function makeBuffer(arr) {
    const b = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(arr), gl.STATIC_DRAW);
    return b;
  }
  function bindAttribs(buf, stride, specs) {
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    specs.forEach(function (s) {
      gl.enableVertexAttribArray(s[0]);
      gl.vertexAttribPointer(s[0], s[1], gl.FLOAT, false, stride, s[2]);
    });
  }
  function unbindAttribs(n) { for (let i = 0; i < n; i++) gl.disableVertexAttribArray(i); }

  const PREC = `
    #ifdef GL_FRAGMENT_PRECISION_HIGH
    precision highp float;
    #else
    precision mediump float;
    #endif
  `;

  /* ===================== PASS A: sky + grid + rain ===================== */
  const QUAD_VS = `attribute vec2 aP; void main(){ gl_Position = vec4(aP, 0., 1.); }`;

  const BG_FS = PREC + `
    uniform vec2 uRes; uniform float uTime; uniform float uFlow; uniform vec2 uMouse; uniform vec4 uGlobe;
    uniform vec3 uTint; uniform vec4 uRip; uniform vec3 uRipCol; uniform float uScroll; uniform float uFlash;

    float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
    float noise(vec2 p){
      vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
      float a = hash(i), b = hash(i + vec2(1., 0.)), c = hash(i + vec2(0., 1.)), d = hash(i + vec2(1., 1.));
      return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
    }
    float fbm(vec2 p){
      float v = 0., a = .5;
      for (int i = 0; i < 5; i++) { v += a * noise(p); p = p * 2.03 + vec2(17., 9.); a *= .5; }
      return v;
    }

    void main(){
      vec2 frag = gl_FragCoord.xy;
      vec2 uv = frag / uRes;
      vec2 p = (frag - .5 * uRes) / uRes.y;
      float t = uTime;
      float horizon = -.16 + uMouse.y * .015 + uScroll * .05;

      // base sky
      vec3 col = mix(vec3(.012, .016, .05), vec3(.035, .02, .11), smoothstep(-.5, .5, p.y));

      // nebula (domain-warped fbm)
      vec2 q = p * 1.6 + vec2(uMouse.x * .06, uMouse.y * .03);
      vec2 w = vec2(fbm(q * 1.5 + vec2(t * .04, 0.)), fbm(q * 1.5 + vec2(5.2, 1.3 - t * .03)));
      float n = fbm(q * 2. + 2.2 * w + t * .03);
      vec3 neb = mix(vec3(0., .75, 1.), vec3(.62, .2, 1.), smoothstep(.25, .75, n + .35 * w.x + p.x * .25));
      neb = mix(neb, vec3(1., .15, .5), smoothstep(.7, 1., w.y) * .35);
      neb = mix(neb, uTint, .22);
      float sky = smoothstep(horizon - .05, .45, p.y);
      col += neb * pow(n, 2.6) * .55 * (.25 + .75 * sky);

      // aurora curtains
      float cur = fbm(vec2(p.x * 3. + t * .05, t * .1));
      float aur = smoothstep(.35, .9, cur) * exp(-abs(p.y - .27 - .13 * sin(p.x * 3. + t * .3)) * 5.5);
      col += mix(vec3(0., 1., .75), vec3(.3, .5, 1.), uv.x) * aur * .32 * sky;

      // stars
      vec2 sp = frag / (uRes.y * .012);
      vec2 si = floor(sp);
      float sh = hash(si);
      float star = step(.986, sh) * smoothstep(.36, 0., length(fract(sp) - .5));
      float tw = .6 + .4 * sin(t * 2. + sh * 40.);
      col += vec3(.8, .9, 1.) * star * tw * smoothstep(horizon, .3, p.y);

      // code rain (shader based)
      {
        float cs = 20.;
        vec2 grd = vec2(floor(uRes.x / cs), floor(uRes.y / cs));
        vec2 gp = uv * grd;
        vec2 cell = floor(gp);
        vec2 f = fract(gp);
        float cseed = hash(vec2(cell.x, 3.7));
        float spd = .18 + cseed * .5;
        float head = fract(cseed * 9. - uFlow * spd);
        float trail = fract(uv.y - head);
        float len = .25 + hash(vec2(cell.x, 8.1)) * .5;
        float inten = clamp(1. - trail / len, 0., 1.);
        inten = inten * inten;
        vec2 gcell = floor(f * vec2(3., 5.));
        float on = step(.42, hash(cell * 7.7 + gcell + floor(t * (2. + cseed * 4.))));
        float mask = step(.18, f.x) * step(f.x, .82) * step(.12, f.y) * step(f.y, .88);
        float colOn = step(.55, hash(vec2(cell.x, 2.2)));
        vec3 rc = mix(vec3(0., .8, 1.), vec3(.9, 1., 1.), smoothstep(.12, 0., trail / len));
        float rmask = smoothstep(horizon - .08, horizon + .3, p.y);
        col += rc * inten * on * mask * colOn * rmask * .55;
      }

      // shooting stars
      for (int k = 0; k < 2; k++) {
        float fk = float(k);
        float per = 5.5 + fk * 2.3;
        float sid = floor(t / per + fk * .37);
        float lt = fract(t / per + fk * .37);
        vec2 s0 = vec2(hash(vec2(sid, fk + 1.)) * 1.6 - .8, .12 + hash(vec2(sid, fk + 7.)) * .4);
        vec2 dir = normalize(vec2(-.8, -.5 - hash(vec2(sid, fk + 3.)) * .3));
        float life = smoothstep(0., .02, lt) * (1. - smoothstep(.12, .2, lt));
        vec2 hd = s0 + dir * lt * 5.;
        vec2 ta = hd - dir * .26;
        vec2 pa = p - ta, ba = hd - ta;
        float hh = clamp(dot(pa, ba) / dot(ba, ba), 0., 1.);
        float dd = length(pa - ba * hh);
        col += vec3(.8, .95, 1.) * exp(-dd * dd * 9000.) * hh * hh * life * smoothstep(horizon, horizon + .2, p.y);
      }

      // neon grid floor
      if (p.y < horizon) {
        float dy = horizon - p.y;
        float z = .42 / dy;
        float x = (p.x - uMouse.x * .05) * z;
        vec2 g = vec2(x, z + uFlow * 2.2);
        vec2 aa = vec2(z, z * z / .42) / uRes.y * 1.6;
        vec2 d = abs(fract(g) - .5);
        vec2 ln = 1. - smoothstep(vec2(0.), aa + vec2(.035), .5 - d);
        float line = max(ln.x, ln.y);
        float fade = exp(-z * .07);
        vec3 gc = mix(vec3(0., .9, 1.), vec3(.75, .25, 1.), smoothstep(2., 14., z));
        gc = mix(gc, uTint, .32);
        col += gc * line * fade * 1.1;
        col += vec3(0., .25, .5) * exp(-dy * 5.) * .25;
      }
      float hg = exp(-abs(p.y - horizon) * 14.);
      col += mix(vec3(0., .55, 1.), uTint, .6) * hg * .5 * (.6 + .4 * sin(t * .7));

      // globe halo + solid hologram body (so the wireframe pops)
      vec2 gcen = uGlobe.xy;
      float gr = uGlobe.z;
      float dg = length(p - gcen);
      col += uTint * .75 * exp(-max(dg - gr, 0.) * 7.) * .32;
      float inside = 1. - smoothstep(gr * .985, gr, dg);
      col = mix(col, vec3(.008, .03, .085), inside * .82);
      col += uTint * .7 * pow(clamp(dg / gr, 0., 1.), 6.) * inside * .55;
      // holographic energy inside the globe
      col += uTint * inside * (.035 * sin(p.y * 380. - t * 2.5) + .10 * pow(fbm(p * 5. + vec2(0., t * .25)), 3.));
      float rim = smoothstep(gr * .975, gr, dg) * (1. - smoothstep(gr, gr * 1.025, dg));
      col += mix(uTint, vec3(1.), .35) * rim * .9;

      // shockwave ripple (click / state change) + flash
      float ra = uTime - uRip.z;
      if (ra > 0. && ra < 3.) {
        float dd2 = length(p - uRip.xy);
        float ring = exp(-pow((dd2 - ra * 1.0) * 16., 2.));
        col += uRipCol * ring * uRip.w * exp(-ra * 1.4) * .7;
        col += uRipCol * uRip.w * exp(-ra * 6.) * exp(-dd2 * 4.) * .25;
      }
      col += uTint * uFlash * .12 * clamp(1. - dot(p, p), 0., 1.);

      // sweeping scan band across the whole screen
      float sweep = exp(-pow((uv.y - fract(t * .09)) * 40., 2.));
      col += vec3(0., .5, .8) * sweep * .06;

      // vignette, scanlines, soft tone map, dither
      col *= 1. - dot(p, p) * .5;
      col *= .965 + .035 * sin(frag.y * 1.6);
      col = col / (1. + col * .3);
      col += (hash(frag + t) - .5) / 255.;
      gl_FragColor = vec4(col, 1.);
    }
  `;

  /* ========================= PASS B: particles ========================= */
  const PART_VS = `
    attribute vec4 aSeed;
    uniform float uTime; uniform float uFlow; uniform vec2 uRes; uniform vec2 uMouse;
    varying vec3 vCol; varying float vA;
    void main(){
      float t = uTime;
      float depth = fract(aSeed.z + uFlow * (.035 + aSeed.w * .05));
      float z = mix(-6., 2.2, depth);
      vec3 pos;
      pos.x = (aSeed.x * 2. - 1.) * 7. + sin(t * .3 + aSeed.w * 30.) * .25;
      pos.y = (aSeed.y * 2. - 1.) * 4. + sin(t * .4 + aSeed.x * 20.) * .3;
      float dz = 4.2 - z;
      vec2 s = pos.xy / dz * 1.2 + uMouse * .05 * depth;
      gl_Position = vec4(s.x * uRes.y / uRes.x * 2., s.y * 2., 0., 1.);
      gl_PointSize = (1.4 + aSeed.w * 3.6) * (uRes.y / 800.) * (3.2 / dz) * 2.;
      float tw = .55 + .45 * sin(t * 3. + aSeed.w * 60.);
      vA = smoothstep(0., .12, depth) * smoothstep(1., .85, depth) * tw;
      vec3 c = vec3(0., .9, 1.);
      if (aSeed.w > .55) c = vec3(.62, .35, 1.);
      if (aSeed.w > .85) c = vec3(.9, 1., 1.);
      if (aSeed.w > .96) c = vec3(1., .25, .45);
      vCol = c;
    }
  `;
  const PART_FS = PREC + `
    varying vec3 vCol; varying float vA;
    void main(){
      float d = length(gl_PointCoord - .5);
      float a = smoothstep(.5, 0., d); a *= a;
      gl_FragColor = vec4(vCol * a * vA * 1.4, 1.);
    }
  `;

  /* ===================== PASS C/D: globe lines + nodes ===================== */
  const GLOBE_COMMON = `
    uniform vec2 uRes; uniform float uTime; uniform float uFlow; uniform vec2 uRot; uniform vec4 uGlobe; uniform vec2 uScan;
    uniform vec3 uTint; uniform vec2 uOff; uniform float uGain;
    varying vec3 vC;
    mat3 rotX(float a){ float c = cos(a), s = sin(a); return mat3(1., 0., 0., 0., c, s, 0., -s, c); }
    mat3 rotY(float a){ float c = cos(a), s = sin(a); return mat3(c, 0., -s, 0., 1., 0., s, 0., c); }
    mat3 rotZ(float a){ float c = cos(a), s = sin(a); return mat3(c, s, 0., -s, c, 0., 0., 0., 1.); }
    vec4 project(vec3 v){
      vec2 sp = (v.xy / (4. - v.z)) * 1.2 * uGlobe.w + uGlobe.xy;
      return vec4(sp.x * uRes.y / uRes.x * 2. + uOff.x * 2. / uRes.x, sp.y * 2. + uOff.y * 2. / uRes.y, 0., 1.);
    }
    vec4 projectFree(vec3 v){
      vec2 sp = (v.xy / (4. - v.z)) * 1.2;
      return vec4(sp.x * uRes.y / uRes.x * 2. + uOff.x * 2. / uRes.x, sp.y * 2. + uOff.y * 2. / uRes.y, 0., 1.);
    }
  `;

  const LINE_VS = `
    attribute vec3 aPos; attribute vec4 aInfo;
  ` + GLOBE_COMMON + `
    void main(){
      float kind = aInfo.x;
      vec3 v = aPos;
      vec3 col = vec3(0.);
      float t = uTime;
      if (kind < .5) {
        // lat/long mesh
        v = rotX(uRot.y) * (rotY(uRot.x) * v);
        float front = smoothstep(-1., 1., v.z);
        col = uTint * (.10 + .30 * front);
        float sc = exp(-pow((v.y - uScan.x) * 8., 2.));
        vec3 sc3 = mix(vec3(.3, 1., 1.), vec3(1., .2, .35), uScan.y);
        col += sc3 * sc * (.35 + .65 * front);
      } else if (kind < 1.5) {
        // gyroscope rings with comets
        float id = aInfo.w;
        float dir = mod(id, 2.) > .5 ? -1. : 1.;
        v = rotY(t * .25 * (1. + id * .35) * dir) * v;
        v = rotZ(id * .9 - .5 + .18 * sin(t * .35 + id)) * v;
        v = rotX(.9 + id * .45 + uRot.y) * v;
        vec3 base = id < .5 ? vec3(0., .9, 1.) : (id < 1.5 ? vec3(.62, .25, 1.) : vec3(0., 1., .7));
        base = mix(base, uTint, .35);
        float head = fract(t * (.10 + .03 * id) * dir + aInfo.z);
        float d = fract((head - aInfo.y) * dir);
        float comet = exp(-d * 16.);
        float front = smoothstep(-1.4, 1.4, v.z);
        col = base * (.16 + .2 * front) + base * comet * 1.6 + vec3(1.) * comet * comet * .6;
      } else if (kind < 2.5) {
        // attack arcs with travelling packets
        v = rotX(uRot.y) * (rotY(uRot.x) * v);
        float head = fract(t * .28 + aInfo.z);
        float d = fract(head - aInfo.y);
        float comet = exp(-d * 9.);
        float front = smoothstep(-1.2, 1., v.z);
        float arc = sin(3.14159 * aInfo.y);
        col = vec3(1., .2, .4) * (.20 + .30 * front) * arc
            + vec3(1., .55, .65) * comet * (.5 + .5 * front) * 2.4 * arc;
      } else {
        // orbiting wireframe data cubes
        float id = aInfo.w;
        float s1 = fract(sin(id * 12.9898) * 43758.5453);
        float s2 = fract(sin(id * 78.233) * 12345.6789);
        float ang = uFlow * .06 * (.5 + s1) + id * 2.4;
        vec3 c = vec3(cos(ang) * (1.7 + s1 * 1.0), (s2 - .5) * 1.8 + sin(t * .5 + id) * .12, sin(ang) * (1.4 + s2 * 1.0) - .5);
        float sc = .10 + .13 * s1;
        v = rotX(t * (.3 + s2)) * (rotY(t * (.4 + s1) + id) * (aPos * sc)) + c;
        float front = smoothstep(-2.5, 1.8, v.z);
        vec3 cc = mix(vec3(0., .9, 1.), vec3(.62, .3, 1.), s1);
        cc = mix(cc, uTint, .3);
        col = cc * (.18 + .55 * front) * (.7 + .3 * sin(t * 1.7 + id * 5.));
      }
      gl_Position = kind > 2.5 ? projectFree(v) : project(v);
      vC = col * uGain;
    }
  `;
  const LINE_FS = PREC + `varying vec3 vC; void main(){ gl_FragColor = vec4(vC, 1.); }`;

  const NODE_VS = `
    attribute vec3 aPos; attribute vec3 aData;
  ` + GLOBE_COMMON + `
    void main(){
      vec3 v = rotX(uRot.y) * (rotY(uRot.x) * aPos);
      float front = smoothstep(-1., 1., v.z);
      float pulse = 1.;
      vec3 col;
      if (aData.x > .5) {
        float s = abs(sin(uTime * 2.6 + aData.y));
        pulse = 1. + .9 * s * s;
        col = vec3(1., .18, .32) * (.5 + .5 * s) * (.45 + .55 * front) * 1.6;
      } else {
        col = vec3(.4, .95, 1.) * (.12 + .5 * front) * (.6 + .4 * sin(uTime * 2. + aData.y * 30.));
      }
      gl_Position = project(v);
      vC = col * uGain;
      gl_PointSize = aData.z * pulse * (uRes.y / 800.) * (4. / (4. - v.z)) * uGlobe.w;
    }
  `;
  const NODE_FS = PREC + `
    varying vec3 vC;
    void main(){
      float d = length(gl_PointCoord - .5);
      float a = smoothstep(.5, 0., d); a *= a;
      gl_FragColor = vec4(vC * a, 1.);
    }
  `;

  const progBG    = makeProgram(QUAD_VS, BG_FS, ["aP"]);
  const progPart  = makeProgram(PART_VS, PART_FS, ["aSeed"]);
  const progLines = makeProgram(LINE_VS, LINE_FS, ["aPos", "aInfo"]);
  const progNodes = makeProgram(NODE_VS, NODE_FS, ["aPos", "aData"]);
  if (!progBG) { console.warn("RealCheck background: shaders failed, using plain fallback"); badge("3D BACKGROUND ERROR: shader failed (see console)", false); return; }

  /* ---------------------------- geometry ---------------------------- */
  const quadBuf = makeBuffer([-1, -1, 1, -1, -1, 1, 1, 1]);

  // particles
  const PN = window.innerWidth < 700 ? 700 : 1400;
  const partData = [];
  for (let i = 0; i < PN; i++) partData.push(Math.random(), Math.random(), Math.random(), Math.random());
  const partBuf = makeBuffer(partData);

  // globe geometry
  function sph(lat, lon) {
    const cl = Math.cos(lat);
    return [cl * Math.sin(lon), Math.sin(lat), cl * Math.cos(lon)];
  }
  const LV = [];                       // x y z | kind t phase id
  function seg(a, b, i1, i2) {
    LV.push(a[0], a[1], a[2], i1[0], i1[1], i1[2], i1[3]);
    LV.push(b[0], b[1], b[2], i2[0], i2[1], i2[2], i2[3]);
  }
  const Z4 = [0, 0, 0, 0];
  for (let la = -75; la <= 75; la += 15) {                        // latitude rings
    const lat = la * Math.PI / 180;
    for (let i = 0; i < 64; i++) {
      seg(sph(lat, i / 64 * 6.2832), sph(lat, (i + 1) / 64 * 6.2832), Z4, Z4);
    }
  }
  for (let k = 0; k < 24; k++) {                                  // meridians
    const lon = k / 24 * 6.2832;
    for (let i = 0; i < 48; i++) {
      seg(sph(-1.5708 + i / 48 * 3.1416, lon), sph(-1.5708 + (i + 1) / 48 * 3.1416, lon), Z4, Z4);
    }
  }
  for (let r = 0; r < 3; r++) {                                   // gyroscope rings
    const rad = 1.32 + 0.22 * r;
    for (let i = 0; i < 128; i++) {
      const a0 = i / 128 * 6.2832, a1 = (i + 1) / 128 * 6.2832;
      seg([Math.cos(a0) * rad, 0, Math.sin(a0) * rad], [Math.cos(a1) * rad, 0, Math.sin(a1) * rad],
          [1, i / 128, r * 0.37, r], [1, (i + 1) / 128, r * 0.37, r]);
    }
  }
  const THREATS = [[0.5, 0.6], [0.1, -0.9], [-0.4, 1.9], [0.7, -2.4], [-0.1, 3.0], [0.3, 2.4], [-0.6, -1.6]];
  const tpos = THREATS.map(function (t) { return sph(t[0], t[1]); });
  for (let i = 0; i < tpos.length; i++) {                         // attack arcs
    const a = tpos[i], b = tpos[(i + 2) % tpos.length];
    const dot = Math.max(-0.999, Math.min(0.999, a[0]*b[0] + a[1]*b[1] + a[2]*b[2]));
    const om = Math.acos(dot), so = Math.sin(om);
    const pt = function (t) {
      const s0 = Math.sin((1 - t) * om) / so, s1 = Math.sin(t * om) / so;
      let v = [s0*a[0] + s1*b[0], s0*a[1] + s1*b[1], s0*a[2] + s1*b[2]];
      const l = Math.hypot(v[0], v[1], v[2]);
      const h = 1 + 0.32 * Math.sin(3.1416 * t);
      return [v[0] / l * h, v[1] / l * h, v[2] / l * h];
    };
    for (let s = 0; s < 40; s++) {
      seg(pt(s / 40), pt((s + 1) / 40), [2, s / 40, i * 0.19, i], [2, (s + 1) / 40, i * 0.19, i]);
    }
  }
  for (let id = 0; id < 10; id++) {                               // orbiting cubes
    const cv = [];
    for (let i = 0; i < 8; i++) cv.push([(i & 1) ? 1 : -1, (i & 2) ? 1 : -1, (i & 4) ? 1 : -1]);
    for (let i = 0; i < 8; i++) for (let b = 0; b < 3; b++) {
      const j = i ^ (1 << b);
      if (j > i) seg(cv[i], cv[j], [3, 0, 0, id], [3, 0, 0, id]);
    }
  }
  const lineBuf = makeBuffer(LV);
  const lineCount = LV.length / 7;

  // globe nodes
  const NV = [];                                                  // x y z | kind phase size
  const NN = 170;
  for (let i = 0; i < NN; i++) {
    const y = 1 - (i + 0.5) / NN * 2, r = Math.sqrt(1 - y * y), phi = i * 2.39996;
    NV.push(Math.cos(phi) * r, y, Math.sin(phi) * r, 0, Math.random(), 1 + Math.random() * 1.3);
  }
  tpos.forEach(function (p, i) { NV.push(p[0], p[1], p[2], 1, i * 0.9, 8.5); });
  const nodeBuf = makeBuffer(NV);
  const nodeCount = NV.length / 6;

  /* ------------------ app state -> background mood ------------------ */
  const MOODS = [
    { tint: [0.00, 0.75, 1.00], speed: 1.0, label: "SYSTEM STANDBY",                       col: "#00eaff" },
    { tint: [1.00, 0.78, 0.25], speed: 3.4, label: "ANALYZING MEDIA...",                   col: "#ffc857" },
    { tint: [1.00, 0.20, 0.32], speed: 1.7, label: "THREAT DETECTED - LIKELY AI-GENERATED", col: "#ff5d73" },
    { tint: [0.10, 1.00, 0.60], speed: 1.2, label: "LIKELY AUTHENTIC",                     col: "#00ffb0" }
  ];
  let moodTarget = 0, flash = 0;
  const tint = MOODS[0].tint.slice();
  const rip = { x: 0, y: 0, t0: -100, str: 0, col: [0, 0.9, 1] };
  const lastG = { x: 0, y: 0.09 };
  let nowSec = 0;

  let hud = null;
  if (SHOW_STATUS_HUD) {
    hud = document.getElementById("rc-bg-hud");
    if (!hud) {
      hud = document.createElement("div");
      hud.id = "rc-bg-hud";
      hud.style.cssText = "position:fixed;right:16px;bottom:12px;z-index:2147483000;pointer-events:none;" +
        "font:600 11px/1 ui-monospace,Consolas,monospace;letter-spacing:.12em;padding:8px 12px;" +
        "border-radius:8px;background:rgba(2,8,24,.82);display:flex;align-items:center;gap:8px;";
      document.body.appendChild(hud);
    }
  }
  function setHud(m) {
    if (!hud) return;
    const c = MOODS[m].col;
    hud.textContent = "";
    const dot = document.createElement("span");
    dot.style.cssText = "width:8px;height:8px;border-radius:50%;display:inline-block;background:" + c + ";box-shadow:0 0 10px " + c + ";";
    const txt = document.createElement("span");
    txt.textContent = MOODS[m].label;
    hud.appendChild(dot); hud.appendChild(txt);
    hud.style.color = c;
    hud.style.border = "1px solid " + c + "66";
  }
  setHud(0);

  function setMood(m) {
    if (m === moodTarget) return;
    moodTarget = m;
    flash = 1;
    rip.x = lastG.x; rip.y = lastG.y; rip.t0 = nowSec; rip.str = 1.6; rip.col = MOODS[m].tint.slice();
    setHud(m);
  }
  function detectMood() {
    if (document.querySelector('[data-testid="stSpinner"]')) return 1;
    let fake = false, real = false;
    const al = document.querySelectorAll('[data-testid="stAlert"]');
    for (let i = 0; i < al.length; i++) {
      const tx = (al[i].textContent || "").toUpperCase();
      if (tx.indexOf("AI-GENERATED") >= 0 || tx.indexOf("LIKELY AI") >= 0) fake = true;
      if (tx.indexOf("LIKELY REAL") >= 0) real = true;
    }
    return fake ? 2 : (real ? 3 : 0);
  }
  if (REACT_TO_APP) {
    let pending = null;
    const obs = new MutationObserver(function () {
      if (!alive()) { obs.disconnect(); return; }
      if (pending) return;
      pending = setTimeout(function () { pending = null; if (alive()) setMood(detectMood()); }, 200);
    });
    obs.observe(document.body, { childList: true, subtree: true, characterData: true });
    setMood(detectMood());
  }

  /* ----------------------------- input ----------------------------- */
  const mouse = { x: 0, y: 0 }, ms = { x: 0, y: 0 };
  window.addEventListener("pointermove", function (e) {
    if (!alive()) return;
    mouse.x = (e.clientX / window.innerWidth - .5) * 2;
    mouse.y = (e.clientY / window.innerHeight - .5) * 2;
  });
  window.addEventListener("pointerdown", function (e) {
    if (!alive()) return;
    rip.x = (e.clientX / window.innerWidth - .5) * (window.innerWidth / window.innerHeight);
    rip.y = -(e.clientY / window.innerHeight - .5);
    rip.t0 = nowSec; rip.str = 1.0; rip.col = [0.0, 0.9, 1.0];
  }, true);
  let scrollT = 0, scrollS = 0;
  window.addEventListener("scroll", function (e) {
    if (!alive()) return;
    const el = e.target;
    const y = (el === document || el === document.documentElement) ? window.scrollY : (el.scrollTop || 0);
    scrollT = Math.max(0, Math.min(1, y / 1600));
  }, true);

  /* ---------------------- sizing + adaptive quality ---------------------- */
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  let scale = 1, cw = 2, ch = 2;
  function resize() {
    if (!alive()) return;
    cw = Math.max(2, Math.floor(window.innerWidth * dpr * scale));
    ch = Math.max(2, Math.floor(window.innerHeight * dpr * scale));
    canvas.width = cw; canvas.height = ch;
    gl.viewport(0, 0, cw, ch);
    if (reduce) draw(6, 6, 6);
  }
  window.addEventListener("resize", resize);

  /* ------------------------------ draw ------------------------------ */
  function draw(t, flow, scanT) {
    const aspect = cw / ch;
    const gs = Math.min(1, aspect / 1.15) * (1 - scrollS * 0.18);   // keep globe on narrow screens
    const rSil = 1.2 / Math.sqrt(15) * gs;
    const gx = ms.x * 0.012, gy = 0.09 - ms.y * 0.01 + scrollS * 0.12;
    lastG.x = gx; lastG.y = gy;
    const my = -ms.y;
    const rotX = flow * 0.28 + scrollS * 1.5, tilt = 0.38 + Math.sin(t * 0.2) * 0.08 + my * 0.05;
    const scanY = Math.sin(scanT) * 0.95, scanDown = Math.cos(scanT) < 0 ? 1 : 0;
    const pxs = cw / window.innerWidth;

    gl.disable(gl.BLEND);
    gl.useProgram(progBG.p);
    gl.uniform2f(progBG.u("uRes"), cw, ch);
    gl.uniform1f(progBG.u("uTime"), t);
    gl.uniform1f(progBG.u("uFlow"), flow);
    gl.uniform2f(progBG.u("uMouse"), ms.x, my);
    gl.uniform4f(progBG.u("uGlobe"), gx, gy, rSil, gs);
    gl.uniform3f(progBG.u("uTint"), tint[0], tint[1], tint[2]);
    gl.uniform4f(progBG.u("uRip"), rip.x, rip.y, rip.t0, rip.str);
    gl.uniform3f(progBG.u("uRipCol"), rip.col[0], rip.col[1], rip.col[2]);
    gl.uniform1f(progBG.u("uScroll"), scrollS);
    gl.uniform1f(progBG.u("uFlash"), flash);
    bindAttribs(quadBuf, 8, [[0, 2, 0]]);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    unbindAttribs(2);

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE);

    if (progPart) {
      gl.useProgram(progPart.p);
      gl.uniform2f(progPart.u("uRes"), cw, ch);
      gl.uniform1f(progPart.u("uTime"), t);
      gl.uniform1f(progPart.u("uFlow"), flow);
      gl.uniform2f(progPart.u("uMouse"), ms.x, my);
      bindAttribs(partBuf, 16, [[0, 4, 0]]);
      gl.drawArrays(gl.POINTS, 0, PN);
      unbindAttribs(2);
    }
    function globeUniforms(P) {
      gl.uniform2f(P.u("uRes"), cw, ch);
      gl.uniform1f(P.u("uTime"), t);
      gl.uniform2f(P.u("uRot"), rotX, tilt);
      gl.uniform4f(P.u("uGlobe"), gx, gy, rSil, gs);
      gl.uniform2f(P.u("uScan"), scanY, scanDown);
      gl.uniform1f(P.u("uFlow"), flow);
      gl.uniform3f(P.u("uTint"), tint[0], tint[1], tint[2]);
    }
    if (progLines) {
      gl.useProgram(progLines.p);
      globeUniforms(progLines);
      gl.uniform1f(progLines.u("uGain"), 0.62);
      bindAttribs(lineBuf, 28, [[0, 3, 0], [1, 4, 12]]);
      const OFFS = [[0, 0], [1, 0], [0, 1]];                    // 3 slightly shifted passes = thicker, glowier lines
      for (let k = 0; k < OFFS.length; k++) {
        gl.uniform2f(progLines.u("uOff"), OFFS[k][0] * pxs, OFFS[k][1] * pxs);
        gl.drawArrays(gl.LINES, 0, lineCount);
      }
      unbindAttribs(2);
    }
    if (progNodes) {
      gl.useProgram(progNodes.p);
      globeUniforms(progNodes);
      gl.uniform1f(progNodes.u("uGain"), 1.0);
      gl.uniform2f(progNodes.u("uOff"), 0, 0);
      bindAttribs(nodeBuf, 24, [[0, 3, 0], [1, 3, 12]]);
      gl.drawArrays(gl.POINTS, 0, nodeCount);
      unbindAttribs(2);
    }
  }

  /* ------------------------------ loop ------------------------------ */
  const t0 = performance.now();
  let last = t0, slow = 0, ema = 16, shown = false, flow = 0, scanT = 0;
  let speedCur = 1;
  resize();

  function tick(now) {
    if (!alive()) return;
    const dt = now - last; last = now;
    const dts = Math.min(dt, 100) / 1000;
    ms.x += (mouse.x - ms.x) * 0.05;
    ms.y += (mouse.y - ms.y) * 0.05;
    scrollS += (scrollT - scrollS) * 0.06;

    // ease toward the current mood (color + speed)
    const M = MOODS[moodTarget];
    for (let i = 0; i < 3; i++) tint[i] += (M.tint[i] - tint[i]) * 0.06;
    speedCur += (M.speed - speedCur) * 0.05;
    flow  += dts * speedCur;
    scanT += dts * 1.3 * (1 + (speedCur - 1) * 0.6);
    flash *= 0.94;

    nowSec = (now - t0) / 1000;
    draw(nowSec, flow, scanT);
    window.__rcBgFrames++;
    if (!shown && now - t0 > 2000) {
      shown = true;
      badge("3D BACKGROUND RUNNING - " + Math.round(window.__rcBgFrames / ((now - t0) / 1000)) + " FPS", true, 6000);
    }

    // adaptive quality: lower internal resolution on slow GPUs
    ema = ema * 0.95 + Math.min(dt, 100) * 0.05;
    if (ema > 30 && scale > 0.55) {
      if (++slow > 45) { scale *= 0.85; slow = 0; ema = 16; resize(); }
    } else { slow = 0; }

    window.requestAnimationFrame(tick);
  }
  if (!reduce) window.requestAnimationFrame(tick); else { draw(6, 6, 6); badge("3D BACKGROUND STATIC (reduced motion)", false, 6000); }
}

/* =====================================================================
   Launcher: run rcMain() in the MAIN page (or in the iframe as fallback).
   ===================================================================== */
(function () {
  let host = window, inParent = false;
  try {
    if (window.parent && window.parent !== window && window.parent.document) {
      host = window.parent; inParent = true;
    }
  } catch (e) { host = window; inParent = false; }

  if (!inParent) {
    try {
      const f = window.frameElement;
      if (f) f.style.cssText =
        "position:fixed;top:0;left:0;width:100vw;height:100vh;border:0;" +
        "z-index:1;pointer-events:none;background:transparent;color-scheme:normal;";
    } catch (e) {}
  }

  try {
    const s = host.document.createElement("script");
    s.textContent = "(" + rcMain.toString() + ")();";
    host.document.head.appendChild(s);
  } catch (e) { console.warn("RealCheck background failed:", e); }
})();
</script>
</body>
</html>
"""


def render_3d_background():
    """Render the fullscreen 3D animated background behind the Streamlit app."""
    components.html(_BACKGROUND_HTML, height=0)