---
layout: page
title: Design Optimisation
permalink: /optim-grid/
---

<!-- model-viewer runtime (same as your single-view page) -->
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
    background: #ffffff;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 6px 20px rgba(0,0,0,.12);
  }
  .tile model-viewer {
    width: 100%;
    height: 260px;      /* adjust height if you want */
    background: #ffffff;
    outline: none;
  }
</style>

<div class="grid">
  <!-- Eight tiles; src is set by JS from data-file to avoid path issues -->
  <div class="tile"><model-viewer data-file="assets/flow/pop_00_opt.glb"
       camera-controls disable-zoom disable-pan interaction-prompt="none"
       exposure="1" shadow-intensity="0"
       camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer></div>

  <div class="tile"><model-viewer data-file="assets/flow/pop_01_opt.glb"
       camera-controls disable-zoom disable-pan interaction-prompt="none"
       exposure="1" shadow-intensity="0"
       camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer></div>

  <div class="tile"><model-viewer data-file="assets/flow/pop_02_opt.glb"
       camera-controls disable-zoom disable-pan interaction-prompt="none"
       exposure="1" shadow-intensity="0"
       camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer></div>

  <div class="tile"><model-viewer data-file="assets/flow/pop_03_opt.glb"
       camera-controls disable-zoom disable-pan interaction-prompt="none"
       exposure="1" shadow-intensity="0"
       camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer></div>

  <div class="tile"><model-viewer data-file="assets/flow/pop_04_opt.glb"
       camera-controls disable-zoom disable-pan interaction-prompt="none"
       exposure="1" shadow-intensity="0"
       camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer></div>

  <div class="tile"><model-viewer data-file="assets/flow/pop_05_opt.glb"
       camera-controls disable-zoom disable-pan interaction-prompt="none"
       exposure="1" shadow-intensity="0"
       camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer></div>

  <div class="tile"><model-viewer data-file="assets/flow/pop_06_opt.glb"
       camera-controls disable-zoom disable-pan interaction-prompt="none"
       exposure="1" shadow-intensity="0"
       camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer></div>

  <div class="tile"><model-viewer data-file="assets/flow/pop_07_opt.glb"
       camera-controls disable-zoom disable-pan interaction-prompt="none"
       exposure="1" shadow-intensity="0"
       camera-orbit="180deg 75deg auto" loading="lazy" reveal="auto"></model-viewer></div>
</div>

<script>
  // Compute site base path once (works on user & project pages)
  const BASE = '{{ "/" | relative_url }}'.replace(/\/+$/, '') + '/';

  document.addEventListener('DOMContentLoaded', () => {
    const viewers = document.querySelectorAll('model-viewer[data-file]');
    viewers.forEach(mv => {
      // Set src with correct base path
      const file = mv.getAttribute('data-file').replace(/^\/+/, '');
      mv.src = BASE + file;

      // Autoplay the "frames" animation exactly once, then hold final
      mv.addEventListener('load', () => {
        try {
          mv.animationName = 'frames';
          // play then pause at the end
          const onTick = () => {
            // mv.duration becomes available after load; pause when done
            if (mv.duration > 0 && mv.currentTime >= mv.duration) {
              mv.pause();
              mv.removeEventListener('timeupdate', onTick);
            }
          };
          mv.addEventListener('timeupdate', onTick);
          mv.play();
        } catch (e) { /* ignore */ }
      });
    });
  });
</script>
