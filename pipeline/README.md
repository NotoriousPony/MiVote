# Pipeline

How the data in `../data/` was produced.

| File | Does |
|---|---|
| `download_ceo_haryana.py` | Pulls Form 20 PDFs for any election/year from the CEO Haryana JSON API |
| `download_form20.py` | Older link-scraping downloader (kept for reference) |
| `sort_pdfs.py` | Splits them into digital-text vs scanned |
| `batch_pipeline.py` | Parses digital Form 20s, joins booths to villages |
| `form20_gemini.py` | Sends scanned pages for transcription |
| `ls_parse.py` | Reads transcribed CSVs, validates every row's arithmetic |
| `ls_align.py` | Aligns Lok Sabha booths to villages by name sequence |
| `build_ls.py` | Builds the Lok Sabha village layer, withholding what fails |
| `match_parties.py` | Attaches party labels to candidates |
| `build_report.py` | Reconciliation report |
| `build_site.py` | Assembles `index.html` + `data/` into the deployable site |
| `parse_2019_ls.py` | Parses a digital 2019 Lok Sabha Form 20 |
| `parse_2019_vs.py` | Grid detection + cell OCR for a scanned 2019 Form 20 |
| `vs2019_rows.py` | Dabwali VS 2019 rows read off the scan (checksum-verified) |
| `build_2019.py` | Builds the 2019 village layers |
| `ls_sirsa_audit.md` | Transcription audit for the Sirsa Lok Sabha data |

Run order: download -> sort -> batch_pipeline -> match_parties -> build_site.
The raw PDFs are not committed; `download_form20.py` fetches them.
Adding a state or year is a new config folder in `form20_pipeline/elections/`,
not new code.
