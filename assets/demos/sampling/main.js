// ---- tiny error surface so blank screens are obvious ----
window.onerror = (msg, src, line, col, err) => {
  const box = document.getElementById("err");
  if (box) box.textContent = `[JS error] ${msg} at ${src}:${line}:${col}`;
};

// ---- seeded RNG ----
function RNG(seed = 42) {
  let s = seed >>> 0;
  return () => ((s = Math.imul(1664525, s) + 1013904223) >>> 0) / 2 ** 32;
}
let rng = RNG(42);

// ---- toy vocabulary & base logits (deterministic) ----
const TOKENS = Array.from({ length: 20 }, (_, i) => `t${String(i + 1).padStart(2, "0")}`);
const baseLogits = (() => {
  const r = RNG(7);
  return TOKENS.map(() => r() * 4 - 2);
})();

// ---- math helpers ----
const softmax = (arr) => {
  const m = Math.max(...arr);
  const exps = arr.map((v) => Math.exp(v - m));
  const s = exps.reduce((a, b) => a + b, 0) || 1;
  return exps.map((v) => v / s);
};
function applyTopK(probs, k) {
  const idx = probs.map((p, i) => [p, i]).sort((a, b) => b[0] - a[0]).map((x) => x[1]);
  const keep = new Set(idx.slice(0, k));
  const out = probs.map((p, i) => (keep.has(i) ? p : 0));
  const Z = out.reduce((a, b) => a + b, 0) || 1;
  return out.map((v) => v / Z);
}
function applyTopP(probs, p) {
  const pairs = probs.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]);
  let cum = 0;
  const keep = new Set();
  for (const [v, i] of pairs) {
    keep.add(i);
    cum += v;
    if (cum >= p) break;
  }
  const out = probs.map((v, i) => (keep.has(i) ? v : 0));
  const Z = out.reduce((a, b) => a + b, 0) || 1;
  return out.map((v) => v / Z);
}
function sample(probs) {
  const u = rng();
  let cum = 0;
  for (let i = 0; i < probs.length; i++) {
    cum += probs[i];
    if (u <= cum) return i;
  }
  return probs.length - 1;
}

// ---- DOM wiring (after DOM ready thanks to defer) ----
const q = (s) => document.querySelector(s);
const chart = q("#chart");
const ctx = chart.getContext("2d");

const tempEl = q("#temp"), topkEl = q("#topk"), toppEl = q("#topp"), modeEl = q("#mode");
const tempOut = q("#tempOut"), topkOut = q("#topkOut"), toppOut = q("#toppOut");
const play = q("#play"), pauseBtn = q("#pause"), step = q("#step"), seedEl = q("#seed"), resetBtn = q("#reset");
const sampleOut = q("#sampleOut"), supportOut = q("#supportOut"), sumOut = q("#sumOut");

let playing = false, animId = null;

function compute() {
  const T = +tempEl.value;
  const k = (+topkEl.value) | 0;
  const p = +toppEl.value;

  tempOut.textContent = T.toFixed(2);
  topkOut.textContent = String(k);
  toppOut.textContent = p.toFixed(2);

  const scaled = baseLogits.map((v) => v / T);
  let probs = softmax(scaled);

  const mode = modeEl ? modeEl.value : "both";
  if (mode === "topk") {
    probs = applyTopK(probs, k);
  } else if (mode === "topp") {
    probs = applyTopP(probs, p);
  } else if (mode === "both") {
    probs = applyTopK(probs, k);
    probs = applyTopP(probs, p);
  } // mode === "none" => no pruning

  const support = probs.filter((v) => v > 0).length;
  const sum = probs.reduce((a, b) => a + b, 0);
  return { probs, support, sum };
}

function draw({ probs }) {
  const W = chart.width, H = chart.height, pad = 24;
  ctx.clearRect(0, 0, W, H);

  // axis
  ctx.strokeStyle = "#999"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(pad, H - pad); ctx.lineTo(W - pad, H - pad); ctx.stroke();

  // bars
  const bw = (W - pad * 2) / probs.length;
  ctx.fillStyle = "#67b7ff";
  probs.forEach((p, i) => {
    const h = Math.max(0, (H - 2 * pad) * p);
    const x = pad + i * bw + 2, y = H - pad - h;
    ctx.globalAlpha = p > 0 ? 1 : 0.25;
    ctx.fillRect(x, y, bw - 4, h);
  });

  // labels (every 2)
  ctx.globalAlpha = 1; ctx.fillStyle = "#666"; ctx.font = "12px system-ui";
  probs.forEach((_, i) => {
    if (i % 2) return;
    const x = pad + i * bw + bw / 2;
    ctx.textAlign = "center";
    ctx.fillText(TOKENS[i], x, H - 6);
  });
}

function tick() {
  try {
    const state = compute();
    draw(state);
    supportOut.textContent = state.support;
    sumOut.textContent = state.sum.toFixed(3);
    if (playing) {
      const idx = sample(state.probs);
      sampleOut.textContent = `${TOKENS[idx]} (${state.probs[idx].toFixed(3)})`;
      animId = requestAnimationFrame(tick);
    }
  } catch (e) {
    const box = document.getElementById("err");
    if (box) box.textContent = `[tick failed] ${e.message}`;
    throw e;
  }
}

function refresh() { cancelAnimationFrame(animId); tick(); }

// listeners
["input", "change"].forEach(evt => {
  tempEl.addEventListener(evt, refresh);
  topkEl.addEventListener(evt, refresh);
  toppEl.addEventListener(evt, refresh);
});
if (modeEl) modeEl.addEventListener("change", refresh);

play.onclick = () => { playing = true; refresh(); };
pauseBtn.onclick = () => { playing = false; cancelAnimationFrame(animId); };
step.onclick = () => { playing = false; cancelAnimationFrame(animId);
  const s = compute(); draw(s);
  const idx = sample(s.probs);
  sampleOut.textContent = `${TOKENS[idx]} (${s.probs[idx].toFixed(3)})`;
  supportOut.textContent = s.support; sumOut.textContent = s.sum.toFixed(3);
};
seedEl.onchange = () => { rng = RNG(+seedEl.value | 0); };
resetBtn.onclick = () => {
  tempEl.value = "1.00"; topkEl.value = "10"; toppEl.value = "0.90"; modeEl.value = "topp";
  rng = RNG(+seedEl.value | 0); refresh();
};

// initial paint
refresh();
