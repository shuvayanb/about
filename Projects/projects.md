<!-- ── Scramjet param sweep block (Markdown-safe) ─────────── -->
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>

<style>
  .scramjet-wrap { max-width:980px; margin:.75rem auto; position:relative; padding:0 0 0 .5rem; } /* no right padding */
  .scramjet-controls{display:flex;gap:1rem;align-items:center;justify-content:space-between;margin:0 0 .5rem}
  .scramjet-ctl{flex:1}
  .scramjet-ctl label{display:flex;align-items:center;justify-content:space-between;font:600 14px/1.2 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0 0 .25rem}
  .scramjet-ctl output{font:600 14px;color:#111;background:#eef;padding:.15rem .45rem;border-radius:.4rem;border:1px solid #cfe}
  .scramjet-ticks{display:flex;justify-content:space-between;font:12px system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#555;margin:.2rem 0 0}
  .scramjet-viewer{width:100%;height:560px;background:transparent;display:block}
  .scramjet-arrow{
    position:absolute; right:0;               /* truly flush right */
    top:35%; transform:translateY(-50%);
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

  <model-viewer
    id="scramjet-mv"
    class="scramjet-viewer"
    src="{{ '/assets/flow/scramjet/scramjet.glb' | relative_url }}"
    alt="Scramjet intake walls colored by Mach; translucent side plates"
    camera-controls
    auto-rotate
    rotation-per-second="0deg"
    auto-rotate-delay="0"
    camera-orbit="-90deg 160deg 120%"
    exposure="1.0"
    shadow-intensity="0"
    ar>
  </model-viewer>

  <!-- Freestream arrow (viewport is 100x20 'units'; we draw with %) -->
  <svg aria-hidden="true" viewBox="0 0 100 20" preserveAspectRatio="xMidYMid meet" class="scramjet-arrow">
    <defs>
      <marker id="scramjet-fs-head" markerWidth="10" markerHeight="6" refX="7" refY="3" orient="auto">
        <polygon points="0 0, 8 3, 0 6" fill="#1d4ed8"></polygon>
      </marker>
    </defs>
    <line id="scramjet-fs-line"
          x1="95%" y1="50%" x2="15%" y2="50%"   <!-- default: right→left -->
          stroke="#1d4ed8" stroke-width="2.5" stroke-linecap="round"
          marker-end="url(#scramjet-fs-head)"></line>
  </svg>
</div>

<script>
(function(){
  // 'rtl' = right→left (arrowhead on LEFT).  'ltr' = left→right (arrowhead on RIGHT).
  const FLOW_DIR = 'rtl';

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

  // Apply arrow direction exactly once.
  if (FLOW_DIR === 'ltr'){
    fsLine.setAttribute('x1','15%'); fsLine.setAttribute('x2','95%');
  } else { // 'rtl'
    fsLine.setAttribute('x1','95%'); fsLine.setAttribute('x2','15%');
  }

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

    // start sliders at the middle value
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

    // keep your default camera if desired
    // mv.cameraOrbit = '-90deg 160deg 120%'; mv.jumpCameraToGoal();

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
