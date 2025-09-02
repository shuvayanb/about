---
layout: page
title: Interactive CFD
permalink: /interactive-flow/
---

<!-- model-viewer runtime -->
<script type="module" src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer.min.js"></script>
<script nomodule src="https://unpkg.com/@google/model-viewer@latest/dist/model-viewer-legacy.js"></script>

<model-viewer
  src="{{ '/assets/flow/body_unlit.glb' | relative_url }}"
  camera-controls
  camera-orbit="180deg 75deg auto"
  style="width:100%; height:82vh; background:#ffffff;"
  auto-rotate
  exposure="1.0"
  shadow-intensity="0"
  interaction-prompt="none">
</model-viewer>

<p style="color:#8a91a2; font-size:0.9rem; margin-top:0.6rem;">
  Drag to orbit • Scroll to zoom • Colors = PR baked into vertices (blue → white → red)
</p>
