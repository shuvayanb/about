/* ---------------------------------------------------------------------------
 * Career / research rail.
 *
 * The connecting paths are drawn from measured DOM positions rather than
 * hard-coded geometry, so the graph stays correct at any font size, label
 * length or breakpoint. Active emphasis slides along the trunk via
 * stroke-dashoffset.
 * ------------------------------------------------------------------------- */
(function () {
  'use strict';

  var rail = document.getElementById('rail');
  if (!rail) return;

  var svg   = rail.querySelector('.rail__graph');
  var trunk = rail.querySelector('.rail__trunk');
  var lead  = rail.querySelector('.rail__lead');
  var nav   = rail.querySelector('.rail__nav');
  var items = Array.prototype.slice.call(rail.querySelectorAll('.rail__item[data-node]'));

  var geom = { y0: 0, y1: 0, x: 0, byNode: {} };

  function isStacked() {
    return !svg || getComputedStyle(svg).display === 'none';
  }

  function measure() {
    if (isStacked()) return false;

    var base = svg.getBoundingClientRect();
    if (!base.width || !base.height) return false;

    svg.setAttribute('viewBox', '0 0 ' + base.width + ' ' + base.height);

    var mains = [], subs = [], byNode = {};

    items.forEach(function (a) {
      var dot = a.querySelector('.rail__dot');
      if (!dot) return;
      var r = dot.getBoundingClientRect();
      if (!r.width) return;
      var p = {
        node: a.getAttribute('data-node'),
        kind: a.getAttribute('data-kind'),
        x: r.left - base.left + r.width / 2,
        y: r.top - base.top + r.height / 2
      };
      byNode[p.node] = p;
      (p.kind === 'sub' ? subs : mains).push(p);
    });

    if (mains.length < 2) return false;

    var x = mains[0].x;
    var y0 = mains[0].y;
    var y1 = mains[mains.length - 1].y;

    var d = 'M' + x + ',' + y0 + 'V' + y1;
    subs.forEach(function (p) {
      d += 'M' + x + ',' + p.y + 'H' + (p.x - 1);
    });
    trunk.setAttribute('d', d);

    var leadD = 'M' + x + ',' + y0 + 'V' + y1;
    lead.setAttribute('d', leadD);
    var len = Math.max(1, y1 - y0);
    lead.style.strokeDasharray = len + ' ' + len;
    lead.style.strokeDashoffset = len;

    geom = { y0: y0, y1: y1, x: x, len: len, byNode: byNode };
    return true;
  }

  function setLead(node) {
    if (isStacked() || !geom.len) return;
    var p = geom.byNode[node];
    if (!p) { lead.style.strokeDashoffset = geom.len; return; }
    var reach = Math.max(0, Math.min(geom.len, p.y - geom.y0));
    lead.style.strokeDashoffset = (geom.len - reach);
  }

  /* ------------------------------------------------------------ active */

  var activeNode = null;

  /* On the stacked layout the rail is a horizontal strip, so keep whatever is
     active scrolled into view. */
  function reveal(node) {
    if (!isStacked() || !nav) return;
    var el = rail.querySelector('.rail__item[data-node="' + node + '"]');
    if (!el) return;
    var n = nav.getBoundingClientRect();
    var e = el.getBoundingClientRect();
    if (e.left >= n.left + 8 && e.right <= n.right - 30) return;
    nav.scrollTo({
      left: nav.scrollLeft + (e.left - n.left) - n.width / 2 + e.width / 2,
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
    });
  }

  function mark(node) {
    if (node === activeNode) return;
    activeNode = node;
    items.forEach(function (a) {
      var on = a.getAttribute('data-node') === node;
      a.classList.toggle('is-here', on && a.getAttribute('data-kind') === 'chapter');
      if (a.getAttribute('data-kind') !== 'chapter') a.classList.toggle('is-active', on);
    });
    setLead(node);
    reveal(node);
  }

  function markSection() {
    var main = document.getElementById('main');
    var id = main ? main.getAttribute('data-nav-id') : null;
    items.forEach(function (a) {
      var on = a.getAttribute('data-node') === id;
      a.classList.toggle('is-active', on && a.getAttribute('data-kind') !== 'chapter');
      a.classList.remove('is-here');
      if (on) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    activeNode = id;
    setLead(id);
    if (id) reveal(id);
  }

  /* ---------------------------------------------------------- scrollspy */

  var spy = null;

  function startSpy() {
    stopSpy();
    var chapters = Array.prototype.slice.call(document.querySelectorAll('.chapter[data-chapter]'));
    if (!chapters.length || !('IntersectionObserver' in window)) return;

    var seen = new Map();
    spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { seen.set(e.target, e); });
      var best = null;
      seen.forEach(function (e) {
        if (!e.isIntersecting) return;
        if (!best || e.boundingClientRect.top < best.boundingClientRect.top) best = e;
      });
      chapters.forEach(function (c) { c.classList.toggle('is-here', !!best && c === best.target); });
      if (best) mark(best.target.getAttribute('data-chapter'));
    }, { rootMargin: '-15% 0px -55% 0px', threshold: 0 });

    chapters.forEach(function (c) { spy.observe(c); });
  }

  function stopSpy() {
    if (spy) { spy.disconnect(); spy = null; }
  }

  /* ------------------------------------------------------------- sync */

  function sync() {
    measure();
    var isHome = !!document.querySelector('.chapter[data-chapter]');
    if (isHome) {
      markSection();          // clears stale section highlight
      startSpy();
    } else {
      stopSpy();
      document.querySelectorAll('.chapter').forEach(function (c) { c.classList.remove('is-here'); });
      markSection();
    }
  }

  /* --------------------------------------------------------- theme flip */

  var toggle = document.getElementById('themetoggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var root = document.documentElement;
      var explicit = root.getAttribute('data-theme');
      var dark = explicit
        ? explicit === 'dark'
        : window.matchMedia('(prefers-color-scheme: dark)').matches;
      var next = dark ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('sb-theme', next); } catch (e) {}
      toggle.setAttribute('aria-pressed', String(next === 'dark'));
    });
  }

  /* ------------------------------------------------------------- events */

  var rt = null;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(function () { measure(); setLead(activeNode); }, 120);
  });

  if ('ResizeObserver' in window && nav) {
    new ResizeObserver(function () { measure(); setLead(activeNode); }).observe(nav);
  }

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () { measure(); setLead(activeNode); });
  }

  window.SBRail = { sync: sync, measure: measure };

  sync();
})();
