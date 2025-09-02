---
layout: page
title: Single GLB Test
permalink: /glb-test/
---

<!-- model-viewer runtime -->
<script type="module" src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer.min.js"></script>
<script nomodule src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer-legacy.js"></script>

<!-- Viewer -->
<model-viewer id="mv"
  src="{{ '/assets/flow/pop_00_opt.glb' | relative_url }}?v={{ site.time | date: '%s' }}"
  style="width:100%; height:82vh; background:#ffffff;"
  camera-controls
  exposure="1"
  shadow-intensity="0"
  interaction-prompt="none">
</model-viewer>

<script>
  // Ensure the timeline animation actually plays so the model is visible
  document.addEventListener('DOMContentLoaded', () => {
    const mv = document.getElementById('mv');
    mv.addEventListener('load', () => {
      // Prefer the "frames" animation; fall back to the first available
      const anims = mv.availableAnimations || [];
      mv.animationName = anims.includes('frames') ? 'frames' : (anims[0] || null);
      if (mv.animationName) {
        mv.autoplay = true;
        mv.play();
      }
    });
  });
</script>
