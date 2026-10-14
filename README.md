# मीणा ग्रन्थ: Meena Books, interactive

A small Flask website for two books about the Meena community:

1. **मीना क्षत्रिय गोत्र संग्रह** (*Meena Kshatriya Gotra Sangrah*): compiled by Acharya Muni Magnasagar ji and
   Narayan Singh ji Naurawat, published by Madan Singh Dudawat, Sabalgarh (V.S. 2057). It lists 5,431 gotras,
   hand-typed from the scan with their page numbers (`data/gotra-pages/`), plus the foreword and the 15 "Amulya Ratna" sayings.
2. **मीणा-इतिहास** (*Meena Itihas*): by Rawat Saraswat, published by Bhuthalal Nadhla, Bassi (Jaipur), V.S. 2025 (1968).
   It has 322 scanned pages with OCR text, chapters, and the printed page numbers.

## What you can do on the site
- Search gotras in Hindi or English letters. `Chauhan`, `Chouhan` and `चौहान` all find चौहान.
- Browse gotras by letter (अ … ह), or pick a random one.
- Each gotra page shows its page in the booklet (with the scan), names that sound alike, nearby names,
  and **every page of Meena Itihas that mentions it**.
- Read Meena Itihas page by page, with the scan beside the text. You can jump by chapter or printed page number,
  matches are highlighted, and the ← → keys turn pages.
- Full-text search across both books. Light and dark themes. Works on phones.

## Run it
```bash
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
```
Page images are rendered from the PDFs the first time they are viewed and then cached in `cache/`.

## Data
| File | What |
|---|---|
| `data/gotra-pages/page-NN.txt` | gotras as printed on booklet page NN, one per line (`#क` = section letter). **Fix typos here.** |
| `data/gotras.json` | built from the above |
| `data/itihas.json` | OCR text of every page of Meena Itihas, page numbers, chapters |
| `data/booklet.json` | the booklet's foreword, note and sayings (from `tools/booklet_text.py`) |
| `books/meena-kshatriya-gotra-sangrah.pdf`, `2015.400496.Meena-Itiyas.pdf` | the scans |

To rebuild after editing the gotra pages:
```bash
python tools/build_data.py data/gotra-pages OCR_DIR   # OCR_DIR = tesseract output img-000.txt … img-321.txt
```
The history text comes from Tesseract (`-l hin`), so it contains OCR mistakes. The scan is always shown next to it.
