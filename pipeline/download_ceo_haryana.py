"""
MiVote - Form 20 downloader for CEO Haryana (any election, any year).

The booth-wise results page is driven by a small JSON API rather than a static
list of links, so this talks to that API directly instead of scraping HTML that
changes whenever the site is restyled:

    POST /WebCMS/GetYearListByElectionType   electionType=2|3|4
    POST /WebCMS/FindBoothWiseResult         electionType=..&yearId=..

The second call returns one record per assembly segment, carrying the district,
the constituency name and the file path. Files land named by constituency, so
the rest of the pipeline can match them without a lookup table.

WHAT YOU GET
    Form20_LokSabha_2019/01-Kalka.pdf ... 90-Tigaon.pdf
    Form20_LokSabha_2019/_manifest.csv      file -> district, constituency, URL

HOW TO RUN
    pip install requests
    python download_ceo_haryana.py

    Edit ELECTION and YEAR below to pick a dataset. Re-running is safe: files
    already on disk are skipped, so you can stop and resume freely.

SIZES (Haryana, checked against the live site)
    Lok Sabha 2019     90 files    ~227 MB    mostly digital PDFs
    Vidhan Sabha 2019  90 files   ~1.15 GB    almost all scans
    Lok Sabha 2024     90 files    ~600 MB
    Vidhan Sabha 2024  90 files    ~250 MB
"""

import csv
import os
import re
import sys
import time
from urllib.parse import quote

import requests

# ---------------- settings: edit these two ----------------
ELECTION = "LOK SABHA"        # "LOK SABHA" | "VIDHAN SABHA" | "BYE ELECTION"
YEAR = "2019"                 # "2004" "2009" "2014" "2019" "2024" ...
OUT_DIR = None                # None = auto-name, e.g. Form20_LokSabha_2019
# ----------------------------------------------------------

BASE = "https://www.ceoharyana.gov.in"
PAGE = BASE + "/WebCMS/Start/1449"
FILES_ROOT = BASE + "/BoothWiseResult/"
ELECTION_TYPE = {"BYE ELECTION": 4, "LOK SABHA": 2, "VIDHAN SABHA": 3}

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": PAGE,
}


def safe(text, fallback):
    text = re.sub(r"[\\/:*?\"<>|]+", "-", (text or "").strip())
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:70] or fallback


def file_url(name):
    """FileName comes back with Windows separators and spaces; make it a URL."""
    parts = name.replace("\\", "/").split("/")
    return FILES_ROOT + "/".join(quote(p) for p in parts)


def looks_like_pdf(path):
    try:
        if os.path.getsize(path) < 5000:
            return False
        with open(path, "rb") as fh:
            return fh.read(5) == b"%PDF-"
    except OSError:
        return False


def listing(session, election, year):
    et = ELECTION_TYPE[election.upper()]
    r = session.post(BASE + "/WebCMS/GetYearListByElectionType",
                     data={"electionType": et}, timeout=60)
    r.raise_for_status()
    years = {str(y["YearName"]).strip(): y["YearId"] for y in r.json()}
    if year not in years:
        sys.exit(f"{election} has no {year}. Available: {', '.join(sorted(years))}")
    r = session.post(BASE + "/WebCMS/FindBoothWiseResult",
                     data={"electionType": et, "yearId": years[year]}, timeout=90)
    r.raise_for_status()
    return r.json()


def download(session, url, dest, tries=3):
    for attempt in range(1, tries + 1):
        try:
            with session.get(url, timeout=300, stream=True) as r:
                r.raise_for_status()
                tmp = dest + ".part"
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 16):
                        fh.write(chunk)
                os.replace(tmp, dest)
            if looks_like_pdf(dest):
                return True, os.path.getsize(dest)
            os.remove(dest)                      # an error page, not a PDF
            return False, 0
        except Exception as exc:                 # noqa: BLE001 - report and retry
            if attempt == tries:
                return False, str(exc)[:70]
            time.sleep(2 * attempt)
    return False, 0


def main():
    out = OUT_DIR or f"Form20_{ELECTION.title().replace(' ', '')}_{YEAR}"
    os.makedirs(out, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)
    session.get(PAGE, timeout=60)                # pick up cookies

    rows = listing(session, ELECTION, YEAR)
    print(f"{ELECTION} {YEAR}: {len(rows)} constituencies listed\n")

    got = skipped = failed = 0
    total_bytes = 0
    manifest = []
    for i, row in enumerate(rows, 1):
        ac = row.get("AssemblyConstituencyName") or f"AC{i}"
        district = row.get("DistrictName") or ""
        acid = row.get("AssemblyConstituencyId") or i
        url = file_url(row["FileName"])
        fname = f"{int(acid):02d}-{safe(ac, str(i))}.pdf"
        dest = os.path.join(out, fname)
        manifest.append({"file": fname, "ac_no": acid, "constituency": ac,
                         "district": district, "url": url})

        if looks_like_pdf(dest):
            skipped += 1
            total_bytes += os.path.getsize(dest)
            print(f"[{i:>2}/{len(rows)}] have  {fname}")
            continue

        ok, info = download(session, url, dest)
        if ok:
            got += 1
            total_bytes += info
            print(f"[{i:>2}/{len(rows)}] ok    {fname}  ({info/1e6:.1f} MB)")
        else:
            failed += 1
            print(f"[{i:>2}/{len(rows)}] FAIL  {fname}  {info}")
        time.sleep(0.4)                          # be gentle with a .gov.in host

    with open(os.path.join(out, "_manifest.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "ac_no", "constituency", "district", "url"])
        w.writeheader()
        w.writerows(manifest)

    print(f"\ndownloaded {got}, already had {skipped}, failed {failed}")
    print(f"folder: {os.path.abspath(out)}  ({total_bytes/1e6:.0f} MB)")
    print("manifest: _manifest.csv")

    # a file with a real text layer can be parsed directly; the rest need reading
    try:
        import fitz
    except ImportError:
        print("\n(install pymupdf to also report which files are scans)")
        return
    digital = scanned = 0
    for m in manifest:
        p = os.path.join(out, m["file"])
        if not looks_like_pdf(p):
            continue
        try:
            doc = fitz.open(p)
            chars = sum(len(doc[i].get_text().strip()) for i in range(min(3, doc.page_count)))
            doc.close()
        except Exception:                        # noqa: BLE001
            continue
        if chars > 600:
            digital += 1
        else:
            scanned += 1
    print(f"\ntext layer present (parse directly): {digital}")
    print(f"scanned images (need reading):       {scanned}")


if __name__ == "__main__":
    main()
