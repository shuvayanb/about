---
layout: page
title: Projects
---

* # <span style="color:blue">Shape design and optimization </span>

<!-- model-viewer runtime -->
<script type="module" src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer.min.js"></script>
<script nomodule src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer-legacy.js"></script>

<style>
  .mv-wrap {
    position: relative;
    width: min(500px, 60vw);   /* narrower card */
    height: 40vh;              /* a bit shorter */
    margin: 0 auto;            /* center on page */
    background: #ffffff;
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,.10);
    overflow: hidden;
  }
  .mv-layer {
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    background: #ffffff;
  
    /* enlarge + nudge down so the nose fits in frame */
    transform: translateY(24px) scale(2.5);   /* tweak 16–40px to taste */
    transform-origin: 50% 40%;                /* pivot slightly above center */
    will-change: transform;
  }
  .hidden { visibility: hidden; }

  /* === NEW: big HUD for Cd === */
  .hud {
    font-family: "Times New Roman", Times, serif;
    font-size: 28px;
    font-weight: 600;
    position: absolute; top: 14px; left: 16px;
    padding: 8px 12px;
    background: rgba(255,255,255,0.92);
    color: #111;
    border-radius: 10px;
    font: 700 20px/1.1 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }
  .hud .sym em { font-style: italic; }
  .hud .sym sub { font-size: 0.65em; vertical-align: -0.25em; }

  #cdVal { font-weight: 400; }
  
  .hud .small { font-weight: 600; font-size: 13px; opacity: .8; margin-left: 8px; }
</style>

<div class="mv-wrap">
  <!-- double buffer: A (front) + B (back) -->
  <!-- mvA -->
<model-viewer id="mvA" class="mv-layer"
  camera-controls disable-zoom disable-pan interaction-prompt="none"
  exposure="1" shadow-intensity="0"
  camera-orbit="200deg 65deg 100%"
  min-camera-orbit="200deg 65deg 100%"
  max-camera-orbit="200deg 65deg 100%"
  field-of-view="22deg"
  camera-target="0m 0m 0m"
  autoplay></model-viewer>

<!-- mvB (must match mvA exactly) -->
<model-viewer id="mvB" class="mv-layer hidden"
  camera-controls disable-zoom disable-pan interaction-prompt="none"
  exposure="1" shadow-intensity="0"
  camera-orbit="200deg 65deg 100%"
  min-camera-orbit="200deg 65deg 100%"
  max-camera-orbit="200deg 65deg 100%"
  field-of-view="22deg"
  camera-target="0m 0m 0m"
  autoplay></model-viewer>


  <!-- === NEW: Cd overlay -->
  <div class="hud"><span class="sym"><em>C</em><sub>d</sub></span> <span id="cdVal">—</span> <span class="small">(gen <span id="genIdx">0</span>)</span></div>

</div>

