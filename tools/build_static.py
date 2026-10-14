"""Save the whole Flask site as plain files, for GitHub Pages.

    python tools/build_static.py OUT_DIR [--base /meena]

--base is the path the site is served under (https://USER.github.io/REPO/ -> /REPO).
Every page becomes OUT_DIR/<path>/index.html; scans and search data are saved alongside.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import BOOKLET, GOTRAS, LETTERS, PAGES, app  # noqa: E402


def main():
    out = sys.argv[1]
    base = sys.argv[sys.argv.index('--base') + 1].rstrip('/') if '--base' in sys.argv else ''
    if os.path.exists(out):
        shutil.rmtree(out)
    client = app.test_client()

    urls = ['/', '/gotra/', '/gotra/random/', '/itihas/', '/booklet/', '/search/', '/about/',
            '/data/gotras.json', '/data/itihas.json']
    urls += [f'/gotra/letter/{l}/' for l in LETTERS]
    urls += [f'/gotra/{g["id"]}/' for g in GOTRAS]
    urls += [f'/itihas/page/{p["pdf"]}/' for p in PAGES]
    urls += sorted({f'/itihas/book/{p["book"]}/' for p in PAGES if p['book']})
    urls += [f'/booklet/page/{n}/' for n in range(1, BOOKLET['pdf_pages'] + 1)]
    urls += [f'/scan/itihas/{p["pdf"]}.png' for p in PAGES]
    urls += [f'/scan/gotra/{n}.jpg' for n in range(1, BOOKLET['pdf_pages'] + 1)]

    for i, u in enumerate(urls):
        r = client.get(u, environ_overrides={'SCRIPT_NAME': base})
        if r.status_code != 200:
            raise SystemExit(f'{u}: HTTP {r.status_code}')
        path = os.path.join(out, u.lstrip('/'))
        if u.endswith('/'):
            path = os.path.join(path, 'index.html')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(r.get_data())
        r.close()
        if i % 1000 == 0:
            print(f'{i}/{len(urls)}', u, flush=True)

    r = client.get('/no-such-page/', environ_overrides={'SCRIPT_NAME': base})
    with open(os.path.join(out, '404.html'), 'wb') as f:
        f.write(r.get_data())
    shutil.copytree(os.path.join(app.root_path, 'static'), os.path.join(out, 'static'))
    open(os.path.join(out, '.nojekyll'), 'w').close()  # serve folders as they are
    print(f'done: {len(urls)} files in {out}')


if __name__ == '__main__':
    main()
