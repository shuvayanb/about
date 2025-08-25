---
layout: page
title: Publications
---

<style>
/* Hide the outer <ol> numbers so only IEEE’s [n] remains */
ol.bibliography { list-style: none; margin-left: 0; padding-left: 0; }
ol.bibliography > li { margin-left: 0; }
ol.bibliography > li::marker { content: ""; }

/* If CSL emits a span for the index (many ieee styles do), style it */
.csl-left-margin { font-weight: 700; }
.csl-left-margin::after { content: " "; }

/* Keep each entry on one line */
.csl-entry { display: inline; }
</style>

<script>
// Make [n] bold + add a single space in ALL cases.
// Works whether CSL emits .csl-left-margin or the [n] is just plain text.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('ol.bibliography > li').forEach(li => {
    const left = li.querySelector('.csl-left-margin');
    if (left) {
      // ensure bold + exactly one space after
      left.style.fontWeight = '700';
      const next = left.nextSibling;
      if (!(next && next.nodeType === Node.TEXT_NODE && /^\s/.test(next.textContent))) {
        left.insertAdjacentText('afterend', ' ');
      }
    } else {
      // wrap leading [number] and normalize spacing
      li.innerHTML = li.innerHTML.replace(/^\s*\[([0-9]+)\]\s*/, (_m, n) => `<strong>[${n}]</strong> `);
    }
  });
});
</script>

### Journals
{% bibliography --template bibitem %}
