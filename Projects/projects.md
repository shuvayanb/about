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
    width: min(500px, 60vw);
    height: 40vh;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,.10);
    overflow: hidden;
  }
  .mv-layer {
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    background: #ffffff;
    transform: translateY(24px) scale(2.5);
    transform-origin: 50% 40%;
    will-change: transform;
  }
  .hidden { visibility: hidden; }

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

<div class="card-row">
  <div class="mv-wrap">
    <model-viewer id="mvA" class="mv-layer"
      camera-controls disable-zoom disable-pan interaction-prompt="none"
      exposure="1" shadow-intensity="0"
      camera-orbit="200deg 65deg 100%"
      min-camera-orbit="200deg 65deg 100%"
      max-camera-orbit="200deg 65deg 100%"
      field-of-view="22deg"
      camera-target="0m 0m 0m"
      autoplay></model-viewer>

    <model-viewer id="mvB" class="mv-layer hidden"
      camera-controls disable-zoom disable-pan interaction-prompt="none"
      exposure="1" shadow-intensity="0"
      camera-orbit="200deg 65deg 100%"
      min-camera-orbit="200deg 65deg 100%"
      max-camera-orbit="200deg 65deg 100%"
      field-of-view="22deg"
      camera-target="0m 0m 0m"
      autoplay></model-viewer>

    <div class="hud"><span class="sym"><em>C</em><sub>d</sub></span> <span id="cdVal">—</span> <span class="small">(gen <span id="genIdx">0</span>)</span></div>
  </div>

  <aside class="sidebox">
    <h3>Nose cone optimisation</h3>
    <p>Animated history of candidate shapes; the badge shows the drag coefficient
       <em>C</em><sub>d</sub> for each generation.</p>
  </aside>
</div>

<script>
(function(){
  const BASE   = '{{ "/" | relative_url }}'.replace(/\/+$/, '') + '/';
  const FOLDER = 'assets/flow/history_pop_00/';
  const START  = 0, END = 50, PAD = 3, FPS = 5, LOOP = true;
  const SUFFIX = '_unlit', EXT = '.glb';
  const CACHE_BUST = '?v={{ site.time | date: "%s" }}';
  const CD_JSON = BASE + FOLDER + 'pop_00_meta.json' + CACHE_BUST;

  const mvA = document.getElementById('mvA');
  const mvB = document.getElementById('mvB');
  const cdEl  = document.getElementById('cdVal');
  const genEl = document.getElementById('genIdx');

  let cur = START, front = mvA, back = mvB, cdArr = null;

  function framePath(i){ return BASE + FOLDER + 'frame_' + String(i).padStart(PAD,'0') + SUFFIX + EXT + CACHE_BUST; }
  function updateHUD(i){
    if (genEl) genEl.textContent = i;
    if (!cdArr || !cdArr.length){ if(cdEl) cdEl.textContent = '—'; return; }
    const v = cdArr[Math.max(0, Math.min(i, cdArr.length-1))];
    cdEl.textContent = (typeof v === 'number') ? v.toFixed(4) : '—';
  }
  function swapLayers(){ front.classList.add('hidden'); back.classList.remove('hidden'); const t=front; front=back; back=t; }
  function scheduleNext(){
    if (cur > END){ if(!LOOP) return; cur = START; }
    back.src = framePath(cur);
    const onLoaded = () => { back.removeEventListener('load', onLoaded); swapLayers(); updateHUD(cur); cur++; setTimeout(scheduleNext, 1000/FPS); };
    const onError  = () => { back.removeEventListener('error', onError);  cur++; setTimeout(scheduleNext, 0); };
    back.addEventListener('load', onLoaded, {once:true});
    back.addEventListener('error', onError, {once:true});
  }
  function start(){ front.src = framePath(START); front.addEventListener('load', ()=>{ updateHUD(START); cur=START+1; setTimeout(scheduleNext, 1000/FPS); }, {once:true}); }
  function loadCd(){ return fetch(CD_JSON).then(r=>r.ok?r.json():null).then(j=>{ if(j && Array.isArray(j.cd)) cdArr=j.cd; }).catch(()=>{}); }
  document.addEventListener('DOMContentLoaded', ()=>{ loadCd().finally(start); });
})();
</script>

<style>
  .card-row{
    display:grid;
    grid-template-columns: min(500px, 60vw) minmax(260px, 1fr);
    align-items:start;
    gap: 1.25rem;
    max-width: 1100px;
    margin: .75rem auto;
  }
  .sidebox h3{
    margin: 0 0 .4rem;
    font: 700 20px/1.25 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    color:#111;
  }
  .sidebox p{
    margin:0;
    font: 400 15px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    color:#222;
  }
  .card-cell{ position:relative; }
  @media (max-width: 900px){ .card-row{ grid-template-columns: 1fr; } }
</style>

<!-- ── Scramjet param sweep block ─────────── -->
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>

