---
layout: page
title: Single GLB — Simple Test
permalink: /glb-test/
---

<!-- model-viewer runtime -->
<script type="module" src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer.min.js"></script>
<script nomodule src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer-legacy.js"></script>

<!-- One GLB, no animation required -->
<model-viewer
  src="{{ '/assets/flow/history_pop_00/frame_000.glb' | relative_url }}?v={{ site.time | date: '%s' }}"
  style="width:100%; height:82vh; background:#ffffff;"
  camera-controls
  exposure="1"
  shadow-intensity="0"
  interaction-prompt="none">
</model-viewer>
