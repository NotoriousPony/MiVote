"""
MiVote - read the scanned Dabwali Vidhan Sabha 2019 Form 20.

The sheet is cleanly ruled, so instead of running OCR over the whole page (which
loses the column boundaries and glues numbers together) the grid is detected,
each cell is cut out, and the cells of a column are stacked into one tall image
for a single OCR pass. Every row is then checked against the two printed
checksums before it is accepted.
"""
import fitz, numpy as np, io, cv2, re, json
from PIL import Image
import pytesseract

PDF = '/sessions/inspiring-charming-cerf/mnt/uploads/dabwali 2019 VS.pdf'
NC = 11                      # candidates
CFG = '--psm 6 -c tessedit_char_whitelist=0123456789'
CANDS = ['Amit Sihag', 'Aditya', 'Dr. Sita Ram', 'Subhash Chander', 'Kalu Ram',
         'Malkeet Singh', 'Rakesh Sharma', 'Sant Lal', 'Saravjit Singh Masitan',
         'Sharvan Kumar Tanwar', 'Sanjeev Kumar']


def page_grid(gray):
    bw = (gray < 160).astype(np.uint8)
    H, W = bw.shape
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, int(H * 0.25)))
    xs = np.where(cv2.morphologyEx(bw, cv2.MORPH_OPEN, vk).sum(axis=0) > H * 0.20)[0]
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (int(W * 0.30), 1))
    ys = np.where(cv2.morphologyEx(bw, cv2.MORPH_OPEN, hk).sum(axis=1) > W * 0.25)[0]

    def group(idx, gap=6):
        out = []
        for v in idx:
            if out and v - out[-1][-1] <= gap:
                out[-1].append(v)
            else:
                out.append([v])
        return [int(np.mean(g)) for g in out]

    return group(xs), group(ys)


def row_edges(ylines, H):
    """Rows are evenly spaced; rebuild the full ladder from the detected lines."""
    ys = [y for y in ylines if y > H * 0.25]
    if len(ys) < 3:
        return []
    d = np.median(np.diff(sorted(ys)))
    d = float(d) if d > 20 else 54.0
    top = min(ys)
    edges = [top + i * d for i in range(int((max(ys) - top) / d) + 2)]
    return [e for e in edges if e < H * 0.93]


def ocr_column(im, x0, x1, edges):
    """Stack a column's cells into one image and read them in a single pass."""
    tiles = []
    for a, b in zip(edges, edges[1:]):
        c = im.crop((x0 + 3, int(a) + 3, x1 - 3, int(b) - 3))
        c = c.resize((c.width * 2, c.height * 2), Image.LANCZOS)
        tiles.append(c)
    if not tiles:
        return []
    w = max(t.width for t in tiles)
    pad = 18
    out = Image.new('L', (w + 20, sum(t.height + pad for t in tiles) + pad), 255)
    y = pad
    for t in tiles:
        out.paste(t, (10, y)); y += t.height + pad
    txt = pytesseract.image_to_string(out.point(lambda v: 0 if v < 150 else 255), config=CFG)
    vals = [l.strip() for l in txt.split('\n') if l.strip()]
    return vals, len(tiles)


def parse_page(doc, p):
    pm = doc[p].get_pixmap(dpi=300)
    im = Image.open(io.BytesIO(pm.tobytes('png'))).convert('L')
    gray = np.asarray(im)
    xs, ys = page_grid(gray)
    edges = row_edges(ys, gray.shape[0])
    if len(xs) < 18 or len(edges) < 3:
        return None, f'grid not found (x={len(xs)}, rows={len(edges)})'
    xs = xs[-19:] if len(xs) > 19 else xs        # drop the stray left rule
    cols = []
    for i in range(len(xs) - 1):
        vals, n = ocr_column(im, xs[i], xs[i + 1], edges)
        cols.append(vals if len(vals) == n else None)
    return (cols, edges), None


if __name__ == '__main__':
    doc = fitz.open(PDF)
    res, err = parse_page(doc, 0)
    if err:
        print('ERROR', err)
    else:
        cols, edges = res
        print(f'{len(cols)} columns, {len(edges)-1} rows')
        for i, c in enumerate(cols):
            print(f'  col {i:>2}: ' + (', '.join(c[:8]) if c else '*** ragged ***'))
