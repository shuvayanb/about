---
layout: page
title: Publications
---

<style>
/* Hide outer <ol> numbers so only IEEE’s [n] remains */
ol.bibliography { list-style: none; margin-left: 0; padding-left: 0; }
ol.bibliography > li { margin-left: 0; }
ol.bibliography > li::marker { content: ""; }

/* Make the IEEE index [n] bold and add space after it */
.csl-left-margin { 
  font-weight: 700;         /* bold [n] */
  margin-right: 0.5ch;      /* space between [n] and the text */
}

/* (Some CSLs wrap each item in .csl-entry; this keeps the line tidy) */
.csl-entry { display: inline; }
</style>

### Journals
{% bibliography %}
