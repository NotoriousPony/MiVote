"""
MiVote - parse the Dabwali Lok Sabha 2019 Form 20 (digital text layer).

The tail of a row is variable: when 'Rejected votes' is blank in the PDF the cell
is simply absent, so a row carries either three or four figures after the
candidate votes. Position from the end plus the printed checksum
(valid + rejected + NOTA = total) resolves which is which.
"""
import fitz, re, json

PDF = '/sessions/inspiring-charming-cerf/mnt/uploads/dabwali 2019 LS.pdf'
NC = 20


def candidates(doc):
    lines = [l.strip() for l in doc[0].get_text().split('\n')]
    out, i = [], lines.index('Sr. No Polling station') + 1
    while i < len(lines) and not lines[i].startswith('Total of valid'):
        if lines[i]:
            # a name wrapped onto two lines, e.g. "Vinod Kumar Sirkiband\n(Gihara)"
            if lines[i].startswith('(') and out:
                out[-1] += ' ' + lines[i]
            else:
                out.append(lines[i])
        i += 1
    return out


def parse():
    doc = fitz.open(PDF)
    cands = candidates(doc)
    text = '\n'.join(doc[p].get_text() for p in range(doc.page_count))
    rows, bad = [], []
    # a booth starts with "<n>-<NAME>" and is followed by its run of numbers
    parts = re.split(r'\n(?=\d{1,3}-[A-Z])', text)
    for chunk in parts:
        m = re.match(r'(\d{1,3})-([^\n]+)', chunk)
        if not m:
            continue
        booth, station = m.group(1), m.group(2).strip()
        nums = [int(x) for x in re.findall(r'(?<![\d.])\d+(?![\d.])', chunk[m.end():])]
        if len(nums) < NC + 3:
            continue
        cand = nums[:NC]
        cs = sum(cand)
        # Try the four-figure tail and the three-figure one, and keep whichever
        # balances. Reading a fixed length picks up a stray number from the row
        # or page total that follows.
        valid = rej = nota = total = 0
        ok = False
        for t in (nums[NC:NC+4], nums[NC:NC+3]):
            if len(t) == 4:
                v, rj, nt, tl = t
            elif len(t) == 3:
                # rejected votes are effectively always zero on EVMs, so an
                # absent cell is the rejected one and the figure shown is NOTA
                v, rj, nt, tl = t[0], 0, t[1], t[2]
            else:
                continue
            if cs == v and v + rj + nt == tl:
                valid, rej, nota, total, ok = v, rj, nt, tl, True
                break
        if not ok:                      # keep the 4-figure reading for the report
            t = nums[NC:NC+4]
            if len(t) == 4:
                valid, rej, nota, total = t
        rec = {'booth': booth, 'station': station, 'cands': cand, 'valid': valid,
               'rejected': rej, 'nota': nota, 'total': total}
        (rows if ok else bad).append(rec)
    return cands, rows, bad


if __name__ == '__main__':
    cands, rows, bad = parse()
    print(f'{len(cands)} candidates, {len(rows)} booths reconciled, {len(bad)} failed')
    for c in cands:
        print('  -', c)
    tot = [sum(r['cands'][i] for r in rows+bad) for i in range(NC)]
    print('\nconstituency-segment totals:')
    for i in sorted(range(NC), key=lambda i:-tot[i])[:6]:
        print(f'   {cands[i][:32]:<34}{tot[i]:>7}')
    print('   NOTA', sum(r['nota'] for r in rows+bad))
    print('   valid', sum(r['valid'] for r in rows+bad))
    if bad:
        print('\nfailed rows:')
        for r in bad[:6]:
            print('  ', r['booth'], r['station'], sum(r['cands']), r['valid'], r['rejected'], r['nota'], r['total'])
    json.dump({'cands':cands,'rows':rows+bad,'failed':[r['booth'] for r in bad]},
              open('dabwali_ls2019.json','w'), indent=1)
