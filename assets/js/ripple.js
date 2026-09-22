/* ---------------------------------------------------------------------------
 * Interactive damped wave field.
 *
 *   d2h/dt2 = c^2 * laplacian(h) - gamma * dh/dt
 *
 * Discretised on a uniform grid with the standard second-order leapfrog stencil
 *
 *   h[n+1] = (2h[n] - h[n-1] + C2 * lap(h[n])) * damping,   C2 = (c dt / dx)^2
 *
 * which is stable for C2 <= 0.5 in 2D (CFL). We run at C2 = 0.45, two solver
 * iterations per frame, with an absorbing layer at the domain boundary.
 *
 * Primary path: WebGL2, ping-ponged RGBA16F textures holding vec2(h, h_prev).
 * Fallback:     Canvas2D on a small Float32Array grid.
 * Last resort:  static background (handled by CSS).
 *
 * Rendered as numerical schlieren, S = 1 - exp(-k|grad h|), so the wavefronts
 * read the way they would in a knife-edge schlieren image.
 * ------------------------------------------------------------------------- */
(function () {
  'use strict';

  var canvas = document.querySelector('[data-ripple]');
  if (!canvas) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var coarse  = window.matchMedia('(pointer: coarse)');
  var small   = window.matchMedia('(max-width: 1020px)');

  var C2      = 0.45;         // (c·dt/dx)^2 — CFL limit is 0.5 in 2D
  var DAMPING = 0.9975;       // waves travel further before dissipating
  var MAX_STRENGTH = 0.030;
  var SPEED_GAIN   = 0.017;   // sim px per ms -> impulse
  var CLICK_STRENGTH = 0.115;
  var STEP_MS = 1000 / 60;
  // two solver iterations per frame so wavefronts actually cross the domain
  var SUBSTEPS = small.matches ? 1 : 2;

  var GAIN = 104.0;           // schlieren contrast, normalised by grid spacing

  /* ---------------------------------------------------------------- utils */

  var probe = document.createElement('span');
  probe.style.display = 'none';
  document.documentElement.appendChild(probe);

  function cssColor(name) {
    var raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    probe.style.color = '';
    probe.style.color = raw || '#000';
    var m = getComputedStyle(probe).color.match(/[\d.]+/g);
    if (!m) return [0, 0, 0];
    return [+m[0] / 255, +m[1] / 255, +m[2] / 255];
  }

  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

  /* --------------------------------------------------------- shared state */

  var running = false;
  var visible = false;
  var hero = null;
  var impl = null;

  // pointer state, in sim-grid coordinates
  var pPrev = null;       // [x, y] last applied point
  var pNext = null;       // [x, y] newest point
  var pStrength = 0;
  var click = null;       // [x, y]
  var lastMoveT = 0;

  function heroRect() {
    if (!hero) return null;
    var r = hero.getBoundingClientRect();
    if (r.bottom <= 0 || r.top >= window.innerHeight) return null;
    return r;
  }

  function onPointerMove(e) {
    if (!running || !impl) return;
    var r = heroRect();
    if (!r) return;
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
      pNext = null;
      pPrev = null;
      return;
    }
    var c = canvas.getBoundingClientRect();
    var gx = ((e.clientX - c.left) / c.width) * impl.w;
    var gy = (1 - (e.clientY - c.top) / c.height) * impl.h;   // GL origin bottom-left

    var now = performance.now();
    if (pNext) {
      var dt = Math.max(now - lastMoveT, 8);
      var speed = Math.hypot(gx - pNext[0], gy - pNext[1]) / dt;
      pStrength = Math.min(pStrength + speed * SPEED_GAIN, MAX_STRENGTH);
    }
    lastMoveT = now;
    if (!pPrev) pPrev = [gx, gy];
    pNext = [gx, gy];
  }

  function onPointerDown(e) {
    if (!running || !impl) return;
    var r = heroRect();
    if (!r) return;
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) return;
    var c = canvas.getBoundingClientRect();
    click = [
      ((e.clientX - c.left) / c.width) * impl.w,
      (1 - (e.clientY - c.top) / c.height) * impl.h
    ];
  }

  function onPointerLeave() { pNext = null; pPrev = null; pStrength = 0; }

  /* ------------------------------------------------------------ ambient */

  var nextAmbient = 0;
  function ambient(now) {
    if (reduced.matches) return null;
    if (now < nextAmbient) return null;
    nextAmbient = now + 4500 + Math.random() * 4500;
    return [
      (0.12 + Math.random() * 0.76) * impl.w,
      (0.25 + Math.random() * 0.68) * impl.h,
      0.0045 + Math.random() * 0.0045
    ];
  }

  /* ------------------------------------------------------------- WebGL2 */

  var VERT = [
    '#version 300 es',
    'out vec2 vUv;',
    'void main(){',
    '  vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));',
    '  vUv = p;',
    '  gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);',
    '}'
  ].join('\n');

  var SIM = [
    '#version 300 es',
    'precision highp float;',
    'uniform sampler2D uState;',
    'uniform vec2  uTexel;',
    'uniform vec2  uRes;',
    'uniform vec2  uP0;',
    'uniform vec2  uP1;',
    'uniform float uStrength;',
    'uniform float uRadius;',
    'uniform vec2  uClickPos;',
    'uniform float uClickStrength;',
    'uniform float uClickRadius;',
    'uniform float uC2;',
    'uniform float uDamp;',
    'out vec4 outColor;',
    '',
    'float segDist(vec2 p, vec2 a, vec2 b){',
    '  vec2 pa = p - a, ba = b - a;',
    '  float t = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0);',
    '  return length(pa - ba * t);',
    '}',
    '',
    'void main(){',
    '  vec2 uv = gl_FragCoord.xy * uTexel;',
    '  vec2 st = texture(uState, uv).rg;',
    '  float h  = st.r;',
    '  float hp = st.g;',
    '',
    '  float l = texture(uState, uv - vec2(uTexel.x, 0.0)).r;',
    '  float r = texture(uState, uv + vec2(uTexel.x, 0.0)).r;',
    '  float d = texture(uState, uv - vec2(0.0, uTexel.y)).r;',
    '  float u = texture(uState, uv + vec2(0.0, uTexel.y)).r;',
    '',
    '  float lap = l + r + u + d - 4.0 * h;',
    '  float hn = (2.0 * h - hp + uC2 * lap) * uDamp;',
    '',
    '  if (uStrength > 0.0) {',
    '    float s = segDist(gl_FragCoord.xy, uP0, uP1);',
    '    hn -= uStrength * exp(-(s * s) / (uRadius * uRadius));',
    '  }',
    '  if (uClickStrength > 0.0) {',
    '    float c = distance(gl_FragCoord.xy, uClickPos);',
    '    hn -= uClickStrength * exp(-(c * c) / (uClickRadius * uClickRadius));',
    '  }',
    '',
    '  // absorbing border so the domain does not read as a box',
    '  vec2 e = min(gl_FragCoord.xy, uRes - gl_FragCoord.xy);',
    '  hn *= mix(0.84, 1.0, smoothstep(0.0, 16.0, min(e.x, e.y)));',
    '',
    '  hn = clamp(hn, -1.2, 1.2);',
    '  if (!(hn == hn)) { hn = 0.0; }',   // NaN guard
    '  outColor = vec4(hn, h, 0.0, 1.0);',
    '}'
  ].join('\n');

  var DRAW = [
    '#version 300 es',
    'precision highp float;',
    'in vec2 vUv;',
    'uniform sampler2D uState;',
    'uniform vec2  uTexel;',
    'uniform vec3  uBg;',
    'uniform vec3  uInk;',
    'uniform vec3  uAccent;',
    'uniform float uGain;',
    'out vec4 outColor;',
    '',
    '// Numerical schlieren:  S = 1 - exp(-k |grad h|)',
    '// The standard density-gradient rendering, so wavefronts appear as sharp',
    '// bands the way they do in a knife-edge schlieren photograph. Mixing',
    '// towards --ink means the bands are dark on the light theme and bright on',
    '// the dark one without any branching.',
    'void main(){',
    '  // central differences -> grad h',
    '  float hx = (texture(uState, vUv + vec2(uTexel.x, 0.0)).r',
    '            - texture(uState, vUv - vec2(uTexel.x, 0.0)).r) * 0.5;',
    '  float hy = (texture(uState, vUv + vec2(0.0, uTexel.y)).r',
    '            - texture(uState, vUv - vec2(0.0, uTexel.y)).r) * 0.5;',
    '',
    '  float s = pow(1.0 - exp(-length(vec2(hx, hy)) * uGain), 0.85);',
    '',
    '  vec3 col = mix(uBg, uInk, s * 0.62);',
    '  col = mix(col, uAccent, smoothstep(0.50, 1.0, s) * 0.20);',
    '  outColor = vec4(clamp(col, 0.0, 1.0), 1.0);',
    '}'
  ].join('\n');

  function compile(gl, type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.warn('[ripple] shader:', gl.getShaderInfoLog(s));
      gl.deleteShader(s);
      return null;
    }
    return s;
  }

  function program(gl, fsSrc) {
    var vs = compile(gl, gl.VERTEX_SHADER, VERT);
    var fs = compile(gl, gl.FRAGMENT_SHADER, fsSrc);
    if (!vs || !fs) return null;
    var p = gl.createProgram();
    gl.attachShader(p, vs); gl.attachShader(p, fs); gl.linkProgram(p);
    gl.deleteShader(vs); gl.deleteShader(fs);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
      console.warn('[ripple] link:', gl.getProgramInfoLog(p));
      return null;
    }
    return p;
  }

  function initGL() {
    var gl = canvas.getContext('webgl2', {
      alpha: false, antialias: false, depth: false, stencil: false,
      preserveDrawingBuffer: false, powerPreference: 'low-power'
    });
    if (!gl) return null;
    if (!gl.getExtension('EXT_color_buffer_float') &&
        !gl.getExtension('EXT_color_buffer_half_float')) return null;

    var simP = program(gl, SIM);
    var drawP = program(gl, DRAW);
    if (!simP || !drawP) return null;

    var vao = gl.createVertexArray();
    gl.bindVertexArray(vao);

    var fbo = gl.createFramebuffer();
    var tex = [null, null];
    var src = 0;
    var W = 0, H = 0;

    function makeTex(w, h) {
      var t = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      return t;
    }

    var uSim = {}, uDraw = {};
    ['uState', 'uTexel', 'uRes', 'uP0', 'uP1', 'uStrength', 'uRadius',
     'uClickPos', 'uClickStrength', 'uClickRadius', 'uC2', 'uDamp']
      .forEach(function (n) { uSim[n] = gl.getUniformLocation(simP, n); });
    ['uState', 'uTexel', 'uBg', 'uInk', 'uAccent', 'uGain']
      .forEach(function (n) { uDraw[n] = gl.getUniformLocation(drawP, n); });

    var colors = { bg: [1, 1, 1], ink: [0, 0, 0], accent: [0, 0.4, 0.4] };
    function readColors() {
      colors.bg = cssColor('--bg');
      colors.ink = cssColor('--ink');
      colors.accent = cssColor('--accent');
    }
    readColors();

    return {
      kind: 'webgl2',
      get w() { return W; },
      get h() { return H; },
      readColors: readColors,

      resize: function (cssW, cssH, dpr, simScale, cap) {
        canvas.width  = Math.max(1, Math.round(cssW * dpr));
        canvas.height = Math.max(1, Math.round(cssH * dpr));

        var w = Math.round(cssW * simScale);
        var h = Math.round(cssH * simScale);
        var k = Math.min(1, cap / Math.max(w, h));
        W = Math.max(8, Math.round(w * k));
        H = Math.max(8, Math.round(h * k));

        if (tex[0]) { gl.deleteTexture(tex[0]); gl.deleteTexture(tex[1]); }
        tex[0] = makeTex(W, H);
        tex[1] = makeTex(W, H);
        src = 0;

        // zero both targets
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
        for (var i = 0; i < 2; i++) {
          gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex[i], 0);
          gl.viewport(0, 0, W, H);
          gl.clearColor(0, 0, 0, 1);
          gl.clear(gl.COLOR_BUFFER_BIT);
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      },

      step: function (seg, strength, radius, clk) {
        var dst = 1 - src;
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex[dst], 0);
        gl.viewport(0, 0, W, H);
        gl.useProgram(simP);
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, tex[src]);
        gl.uniform1i(uSim.uState, 0);
        gl.uniform2f(uSim.uTexel, 1 / W, 1 / H);
        gl.uniform2f(uSim.uRes, W, H);
        gl.uniform1f(uSim.uC2, C2);
        gl.uniform1f(uSim.uDamp, DAMPING);
        if (seg && strength > 0) {
          gl.uniform2f(uSim.uP0, seg[0], seg[1]);
          gl.uniform2f(uSim.uP1, seg[2], seg[3]);
          gl.uniform1f(uSim.uStrength, strength);
          gl.uniform1f(uSim.uRadius, radius);
        } else {
          gl.uniform1f(uSim.uStrength, 0);
          gl.uniform2f(uSim.uP0, 0, 0);
          gl.uniform2f(uSim.uP1, 0, 0);
          gl.uniform1f(uSim.uRadius, 1);
        }
        if (clk) {
          gl.uniform2f(uSim.uClickPos, clk[0], clk[1]);
          gl.uniform1f(uSim.uClickStrength, clk[2]);
          gl.uniform1f(uSim.uClickRadius, clk[3]);
        } else {
          gl.uniform1f(uSim.uClickStrength, 0);
          gl.uniform2f(uSim.uClickPos, 0, 0);
          gl.uniform1f(uSim.uClickRadius, 1);
        }
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        src = dst;
      },

      draw: function () {
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.useProgram(drawP);
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, tex[src]);
        gl.uniform1i(uDraw.uState, 0);
        gl.uniform2f(uDraw.uTexel, 1 / W, 1 / H);
        gl.uniform3fv(uDraw.uBg, colors.bg);
        gl.uniform3fv(uDraw.uInk, colors.ink);
        gl.uniform3fv(uDraw.uAccent, colors.accent);
        // gradients scale with grid spacing, so normalise the gain by it
        gl.uniform1f(uDraw.uGain, GAIN * (W / 560));
        gl.drawArrays(gl.TRIANGLES, 0, 3);
      }
    };
  }

  /* ------------------------------------------------------- Canvas2D path */

  function init2D() {
    var ctx = canvas.getContext('2d');
    if (!ctx) return null;

    var W = 0, H = 0;
    var cur, prv, img, buf;
    var back = document.createElement('canvas');
    var bctx = back.getContext('2d');
    var colors = { bg: [1, 1, 1], ink: [0, 0, 0], accent: [0, 0.4, 0.4] };

    function readColors() {
      colors.bg = cssColor('--bg');
      colors.ink = cssColor('--ink');
      colors.accent = cssColor('--accent');
    }
    readColors();

    function splat(cx, cy, amp, rad) {
      var r2 = rad * rad;
      var x0 = Math.max(1, (cx - rad) | 0), x1 = Math.min(W - 2, (cx + rad) | 0);
      var y0 = Math.max(1, (cy - rad) | 0), y1 = Math.min(H - 2, (cy + rad) | 0);
      for (var y = y0; y <= y1; y++) {
        for (var x = x0; x <= x1; x++) {
          var dx = x - cx, dy = y - cy, d2 = dx * dx + dy * dy;
          if (d2 > r2 * 4) continue;
          cur[y * W + x] -= amp * Math.exp(-d2 / r2);
        }
      }
    }

    return {
      kind: 'canvas2d',
      get w() { return W; },
      get h() { return H; },
      readColors: readColors,

      resize: function (cssW, cssH, dpr, simScale, cap) {
        canvas.width = Math.max(1, Math.round(cssW));
        canvas.height = Math.max(1, Math.round(cssH));
        var w = Math.round(cssW * simScale * 0.55);
        var h = Math.round(cssH * simScale * 0.55);
        var k = Math.min(1, (cap * 0.45) / Math.max(w, h));
        W = Math.max(8, Math.round(w * k));
        H = Math.max(8, Math.round(h * k));
        cur = new Float32Array(W * H);
        prv = new Float32Array(W * H);
        back.width = W; back.height = H;
        img = bctx.createImageData(W, H);
        buf = img.data;
        for (var i = 3; i < buf.length; i += 4) buf[i] = 255;
      },

      step: function (seg, strength, radius, clk) {
        var next = prv;   // reuse the old previous buffer as the new current
        for (var y = 1; y < H - 1; y++) {
          var row = y * W;
          for (var x = 1; x < W - 1; x++) {
            var i = row + x;
            var h = cur[i];
            var lap = cur[i - 1] + cur[i + 1] + cur[i - W] + cur[i + W] - 4 * h;
            var v = (2 * h - prv[i] + C2 * lap) * DAMPING;
            next[i] = v > 1.2 ? 1.2 : v < -1.2 ? -1.2 : v;
          }
        }
        prv = cur; cur = next;

        if (seg && strength > 0) {
          // sample a few points along the swept segment for a wake
          var n = 4;
          for (var s = 0; s <= n; s++) {
            var t = s / n;
            splat(seg[0] + (seg[2] - seg[0]) * t,
                  H - 1 - (seg[1] + (seg[3] - seg[1]) * t),
                  strength, radius);
          }
        }
        if (clk) splat(clk[0], H - 1 - clk[1], clk[2], clk[3]);
      },

      draw: function () {
        var bg = colors.bg, ink = colors.ink, ac = colors.accent;
        var gain = GAIN * (W / 560);
        for (var y = 1; y < H - 1; y++) {
          var row = y * W;
          for (var x = 1; x < W - 1; x++) {
            var i = row + x;
            var hx = (cur[i + 1] - cur[i - 1]) * 0.5;
            var hy = (cur[i + W] - cur[i - W]) * 0.5;
            // numerical schlieren, matching the WebGL path
            var s = Math.pow(1 - Math.exp(-Math.sqrt(hx * hx + hy * hy) * gain), 0.85);
            var k = s * 0.62;
            var a = s > 0.50 ? (s - 0.50) / 0.50 * 0.20 : 0;
            var p = i * 4;
            buf[p]     = clamp((bg[0] + (ink[0] - bg[0]) * k) * (1 - a) + ac[0] * a, 0, 1) * 255;
            buf[p + 1] = clamp((bg[1] + (ink[1] - bg[1]) * k) * (1 - a) + ac[1] * a, 0, 1) * 255;
            buf[p + 2] = clamp((bg[2] + (ink[2] - bg[2]) * k) * (1 - a) + ac[2] * a, 0, 1) * 255;
          }
        }
        bctx.putImageData(img, 0, 0);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(back, 0, 0, canvas.width, canvas.height);
      }
    };
  }

  /* ------------------------------------------------------------- driver */

  impl = initGL() || init2D();
  if (!impl) return;

  function metrics() {
    var dpr = Math.min(window.devicePixelRatio || 1, small.matches ? 1.5 : 2);
    var simScale = small.matches ? 0.34 : 0.5;
    var cap = small.matches ? 340 : 700;
    return { dpr: dpr, simScale: simScale, cap: cap };
  }

  var lastW = 0, lastH = 0;
  function resize() {
    var r = canvas.getBoundingClientRect();
    var w = Math.max(1, r.width), h = Math.max(1, r.height);
    if (Math.abs(w - lastW) < 1 && Math.abs(h - lastH) < 1) return;
    lastW = w; lastH = h;
    var m = metrics();
    impl.resize(w, h, m.dpr, m.simScale, m.cap);
    impl.draw();
  }

  var acc = 0, last = 0, raf = 0;

  function frame(now) {
    raf = 0;
    if (!running) return;

    if (!last) last = now;
    acc += Math.min(now - last, 100);
    last = now;

    var frames = Math.min(Math.floor(acc / STEP_MS), 2);
    acc -= frames * STEP_MS;
    var steps = frames * SUBSTEPS;

    var radius = Math.max(5, impl.w * 0.022);

    for (var s = 0; s < steps; s++) {
      var seg = null, strength = 0;
      if (pNext && pPrev && pStrength > 0.0002) {
        seg = [pPrev[0], pPrev[1], pNext[0], pNext[1]];
        strength = pStrength / steps;
      }
      var clk = null;
      if (click) {
        clk = [click[0], click[1], CLICK_STRENGTH, radius * 1.5];
        click = null;
      } else {
        var amb = ambient(now);
        if (amb) clk = [amb[0], amb[1], amb[2], radius * 1.25];
      }
      impl.step(seg, strength, radius, clk);
      if (pNext) pPrev = pNext.slice();
    }

    if (steps > 0) pStrength *= 0.55;   // decay so a stopped pointer stops forcing
    if (pStrength < 0.0002) pStrength = 0;

    impl.draw();
    raf = requestAnimationFrame(frame);
  }

  function start() {
    if (running) return;
    if (reduced.matches) { impl.draw(); return; }
    running = true;
    last = 0; acc = 0;
    raf = requestAnimationFrame(frame);
  }

  function stop() {
    running = false;
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  }

  function evaluate() {
    if (document.hidden || !visible) stop();
    else start();
  }

  /* observers */

  var io = ('IntersectionObserver' in window)
    ? new IntersectionObserver(function (entries) {
        visible = entries.some(function (e) { return e.isIntersecting; });
        evaluate();
      }, { threshold: 0 })
    : null;

  function bindHero() {
    if (io && hero) io.unobserve(hero);
    hero = document.querySelector('[data-hero]');
    if (hero && io) { io.observe(hero); }
    else { visible = !!hero; }
    if (!hero) { visible = false; }
    evaluate();

    var hint = document.querySelector('[data-hint]');
    if (hint && !coarse.matches) {
      setTimeout(function () { hint.classList.add('is-shown'); }, 1200);
    }
  }

  if ('ResizeObserver' in window) {
    new ResizeObserver(function () { resize(); }).observe(canvas);
  } else {
    window.addEventListener('resize', resize);
  }

  document.addEventListener('visibilitychange', evaluate);
  window.addEventListener('pointermove', onPointerMove, { passive: true });
  window.addEventListener('pointerdown', onPointerDown, { passive: true });
  window.addEventListener('pointerleave', onPointerLeave, { passive: true });
  window.addEventListener('blur', onPointerLeave);

  // re-read palette when the theme flips
  new MutationObserver(function () { impl.readColors(); if (!running) impl.draw(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  var scheme = window.matchMedia('(prefers-color-scheme: dark)');
  (scheme.addEventListener ? scheme.addEventListener.bind(scheme, 'change')
                           : scheme.addListener.bind(scheme))(function () {
    impl.readColors(); if (!running) impl.draw();
  });

  window.SBRipple = {
    refresh: function () { bindHero(); resize(); },
    pause: stop,
    kind: impl.kind
  };

  resize();
  bindHero();
})();
