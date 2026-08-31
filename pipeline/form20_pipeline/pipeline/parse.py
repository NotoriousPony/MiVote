"""Parse a Form 20 PDF (ECI ENCORE format) into booth-wise vote rows.

Row layout per booth: [serial, ps_no, votes per candidate..., total_valid,
rejected, nota, total, tendered]. Handles: numbers glued together in the text
layer, alphanumeric auxiliary booths (160A), scanned PDFs via OCR cache.
"""
import fitz, re, os, json

TOK = re.compile(r'^\d+[A-Z]?$')


def get_pages_text(doc, ocr_cache_dir=None, cache_key=None):
    pages = [p.get_text() for p in doc]
    if sum(len(t) for t in pages) > 200 * len(pages):
        return pages, False
    cache = os.path.join(ocr_cache_dir or '.', (cache_key or 'x') + '.json')
    if cache_key and os.path.exists(cache):
        return json.load(open(cache)), True
    # OCR inline (slow). For very large scanned files consider pre-OCR into the cache.
    try:
        import pytesseract
        from PIL import Image
        import io
    except ImportError:
        raise RuntimeError('scanned PDF needs pytesseract installed: ' + str(cache_key))
    out = []
    for p in doc:
        pix = p.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes('png')))
        out.append(pytesseract.image_to_string(img, config='--psm 6'))
    if ocr_cache_dir:
        os.makedirs(ocr_cache_dir, exist_ok=True)
        json.dump(out, open(cache, 'w'))
    return out, True


def consume(toks, w):
    """Consume rows of width w; serial must increment 1,2,3... Stops at totals."""
    i, expect, rows = 0, 1, []
    while i < len(toks):
        t = toks[i]
        if isinstance(t, str):
            pre = str(expect)
            if t.startswith(pre) and re.fullmatch(r'\d+[A-Z]', t[len(pre):]):
                serial, ps, j = expect, t[len(pre):], i + 1
            else:
                break
        elif t == expect:
            if i + 1 >= len(toks):
                break
            ps = toks[i + 1]
            if isinstance(ps, str) and not re.fullmatch(r'\d+[A-Z]', ps):
                break
            serial, j = expect, i + 2
        else:
            break
        body = toks[j:j + w - 2]
        if len(body) < w - 2 or not all(isinstance(x, int) for x in body):
            break
        rows.append([serial, ps] + body)
        i = j + w - 2
        expect += 1
    return rows, toks[i:]


def parse_form20(path, ocr_cache_dir=None):
    if os.path.getsize(path) < 5000:
        return {'error': 'file too small - likely a broken download (404 page)'}
    doc = fitz.open(path)
    cache_key = os.path.basename(path).rsplit('.', 1)[0]
    pages, ocred = get_pages_text(doc, ocr_cache_dir, cache_key)

    lines0 = pages[0].split('\n')
    ac_name = ''
    for l in lines0:
        if 'Name of Assembly' in l:
            ac_name = l.split('...')[-1].strip()
    i_tv = [i for i, l in enumerate(lines0) if l.strip() == 'Votes']
    start = i_tv[-1] + 1 if i_tv else 0
    names_raw = []
    for l in lines0[start:]:
        if re.fullmatch(r'\d+(\s+\d+)*', l.strip()):
            break
        names_raw.append(l.strip())
    header_text = ' '.join(w for w in names_raw if w)

    flat = []
    for pt in pages:
        for l in pt.split('\n'):
            toks = l.split()
            if toks and all(TOK.fullmatch(t) for t in toks):
                flat.extend(int(t) if t.isdigit() else t for t in toks)

    best = None
    for w in range(8, 45):
        rows, rest = consume(flat, w)
        if best is None or len(rows) > len(best[1]):
            best = (w, rows, rest)
    W, rows, leftover = best
    leftover = [x for x in leftover if isinstance(x, int)]
    ncand = W - 7
    if ncand < 2 or len(rows) < 20:
        return {'error': 'parse failed (width=%d, rows=%d)' % (W, len(rows))}

    internal_bad = 0
    for r in rows:
        if sum(r[2:2 + ncand]) != r[2 + ncand] or r[2 + ncand] + r[3 + ncand] + r[4 + ncand] != r[5 + ncand]:
            internal_bad += 1

    L = ncand + 5  # totals rows: EVM, postal, grand
    evm = leftover[0:L] if len(leftover) >= L else None
    postal = leftover[L:2 * L] if len(leftover) >= 2 * L else None
    grand = leftover[2 * L:3 * L] if len(leftover) >= 3 * L else None

    booth_sums = [sum(r[2 + i] for r in rows) for i in range(ncand)]
    valid_sum = sum(r[2 + ncand] for r in rows)
    evm_match = evm is not None and booth_sums == evm[:ncand] and valid_sum == evm[ncand]
    if not evm_match and evm:  # tolerate glued numbers in the printed totals row
        expected = ''.join(str(x) for x in booth_sums + [valid_sum])
        actual = ''.join(str(x) for x in evm[:ncand + 1])
        evm_match = actual.startswith(expected)

    return {'ac_name': ac_name, 'ncand': ncand, 'rows': rows, 'header': header_text,
            'ocred': ocred, 'internal_bad': internal_bad, 'evm_match': evm_match,
            'evm': evm, 'postal': postal, 'grand': grand}
