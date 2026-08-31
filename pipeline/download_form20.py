"""
MiVote - Form 20 bulk downloader (CEO Haryana)

WHAT IT DOES
  Opens the Form 20 listing page, finds every PDF link on it, and downloads
  them all into a folder - named after the link text (constituency name).

HOW TO USE (in IDLE / VS Code / any Python)
  1. Install the two libraries once. In a terminal or command prompt:
        pip install requests beautifulsoup4
  2. In your browser, open the CEO Haryana page that lists the Form 20 PDFs
     for Lok Sabha 2024 (the same kind of page you used for the assembly
     Form 20s). Copy its address and paste it below as PAGE_URL.
  3. Run this file. PDFs land in the folder set in OUT_DIR.
  4. Re-running is safe: already-downloaded files are skipped, so you can
     resume any time.

  Files smaller than 5 KB are flagged as SUSPECT - those are usually
  error pages, not real PDFs (that is what happened with Shahbad last time).
"""

import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ------------- SETTINGS: edit these two lines -------------
PAGE_URL = "https://www.ceoharyana.gov.in/WebCMS/Start/1449"
OUT_DIR = "Form20_LokSabha_2024"
# ----------------------------------------------------------

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0 Safari/537.36"),
    "Accept-Language": "en-IN,en;q=0.9",
}


def clean_name(text, url):
    """Make a safe filename from the link text (fall back to the URL name)."""
    text = (text or "").strip()
    if not text or len(text) < 2:
        text = url.split("/")[-1].replace(".pdf", "")
    text = re.sub(r"[\\/:*?\"<>|]+", "-", text)
    text = re.sub(r"\s+", " ", text).strip()[:80]
    return text + ".pdf"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    print("Opening listing page:", PAGE_URL)
    r = session.get(PAGE_URL, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if ".pdf" in href.lower():
            links.append((a.get_text(" ", strip=True), urljoin(PAGE_URL, href)))

    # de-duplicate while keeping order
    seen = set()
    links = [(t, u) for t, u in links if not (u in seen or seen.add(u))]

    print("PDF links found:", len(links))
    if not links:
        print("No PDF links found. The page may load its links with JavaScript -")
        print("tell Claude, and we will adapt the script for this page.")
        return

    done = skipped = failed = suspect = 0
    for i, (text, url) in enumerate(links, 1):
        fname = clean_name(text, url)
        path = os.path.join(OUT_DIR, fname)
        if os.path.exists(path) and os.path.getsize(path) > 5000:
            skipped += 1
            continue
        try:
            resp = session.get(url, timeout=120)
            resp.raise_for_status()
            with open(path, "wb") as f:
                f.write(resp.content)
            size = os.path.getsize(path)
            if size < 5000 or not resp.content[:5].startswith(b"%PDF"):
                suspect += 1
                print(f"[{i}/{len(links)}] SUSPECT (not a real PDF?): {fname} ({size} bytes)")
            else:
                done += 1
                print(f"[{i}/{len(links)}] ok: {fname} ({size//1024} KB)")
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(links)}] FAILED: {fname} -> {e}")
        time.sleep(1.5)  # be gentle with the government server

    print("\nFinished. downloaded:", done, "| skipped (already had):", skipped,
          "| failed:", failed, "| suspect:", suspect)
    print("Folder:", os.path.abspath(OUT_DIR))
    if failed or suspect:
        print("Re-run this script to retry failures. Check SUSPECT files by opening them.")
    print("\nNext: zip the folder and upload it to Claude to run the MiVote pipeline.")


if __name__ == "__main__":
    main()
