"""
MiVote - sort Form 20 PDFs into DIGITAL and SCANNED

Digital PDFs have real text inside and can be read instantly by the normal
pipeline. Scanned ones are pictures of paper and need to be read by eye.

This takes a few seconds and changes nothing - it only copies files into two
new folders so we know what we are dealing with.

RUN
      cd C:\\MiVote
      python sort_pdfs.py
"""

import os
import shutil

import fitz

SOURCE_DIR = "Form20_LokSabha_2024"
DIGITAL_DIR = "pdf_digital"
SCANNED_DIR = "pdf_scanned"


def kind(path):
    """Return ('digital'|'scanned', pages, chars_on_first_pages)."""
    doc = fitz.open(path)
    n = doc.page_count
    check = min(n, 3)
    chars = sum(len(doc[i].get_text().strip()) for i in range(check))
    doc.close()
    # a real text layer gives hundreds of characters per page
    return ("digital" if chars > 200 * check else "scanned"), n, chars


def main():
    if not os.path.isdir(SOURCE_DIR):
        print("Cannot find folder:", os.path.abspath(SOURCE_DIR))
        return
    os.makedirs(DIGITAL_DIR, exist_ok=True)
    os.makedirs(SCANNED_DIR, exist_ok=True)
    pdfs = sorted(f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(".pdf"))
    dig, scn, bad = [], [], []

    for f in pdfs:
        p = os.path.join(SOURCE_DIR, f)
        try:
            k, pages, chars = kind(p)
        except Exception as e:
            bad.append((f, str(e)[:60]))
            continue
        dest = DIGITAL_DIR if k == "digital" else SCANNED_DIR
        target = os.path.join(dest, f)
        if not os.path.exists(target):
            shutil.copy2(p, target)
        size_mb = os.path.getsize(p) / 1e6
        (dig if k == "digital" else scn).append((f, pages, size_mb))

    print(f"\nTotal PDFs: {len(pdfs)}")
    print(f"  DIGITAL (no OCR needed): {len(dig)}  ->  folder {DIGITAL_DIR}")
    print(f"  SCANNED (need reading):  {len(scn)}  ->  folder {SCANNED_DIR}")
    if bad:
        print(f"  COULD NOT OPEN: {len(bad)}")
        for f, e in bad:
            print("     ", f, "-", e)

    if scn:
        total_mb = sum(s for _, _, s in scn)
        total_pages = sum(p for _, p, _ in scn)
        print(f"\nScanned set: {total_pages} pages, {total_mb:.0f} MB total")
        print("Upload the pdf_scanned folder to Claude in batches of about 10 files.")
        print("\nScanned files:")
        for f, p, s in scn:
            print(f"   {f}  ({p} pages, {s:.1f} MB)")

    print("\nDigital files can be processed automatically - tell Claude how many there are.")


if __name__ == "__main__":
    main()
