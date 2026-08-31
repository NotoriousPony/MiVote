"""
MiVote - Lok Sabha 2024 Form 20 CSV parser (Sirsa PC, 9 assembly segments).

Reads the Gemini-transcribed CSV text files and rebuilds booth-wise rows.

Key rule: the 5 trailing figures (valid, rejected, NOTA, total, tendered) are
anchored to the END of the row, and the candidate votes are anchored to the
START. Anything left over in between is a transcription artefact and is
dropped - never the first candidate. An earlier version trimmed from the front,
which silently deleted the leading candidate's votes and shifted the whole row.
"""
import csv, json, re, os

UPL = '/sessions/inspiring-charming-cerf/mnt/uploads'
FILES = {'Dabwali':'Dabwali.txt','Ellenabad':'Ellanabad.txt','Kalanwali':'Kalanwali SC.txt',
         'Rania':'Rania.txt','Ratia':'Ratia SC.txt','Sirsa':'Sirsa.txt',
         'Fatehabad':'fatehabad.txt','Narwana':'narwana.txt','Tohana':'Tohana.txt'}

ROW = re.compile(r'(\d{1,4}[A-Z]?)\s*,\s*"([^"]*)"\s*,\s*((?:[0-9?]+\s*,\s*)*[0-9?]+)')


def header_cands(flat):
    """Candidate names sit between the 'station' column and the totals block."""
    cut = flat.lower().find('tendered')
    cols = [c.strip() for c in next(csv.reader([flat[:cut + 8]]))]
    start = next((i for i, c in enumerate(cols) if c.lower().endswith('station')), -1)
    out = []
    for c in cols[start + 1:]:
        lc = c.lower()
        if lc.startswith('nota') or 'valid' in lc or 'reject' in lc or lc in ('total',) or 'tender' in lc:
            break
        if c:
            out.append(c)
    return out


def parse(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    txt = re.sub(r'\s*CHECK\s*,[^\n]*', ' ', txt)
    flat = re.sub(r'\s+', ' ', txt)
    cands = header_cands(flat)
    nc = len(cands)
    cut = flat.lower().find('tendered')
    body = flat[cut + 8:]

    rows, notes = [], []
    for m in ROW.finditer(body):
        booth, station = m.group(1), m.group(2).strip()
        raw = [x.strip() for x in m.group(3).split(',') if x.strip()]
        if any('?' in x for x in raw):
            notes.append((booth, 'illegible digit'))
            continue
        nums = [int(x) for x in raw]
        if len(nums) < nc + 5:
            notes.append((booth, f'short row: {len(nums)} of {nc+5}'))
            continue
        # totals are anchored to the END of the row; candidates to the START
        tail = nums[-5:]
        cand = nums[:-5]
        # Some rows carry spurious extra zeros inserted by the transcriber.
        # Removing the LAST zero preserves every real candidate's position;
        # trimming from the front (the old bug) deleted the first candidate
        # and shifted the whole row.
        while len(cand) > nc and 0 in cand:
            cand.pop(len(cand) - 1 - cand[::-1].index(0))
        if len(cand) != nc:
            notes.append((booth, f'{len(cand)} candidate values, expected {nc} - row flagged'))
            continue
        if station.lower().startswith(('total', 'round', 'grand', 'sub')):
            continue
        rows.append({'booth': booth, 'station': station, 'cands': cand,
                     'valid': tail[0], 'rejected': tail[1], 'nota': tail[2],
                     'total': tail[3], 'tendered': tail[4]})
    return cands, rows, notes


def convention(rows):
    inc = sum(1 for r in rows if sum(r['cands']) + r['nota'] == r['valid'])
    exc = sum(1 for r in rows if sum(r['cands']) == r['valid'])
    return 'incl' if inc > exc else 'excl'


def validate(rows, conv):
    ok, bad = [], []
    for r in rows:
        cs = sum(r['cands'])
        exp = cs + r['nota'] if conv == 'incl' else cs
        good = exp == r['valid'] and r['valid'] + r['rejected'] + (0 if conv == 'incl' else r['nota']) == r['total']
        (ok if good else bad).append(r)
    return ok, bad


def main():
    out, summary = {}, []
    for seg, fn in FILES.items():
        p = os.path.join(UPL, fn)
        if not os.path.exists(p):
            summary.append((seg, 0, '-', 0, 0)); continue
        cands, rows, notes = parse(p)
        conv = convention(rows)
        ok, bad = validate(rows, conv)
        out[seg] = {'cands': cands, 'convention': conv,
                    'rows': rows, 'verified': [r['booth'] for r in ok],
                    'flagged': [r['booth'] for r in bad], 'notes': notes}
        summary.append((seg, len(rows), conv, len(ok), len(bad)))
    json.dump(out, open('ls_sirsa_clean.json', 'w'), indent=1)

    print(f"{'segment':<12}{'rows':>6}{'conv':>7}{'verified':>10}{'flagged':>9}{'pct':>7}")
    tr = tv = 0
    for seg, n, conv, o, b in summary:
        tr += n; tv += o
        print(f"{seg:<12}{n:>6}{conv:>7}{o:>10}{b:>9}{(100*o/n if n else 0):>6.0f}%")
    print(f"{'TOTAL':<12}{tr:>6}{'':>7}{tv:>10}{tr-tv:>9}{100*tv/tr:>6.1f}%")


if __name__ == '__main__':
    main()
