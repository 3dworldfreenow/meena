// Live gotra suggestions under the header search box, theme toggle, reader tabs and keys.
(function () {
  var input = document.getElementById('qs');
  var box = document.getElementById('suggest');
  var timer = null, sel = -1;

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }

  function show(items, q) {
    if (!q) { box.hidden = true; return; }
    var html = items.map(function (g) {
      return '<a href="' + g.url + '"><span>' + esc(g.name) + ' <small>' + esc(g.roman) + '</small></span><small>पृ. ' + g.page + '</small></a>';
    }).join('');
    html += '<a class="all" href="/search?q=' + encodeURIComponent(q) + '">दोनों पुस्तकों में खोजें / search both books →</a>';
    box.innerHTML = html; box.hidden = false; sel = -1;
  }

  if (input) {
    input.addEventListener('input', function () {
      clearTimeout(timer);
      var q = input.value.trim();
      timer = setTimeout(function () {
        if (!q) { show([], ''); return; }
        fetch('/api/gotras?q=' + encodeURIComponent(q)).then(function (r) { return r.json(); })
          .then(function (items) { if (input.value.trim() === q) show(items, q); });
      }, 150);
    });
    input.addEventListener('keydown', function (e) {
      var links = box.querySelectorAll('a');
      if (box.hidden || !links.length) return;
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + links.length) % links.length;
        links.forEach(function (a, i) { a.classList.toggle('sel', i === sel); });
      } else if (e.key === 'Enter' && sel >= 0) {
        e.preventDefault(); location.href = links[sel].href;
      } else if (e.key === 'Escape') { box.hidden = true; }
    });
    document.addEventListener('click', function (e) { if (!box.contains(e.target) && e.target !== input) box.hidden = true; });
  }

  // theme: follows the system until the reader picks one
  var btn = document.getElementById('theme');
  if (btn) btn.addEventListener('click', function () {
    var root = document.documentElement;
    var dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('theme', root.dataset.theme); } catch (e) {}
  });

  // reader: scan / text tabs on phones, arrow keys for pages
  var reader = document.querySelector('.reader');
  document.querySelectorAll('.tabs button').forEach(function (b) {
    b.addEventListener('click', function () {
      reader.dataset.show = b.dataset.show;
      document.querySelectorAll('.tabs button').forEach(function (x) { x.classList.toggle('on', x === b); });
      try { localStorage.setItem('readerTab', b.dataset.show); } catch (e) {}
    });
  });
  try {
    var t = localStorage.getItem('readerTab');
    if (t && reader) { var b = document.querySelector('.tabs button[data-show="' + t + '"]'); if (b) b.click(); }
  } catch (e) {}
  document.addEventListener('keydown', function (e) {
    if (/INPUT|TEXTAREA/.test(document.activeElement.tagName)) return;
    var a = e.key === 'ArrowLeft' ? document.querySelector('[rel=prev]') : e.key === 'ArrowRight' ? document.querySelector('[rel=next]') : null;
    if (a) location.href = a.href;
  });

  // gotra page: filter the visible list as you type
  var f = document.getElementById('listfilter');
  if (f) f.addEventListener('input', function () {
    var q = f.value.trim().toLowerCase(), n = 0;
    document.querySelectorAll('.gotras li').forEach(function (li) {
      var hit = !q || li.textContent.toLowerCase().indexOf(q) >= 0;
      li.hidden = !hit; if (hit) n++;
    });
    var c = document.getElementById('count'); if (c) c.textContent = n;
  });
})();
