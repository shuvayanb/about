/* ---------------------------------------------------------------------------
 * Persistent-shell navigation.
 *
 * Progressive enhancement over ordinary links: fetch the target, swap only the
 * <main> subtree, keep the rail and the simulation alive. Falls back to a full
 * page load on any failure, and does nothing at all without fetch/pushState.
 * ------------------------------------------------------------------------- */
(function () {
  'use strict';

  if (!window.fetch || !window.history || !history.pushState || !window.DOMParser) return;

  var main = document.getElementById('main');
  if (!main) return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var OUT_MS = 150;

  var cache = new Map();
  var loadedSrc = new Set();
  var busy = false;

  Array.prototype.forEach.call(document.scripts, function (s) {
    if (s.src) loadedSrc.add(s.src);
  });

  /* -------------------------------------------------------------- helpers */

  function sameOrigin(url) {
    return url.origin === location.origin;
  }

  function navigable(a) {
    if (!a || a.target === '_blank' || a.hasAttribute('download')) return false;
    if (a.getAttribute('rel') === 'external') return false;
    var href = a.getAttribute('href');
    if (!href || href[0] === '#') return false;
    if (/^(mailto|tel|javascript):/i.test(href)) return false;

    var url;
    try { url = new URL(a.href, location.href); } catch (e) { return false; }
    if (!sameOrigin(url)) return false;

    var last = url.pathname.split('/').pop();
    if (last && last.indexOf('.') !== -1 && !/\.html?$/i.test(last)) return false;
    return url;
  }

  function fetchPage(url) {
    var key = url.pathname + url.search;
    if (cache.has(key)) return Promise.resolve(cache.get(key));
    return fetch(url.href, { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      })
      .then(function (html) {
        if (cache.size > 12) cache.clear();
        cache.set(key, html);
        return html;
      });
  }

  function runScripts(list) {
    return list.reduce(function (chain, info) {
      return chain.then(function () {
        if (info.src) {
          if (loadedSrc.has(info.src)) return;
          loadedSrc.add(info.src);
          return new Promise(function (resolve) {
            var s = document.createElement('script');
            Object.keys(info.attrs).forEach(function (k) { s.setAttribute(k, info.attrs[k]); });
            s.onload = s.onerror = function () { resolve(); };
            document.head.appendChild(s);
          });
        }
        var s = document.createElement('script');
        Object.keys(info.attrs).forEach(function (k) { s.setAttribute(k, info.attrs[k]); });
        s.textContent = info.text;
        try { main.appendChild(s); }
        catch (e) { console.warn('[nav] inline script failed', e); }
      });
    }, Promise.resolve());
  }

  function swap(html, url, restoreY) {
    var doc = new DOMParser().parseFromString(html, 'text/html');
    var incoming = doc.getElementById('main');
    if (!incoming) throw new Error('no #main in response');

    var scripts = Array.prototype.map.call(incoming.querySelectorAll('script'), function (s) {
      var attrs = {};
      Array.prototype.forEach.call(s.attributes, function (at) { attrs[at.name] = at.value; });
      return { src: s.src || null, text: s.textContent, attrs: attrs };
    });
    Array.prototype.forEach.call(incoming.querySelectorAll('script'), function (s) { s.remove(); });

    main.innerHTML = incoming.innerHTML;
    main.setAttribute('data-nav-id', incoming.getAttribute('data-nav-id') || '');
    document.title = doc.title || document.title;

    var desc = doc.querySelector('meta[name="description"]');
    var here = document.querySelector('meta[name="description"]');
    if (desc && here) here.setAttribute('content', desc.getAttribute('content') || '');

    var swapEl = main.querySelector('[data-swap]');
    if (swapEl && !reduced.matches) {
      swapEl.classList.add('is-entering');
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { swapEl.classList.remove('is-entering'); });
      });
    }

    if (window.SBRail) window.SBRail.sync();
    if (window.SBPubs) window.SBPubs.enhance();
    if (window.SBRipple) window.SBRipple.refresh();

    return runScripts(scripts).then(function () {
      if (typeof restoreY === 'number') {
        window.scrollTo(0, restoreY);
      } else if (url.hash) {
        var t = document.getElementById(decodeURIComponent(url.hash.slice(1)));
        if (t) t.scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' });
        else window.scrollTo(0, 0);
      } else {
        window.scrollTo(0, 0);
      }
      main.setAttribute('tabindex', '-1');
      main.focus({ preventScroll: true });
    });
  }

  function go(url, push, restoreY) {
    if (busy) return;
    busy = true;

    var swapEl = main.querySelector('[data-swap]');
    var wait = (swapEl && !reduced.matches)
      ? (swapEl.classList.add('is-leaving'), new Promise(function (r) { setTimeout(r, OUT_MS); }))
      : Promise.resolve();

    Promise.all([fetchPage(url), wait])
      .then(function (res) {
        if (push) history.pushState({ y: 0 }, '', url.href);
        return swap(res[0], url, restoreY);
      })
      .catch(function (err) {
        console.warn('[nav] falling back to full load:', err);
        location.href = url.href;
      })
      .then(function () { busy = false; });
  }

  /* --------------------------------------------------------------- events */

  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

    var a = e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;

    var url = navigable(a);
    if (!url) return;

    // in-page hash on the current document: let the browser handle it
    if (url.pathname === location.pathname && url.search === location.search && url.hash) {
      return;
    }
    if (url.href === location.href) { e.preventDefault(); return; }

    e.preventDefault();
    history.replaceState({ y: window.scrollY }, '');
    go(url, true);
  });

  window.addEventListener('popstate', function (e) {
    var url = new URL(location.href);
    var y = e.state && typeof e.state.y === 'number' ? e.state.y : 0;
    go(url, false, url.hash ? undefined : y);
  });

  // cheap prefetch on intent
  function prefetch(e) {
    var a = e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var url = navigable(a);
    if (!url) return;
    var key = url.pathname + url.search;
    if (cache.has(key)) return;
    fetchPage(url).catch(function () {});
  }
  document.addEventListener('pointerenter', prefetch, true);
  document.addEventListener('focusin', prefetch);

  history.replaceState({ y: window.scrollY }, '');
})();
