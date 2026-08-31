# Form 20 → village-wise results pipeline

Converts booth-wise Form 20 election results into a validated village-wise SQLite
database + validation report. Built for Haryana 2024; add any state/year by creating
a new election folder.

## Requirements

Python 3.9+ with: `pymupdf`, `openpyxl`. Optional for scanned PDFs: `pytesseract` + tesseract.

```
pip install pymupdf openpyxl pytesseract
```

## Folder structure

```
form20_pipeline/
  run_pipeline.py          <- run this
  pipeline/                <- shared code (don't edit per election)
  elections/
    haryana_2024/
      config.py            <- all election-specific settings
      party_list.txt       <- alliance/party candidate list (optional)
      data/
        form20/            <- one Form 20 PDF per constituency
        mapping.xlsx       <- booth->village mapping, one sheet per constituency
      output/              <- generated: DB, CSVs, report
```

## Run

```
python run_pipeline.py elections/haryana_2024
```

Steps executed: parse PDFs -> extract candidate names -> join mapping -> aggregate ->
validate -> build SQLite -> match parties -> validation report.

## Adding a new election (e.g. haryana_2029, punjab_2027)

1. Copy `elections/haryana_2024` to a new folder, empty the `data/` dir.
2. Collect inputs:
   - Form 20 PDFs (from the state CEO website), one per constituency.
     Digital ENCORE PDFs parse automatically; scanned PDFs are OCR'd (slower, verify carefully).
   - Booth->village mapping xlsx: one sheet per constituency, columns `Booth | Village`.
     Source: CEO polling station lists.
   - Party candidate list (optional): `party_list.txt`, one line per constituency:
     `12 Constituency Name | BJP Name One | INC Name Two | ...`
3. Edit `config.py`:
   - `AC_ALIASES`: PDF filename -> mapping sheet name, where spellings differ.
   - `RANGE_FIXES` / `SHEET_SKIP`: booth-range corrections for bad mapping sheets.
   - `MATCH_OVERRIDES`: force party matches the fuzzy matcher gets wrong.
   - `MANUAL_ENTRIES`: constituencies with no Form 20 (AC-level totals only).
4. Run, read the console validation summary, fix whatever it flags, re-run
   (parsed PDFs are cached in `output/parse_cache`; delete a file there to re-parse it).

## Validation (never skip)

The pipeline checks every booth row (candidate sum = valid total; valid+rejected+NOTA = total)
and matches per-candidate booth sums against the Form 20 printed totals row. A constituency
is only clean when: badrows=0, evm_match=True, unmapped=0. Also spot-check 3-4 known
results (winner + margin) against ECI published numbers before publishing anything.

## Output

- `results.db` (SQLite): tables `assembly`, `candidate`, `village`, `result` — ship this in the app.
- `village_results_readable.csv`, `candidates.csv`
- `validation_report.xlsx`

Postal ballots are AC-level and excluded from village numbers — show separately.
Auxiliary booths (e.g. `160A`) are credited to their parent booth's village.