<script>
(function(){
  // ----- CONFIG (edit these only) -----
  const BASE   = '{{ "/" | relative_url }}'.replace(/\/+$/, '') + '/';
  const FOLDER = 'assets/flow/history_pop_00/'; // change folder to another population if needed
  const START  = 0;          // first frame index
  const END    = 50;         // last frame index (inclusive)
  const PAD    = 3;          // zero-padding width in filenames
  const FPS    = 5;          // playback speed (frames per second)
  const LOOP   = true;      // play forward once
  const SUFFIX = '_unlit';   // '' if you overwrote originals; '_unlit' if you created copies
  const EXT    = '.glb';
  const CACHE_BUST = '?v={{ site.time | date: "%s" }}'; // avoid stale cache on GH Pages

  // === NEW: Cd JSON path (sits next to frames) ===
  // Expecting: { "cd": [cd_gen0, cd_gen1, ...] }
  const CD_JSON = BASE + FOLDER + 'pop_00_meta.json' + CACHE_BUST;

  const mvA = document.getElementById('mvA');
  const mvB = document.getElementById('mvB');
  const cdEl  = document.getElementById('cdVal');
  const genEl = document.getElementById('genIdx');

  let cur = START;
  let front = mvA;  // currently visible
  let back  = mvB;  // preloads next frame
  let cdArr = null; // will hold array of Cd values

  function framePath(i){
    const id = String(i).padStart(PAD, '0');
    return BASE + FOLDER + 'frame_' + id + SUFFIX + EXT + CACHE_BUST;
  }

  function updateHUD(i){
    if (genEl) genEl.textContent = i;
    if (!cdArr || !cdArr.length) { cdEl && (cdEl.textContent = '—'); return; }
    const val = cdArr[Math.max(0, Math.min(i, cdArr.length - 1))];
    cdEl.textContent = (typeof val === 'number') ? val.toFixed(4) : '—';
  }

  function swapLayers(){
    front.classList.add('hidden');
    back.classList.remove('hidden');
    const tmp = front; front = back; back = tmp;
  }

  function scheduleNext(){
    if (cur > END) { if (!LOOP) return; cur = START; }

    back.src = framePath(cur);

    const onLoaded = () => {
      back.removeEventListener('load', onLoaded);
      swapLayers();
      updateHUD(cur);           // === NEW: update Cd for this gen
      cur += 1;
      setTimeout(scheduleNext, 1000 / FPS);
    };
    back.addEventListener('load', onLoaded, { once: true });

    const onError = () => {
      back.removeEventListener('error', onError);
      cur += 1;
      setTimeout(scheduleNext, 0);
    };
    back.addEventListener('error', onError, { once: true });
  }

  function startPlayback(){
    front.src = framePath(START);
    front.addEventListener('load', () => {
      updateHUD(START);        // === NEW: show Cd for first gen
      cur = START + 1;
      setTimeout(scheduleNext, 1000 / FPS);
    }, { once: true });
  }

  // === NEW: fetch Cd data first (non-fatal if missing) ===
  function loadCd(){
    return fetch(CD_JSON)
      .then(r => r.ok ? r.json() : null)
      .then(j => {
        if (j && Array.isArray(j.cd)) cdArr = j.cd;
      })
      .catch(() => { /* ignore; no HUD update if missing */ });
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadCd().finally(startPlayback);
  });
})();
</script>






<!-- ── Scramjet param sweep block (Markdown-safe) ─────────── -->
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>

