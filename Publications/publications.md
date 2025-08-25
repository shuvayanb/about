---
layout: page
title: Publications
---

<style>
/* Hide outer <ol> numbers so only IEEE’s [n] remains */
ol.bibliography { list-style: none; margin-left: 0; padding-left: 0; }
ol.bibliography > li { margin-left: 0; }
ol.bibliography > li::marker { content: ""; }

/* If CSL emits a separate span for the index, make it bold and add a space */
.csl-left-margin { font-weight: 700; }
.csl-left-margin::after { content: " "; }

/* Keep entries inline */
.csl-entry { display: inline; }
</style>

<script>
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('ol.bibliography > li').forEach(li => {
    const left = li.querySelector('.csl-left-margin');
    if (left) {
      // Ensure bold + exactly one space after the bracketed number
      left.style.fontWeight = '700';
      // Add a space node after if not already there
      const next = left.nextSibling;
      if (!(next && next.nodeType === Node.TEXT_NODE && /^\s/.test(next.textContent))) {
        left.insertAdjacentText('afterend', ' ');
      }
    } else {
      // No separate span → wrap a leading “[n]” and normalize spacing
      li.innerHTML = li.innerHTML.replace(/^\s*\[([0-9]+)\]\s*/, (_m, n) => `<strong>[${n}]</strong> `);
    }
  });
});
</script>


### Journals
{% bibliography %}
