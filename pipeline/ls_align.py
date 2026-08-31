"""
MiVote - align Lok Sabha 2024 polling stations to the existing village mapping.

Booths were renumbered between the May 2024 Lok Sabha poll and the October 2024
assembly poll, so joining on booth number alone silently attributes a village's
votes to its neighbour. What did NOT change is the ORDER in which villages
appear down the Form 20. This aligns the two sequences (Needleman-Wunsch) using
name similarity, so each Lok Sabha booth inherits the village its station
actually belongs to.

Village names and counts come from the existing mapping and are never invented.
"""
import re, difflib

GENERIC = {'sirsa', 'kalanwali', 'kasbakalanwali', 'kasbadabwali', 'dabwali',
           'townfatehabad', 'fatehabad', 'tohana', 'narwana', 'ratia', 'ellenabad'}
NOISE = re.compile(r'\b(g\.?p\.?s|g\.?m\.?s|g\.?s\.?s\.?s|g\.?g\.?s\.?s\.?s|govt|government'
                   r'|school|primary|middle|senior|secondary|sr|sec|high|chaupal|dharamshala'
                   r'|room|no|block|left|right|part|wing|east|west|north|south|new|old'
                   r'|building|centre|center|anganwadi|panchayat|ghar|bhawan|samiti)\b',
                  re.I)


def norm(s):
    return re.sub(r'[^a-z]', '', str(s).lower())


def core(s):
    """Strip building words so 'G.S.S.S., DHANAURI' reduces to 'dhanauri'."""
    s = re.sub(r'\(.*?\)', ' ', str(s))
    s = NOISE.sub(' ', s)
    s = re.sub(r'\bmajra\s+\w+', ' ', s, flags=re.I)
    return norm(s) or norm(s)


def sim(station, village):
    a, b = core(station), core(village)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a.startswith(b) or b.startswith(a) or b in a or a in b:
        return 0.94
    r = difflib.SequenceMatcher(None, a, b).ratio()
    for t in re.split(r'[^a-z]+', core(station)) or []:
        if len(t) >= 4:
            r = max(r, difflib.SequenceMatcher(None, t, b).ratio())
    return r


def runs(pairs):
    """Collapse consecutive identical labels into runs of (label, [booths])."""
    out = []
    for booth, label in pairs:
        if out and out[-1][0] == label:
            out[-1][1].append(booth)
        else:
            out.append([label, [booth]])
    return out


def align(ls_runs, vs_runs, gap=-0.45, thresh=0.62):
    """Needleman-Wunsch over the two run sequences. Returns list of (i, j)."""
    n, m = len(ls_runs), len(vs_runs)
    S = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        S[i][0] = S[i - 1][0] + gap
    for j in range(1, m + 1):
        S[0][j] = S[0][j - 1] + gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = sim(ls_runs[i - 1][0], vs_runs[j - 1][0]) - 0.55   # centre on 0
            S[i][j] = max(S[i - 1][j - 1] + s, S[i - 1][j] + gap, S[i][j - 1] + gap)
    i, j, out = n, m, []
    while i > 0 and j > 0:
        s = sim(ls_runs[i - 1][0], vs_runs[j - 1][0]) - 0.55
        if abs(S[i][j] - (S[i - 1][j - 1] + s)) < 1e-9:
            out.append((i - 1, j - 1)); i -= 1; j -= 1
        elif abs(S[i][j] - (S[i - 1][j] + gap)) < 1e-9:
            i -= 1
        else:
            j -= 1
    return list(reversed(out))


def fill_gaps(pairs, ls_runs, vs_runs):
    """
    Villages appear in the same order in both elections, so runs lying between
    two confident anchors can be matched positionally. This recovers city-ward
    booths, whose Form 20 station label is just the town name and therefore
    carries no signal for name matching.
    """
    out = dict(pairs)
    anchors = sorted(pairs)
    bounds = [(-1, -1)] + anchors + [(len(ls_runs), len(vs_runs))]
    for (i1, j1), (i2, j2) in zip(bounds, bounds[1:]):
        gap_ls = list(range(i1 + 1, i2))
        gap_vs = list(range(j1 + 1, j2))
        if not gap_ls or not gap_vs:
            continue
        for n, i in enumerate(gap_ls):
            j = gap_vs[min(int(n * len(gap_vs) / len(gap_ls)), len(gap_vs) - 1)]
            out[i] = j
    return out
