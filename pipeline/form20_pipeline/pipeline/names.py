"""Extract per-candidate names from Form 20 pages using column x-positions.

The PDF text layer often glues adjacent names together; words spanning multiple
vote columns are split character-by-character at column boundaries. The header
repeats on every page, so results are voted across pages.
"""
import fitz, re

STOP = {'No', 'of', 'Valid', 'Votes', 'Cast', 'in', 'favour', 'No.', 'Of',
        'Total', 'Rejected', 'NOTA', 'Tendered', 'Serial', 'Polling', 'Station'}


def names_from_page(page, nc):
    words = page.get_text('words')
    y_fav = min((w[1] for w in words if w[4] == 'favour'), default=None)
    if y_fav is None:
        return None
    data_ys = [w[1] for w in words if re.fullmatch(r'\d+', w[4]) and w[0] < 70 and w[1] > y_fav + 5]
    if not data_ys:
        return None
    y_data = min(data_ys)
    row_words = sorted([w for w in words if abs(w[1] - y_data) < 6
                        and re.fullmatch(r'\d+[A-Z]?', w[4])], key=lambda w: w[0])
    centers = [(w[0] + w[2]) / 2 for w in row_words]
    if len(centers) < nc + 2:
        return None
    cand_centers = centers[2:2 + nc]

    rd = page.get_text('rawdict')
    col_frags = [[] for _ in range(nc)]
    for block in rd['blocks']:
        for line in block.get('lines', []):
            ly = line['bbox'][1]
            if not (y_fav + 2 < ly < y_data - 2):
                continue
            chars = []
            for span in line.get('spans', []):
                for ch in span.get('chars', []):
                    if ch['c'].strip():
                        chars.append((ch['bbox'][0], ch['bbox'][2], ch['c']))
            chars.sort()
            groups, cur = [], []
            for x0, x1, c in chars:
                if cur and x0 - cur[-1][1] > 1.5:
                    groups.append(cur); cur = []
                cur.append((x0, x1, c))
            if cur:
                groups.append(cur)
            for g in groups:
                gx0, gx1 = g[0][0], g[-1][1]
                covered = [i for i in range(nc) if gx0 - 1 <= cand_centers[i] <= gx1 + 1]
                if len(covered) <= 1:
                    cx = (gx0 + gx1) / 2
                    col = min(range(nc), key=lambda i: abs(cand_centers[i] - cx))
                    col_frags[col].append((round(ly), gx0, ''.join(c for _, _, c in g)))
                else:
                    sub = {i: '' for i in covered}
                    for x0, x1, c in g:
                        cx = (x0 + x1) / 2
                        col = min(covered, key=lambda i: abs(cand_centers[i] - cx))
                        sub[col] += c
                    for i, s in sub.items():
                        if s:
                            col_frags[i].append((round(ly), gx0, s))
    out = []
    for col in range(nc):
        toks = [t for _, _, t in sorted(col_frags[col]) if t not in STOP]
        out.append(' '.join(toks).strip())
    return out, sum(1 for n in out if not n)


def extract_candidate_names(pdf_path, nc):
    """Vote across all pages; per-slot majority of non-empty values."""
    doc = fitz.open(pdf_path)
    per_slot = [{} for _ in range(nc)]
    for p in doc:
        r = names_from_page(p, nc)
        if r is None:
            continue
        out, score = r
        for i, n in enumerate(out):
            if n:
                per_slot[i][n] = per_slot[i].get(n, 0) + (2 if score == 0 else 1)
    return [max(s, key=s.get) if s else '' for s in per_slot]
