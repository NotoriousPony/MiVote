"""
MiVote - add the 2019 Lok Sabha and Vidhan Sabha layers for Dabwali.

The Vidhan Sabha 2019 Form 20 prints no polling-station names, only serial
numbers, so it cannot be aligned by name on its own. Both 2019 sheets carry
exactly 217 booths in the same order, and they were polled five months apart, so
the station names from the Lok Sabha sheet identify the booths for both.

Every village is published only if its turnout is consistent with the same
village elsewhere - the same guard used for 2024.
"""
import json, openpyxl, collections
from ls_align import runs, align, sim, fill_gaps
from ls_map import refine
from vs2019_rows import ROWS as VS19

XLSX = '/sessions/inspiring-charming-cerf/mnt/uploads/Haryana_Assembly_Normalized.xlsx'
SLUG = 'webapp_data/dabwali.json'
MAX_DRIFT = 0.35

LS19_PARTY = {0:'INC', 1:'INLD', 2:'BSP', 3:'BJP', 4:'SHS', 8:'BMUP', 10:'PPID', 11:'PSPL',
              5:'RLP', 6:'BSCP', 9:'RMPI', 7:'JJP'}     # by index into the LS 2019 name list
VS19_CANDS = ['Amit Sihag','Aditya','Dr. Sita Ram','Subhash Chander','Kalu Ram','Malkeet Singh',
              'Rakesh Sharma','Sant Lal','Saravjit Singh Masitan','Sharvan Kumar Tanwar','Sanjeev Kumar']
VS19_PARTY = ['INC','BJP','INLD','BSP','BSCP','AAP','HLP','LKSK(P)','JJP','IND','IND']


def mapping():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    b2v = {}
    for r in wb['Dabwali'].iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        try:
            k = int(r[0])
        except (TypeError, ValueError):
            continue
        if k not in b2v:
            b2v[k] = str(r[1]).strip()
    return b2v


def booth_map(ls_rows, b2v):
    vs = runs([(b, b2v[b]) for b in sorted(b2v)])
    ls = runs([(r['booth'], r['station']) for r in ls_rows])
    good = [(i, j) for i, j in align(ls, vs) if sim(ls[i][0], vs[j][0]) >= 0.62]
    full = fill_gaps(good, ls, vs)
    out, anchored, crowded = {}, set(), set()
    for i, j in full.items():
        for b in ls[i][1]:
            out[b] = vs[j][0]
        if len(ls[i][1]) > len(vs[j][1]):
            crowded.update(ls[i][1])
    for i, _ in good:
        anchored.update(ls[i][1])
    refine(out, ls_rows, b2v, anchored, crowded)
    return out, anchored


def aggregate(rows, b2v_ls, nc):
    agg = collections.defaultdict(lambda: {'b':0,'valid':0,'nota':0,'votes':collections.Counter()})
    totals = collections.Counter()
    for r in rows:
        v = b2v_ls.get(r['booth'])
        if not v:
            continue
        a = agg[v]; a['b'] += 1; a['valid'] += r['valid']; a['nota'] += r['nota']
        for i, c in enumerate(r['cands']):
            a['votes'][i] += c; totals[i] += c
    return agg, totals


def layer(agg, totals, names, parties, base, nc):
    order = sorted(range(nc), key=lambda i: -totals[i])
    cands = [{'i': i, 'n': names[i], 'p': parties[i], 'v': totals[i],
              'r': k+1, 't4': 1 if k < 4 else 0} for k, i in enumerate(order)]
    villages, withheld = {}, []
    for v, a in sorted(agg.items()):
        if v.lower().startswith('ward no'):
            withheld.append((v, 'town ward - not separable')); continue
        b = base.get(v, {}).get('valid', 0)
        if b and abs(a['valid'] - b) / b > MAX_DRIFT:
            withheld.append((v, f"turnout {a['valid']} vs {b} in 2024")); continue
        villages[v] = {'b': a['b'], 'valid': a['valid'], 'nota': a['nota'],
                       'votes': {str(k): n for k, n in sorted(a['votes'].items()) if n}}
    return {'cands': cands, 'villages': villages, 'nvill': len(villages),
            'withheld': len(withheld)}, withheld


def main():
    b2v = mapping()
    LS = json.load(open('dabwali_ls2019.json'))
    bm, anchored = booth_map(LS['rows'], b2v)
    print(f"booth map: {len(bm)}/217 booths, {len(anchored)} anchored "
          f"({100*len(anchored)/217:.0f}%)")

    d = json.load(open(SLUG))
    base = d['villages']

    # Lok Sabha 2019
    aggL, totL = aggregate(LS['rows'], bm, 20)
    names = LS['cands']
    partiesL = [LS19_PARTY.get(i, 'IND') for i in range(20)]
    lay_ls, wL = layer(aggL, totL, names, partiesL, base, 20)

    # Vidhan Sabha 2019 - same booths, no station names of its own
    vs_rows = [{'booth': str(b), 'cands': r[:11], 'valid': r[11], 'nota': r[13]}
               for b, r in sorted(VS19.items())]
    aggV, totV = aggregate(vs_rows, bm, 11)
    lay_vs, wV = layer(aggV, totV, VS19_CANDS, VS19_PARTY, base, 11)

    d['ls2019'] = lay_ls; d['vs2019'] = lay_vs
    json.dump(d, open(SLUG, 'w'), separators=(',', ':'))
    print(f"\nls2019: {lay_ls['nvill']} villages published, {len(wL)} withheld")
    print(f"vs2019: {lay_vs['nvill']} villages published, {len(wV)} withheld")
    print('\ntop candidates')
    for c in lay_ls['cands'][:4]:
        print(f"   LS19  {c['n'][:26]:<28}{c['p']:<6}{c['v']:>7}")
    for c in lay_vs['cands'][:4]:
        print(f"   VS19  {c['n'][:26]:<28}{c['p']:<6}{c['v']:>7}")


if __name__ == '__main__':
    main()
