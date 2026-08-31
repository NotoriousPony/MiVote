"""
MiVote - build the Lok Sabha booth -> village mapping for the Sirsa segments.

Three passes:
  1. align  - match the sequence of polling-station names to the sequence of
              villages in the existing mapping (booths were renumbered between
              the May and October 2024 polls, but their order did not change)
  2. fill   - runs sitting between two confident anchors are matched by position,
              which recovers town booths whose station label is just the town name
  3. refine - where the station name matches the village sitting at the SAME booth
              number better than the aligned one, prefer the booth number. This
              splits runs the aligner merged, e.g. Dabwali booths 111 and 112 are
              both printed "PIPLI" but the mapping records them as Vipli and Pipli.
"""
import json, re, openpyxl
from ls_align import runs, align, sim, fill_gaps, core

XLSX = '/sessions/inspiring-charming-cerf/mnt/uploads/Haryana_Assembly_Normalized.xlsx'
SEGMENTS = ['Dabwali','Ellenabad','Kalanwali','Rania','Ratia','Sirsa','Fatehabad','Narwana','Tohana']


def vs_map(wb, seg):
    b2v = {}
    for r in wb[seg].iter_rows(min_row=2, values_only=True):
        if r[0] is None:
            continue
        try:
            k = int(r[0])
        except (TypeError, ValueError):
            continue
        if k not in b2v:
            b2v[k] = str(r[1]).strip()
    return b2v


def refine(booth2village, ls_rows, b2v, anchored, crowded):
    """
    Prefer the village sitting at the same booth number when either

      * its name simply fits the station better, or
      * the run it belongs to is 'crowded' - the aligner matched more Lok Sabha
        booths to a village than that village has booths in the mapping, which
        means it swallowed a neighbour. Dabwali 111 and 112 are both printed
        "PIPLI"; the mapping spells them Vipli and Pipli, so the run matched only
        one of them and took both booths. Booth number splits them correctly.
    """
    fixed = []
    for r in ls_rows:
        m = re.match(r'\d+', r['booth'])
        if not m:
            continue
        same = b2v.get(int(m.group()))
        if not same or str(same).lower().startswith('ward no'):
            continue
        cur = booth2village.get(r['booth'])
        if cur == same:
            continue
        s_same = sim(r['station'], same)
        s_cur = sim(r['station'], cur) if cur else 0
        take = s_same > max(s_cur, 0.85) or (r['booth'] in crowded and s_same >= 0.72)
        if take:
            booth2village[r['booth']] = same
            anchored.add(r['booth'])
            fixed.append((r['booth'], cur, same, r['station']))
    return fixed


def main():
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    LS = json.load(open('ls_sirsa_clean.json'))
    out = {}
    print(f"{'segment':<11}{'booths':>7}{'anchored':>10}{'filled':>8}{'refined':>9}")
    for seg in SEGMENTS:
        b2v = vs_map(wb, seg)
        vs = runs([(b, b2v[b]) for b in sorted(b2v)])
        ls = runs([(r['booth'], r['station']) for r in LS[seg]['rows']])
        pairs = align(ls, vs)
        good = [(i, j) for i, j in pairs if sim(ls[i][0], vs[j][0]) >= 0.62]
        full = fill_gaps(good, ls, vs)

        booth2village, anchored, crowded = {}, set(), set()
        for i, j in full.items():
            for b in ls[i][1]:
                booth2village[b] = vs[j][0]
            # more Lok Sabha booths than the village has in the mapping: the run
            # has almost certainly absorbed an adjacent village
            if len(ls[i][1]) > len(vs[j][1]):
                crowded.update(ls[i][1])
        for i, _ in good:
            anchored.update(ls[i][1])
        n_anchor = len(anchored)
        fixed = refine(booth2village, LS[seg]['rows'], b2v, anchored, crowded)

        out[seg] = {'booth2village': booth2village, 'anchored': sorted(anchored)}
        print(f"{seg:<11}{len(LS[seg]['rows']):>7}{n_anchor:>10}"
              f"{len(booth2village)-n_anchor:>8}{len(fixed):>9}")
        for b, was, now, st in fixed[:4]:
            print(f"      booth {b}: {was!r} -> {now!r}  (station {st!r})")
    json.dump(out, open('ls_booth2village.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
