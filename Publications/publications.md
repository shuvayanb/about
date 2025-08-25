---
layout: page
title: Publications
---

<style>
/* Hide outer <ol> numbers so only IEEE’s [n] remains */
ol.bibliography { list-style: none; margin-left: 0; padding-left: 0; }
ol.bibliography > li { margin-left: 0; }
ol.bibliography > li::marker { content: ""; }
</style>

## Under Review
... (your text)

### Journals
{% bibliography --query '@article' %}

### Book Chapters
{% bibliography --query '@incollection' %}

### Conferences
{% bibliography --query '@inproceedings' %}
