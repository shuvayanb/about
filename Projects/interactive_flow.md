---
layout: page
title: Interactive CFD Viz
permalink: /interactive-flow/
---

<figure style="margin:0">
  <iframe
    src="{{ '/assets/flow/flow.html?v=' | append: site.time | date: '%s' | relative_url }}"
    style="width:100%; height:82vh; border:0;"
    loading="eager"
    allowfullscreen
  ></iframe>
  <figcaption style="font-size:0.9rem; color:#666; margin-top:0.4rem;">
    Live Bézier body + Newtonian pressure visualization. Use the sliders to morph the shape and see Cd/flowfield update.
  </figcaption>
</figure>
