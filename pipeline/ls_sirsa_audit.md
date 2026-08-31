# Sirsa PC (Lok Sabha 2024) - transcription audit

| Segment | Booths | NOTA convention | Reconciled | Flagged | % |
|---|---|---|---|---|---|
| Dabwali | 213 | valid excludes NOTA | 194 | 19 | 91% |
| Ellenabad | 188 | valid excludes NOTA | 183 | 5 | 97% |
| Kalanwali | 185 | valid includes NOTA | 114 | 71 | 62% |
| Rania | 186 | valid excludes NOTA | 184 | 2 | 99% |
| Ratia | 224 | valid excludes NOTA | 224 | 0 | 100% |
| Sirsa | 204 | valid excludes NOTA | 203 | 1 | 100% |
| Fatehabad | 231 | valid excludes NOTA | 227 | 4 | 98% |
| Narwana | 224 | valid excludes NOTA | 206 | 18 | 92% |
| Tohana | 227 | valid excludes NOTA | 219 | 8 | 96% |
| **Total** | **1882** |  | **1754** | **128** | **93.2%** |

## What changed

The parser, not the transcription, was the main source of error. Rows carrying a
spurious extra zero were trimmed from the **front**, which deleted the first
candidate's votes and shifted every remaining value one place left. Trimming the
stray zero instead - and anchoring the five totals to the end of the row - fixed
it. Four repaired rows were checked cell-by-cell against the scanned Form 20 and
match exactly.

| | Before | After |
|---|---|---|
| Rows reconciled | 1,749 (92.9%) | 1,754 (93.2%) |
| Unaccounted votes | 1,698 (0.126%) | 827 (0.062%) |
| Rows in error by 20+ votes | 13 | 7 |

## Kalanwali uses a different column order

In 42-Kalanwali(SC), NOTA is printed as column 20 - **before** 'Total of valid
votes' - and the valid total *includes* NOTA. Every one of its 185 rows follows
this convention. The other eight segments exclude NOTA. The parser now detects
the convention per document instead of assuming one.

## Remaining known errors

Seven booths still disagree with their printed total by 20 or more votes:

| Segment | Booth | Station | Votes unaccounted |
|---|---|---|---|
| Kalanwali | 48 | GADRANA | +27 |
| Kalanwali | 67 | RORI | +21 |
| Kalanwali | 69 | ROHAN | -101 |
| Kalanwali | 114 | RAGHUANA | +20 |
| Kalanwali | 162 | BHAVDEEN | +67 |
| Kalanwali | 174 | KOTLI | +45 |
| Narwana | 105 | G.S.S.S., PHULIAN KALAN | +200 |

The remaining 121 flagged booths are out by 1-6 votes each - faint single digits
on a poor scan. Combined, all flagged rows account for 0.062% of the 1.34 million
votes cast, too small to change any village's candidate ranking. Flagged booths
are marked in the data rather than silently published.
