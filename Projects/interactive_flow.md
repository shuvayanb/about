---
layout: page
title: Shape Optimization
permalink: /pop00-frames/
---

<!-- model-viewer runtime -->
<script type="module" src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer.min.js"></script>
<script nomodule src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer-legacy.js"></script>

<style>
  .mv-wrap {
    position: relative;
    width: 100%;
    height: 82vh;
    background: #ffffff;
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,.10);
    overflow: hidden;
  }
  .mv-layer {
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    background: #ffffff;
  }
  .hidden { visibility: hidden; }
</style>

<div class="mv-wrap">
  <!-- double buffer: A (front) + B (back) -->
  <model-viewer id="mvA" class="mv-layer"
    camera-controls disable-zoom disable-pan interaction-prompt="none"
    exposure="1" shadow-intensity="0"
    camera-orbit="30deg 65deg 120%" autoplay></model-viewer>

  <model-viewer id="mvB" class="mv-layer hidden"
    camera-controls disable-zoom disable-pan interaction-prompt="none"
    exposure="1" shadow-intensity="0"
    camera-orbit="30deg 65deg 120%" autoplay></model-viewer>
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
  const LOOP   = false;      // play forward once
  const SUFFIX = '_unlit';   // <<< set to '' if you overwrote originals; '_unlit' if you created copies
  const EXT    = '.glb';
  const CACHE_BUST = '?v={{ site.time | date: "%s" }}'; // avoid stale cache on GH Pages

  const mvA = document.getElementById('mvA');
  const mvB = document.getElementById('mvB');

  let cur = START;
  let front = mvA;  // currently visible
  let back  = mvB;  // preloads next frame

  function framePath(i){
    const id = String(i).padStart(PAD, '0');
    return BASE + FOLDER + 'frame_' + id + SUFFIX + EXT + CACHE_BUST;
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
      cur += 1;
      setTimeout(scheduleNext, 1000 / FPS);
    };
    back.addEventListener('load', onLoaded, { once: true });

    const onError = () => {
      back.removeEventListener('error', onError);
      // skip missing frames; try next
      cur += 1;
      setTimeout(scheduleNext, 0);
    };
    back.addEventListener('error', onError, { once: true });
  }

  function start(){
    front.src = framePath(START);
    front.addEventListener('load', () => {
      cur = START + 1;
      setTimeout(scheduleNext, 1000 / FPS);
    }, { once: true });
  }

  document.addEventListener('DOMContentLoaded', start);
})();
</script>
