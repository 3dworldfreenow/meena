"""Meena books, interactive: the Meena Kshatriya Gotra Sangrah and Meena Itihas.

Run:  pip install -r requirements.txt  &&  python app.py   ->  http://127.0.0.1:5000
"""
import json
import os
import re
from difflib import SequenceMatcher
from functools import lru_cache

from flask import Flask, abort, jsonify, render_template, request, send_file, url_for

from meena.translit import deva_key, sound_key, to_roman

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'data')
BOOKS = {
    'gotra': os.path.join(ROOT, 'books', 'meena-kshatriya-gotra-sangrah.pdf'),
    'itihas': os.path.join(ROOT, '2015.400496.Meena-Itiyas.pdf'),
}
CACHE = os.path.join(ROOT, 'cache', 'pages')

app = Flask(__name__)


def load(name):
    with open(os.path.join(DATA, name), encoding='utf-8') as f:
        return json.load(f)


BOOKLET = load('booklet.json')    # foreword, sayings, pdf page for each printed page
GOTRAS = load('gotras.json')      # [{name, page}]
ITIHAS = load('itihas.json')      # {chapters: [...], pages: [{pdf, book, text}]}

for i, g in enumerate(GOTRAS):
    g['id'] = i
    g['roman'] = to_roman(g['name'])
    g['dkey'] = deva_key(g['name'])
    g['skey'] = sound_key(g['name'])
    g['letter'] = g['dkey'][:1]

LETTERS = []
for g in GOTRAS:
    if g['letter'] and g['letter'] not in LETTERS:
        LETTERS.append(g['letter'])

PAGES = ITIHAS['pages']
PAGE_BY_PDF = {p['pdf']: p for p in PAGES}
CHAPTERS = ITIHAS['chapters']


def chapter_of(pdf_page):
    cur = None
    for ch in CHAPTERS:
        if ch['pdf'] <= pdf_page:
            cur = ch
    return cur


# ---------- search ----------

def match_gotras(q, limit=None):
    """Hindi input matches spelling; Roman input matches by sound (Chouhan = चौहान)."""
    q = q.strip()
    if not q:
        return []
    if re.search(r'[ऀ-ॿ]', q):
        k = deva_key(q)
        exact = [g for g in GOTRAS if g['dkey'] == k]
        starts = [g for g in GOTRAS if g['dkey'].startswith(k) and g not in exact]
        inside = [g for g in GOTRAS if k in g['dkey'] and g not in exact and g not in starts]
    else:
        ql = re.sub(r'\s+', '', q.lower()).replace('aa', 'a').replace('ee', 'i').replace('oo', 'u')
        k = sound_key(q)
        def close(g):  # spelling closeness to what was typed, for ordering
            return -SequenceMatcher(None, ql, g['roman'].replace(' ', '')).ratio()
        exact = sorted((g for g in GOTRAS if g['roman'].replace(' ', '') == ql or (k and g['skey'] == k)), key=close)
        starts = sorted((g for g in GOTRAS if g not in exact and (g['roman'].startswith(ql) or (len(k) > 1 and g['skey'].startswith(k)))), key=close)
        inside = [g for g in GOTRAS if g not in exact and g not in starts and ql in g['roman'].replace(' ', '')]
    res = exact + starts + inside
    return res[:limit] if limit else res


def snippet(text, pos, length, width=90):
    a = max(0, pos - width)
    b = min(len(text), pos + length + width)
    return (('…' if a else '') + text[a:pos], text[pos:pos + length], text[pos + length:b] + ('…' if b < len(text) else ''))


def search_itihas(q, limit=200):
    """Plain substring search over the OCR text of Meena Itihas."""
    q = q.strip()
    if len(q) < 2:
        return []
    if not re.search(r'[ऀ-ॿ]', q):
        return []  # the history book is Hindi; Roman queries go through the gotra list
    hits = []
    for p in PAGES:
        t = p['text']
        start = 0
        while True:
            i = t.find(q, start)
            if i < 0:
                break
            hits.append({'page': p, 'snip': snippet(t, i, len(q))})
            start = i + len(q)
            if len(hits) >= limit:
                return hits
    return hits


def itihas_mentions(name):
    """Pages of Meena Itihas that mention a gotra (skips names of 1-2 letters: too noisy)."""
    base = re.sub(r'\s*\(.*?\)', '', name).strip()
    if len(base) < 3:
        return []
    pat = re.compile(r'(?<![ऀ-ॿ])' + re.escape(base) + r'(?![ऀ-ॿ])')
    out = []
    for p in PAGES:
        m = pat.search(p['text'])
        if m:
            out.append({'page': p, 'snip': snippet(p['text'], m.start(), len(base), 70)})
    return out


# ---------- pages ----------

@app.context_processor
def globals_():
    return {'n_gotras': len(GOTRAS), 'n_pages': len(PAGES), 'chapters': CHAPTERS, 'to_roman': to_roman}


@app.route('/')
def home():
    return render_template('home.html', booklet=BOOKLET)


