"""Fuzzy-match alliance candidate list to extracted Form 20 candidates; fill party in DB."""
import re, json, sqlite3, difflib, csv, shutil

OUT = '/sessions/inspiring-charming-cerf/mnt/outputs/'
DB = '/tmp/haryana_village_results_2024.db'
con = sqlite3.connect(DB)
db_acs = [r[0] for r in con.execute('SELECT ac_name FROM assembly')]

def norm_ac(s):
    s = s.lower().replace('(sc)', '')
    return re.sub(r'[^a-z]', '', s)

AC_ALIAS = {'ambalacant': 'Ambala Cantt', 'gurgaon': 'Gurugram', 'nangalchaudhry': 'Nangal Chaudhary'}
ac_by_norm = {norm_ac(a): a for a in db_acs}

def norm_name(s):
    s = s.upper().replace('.', ' ')
    toks = [t for t in re.split(r'\s+', s) if t]
    drop = {'DR', 'CAPTAIN', 'CAPT', 'ADVOCATE', 'HAJI', 'THAKUR', 'COMRADE'}
    toks = [t for t in toks if t not in drop]
    return ' '.join(toks)

def score(a, b):
    a, b = norm_name(a), norm_name(b)
    r = difflib.SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    j = len(ta & tb) / max(1, len(ta | tb))
    first = 0.15 if (a.split() and b.split() and a.split()[0] == b.split()[0]) else 0
    return 0.5 * r + 0.5 * j + first

listed = []  # (db_ac, party, name)
for line in open(OUT + 'party_list.txt'):
    line = line.strip()
    if not line:
        continue
    m = re.match(r'^(\d+)\s+([^|]+?)\s*\|(.*)$', line)
    num, ac_raw, rest = m.groups()
    n = norm_ac(ac_raw)
    ac = AC_ALIAS.get(n) or ac_by_norm.get(n)
    assert ac, 'AC not matched: ' + ac_raw
    for part in rest.split('|'):
        part = part.strip()
        pm = re.match(r'^(BJP|INC|INLD|BSP|JJP|ASP\(KR\)|CPI\(M\))\s+(.+)$', part)
        if pm:
            listed.append((ac, pm.group(1), pm.group(2).strip()))
print('listed candidates:', len(listed))

# manual overrides decided by vote-pattern inspection: (ac, party) -> extracted name
OVERRIDES = {
    ('Sohna', 'INC'): 'ROHTAS SINGH',
    ('Jind', 'JJP'): 'DHARAM PAL TANWAR',  # same person, confirmed by user
    ('Tigaon', 'JJP'): 'TIKA RAM',
    ('Badhra', 'JJP'): 'YASHVIR',
    ('Karnal', 'JJP'): 'JETENDER ROYAL',
    ('Rohtak', 'INLD'): 'DILOUR MEHRA',
    ('Pataudi', 'JJP'): 'AMARNATH J. E.',
    ('Sonipat', 'INLD'): 'SARDHARAM SINGH',
    ('Hathin', 'INLD'): 'TAYUB HUSAIN URF NAZIR AHMED',
    ('Hathin', 'JJP'): 'RAVINDER KUMAR',
    ('Israna', 'INLD'): 'SURAJBHAN',
    ('Israna', 'JJP'): 'KUMAR SUNIL',
    ('Baroda', 'BSP'): 'DHARAM VIR',
    ('Guhla', 'JJP'): 'KRISHAN KUMAR',
    ('Badli', 'JJP'): 'KRISHAN KUMAR',
    ('Palwal', 'ASP(KR)'): 'KUMAR HARIT',
}
# glitched extractions to rename to the clean list spelling
RENAMES = {('Julana', 'INC'), ('Hodal', 'INC')}

from collections import defaultdict
by_ac = defaultdict(list)
for ac, party, name in listed:
    if ac != 'Shahbad':  # Shahbad already has parties from ECI
        by_ac[ac].append((party, name))

accepted, unmatched, renamed = [], [], []
for ac, plist in by_ac.items():
    rows = con.execute('SELECT cand_idx, name, rank FROM candidate WHERE ac_name=?', (ac,)).fetchall()
    used_l, used_r = set(), set()
    for li, (party, name) in enumerate(plist):
        tgt = OVERRIDES.get((ac, party))
        if tgt:
            hit = [r for r in rows if norm_name(r[1]) == norm_name(tgt)]
            assert hit, 'override not found: %s %s %s' % (ac, party, tgt)
            idx, dbname, rank = hit[0]
            used_l.add(li); used_r.add(idx)
            accepted.append((ac, party, name, idx, dbname, 1.0))
    pairs = []
    for li, (party, name) in enumerate(plist):
        if li in used_l:
            continue
        for idx, dbname, rank in rows:
            if idx in used_r:
                continue
            s = score(name, dbname)
            # prior: BJP/INC candidates are nearly always the top-ranked pair
            if party in ('BJP', 'INC', 'CPI(M)') and rank <= 3:
                s += 0.18
            elif party not in ('BJP', 'INC') and rank <= 2:
                s -= 0.05
            pairs.append((s, li, idx, dbname, rank))
    pairs.sort(reverse=True)
    for s, li, idx, dbname, rank in pairs:
        if li in used_l or idx in used_r or s < 0.40:
            continue
        used_l.add(li); used_r.add(idx)
        party, name = plist[li]
        accepted.append((ac, party, name, idx, dbname, round(s, 2)))
    for li, (party, name) in enumerate(plist):
        if li not in used_l:
            unmatched.append((ac, party, name))

print('accepted:', len(accepted), '| unmatched:', len(unmatched))
print('\nLOWEST-SCORE ACCEPTED (review):')
for x in sorted(accepted, key=lambda x: x[5])[:20]:
    print('  %-18s %-7s %-26s -> %-30s %.2f' % (x[0], x[1], x[2], x[4], x[5]))
print('\nUNMATCHED (party NOT set):')
for ac, party, name in unmatched:
    print('  %-18s %-7s %s' % (ac, party, name))

for ac, party, name, idx, dbname, s in accepted:
    con.execute('UPDATE candidate SET party=? WHERE ac_name=? AND cand_idx=?', (party, ac, idx))
    if (ac, party) in RENAMES:  # glitched extraction: use the clean list spelling
        con.execute('UPDATE candidate SET name=? WHERE ac_name=? AND cand_idx=?', (name, ac, idx))
        renamed.append((ac, dbname, name))
con.commit()
print('\nnames corrected from party list:', len(renamed))

n_top4_labeled = con.execute('SELECT COUNT(*) FROM candidate WHERE is_top4=1 AND party IS NOT NULL').fetchone()[0]
n_top4 = con.execute('SELECT COUNT(*) FROM candidate WHERE is_top4=1').fetchone()[0]
print('\ntop-4 candidates with party label: %d / %d' % (n_top4_labeled, n_top4))
shutil.copy(DB, OUT + 'haryana_village_results_2024.db')

with open(OUT + 'candidates.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['assembly', 'candidate_index', 'candidate_name', 'party', 'total_votes_evm', 'rank', 'is_top4'])
    w.writerows(con.execute('SELECT ac_name, cand_idx, name, party, total_votes_evm, rank, is_top4 FROM candidate ORDER BY ac_name, rank'))
print('candidates.csv updated')
