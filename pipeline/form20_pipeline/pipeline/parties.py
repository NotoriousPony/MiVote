"""Fuzzy-match a party/alliance candidate list to extracted names; fill party column.

party_list.txt line format:  <num> <AC name> | BJP Name One | INC Name Two | ...
Party tokens are configurable via cfg.PARTY_TOKENS.
"""
import re, csv, sqlite3, difflib
from collections import defaultdict


def norm_ac(s):
    s = s.lower().replace('(sc)', '').replace('(st)', '')
    return re.sub(r'[^a-z]', '', s)


def norm_name(s):
    s = s.upper().replace('.', ' ')
    drop = {'DR', 'CAPTAIN', 'CAPT', 'ADVOCATE', 'HAJI', 'THAKUR', 'COMRADE'}
    return ' '.join(t for t in re.split(r'\s+', s) if t and t not in drop)


def score(a, b):
    a, b = norm_name(a), norm_name(b)
    r = difflib.SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    j = len(ta & tb) / max(1, len(ta | tb))
    first = 0.15 if (a.split() and b.split() and a.split()[0] == b.split()[0]) else 0
    return 0.5 * r + 0.5 * j + first


def run(db_path, cfg):
    con = sqlite3.connect(db_path)
    db_acs = [r[0] for r in con.execute('SELECT ac_name FROM assembly')]
    ac_by_norm = {norm_ac(a): a for a in db_acs}
    ptok = '|'.join(re.escape(p) for p in cfg.PARTY_TOKENS)

    listed = []
    for line in open(cfg.PARTY_LIST):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^(\d+)\s+([^|]+?)\s*\|(.*)$', line)
        if not m:
            print('skipping unparseable line:', line[:60]); continue
        _, ac_raw, rest = m.groups()
        ac = cfg.PARTY_AC_ALIASES.get(norm_ac(ac_raw)) or ac_by_norm.get(norm_ac(ac_raw))
        if not ac:
            print('AC not matched, skipping:', ac_raw); continue
        for part in rest.split('|'):
            pm = re.match(r'^(%s)\s+(.+)$' % ptok, part.strip())
            if pm:
                listed.append((ac, pm.group(1), pm.group(2).strip()))
    print('listed candidates:', len(listed))

    by_ac = defaultdict(list)
    for ac, party, name in listed:
        if ac not in cfg.MANUAL_ENTRIES:  # manual entries already carry parties
            by_ac[ac].append((party, name))

    accepted, unmatched = [], []
    for ac, plist in by_ac.items():
        rows = con.execute('SELECT cand_idx, name, rank FROM candidate WHERE ac_name=?', (ac,)).fetchall()
        used_l, used_r = set(), set()
        for li, (party, name) in enumerate(plist):
            tgt = cfg.MATCH_OVERRIDES.get((ac, party))
            if tgt:
                hit = [r for r in rows if norm_name(r[1]) == norm_name(tgt)]
                assert hit, 'override not found: %s %s %s' % (ac, party, tgt)
                used_l.add(li); used_r.add(hit[0][0])
                accepted.append((ac, party, name, hit[0][0], hit[0][1], 1.0))
        pairs = []
        for li, (party, name) in enumerate(plist):
            if li in used_l:
                continue
            for idx, dbname, rank in rows:
                if idx in used_r:
                    continue
                s = score(name, dbname)
                if party in cfg.MAJOR_PARTIES and rank <= 3:
                    s += 0.18
                elif party not in cfg.MAJOR_PARTIES and rank <= 2:
                    s -= 0.05
                pairs.append((s, li, idx, dbname))
        pairs.sort(reverse=True)
        for s, li, idx, dbname in pairs:
            if li in used_l or idx in used_r or s < 0.40:
                continue
            used_l.add(li); used_r.add(idx)
            party, name = plist[li]
            accepted.append((ac, party, name, idx, dbname, round(s, 2)))
        for li, (party, name) in enumerate(plist):
            if li not in used_l:
                unmatched.append((ac, party, name))

    print('accepted: %d | unmatched: %d' % (len(accepted), len(unmatched)))
    lows = sorted(accepted, key=lambda x: x[5])[:15]
    if lows and lows[0][5] < 0.6:
        print('lowest-score matches - REVIEW THESE:')
        for x in lows:
            if x[5] < 0.6:
                print('  %-20s %-8s %-26s -> %-28s %.2f' % (x[0], x[1], x[2], x[4], x[5]))
    for ac, party, name in unmatched:
        print('  UNMATCHED (no party set): %-20s %-8s %s' % (ac, party, name))

    for ac, party, name, idx, dbname, s in accepted:
        con.execute('UPDATE candidate SET party=? WHERE ac_name=? AND cand_idx=?', (party, ac, idx))
        if (ac, party) in cfg.NAME_FROM_LIST:
            con.execute('UPDATE candidate SET name=? WHERE ac_name=? AND cand_idx=?', (name, ac, idx))
    con.commit()
    con.close()
