---
layout: page
title: Design Optimisation
permalink: /optim-grid/
---

<!-- model-viewer runtime -->
<script type="module" src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer.min.js"></script>
<script nomodule src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer-legacy.js"></script>

<style>
  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }
  @media (max-width: 1200px) { .grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 700px)  { .grid { grid-template-columns: 1fr; } }

  .tile {
    position: relative;
    background: #ffffff;         /* white */
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 6px 20px rgba(0,0,0,.12);
  }
  .tile model-viewer {
    width: 100%;
    height: 260px;               /* adjust as you like */
    background: #ffffff;         /* white canvas */
    outline: none;
  }
  .caption {
    position: absolute;
    left: 10px; bottom: 10px;
    padding: 6px 10px;
    background: rgba(255,255,255,.92);
    color: #111;
    font: 600 13px/1.2 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    border-radius: 8px;
    letter-spacing: .2px;
    box-shadow: 0 2px 6px rgba(0,0,0,.08);
  }
  .caption .meta { opacity: .85; font-weight: 500; }
</style>

<div class="grid">

  <!-- Repeat for eight populations -->
  <div class="tile" data-meta="{{ '/assets/flow/pop_00_meta.json' | relative_url }}">
    <model-viewer
      src="{{ '/assets/flow/pop_00_opt.glb' | relative_url }}"
      autoplay
      camera-controls
      disable-zoom
      disable-pan
      interaction-prompt="none"
      exposure="1"
      shadow-intensity="0"
      animation-name="frames"
      camera-orbit="180deg 75deg auto"  <!-- same feel as your working single viewer -->
      loading="lazy"
      reveal="auto">
    </model-viewer>
    <div class="caption">Pop 00 — <span class="meta">Gen <span class="gen">—</span> • Cd <span class="cd">—</span></span></div>
  </div>

  <div class="tile" data-meta="{{ '/assets/flow/pop_01_meta.json' | relative_url }}">
    <model-viewer src="{{ '/assets/flow/pop_01_opt.glb' | relative_url }}" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" exposure="1" shadow-intensity="0" animation-name="frames"
      camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 01 — <span class="meta">Gen <span class="gen">—</span> • Cd <span class="cd">—</span></span></div>
  </div>

  <div class="tile" data-meta="{{ '/assets/flow/pop_02_meta.json' | relative_url }}">
    <model-viewer src="{{ '/assets/flow/pop_02_opt.glb' | relative_url }}" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" exposure="1" shadow-intensity="0" animation-name="frames"
      camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 02 — <span class="meta">Gen <span class="gen">—</span> • Cd <span class="cd">—</span></span></div>
  </div>

  <div class="tile" data-meta="{{ '/assets/flow/pop_03_meta.json' | relative_url }}">
    <model-viewer src="{{ '/assets/flow/pop_03_opt.glb' | relative_url }}" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" exposure="1" shadow-intensity="0" animation-name="frames"
      camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 03 — <span class="meta">Gen <span class="gen">—</span> • Cd <span class="cd">—</span></span></div>
  </div>

  <div class="tile" data-meta="{{ '/assets/flow/pop_04_meta.json' | relative_url }}">
    <model-viewer src="{{ '/assets/flow/pop_04_opt.glb' | relative_url }}" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" exposure="1" shadow-intensity="0" animation-name="frames"
      camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 04 — <span class="meta">Gen <span class="gen">—</span> • Cd <span class="cd">—</span></span></div>
  </div>

  <div class="tile" data-meta="{{ '/assets/flow/pop_05_meta.json' | relative_url }}">
    <model-viewer src="{{ '/assets/flow/pop_05_opt.glb' | relative_url }}" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" exposure="1" shadow-intensity="0" animation-name="frames"
      camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 05 — <span class="meta">Gen <span class="gen">—</span> • Cd <span class="cd">—</span></span></div>
  </div>

  <div class="tile" data-meta="{{ '/assets/flow/pop_06_meta.json' | relative_url }}">
    <model-viewer src="{{ '/assets/flow/pop_06_opt.glb' | relative_url }}" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" exposure="1" shadow-intensity="0" animation-name="frames"
      camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 06 — <span class="meta">Gen <span class="gen">—</span> • Cd <span class="cd">—</span></span></div>
  </div>

  <div class="tile" data-meta="{{ '/assets/flow/pop_07_meta.json' | relative_url }}">
    <model-viewer src="{{ '/assets/flow/pop_07_opt.glb' | relative_url }}" autoplay camera-controls disable-zoom disable-pan
      interaction-prompt="none" exposure="1" shadow-intensity="0" animation-name="frames"
      camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer>
    <div class="caption">Pop 07 — <span class="meta">Gen <span class="gen">—</span> • Cd <span class="cd">—</span></span></div>
  </div>

</div>

<script>
  // Start animation explicitly and fill labels from meta JSONs
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tile').forEach(tile => {
      const mv = tile.querySelector('model-viewer');
      const genSpan = tile.querySelector('.gen');
      const cdSpan  = tile.querySelector('.cd');
      const metaUrl = tile.getAttribute('data-meta');

      mv.addEventListener('load', () => {
        // play the "frames" animation once
        try {
          mv.animationName = 'frames';
          // model-viewer loops by default; stop at end:
          mv.addEventListener('timeupdate', () => {
            if (mv.currentTime >= mv.duration && mv.duration > 0) mv.pause();
          }, { once: true });
          mv.play();
        } catch (e) { /* ignore */ }
      });

      // Fill Gen/Cd
      if (metaUrl) {
        fetch(metaUrl).then(r => r.json()).then(meta => {
          const gens = Array.isArray(meta.cd) ? meta.cd.length : (meta.gens || null);
          if (gens != null) genSpan.textContent = gens - 1; // zero-based
          if (Array.isArray(meta.cd) && meta.cd.length) {
            cdSpan.textContent = Number(meta.cd[meta.cd.length - 1]).toFixed(4);
          } else if (typeof meta.cd === 'number') {
            cdSpan.textContent = Number(meta.cd).toFixed(4);
          }
        }).catch(() => { /* leave defaults */ });
      }
    });
  });
</script>
