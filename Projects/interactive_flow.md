---
layout: default
title: Optimal Shapes — 4×2 Grid
permalink: /optim-grid/
---

<!-- Minimal CSS for a responsive 4×2 grid -->
<style>
  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  @media (max-width: 1200px) { .grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 700px)  { .grid { grid-template-columns: 1fr; } }

  .tile {
    position: relative;
    background: #0b0b0b;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 6px 20px rgba(0,0,0,.25);
  }
  .tile model-viewer {
    width: 100%;
    height: 260px; /* tweak if you want taller tiles */
    background: #0b0b0b;
  }
  .caption {
    position: absolute;
    left: 8px; bottom: 8px;
    padding: 6px 10px;
    background: rgba(0,0,0,.55);
    color: #fff;
    font: 500 13px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    border-radius: 8px;
    letter-spacing: .2px;
  }
  .caption .meta {
    opacity: .9;
  }
</style>

<!-- model-viewer (works on GitHub Pages) -->
<script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>

<div class="grid">

  <!-- Repeat for 8 populations -->
  <div class="tile" data-meta="/assets/flow/pop_00_meta.json">
    <model-viewer src="/assets/flow/pop_00_opt.glb"
      autoplay
      camera-controls
      disable-zoom
      disable-pan
      interaction-prompt="none"
      shadow-intensity="0"
      exposure="1"
      ar="false"
      animation-name="frames"
      style="background:#0b0b0b"
      camera-orbit="15deg 60deg 120%"
      min-camera-orbit="15deg 60deg 120%"
      max-camera-orbit="15deg 60deg 120%"
      loading="lazy"
      reveal="auto">
    </model-viewer>
    <div class="caption">Pop 00 — <span class="meta">Gen <span class="gen">?</span> • Cd <span class="cd">?</span></span></div>
  </div>

  <div class="tile" data-meta="/assets/flow/pop_01_meta.json">
    <model-viewer src="/assets/flow/pop_01_opt.glb" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" shadow-intensity="0" exposure="1"
      animation-name="frames" style="background:#0b0b0b"
      camera-orbit="15deg 60deg 120%" min-camera-orbit="15deg 60deg 120%" max-camera-orbit="15deg 60deg 120%"
      loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 01 — <span class="meta">Gen <span class="gen">?</span> • Cd <span class="cd">?</span></span></div>
  </div>

  <div class="tile" data-meta="/assets/flow/pop_02_meta.json">
    <model-viewer src="/assets/flow/pop_02_opt.glb" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" shadow-intensity="0" exposure="1"
      animation-name="frames" style="background:#0b0b0b"
      camera-orbit="15deg 60deg 120%" min-camera-orbit="15deg 60deg 120%" max-camera-orbit="15deg 60deg 120%"
      loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 02 — <span class="meta">Gen <span class="gen">?</span> • Cd <span class="cd">?</span></span></div>
  </div>

  <div class="tile" data-meta="/assets/flow/pop_03_meta.json">
    <model-viewer src="/assets/flow/pop_03_opt.glb" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" shadow-intensity="0" exposure="1"
      animation-name="frames" style="background:#0b0b0b"
      camera-orbit="15deg 60deg 120%" min-camera-orbit="15deg 60deg 120%" max-camera-orbit="15deg 60deg 120%"
      loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 03 — <span class="meta">Gen <span class="gen">?</span> • Cd <span class="cd">?</span></span></div>
  </div>

  <div class="tile" data-meta="/assets/flow/pop_04_meta.json">
    <model-viewer src="/assets/flow/pop_04_opt.glb" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" shadow-intensity="0" exposure="1"
      animation-name="frames" style="background:#0b0b0b"
      camera-orbit="15deg 60deg 120%" min-camera-orbit="15deg 60deg 120%" max-camera-orbit="15deg 60deg 120%"
      loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 04 — <span class="meta">Gen <span class="gen">?</span> • Cd <span class="cd">?</span></span></div>
  </div>

  <div class="tile" data-meta="/assets/flow/pop_05_meta.json">
    <model-viewer src="/assets/flow/pop_05_opt.glb" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" shadow-intensity="0" exposure="1"
      animation-name="frames" style="background:#0b0b0b"
      camera-orbit="15deg 60deg 120%" min-camera-orbit="15deg 60deg 120%" max-camera-orbit="15deg 60deg 120%"
      loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 05 — <span class="meta">Gen <span class="gen">?</span> • Cd <span class="cd">?</span></span></div>
  </div>

  <div class="tile" data-meta="/assets/flow/pop_06_meta.json">
    <model-viewer src="/assets/flow/pop_06_opt.glb" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" shadow-intensity="0" exposure="1"
      animation-name="frames" style="background:#0b0b0b"
      camera-orbit="15deg 60deg 120%" min-camera-orbit="15deg 60deg 120%" max-camera-orbit="15deg 60deg 120%"
      loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 06 — <span class="meta">Gen <span class="gen">?</span> • Cd <span class="cd">?</span></span></div>
  </div>

  <div class="tile" data-meta="/assets/flow/pop_07_meta.json">
    <model-viewer src="/assets/flow/pop_07_opt.glb" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" shadow-intensity="0" exposure="1"
      animation-name="frames" style="background:#0b0b0b"
      camera-orbit="15deg 60deg 120%" min-camera-orbit="15deg 60deg 120%" max-camera-orbit="15deg 60deg 120%"
      loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 07 — <span class="meta">Gen <span class="gen">?</span> • Cd <span class="cd">?</span></span></div>
  </div>

</div>

<!-- Sync playback (once), and fill Gen/Cd from meta JSONs -->
<script>
  document.addEventListener('DOMContentLoaded', () => {
    const tiles = document.querySelectorAll('.tile');
    tiles.forEach(tile => {
      const mv = tile.querySelector('model-viewer');
      const genSpan = tile.querySelector('.gen');
      const cdSpan  = tile.querySelector('.cd');
      const metaUrl = tile.getAttribute('data-meta');

      // Ensure single forward play and clamp at final frame
      mv.addEventListener('load', () => {
        try {
          mv.animationName = 'frames';
          // turn off looping via JS to be explicit across versions
          mv.animationLoop = false;
          // Start the animation (autoplay is set, but calling play() is robust)
          mv.play();
        } catch (e) { /* no-op */ }
      });

      // Fill labels from meta JSON (gens & final Cd)
      if (metaUrl) {
        fetch(metaUrl).then(r => r.json()).then(meta => {
          const gens = Array.isArray(meta.cd) ? meta.cd.length : (meta.gens || null);
          if (gens) genSpan.textContent = gens - 1; // zero-based gens, final = N-1
          if (Array.isArray(meta.cd) && meta.cd.length) {
            const lastCd = meta.cd[meta.cd.length - 1];
            cdSpan.textContent = Number(lastCd).toFixed(4);
          } else if (typeof meta.cd === 'number') {
            cdSpan.textContent = Number(meta.cd).toFixed(4);
          }
        }).catch(() => {
          genSpan.textContent = '—';
          cdSpan.textContent  = '—';
        });
      }
    });
  });
</script>
