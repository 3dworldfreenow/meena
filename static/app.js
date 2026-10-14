// Everything interactive runs here, so the site also works as plain files on GitHub Pages:
// gotra search (Hindi or Roman spelling), full-text search of Meena Itihas, live suggestions,
// highlighting, page jumps, theme toggle and reader tabs.
(function () {
  var BASE = document.body.dataset.base || '';
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function url(path) { return BASE + path; }
  function param(name) { return new URLSearchParams(location.search).get(name) || ''; }

  // ---------- data (fetched once, only when needed) ----------
  var cache = {};
  function load(name) {
    if (!cache[name]) cache[name] = fetch(url('/data/' + name + '.json')).then(function (r) { return r.json(); });
    return cache[name];
  }

  // ---------- matching, same rules as meena/translit.py ----------
  var DEVA = /[ऀ-ॿ]/;
  function devaKey(t) {
    return t.normalize('NFC').replace(/़/g, '').replace(/ँ/g, 'ं').replace(/[\s()\-.,]/g, '');
  }
  function soundKey(t) {
    var s = t.toLowerCase().replace(/[^a-z]/g, '');
    [['w', 'v'], ['ph', 'f'], ['sh', 's'], ['z', 'j'], ['q', 'k'], ['x', 'ks']].forEach(function (p) { s = s.split(p[0]).join(p[1]); });
    s = s.replace(/ch+|c/g, 'c');                // c / ch / chh
    s = s.replace(/([kgjtdpbr])h/g, '$1');       // aspirates
    s = s.replace(/(.)\1+/g, '$1');              // doubled letters
    return s.replace(/[aeiouy]/g, '');           // vowels are spelled every which way
  }
  function similarity(a, b) {  // 1 - normalised edit distance
    var m = a.length, n = b.length, d = [], i, j;
    if (!m || !n) return 0;
    for (j = 0; j <= n; j++) d[j] = j;
    for (i = 1; i <= m; i++) {
      var prev = d[0]; d[0] = i;
      for (j = 1; j <= n; j++) {
        var t = d[j];
        d[j] = Math.min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] === b[j - 1] ? 0 : 1));
        prev = t;
      }
    }
    return 1 - d[n] / Math.max(m, n);
  }
  // g = [name, roman, soundKey, devaKey, page, alts]
  function matchGotras(list, q, limit) {
    q = q.trim(); if (!q) return [];
    var exact = [], starts = [], inside = [];
    if (DEVA.test(q)) {
      var k = devaKey(q);
      list.forEach(function (g, id) {
        var d = g[3];
        if (d === k) exact.push(id); else if (d.indexOf(k) === 0) starts.push(id); else if (d.indexOf(k) > 0) inside.push(id);
      });
    } else {
      var ql = q.toLowerCase().replace(/\s+/g, '').replace(/aa/g, 'a').replace(/ee/g, 'i').replace(/oo/g, 'u');
      var sk = soundKey(q);
      list.forEach(function (g, id) {
        var r = g[1].replace(/ /g, '');
        if (r === ql || (sk && g[2] === sk)) exact.push(id);
        else if (r.indexOf(ql) === 0 || (sk.length > 1 && g[2].indexOf(sk) === 0)) starts.push(id);
        else if (r.indexOf(ql) > 0) inside.push(id);
      });
      var byClose = function (a, b) { return similarity(ql, list[b][1].replace(/ /g, '')) - similarity(ql, list[a][1].replace(/ /g, '')); };
      exact.sort(byClose); starts.sort(byClose);
    }
    var res = exact.concat(starts, inside);
    return limit ? res.slice(0, limit) : res;
  }
  function gotraLink(list, id, cls) {
    var g = list[id];
    return '<a href="' + url('/gotra/' + id + '/') + '"' + (cls ? ' class="' + cls + '"' : '') + '><span>' + esc(g[0]) +
      (g[5].length ? ' <small>(' + esc(g[5].join(', ')) + ')</small>' : '') + ' <small>' + esc(g[1]) + '</small></span><small>पृ. ' + g[4] + '</small></a>';
  }

  // ---------- live suggestions under the header search box ----------
  var input = document.getElementById('qs');
  var box = document.getElementById('suggest');
  var timer = null, sel = -1;
  if (input) {
    input.addEventListener('focus', function () { load('gotras'); });
    input.addEventListener('input', function () {
      clearTimeout(timer);
      var q = input.value.trim();
      timer = setTimeout(function () {
        if (!q) { box.hidden = true; return; }
        load('gotras').then(function (list) {
          if (input.value.trim() !== q) return;
          box.innerHTML = matchGotras(list, q, 12).map(function (id) { return gotraLink(list, id); }).join('') +
            '<a class="all" href="' + url('/search/?q=' + encodeURIComponent(q)) + '">दोनों पुस्तकों में खोजें / search both books →</a>';
          box.hidden = false; sel = -1;
        });
      }, 120);
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

  // ---------- search page ----------
  var results = document.getElementById('results');
  if (results) {
    var q = param('q').trim();
    document.getElementById('searchq').value = q;
    document.title = (q ? 'खोज: ' + q : 'खोज') + ' — Meena Books';
    if (q) {
      results.hidden = false;
      load('gotras').then(function (list) {
        var ids = matchGotras(list, q, 300);
        document.getElementById('gcount').textContent = '· ' + ids.length + (ids.length >= 300 ? '+' : '');
        document.getElementById('gres').innerHTML = ids.map(function (id) { return '<li>' + gotraLink(list, id) + '</li>'; }).join('');
        document.getElementById('gnone').hidden = ids.length > 0;
      });
      var msg = document.getElementById('hmsg');
      if (!DEVA.test(q)) {
        msg.textContent = 'इतिहास पुस्तक हिन्दी में है — शब्द देवनागरी में लिखें (जैसे आमेर, मत्स्य)। The history book is in Hindi: type the word in Devanagari.';
      } else if (q.length < 2) {
        msg.textContent = 'कम से कम दो अक्षर लिखें।';
      } else {
        msg.textContent = 'खोज रहे हैं…';
        load('itihas').then(function (pages) {
          var hits = [];
          pages.forEach(function (p) {
            var t = p[2], i = t.indexOf(q);
            while (i >= 0 && hits.length < 300) {
              var a = Math.max(0, i - 90), b = Math.min(t.length, i + q.length + 90);
              hits.push('<li><a href="' + url('/itihas/page/' + p[0] + '/?hl=' + encodeURIComponent(q)) + '">' +
                (p[1] ? 'पृष्ठ ' + p[1] : 'स्कैन ' + p[0]) + '</a><div class="snip">' + (a ? '…' : '') + esc(t.slice(a, i)) +
                '<mark>' + esc(q) + '</mark>' + esc(t.slice(i + q.length, b)) + (b < t.length ? '…' : '') + '</div></li>');
              i = t.indexOf(q, i + q.length);
            }
          });
          document.getElementById('hcount').textContent = '· ' + hits.length + (hits.length >= 300 ? '+' : '') + ' उल्लेख';
          document.getElementById('hres').innerHTML = hits.join('');
          msg.textContent = hits.length ? '' : 'कोई उल्लेख नहीं मिला।';
        });
      }
    }
  }

  // ---------- highlight ?hl= on a history page ----------
  var ocr = document.getElementById('ocr');
  var hl = param('hl').trim();
  if (ocr && hl) {
    var parts = ocr.textContent.split(hl);
    if (parts.length > 1) {
      ocr.innerHTML = parts.map(esc).join('<mark>' + esc(hl) + '</mark>');
      var m = ocr.querySelector('mark'); if (m && innerWidth > 820) m.scrollIntoView({block: 'center'});
    }
  }
  if (hl) document.querySelectorAll('a[rel=prev], a[rel=next]').forEach(function (a) { a.href += '?hl=' + encodeURIComponent(hl); });

  // ---------- jump to a printed page number of Meena Itihas ----------
  document.querySelectorAll('form.jump').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var n = parseInt(f.querySelector('input').value, 10);
      if (n > 0) location.href = url('/itihas/book/' + n + '/');
    });
  });

  // ---------- random gotra ----------
  var rnd = document.getElementById('random');
  if (rnd) location.replace(url('/gotra/' + Math.floor(Math.random() * +rnd.dataset.n) + '/'));

  // ---------- theme: follows the system until the reader picks one ----------
  var btn = document.getElementById('theme');
  if (btn) btn.addEventListener('click', function () {
    var root = document.documentElement;
    var dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('theme', root.dataset.theme); } catch (e) {}
  });

  // ---------- reader: scan / text tabs on phones, arrow keys turn pages ----------
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
    if (t && reader) { var tb = document.querySelector('.tabs button[data-show="' + t + '"]'); if (tb) tb.click(); }
  } catch (e) {}
  document.addEventListener('keydown', function (e) {
    if (/INPUT|TEXTAREA/.test(document.activeElement.tagName)) return;
    var a = e.key === 'ArrowLeft' ? document.querySelector('[rel=prev]') : e.key === 'ArrowRight' ? document.querySelector('[rel=next]') : null;
    if (a) location.href = a.href;
  });

  // ---------- filter the visible gotra list as you type ----------
  var f = document.getElementById('listfilter');
  if (f) f.addEventListener('input', function () {
    var q = f.value.trim().toLowerCase(), n = 0;
    document.querySelectorAll('.gotras li').forEach(function (li) {
      var hit = !q || li.textContent.toLowerCase().indexOf(q) >= 0;
      li.hidden = !hit; if (hit) n++;
    });
    document.getElementById('count').textContent = n;
  });
})();
