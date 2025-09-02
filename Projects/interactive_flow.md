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
    background: #ffffff; /* white page background */
    border-radius: 14px;
    box-shadow: 0 6px 20px rgba(0,0,0,.10);
    overflow: hidden;
  }
  .mv-layer {
    position: absolute; inset: 0;
    width: 100%; height: 100%;
    background: #ffffff; /* white canvas inside viewer */
  }
  .hidden { visibility: hidden; }
</style>

<div class="mv-wrap">
  <!-- double buffer: A (front) + B (back) -->
  <model-viewer id="mvA" class="mv-layer"
    camera-controls disable-zoom disable-pan interaction-prompt="none"
    exposure="1" shadow-intensity="0"
    camera-orbit="180deg 75deg auto" autoplay></model-viewer>

  <model-viewer id="mvB" class="mv-layer hidden"
    camera-controls disable-zoom disable-pan interaction-prompt="none"
    exposure="1" shadow-intensity="0"
    camera-orbit="180deg 75deg auto" autoplay></model-viewer>
</div>

<script>
(function(){
  // ----- CONFIG -----
  const BASE = '{{ "/" | relative_url }}'.replace(/\/+$/, '') + '/';
  const FOLDER = 'assets/flow/history_pop_00/';   // change to another pop folder if you want
  const START  = 0;                                // first frame index
  const END    = 50;                               // last frame index (inclusive)
  const PAD    = 3;                                // zero-padding width in filenames
  const FPS    = 5;                                // playback speed; 5 fps ≈ 0.2s per frame
  const LOOP   = false;                            // play forward once; if true, restarts at START

  const mvA = document.getElementById('mvA');
  const mvB = document.getElementById('mvB');

  let cur = START;
  let front = mvA;         // currently visible
  let back  = mvB;         // loads next frame
  let playing = true;

  function framePath(i){
    const id = String(i).padStart(PAD, '0');
    return BASE + FOLDER + 'frame_' + id + '.glb';
  }

  function swapLayers(){
    // show 'back', hide 'front'
    front.classList.add('hidden');
    back.classList.remove('hidden');
    // swap references
    const tmp = front;
    front = back;
    back = tmp;
  }

  function scheduleNext(){
    if (!playing) return;
    if (cur > END) {
      if (LOOP) { cur = START; } else { return; } // stop at final frame
    }
    // start loading next frame on the hidden viewer
    back.src = framePath(cur);

    // when it finishes loading, swap to it and schedule the subsequent one
    const onLoaded = () => {
      back.removeEventListener('load', onLoaded);
      swapLayers();
      cur += 1;
      setTimeout(scheduleNext, 1000 / FPS);
    };
    back.addEventListener('load', onLoaded, { once: true });

    // if a frame fails (e.g., missing), skip it
    const onError = () => {
      back.removeEventListener('error', onError);
      cur += 1;
      setTimeout(scheduleNext, 0);
    };
    back.addEventListener('error', onError, { once: true });
  }

  // init: show first frame immediately on the front layer, then start advancing
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
