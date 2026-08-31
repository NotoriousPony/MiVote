"""
MiVote - build the Lok Sabha 2024 village layer for the Sirsa parliamentary seat.

Writes an `ls2024` block into each assembly segment's JSON, in the same shape as
the existing Vidhan Sabha data, so the compare screen can read both.

Only segments whose booths could be anchored to villages by name are written.
Where the Form 20 transcription carries no station names, no data is published -
a wrong village is worse than a missing one.
"""
import json, collections, os

SLUG = {'Dabwali':'dabwali','Ellenabad':'ellenabad','Kalanwali':'kalanwali','Rania':'rania',
        'Ratia':'ratia','Sirsa':'sirsa','Fatehabad':'fatehabad','Narwana':'narwana','Tohana':'tohana'}
PARTY = {0:'BJP', 1:'JJP', 3:'INLD', 4:'INC'}          # remainder contest as independents
NAMES = ['Ashok Tanwar','Ramesh Khatak','Lilu Ram Asakhera','Sandeep Lot Valmiki','Selja',
         'Mistri Daulat Ram Rolan','Dharampal Vartia','Rajinder Kumar','Dr. Rajesh Mehandia',
         'Karnail Singh Odhan','Jasvir Singh','Joginder Ram','Naveen Kumar Commando',
         'Bagdawat Ram','Ram Singh Panwar','Rahul Chouhan','Satpal Ladwal',
         'Sukhdev Singh Sandhu','Surender Kumar Phulan']
MIN_ANCHORED = 0.75        # below this the alignment is guesswork, so skip the segment
MAX_DRIFT = 0.35           # a village's electorate cannot swing this much between polls


def prune(villages, vs_villages):
    """
    Drop villages the alignment cannot be trusted for.

    Two things go wrong. Town booths carry only the town's name in the Lok Sabha
    Form 20, so an entire town collapses onto whichever ward it aligned to -
    visible as an absurd vote count. And an occasional village lands on its
    neighbour. Both show up as a large gap against the same village's assembly
    turnout, which barely moved between May and October 2024. Anything that
    drifts more than MAX_DRIFT is withheld rather than published wrong.
    """
    kept, dropped = {}, []
    for v, a in villages.items():
        if v.lower().startswith('ward no'):
            dropped.append((v, 'town ward - not separable in the Lok Sabha sheet'))
            continue
        base = vs_villages.get(v, {}).get('valid', 0)
        if base and abs(a['valid'] - base) / base > MAX_DRIFT:
            dropped.append((v, f"turnout {a['valid']} vs {base} in the assembly poll"))
            continue
        kept[v] = a
    return kept, dropped


def main():
    LS = json.load(open('ls_sirsa_clean.json'))
    MAP = json.load(open('ls_booth2village.json'))
    written, skipped = [], []

    for seg, S in LS.items():
        b2v = MAP[seg]['booth2village']
        anchored = len(set(MAP[seg]['anchored'])) / len(S['rows'])
        if anchored < MIN_ANCHORED:
            skipped.append((seg, round(100 * anchored)))
            continue

        flagged = set(S['flagged'])
        agg = collections.defaultdict(
            lambda: {'b': 0, 'valid': 0, 'nota': 0, 'votes': collections.Counter()})
        totals = collections.Counter()
        for r in S['rows']:
            v = b2v.get(r['booth'])
            if not v:
                continue
            a = agg[v]
            a['b'] += 1; a['valid'] += r['valid']; a['nota'] += r['nota']
            for i, c in enumerate(r['cands']):
                a['votes'][i] += c; totals[i] += c

        order = sorted(range(len(NAMES)), key=lambda i: -totals[i])
        cands = [{'i': i, 'n': NAMES[i], 'p': PARTY.get(i, 'IND'), 'v': totals[i],
                  'r': rank + 1, 't4': 1 if rank < 4 else 0}
                 for rank, i in enumerate(order)]

        villages = {v: {'b': a['b'], 'valid': a['valid'], 'nota': a['nota'],
                        'votes': {str(k): n for k, n in sorted(a['votes'].items()) if n}}
                    for v, a in sorted(agg.items())}

        path = f'webapp_data/{SLUG[seg]}.json'
        d = json.load(open(path))
        villages, dropped = prune(villages, d['villages'])

        d['ls2024'] = {'cands': cands, 'villages': villages,
                       'booths': len(b2v), 'nvill': len(villages),
                       'pc': 'Sirsa', 'flagged': len(flagged),
                       'anchored': round(100 * anchored), 'withheld': len(dropped)}
        json.dump(d, open(path, 'w'), separators=(',', ':'))
        written.append((seg, len(villages), len(dropped), round(100 * anchored), dropped))

    print(f"{'segment':<11}{'published':>10}{'withheld':>10}{'anchored':>10}")
    for s, nv, nd, a, _ in written:
        print(f"{s:<11}{nv:>10}{nd:>10}{a:>9}%")
    print('\nwithheld villages:')
    for s, _, _, _, dropped in written:
        for v, why in dropped:
            print(f"   {s:<11}{v[:34]:<36}{why}")
    print('\nskipped (station names missing or too few anchors):')
    for s, a in skipped:
        print(f"   {s} - only {a}% of booths anchored")
    return [s for s, *_ in written]


if __name__ == '__main__':
    main()