<style>
  .scramjet-wrap{
    position: relative;
    width: min(500px, 60vw);
    margin: .75rem auto;
    padding: 0;
  }
  .scramjet-controls{display:flex;gap:1rem;align-items:center;justify-content:space-between;margin:0 0 .5rem}
  .scramjet-ctl{flex:1}
  .scramjet-ctl label{display:flex;align-items:center;justify-content:space-between;font:600 14px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0 0 .25rem}
  .scramjet-ctl output{font:600 14px;color:#111;background:#eef;padding:.15rem .45rem;border-radius:.4rem;border:1px solid #cfe}
  .scramjet-ticks{display:flex;justify-content:space-between;font:12px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#555;margin:.2rem 0 0}
  .scramjet-viewer{
    width: 100%;
    height: 40vh;
    background: #ffffff;
    display: block;
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,.10);
    overflow: hidden;
  }
  .scramjet-arrow{
    position:absolute; left:0;               /* moved to left side */
    top:5%; transform:translateY(-50%);
    width:18%; height:10%;
    pointer-events:none; opacity:.95; z-index:2;
  }
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
</div>

<!-- IMPORTANT: blank line + flush-left HTML so Markdown doesn't code-block it -->
<div class="card-row">
  <div class="card-cell">
<model-viewer
  id="scramjet-mv"
  class="scramjet-viewer"
  src="{{ '/assets/flow/scramjet/scramjet.glb' | relative_url }}"
  alt="Scramjet intake walls colored by Mach; translucent side plates"
  camera-controls
  interaction-prompt="none"
  auto-rotate
  rotation-per-second="0deg"
  auto-rotate-delay="0"
  camera-orbit="-92deg 160deg 75%"
  exposure="1.0"
  shadow-intensity="0"
  ar>
</model-viewer>

<svg aria-hidden="true" viewBox="0 0 300 60" preserveAspectRatio="xMidYMid meet" class="scramjet-arrow">
  <defs>
    <marker id="scramjet-fs-head" markerWidth="15" markerHeight="10" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#1d4ed8"></polygon>
    </marker>
  </defs>
  <line id="scramjet-fs-line" x1="20" y1="30" x2="290" y2="30"
        stroke="#1d4ed8" stroke-width="6" stroke-linecap="round"
        marker-end="url(#scramjet-fs-head)"></line>
</svg>
  </div>

  <aside class="sidebox">
    <h3>Scramjet intake design</h3>
    <p>Scramjet intake with <strong>n</strong> (external) and <strong>m</strong> (internal) shock;
       See how the Mach number distribution changes along the ramp and cowl walls.</p>
  </aside>
</div>

<script>
(function(){
  const FLOW_DIR = 'ltr';
  const base = "{{ '/assets/flow/scramjet/' | relative_url }}".replace(/\/+$/,'/');
  const manifestUrl = base + "manifest.json";

  const mv   = document.getElementById('scramjet-mv');
  const nEl  = document.getElementById('scramjet-n');
  const mEl  = document.getElementById('scramjet-m');
  const nOut = document.getElementById('scramjet-nOut');
  const mOut = document.getElementById('scramjet-mOut');
  const nTicks = document.getElementById('scramjet-nTicks');
  const mTicks = document.getElementById('scramjet-mTicks');
  const fsLine = document.getElementById('scramjet-fs-line');

  function setArrowDirection(dir){
    if (dir === 'ltr'){ fsLine.setAttribute('x1','20');  fsLine.setAttribute('x2','290'); }
    else { fsLine.setAttribute('x1','290'); fsLine.setAttribute('x2','20'); }
  }
  setArrowDirection(FLOW_DIR);

  let nVals = [2,3,10,32,100], mVals = [2,3,10,32,100];
  let pattern = "scramjet_n{n}_m{m}.glb";

  fetch(manifestUrl, {cache:'no-store'}).then(r => r.ok ? r.json() : null).then(man => {
    if (man){
      if (Array.isArray(man.n_values)) nVals = man.n_values;
      if (Array.isArray(man.m_values)) mVals = man.m_values;
      if (man.pattern) pattern = man.pattern;
    }
    init();
  }).catch(init);

  function init(){
    nEl.max = String(nVals.length - 1);
    mEl.max = String(mVals.length - 1);
    nTicks.innerHTML = nVals.map(v => `<span>${v}</span>`).join('');
    mTicks.innerHTML = mVals.map(v => `<span>${v}</span>`).join('');

    const iN0 = Math.floor(nVals.length / 2);
    const iM0 = Math.floor(mVals.length / 2);
    nEl.value = iN0;  mEl.value = iM0;

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


* # <span style="color:blue">[SciML for forward and inverse problems](Sub_projects/p_deep_learning.md) </span>

![Deep Learning](https://github.com/user-attachments/assets/be1c2e28-2088-48e6-a927-a2e9a19617ce "Differentiable physics-based phiflow fluid solver used as a solver-in-the-loop approach for learning a continuous function for the accurate reconstruction of local (wall boundary properties) and global (cylinder wake frequencies) fluid phenomena. ")


* # <span style="color:blue">[LLM based AI Agents for design and optimisation](Sub_projects/p_immersed_boundary.md) </span>

![LLM Agents](https://github.com/user-attachments/assets/88a11cd4-c813-481f-8f7f-e573ae7724ec "Depiction of an agentic framework that leverages LLM like ChatGPT 3.5 and Llama-3.1-70B model to perform zero shot optimisation for complex single and multi-objective optimisation problems of practical interest. ")