@app.route('/gotra')
def gotra_list():
    q = request.args.get('q', '')
    letter = request.args.get('letter', '')
    if q:
        items = match_gotras(q)
    elif letter:
        items = [g for g in GOTRAS if g['letter'] == letter]
    else:
        items = [g for g in GOTRAS if g['letter'] == LETTERS[0]] if LETTERS else []
        letter = LETTERS[0] if LETTERS else ''
    return render_template('gotra_list.html', items=items, q=q, letter=letter, letters=LETTERS)


@app.route('/gotra/<int:gid>')
def gotra_detail(gid):
    if not 0 <= gid < len(GOTRAS):
        abort(404)
    g = GOTRAS[gid]
    near = GOTRAS[max(0, gid - 6):gid] + GOTRAS[gid + 1:gid + 7]
    alike = [x for x in GOTRAS if x['skey'] == g['skey'] and x is not g][:20] if len(g['skey']) > 1 else []
    return render_template('gotra_detail.html', g=g, near=near, alike=alike,
                           mentions=itihas_mentions(g['name']),
                           pdf_page=BOOKLET['list_pdf_page'][str(g['page'])])


@app.route('/gotra/random')
def gotra_random():
    import random
    return gotra_detail(random.randrange(len(GOTRAS)))


@app.route('/itihas')
def itihas_home():
    return render_template('itihas_home.html')


@app.route('/itihas/page/<int:pdf>')
def itihas_page(pdf):
    p = PAGE_BY_PDF.get(pdf)
    if not p:
        abort(404)
    hl = request.args.get('hl', '').strip()
    # split the text into (piece, is_match) so the template can <mark> matches safely
    parts = [(x, x == hl) for x in re.split('(' + re.escape(hl) + ')', p['text'])] if hl else [(p['text'], False)]
    return render_template('itihas_page.html', p=p, ch=chapter_of(pdf), parts=parts,
                           prev=pdf - 1 if pdf - 1 in PAGE_BY_PDF else None,
                           next=pdf + 1 if pdf + 1 in PAGE_BY_PDF else None,
                           last=PAGES[-1]['pdf'])


@app.route('/itihas/book-page')
def itihas_book_page():
    """Jump by the page number printed in the book."""
    n = request.args.get('n', type=int)
    for p in PAGES:
        if p['book'] == n:
            return itihas_page(p['pdf'])
    abort(404)


@app.route('/booklet')
def booklet():
    return render_template('booklet.html', booklet=BOOKLET)


@app.route('/booklet/page/<int:pdf>')
def booklet_page(pdf):
    if not 1 <= pdf <= BOOKLET['pdf_pages']:
        abort(404)
    return render_template('booklet_page.html', pdf=pdf, last=BOOKLET['pdf_pages'],
                           gotras=[g for g in GOTRAS if BOOKLET['list_pdf_page'].get(str(g['page'])) == pdf])


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    gotras = match_gotras(q, 300) if q else []
    hits = search_itihas(q) if q else []
    return render_template('search.html', q=q, gotras=gotras, hits=hits)


@app.route('/about')
def about():
    return render_template('about.html', booklet=BOOKLET)


# ---------- JSON API (used by the live search box) ----------

@app.route('/api/gotras')
def api_gotras():
    q = request.args.get('q', '')
    return jsonify([{'id': g['id'], 'name': g['name'], 'roman': g['roman'], 'page': g['page'],
                     'url': url_for('gotra_detail', gid=g['id'])} for g in match_gotras(q, 30)])


@app.route('/api/search')
def api_search():
    q = request.args.get('q', '')
    return jsonify([{'pdf': h['page']['pdf'], 'book': h['page']['book'], 'snip': h['snip'],
                     'url': url_for('itihas_page', pdf=h['page']['pdf'], hl=q)} for h in search_itihas(q, 50)])


# ---------- scanned page images ----------

@lru_cache(maxsize=2)
def open_pdf(book):
    import pymupdf
    return pymupdf.open(BOOKS[book])


@app.route('/scan/<book>/<int:pdf>')
def scan(book, pdf):
    """Render one page of a scanned PDF (cached on disk after the first time).
    The booklet is a colour photo -> JPEG; the history is a black-and-white scan -> PNG."""
    import pymupdf
    if book not in BOOKS:
        abort(404)
    doc = open_pdf(book)
    if not 1 <= pdf <= doc.page_count:
        abort(404)
    ext = 'png' if book == 'itihas' else 'jpg'
    path = os.path.join(CACHE, book, f'{pdf}.{ext}')
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if book == 'itihas':
            pix = doc[pdf - 1].get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6), colorspace=pymupdf.csGRAY)
            pix.save(path)
        else:
            pix = doc[pdf - 1].get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3))
            pix.save(path, jpg_quality=78)
    resp = send_file(path, mimetype='image/png' if ext == 'png' else 'image/jpeg')
    resp.cache_control.max_age = 86400 * 30
    return resp


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=bool(os.environ.get('DEBUG')))
