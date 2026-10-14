"""Build data/*.json from the transcribed gotra pages and the OCR of Meena Itihas.

    python tools/build_data.py GOTRA_TXT_DIR ITIHAS_OCR_DIR

GOTRA_TXT_DIR holds page-01.txt .. page-68.txt (one name per line, "#क" = section letter).
ITIHAS_OCR_DIR holds img-000.txt .. img-321.txt (tesseract -l hin output, one per PDF page).
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data')

# ---------------- Meena Itihas: printed page numbers ----------------
# Read by eye from the scan. Photo plates carry no number; the scan also skips
# printed page 33 and repeats pages 62-63 and 116-117.
ITIHAS_PDF_PAGES = 322
FRONT = {6: None, 7: 1, 8: 2, 9: 3, 10: 4, 11: 5, 12: 6, 13: 7, 14: 8}
PLATES = {139, 140, 143, 144, 147, 148, 155, 156, 167, 168, 205, 206, 233, 234, 250, 251, 254, 255, 258}
ANCHORS = {16: 9, 40: 34, 70: 62, 78: 70, 97: 89, 126: 116, 129: 119, 141: 129, 145: 131, 149: 133,
           157: 139, 169: 149, 200: 180, 207: 185, 232: 210, 236: 212, 246: 223, 252: 227, 256: 229,
           259: 231, 261: 233, 309: 281, 313: 285, 317: 289}
CHAPTERS = [
    (1, None, 'मुखपृष्ठ', 'Title page'),
    (3, None, 'विषय-क्रम', 'Contents'),
    (6, None, 'एक सम्मति', 'A word of approval (Nathuram Mirdha)'),
    (7, None, 'दो शब्द', 'Two words (Chief Minister Mohanlal Sukhadia)'),
    (8, None, 'प्रकाशकीय', "Publisher's note (Bhuthalal Nadhla)"),
    (11, None, 'आमुख', "Author's preface (Rawat Saraswat)"),
    (16, 1, 'मीणा जाति', 'The Meena community'),
    (30, 2, 'मीणा जाति का प्रसार', 'Spread of the Meena community'),
    (97, 3, 'आदि काल', 'Ancient period'),
    (111, 4, 'हिन्दू काल', 'Hindu period'),
    (116, 5, 'प्रारम्भिक मुस्लिम काल', 'Early Muslim period'),
    (129, 6, 'मीणा-राजपूत संघर्ष', 'Meena-Rajput conflict'),
    (200, 7, 'मुगल काल', 'Mughal period'),
    (208, 8, 'मराठा काल', 'Maratha period'),
    (213, 9, 'अंग्रेज काल', 'British period'),
    (219, 10, 'मीणा समाज और संस्कृति', 'Meena society and culture'),
    (240, 11, 'मीणों का सामाजिक और राजनैतिक पुनर्जागरण', 'Social and political awakening of the Meenas'),
    (261, 'परिशिष्ट 1', 'कुछ प्रमुख मीणा वंश-वृक्ष', 'Appendix 1: family trees of leading Meena clans'),
    (309, 'परिशिष्ट 2', 'मीणों सम्बन्धी तालिकायें', 'Appendix 2: tables about the Meenas'),
    (313, 'परिशिष्ट 3', 'सन्दर्भ ग्रन्थ-सूची', 'Appendix 3: bibliography'),
    (317, 'परिशिष्ट 4', 'मीणा जाति का बृहद् इतिहास - एक योजना', 'Appendix 4: plan for a larger history'),
]


def itihas_book_pages():
    book, cur = {}, None
    for pdf in range(1, ITIHAS_PDF_PAGES + 1):
        if pdf in FRONT:
            book[pdf] = FRONT[pdf]
        elif pdf < 16:
            book[pdf] = None
        elif pdf in PLATES:
            book[pdf] = None
        else:
            cur = ANCHORS.get(pdf, (cur or 8) + 1)
            book[pdf] = cur
    return book


# The book's typeface draws अ like श्र / ग्र, so OCR spells और as श्रौर. Undo the common cases.
OCR_FIXES = [
    (r'(?<![ऀ-ॿ])[शग]्रौ', 'औ'),
    (r'(?<![ऀ-ॿ])[शग]्रा(?=[^ा-्])', 'आ'),
    (r'(?<![ऀ-ॿ])अ्र', 'अ'),
    (r'(?<![ऀ-ॿ])[शग]्र(?=[कखगघचछजझटठडढतथदधनपफबभमयलवसह])(?!म[^ा]|द्धा|वण)', 'अ'),
    (r'(?<![ऀ-ॿ])[शग]्रध्याय', 'अध्याय'),
]


def clean_ocr(t):
    t = t.replace('\x0c', '')
    for pat, rep in OCR_FIXES:
        t = re.sub(pat, rep, t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


def build_itihas(ocr_dir):
    book = itihas_book_pages()
    pages = []
    for pdf in range(1, ITIHAS_PDF_PAGES + 1):
        with open(os.path.join(ocr_dir, f'img-{pdf - 1:03d}.txt'), encoding='utf-8') as f:
            text = clean_ocr(f.read())
        pages.append({'pdf': pdf, 'book': book[pdf], 'plate': pdf in PLATES, 'text': text})
    chapters = []
    for i, (pdf, num, hi, en) in enumerate(CHAPTERS):
        end = CHAPTERS[i + 1][0] - 1 if i + 1 < len(CHAPTERS) else ITIHAS_PDF_PAGES
        chapters.append({'pdf': pdf, 'end': end, 'num': num, 'title': hi, 'title_en': en, 'book': book[pdf]})
    return {'chapters': chapters, 'pages': pages}


# ---------------- Gotra Sangrah ----------------

def build_gotras(txt_dir):
    out = []
    for page in range(1, 69):
        with open(os.path.join(txt_dir, f'page-{page:02d}.txt'), encoding='utf-8') as f:
            for line in f:
                name = line.strip().rstrip(',.।')
                if not name or name.startswith('#'):
                    continue
                if name.startswith('(') and name.endswith(')') and out and out[-1]['page'] == page:
                    out[-1].setdefault('alt', []).append(name[1:-1].strip())  # variant of the name above
                    continue
                m = re.fullmatch(r'(.+?)\s*\((.+)\)', name)
                g = {'name': m.group(1).strip() if m else name, 'page': page}
                if m:
                    g['alt'] = [m.group(2).strip()]
                out.append(g)
    return out


def main():
    gotra_dir, ocr_dir = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    gotras = build_gotras(gotra_dir)
    itihas = build_itihas(ocr_dir)
    with open(os.path.join(OUT, 'gotras.json'), 'w', encoding='utf-8') as f:
        json.dump(gotras, f, ensure_ascii=False, indent=0)
    with open(os.path.join(OUT, 'itihas.json'), 'w', encoding='utf-8') as f:
        json.dump(itihas, f, ensure_ascii=False, indent=0)
    print(f'{len(gotras)} gotras, {len(itihas["pages"])} history pages')


if __name__ == '__main__':
    main()