<style>
  .scramjet-wrap {max-width:980px;margin:0.75rem auto;position:relative;padding:0 .5rem}
  .scramjet-controls{display:flex;gap:1rem;align-items:center;justify-content:space-between;margin:0 0 .5rem}
  .scramjet-ctl{flex:1}
  .scramjet-ctl label{display:flex;align-items:center;justify-content:space-between;font:600 14px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0 0 .25rem}
  .scramjet-ctl output{font:600 14px;color:#111;background:#eef;padding:.15rem .45rem;border-radius:.4rem;border:1px solid #cfe}
  .scramjet-ticks{display:flex;justify-content:space-between;font:12px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#555;margin:.2rem 0 0}
  .scramjet-viewer{width:100%;height:560px;background:transparent;display:block}
  .scramjet-arrow{position:absolute;right:.75rem;top:35%;transform:translateY(-50%);width:18%;height:10%;pointer-events:none;opacity:.95;z-index:2}
</style>

<div class="scramjet-wrap" id="scramjet-wrap">
  <div class="scramjet-controls">
    <div class="scramjet-ctl">
      <label>n (external shocks) <output id="scramjet-nOut">…</output></label>
      <input id="scramjet-n" type="range" min="0" max="4" step="1" value="0" />
      <div id="scramjet-nTicks" class="scramjet-ticks"></div>
    </div>
    <div class="scramjet-ctl">
      <label>m (internal shocks) <output id="scramjet-mOut">…</output></label>
      <input id="scramjet-m" type="range" min="0" max="4" step="1" value="0" />
      <div id="scramjet-mTicks" class="scramjet-ticks"></div>
    </div>
  </div>

  <!-- Viewer (NO inline comments inside the tag) -->
  <model-viewer
    id="scramjet-mv"
    class="scramjet-viewer"
    src="{{ '/assets/flow/scramjet/scramjet.glb' | relative_url }}"
    alt="Scramjet intake walls colored by Mach; translucent side plates"
    camera-controls
    auto-rotate
    rotation-per-second="0deg"
    auto-rotate-delay="0"
    camera-orbit="90deg -155deg 110%"
    exposure="1.0"
    shadow-intensity="0"
    ar>
  </model-viewer>

  <!-- Freestream arrow -->
  <svg aria-hidden="true" viewBox="0 0 300 60" preserveAspectRatio="xMidYMid meet" class="scramjet-arrow">
    <defs>
      <marker id="scramjet-fs-head" markerWidth="15" markerHeight="10" refX="9" refY="3.5" orient="auto">
        <polygon points="0 0, 10 3.5, 0 7" fill="#1d4ed8"></polygon>
      </marker>
    </defs>
    <g transform="scale(-1,1) translate(-300,0)">
      <line x1="10" y1="30" x2="280" y2="30"
            stroke="#1d4ed8" stroke-width="6" stroke-linecap="round"
            marker-end="url(#scramjet-fs-head)"></line>
    </g>
  </svg>
</div>

<script>
(function(){
  const base = "{{ '/assets/flow/scramjet/' | relative_url }}".replace(/\/+$/,'/');
  const manifestUrl = base + "manifest.json";

  const mv   = document.getElementById('scramjet-mv');
  const nEl  = document.getElementById('scramjet-n');
  const mEl  = document.getElementById('scramjet-m');
  const nOut = document.getElementById('scramjet-nOut');
  const mOut = document.getElementById('scramjet-mOut');
  const nTicks = document.getElementById('scramjet-nTicks');
  const mTicks = document.getElementById('scramjet-mTicks');

  let nVals = [2,3,10,32,100], mVals = [2,3,10,32,100];
  let pattern = "scramjet_n{n}_m{m}.glb";

  fetch(manifestUrl, {cache:'no-store'}).then(r => r.ok ? r.json() : null).then(man => {
    if (man){ if (Array.isArray(man.n_values)) nVals = man.n_values;
              if (Array.isArray(man.m_values)) mVals = man.m_values;
              if (man.pattern) pattern = man.pattern; }
    init();
  }).catch(init);

function init(){
  nEl.max = String(nVals.length - 1);
  mEl.max = String(mVals.length - 1);
  nTicks.innerHTML = nVals.map(v => `<span>${v}</span>`).join('');
  mTicks.innerHTML = mVals.map(v => `<span>${v}</span>`).join('');

  // --- CHANGED: use mid index, not 0 ---
  const iN0 = Math.floor(nVals.length / 2);
  const iM0 = Math.floor(mVals.length / 2);
  nEl.value = iN0;
  mEl.value = iM0;

  // updateModel() will set the outputs and load the correct GLB
  updateModel();
}

  const fileFor = (n, m) => base + pattern.replace("{n}", n).replace("{m}", m);

  const seen = new Set();
  function prefetch(url){
    if (seen.has(url)) return;
    const l = document.createElement('link'); l.rel='prefetch'; l.href=url;
    document.head.appendChild(l); seen.add(url);
  }
  function prefetchNeighbors(iN, iM){
    const idx = [[iN-1,iM],[iN+1,iM],[iN,iM-1],[iN,iM+1],[iN-1,iM-1],[iN+1,iM+1],[iN-1,iM+1],[iN+1,iM-1]];
    for (const [a,b] of idx){
      if (a>=0 && a<nVals.length && b>=0 && b<mVals.length){
        prefetch( fileFor(nVals[a], mVals[b]) );
      }
    }
  }

  function updateModel(){
    const iN = parseInt(nEl.value,10);
    const iM = parseInt(mEl.value,10);
    const n = nVals[iN], m = mVals[iM];
    nOut.textContent = n; mOut.textContent = m;
    mv.src = fileFor(n, m);
    prefetchNeighbors(iN, iM);
  }

  let raf = null;
  function onInput(){
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(()=>{ updateModel(); raf=null; });
  }
  nEl.addEventListener('input', onInput);
  mEl.addEventListener('input', onInput);
})();
</script>
<!-- ───────────────────────────────────────────────────────────── -->





* # <span style="color:blue">[SciML for forward and inverse problems](Sub_projects/p_deep_learning.md) </span>

![Deep Learning](https://github.com/user-attachments/assets/be1c2e28-2088-48e6-a927-a2e9a19617ce "Differentiable physics-based phiflow fluid solver used as a solver-in-the-loop approach for learning a continuous function for the accurate reconstruction of local (wall boundary properties) and global (cylinder wake frequencies) fluid phenomena. ")


* # <span style="color:blue">[LLM based AI Agents for design and optimisation](Sub_projects/p_immersed_boundary.md) </span>

![LLM Agents](https://github.com/user-attachments/assets/88a11cd4-c813-481f-8f7f-e573ae7724ec "Depiction of an agentic framework that leverages LLM like ChatGPT 3.5 and Llama-3.1-70B model to perform zero shot optimisation for complex single and multi-objective optimisation problems of practical interest. ")

