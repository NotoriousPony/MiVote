# MiVote — village-wise election results for India

> **Live app:** https://mivote.pages.dev
> **Log in with:** `Nitish` / `Nitish@123`
>
> The app opens on a login screen, then asks for a 4-digit code — for this
> account the code is shown on screen, so nothing else is needed. The account is
> built into the app, so it works on any device or browser with no setup.

India publishes election results by constituency (too coarse) and by polling
booth (unusable — booth numbers with no village names). Neither answers the
question a voter actually asks: **how did my village vote?**

MiVote joins official Form 20 booth results to the villages those booths serve.
It is the first village-wise election results portal in India.

---

## Test credentials

The app opens on a login screen. A built-in reviewer account ships with the app
and works on any device or browser:

```
username: Nitish
password: Nitish@123
```

These are not printed on the login screen — it is a plain **Log in / Create
account** box, as a real product would be — so keep them from here.

Logging in is two-step: enter the credentials above, then the 4-digit code. For
this account the code appears on screen, because `Nitish` is a username rather
than an inbox. Accounts created with a real email address get the code by email.

Create your own account with **Create one** and the code is **emailed** to the
address you type. Accounts you create are stored in that browser only; the Nitish
account is seeded by the app itself, so it is always available.

Note: the built-in account is deliberately public — it exists so the app can be
reviewed. Real users create their own.

---

## The three required components

### 1. Authentication — two-step, with a 4-digit OTP on every entry
**The app is gated: the login screen is the first thing a visitor sees, and no
constituency, village or saved list is reachable while signed out.**

Sign up, log in, log out. Log out is in the top-right of every screen.

**Both journeys are two-step.** A password on its own never gets you in:

```
sign up  details        -> 4-digit code -> verified -> account created + signed in
log in   username + pw  -> 4-digit code -> verified -> signed in
```

The password is checked *before* a code is issued, so a wrong password never
reaches the second step. Codes expire after 2 minutes, allow 3 attempts, and can
be resent; three wrong codes clears the attempt and returns you to the start.
Validation also covers empty fields, malformed emails, passwords under 6
characters and duplicate accounts. Sessions persist across reloads.

**Codes are emailed for real.** Delivery runs through EmailJS, which sends from
the browser, so the app still needs no server. The three EmailJS ids sit in a
`MAIL` block at the top of `index.html`; they are publishable by design and the
private key is not used.

Two cases fall back to showing the code on screen rather than failing:

- the built-in reviewer account signs in as `Nitish`, which is a username and not
  an inbox, so there is nowhere to send to
- the send errors, or the monthly quota is spent

Either way the flow completes, which means a live demo cannot be derailed by a
mail outage. If a late reply arrives after the user has already verified, it is
discarded rather than written to a cleared session.

### 2. CRUD — saved villages
The core entity is a **saved village with a note**, used by voters, journalists
and campaign teams to track places they care about.

| Operation | Where |
|---|---|
| **Create** | Any village page → "+ Save to my list" |
| **Read** | "My villages" in the header |
| **Update** | Edit the note in My villages → Save |
| **Delete** | "Delete" on any row in My villages |

### 3. Core business flow
```
choose state → election type → year → Lok Sabha seat → Vidhan Sabha seat
   → village → read the result → save it with a note → compare across elections
```

---

## Data

| | VS 2024 | LS 2024 | VS 2019 | LS 2019 |
|---|---|---|---|---|
| Constituencies | 90 of 90 | 7 (Sirsa seat) | 1 (Dabwali) | 1 (Dabwali) |
| Villages and wards | 7,026 | 484 | 66 | 66 |
| Polling booths | 20,632 | 1,403 | 217 | 217 |
| Votes accounted for | 1.36 crore | 13.4 lakh | 1.55 lakh | 1.49 lakh |

**Dabwali is the worked example.** All four elections are loaded for that seat,
so 63 of its villages can be read across a full cycle — Lok Sabha 2019 →
Vidhan Sabha 2019 → Lok Sabha 2024 → Vidhan Sabha 2024. Chautala, for instance,
went BJP → INC → INC → INLD.

Every candidate's booth-sum is reconciled against the printed Form 20 total
before publication. Shahbad shows constituency-level results only, with a visible
note, because the government has not released its booth-wise Form 20.

**Lok Sabha 2024 (Sirsa).** Booths were renumbered between the May general
election and the October assembly election, so booth number alone is not a safe
join — it silently gives a village its neighbour's votes. What did not change is
the order villages appear in down the Form 20, so the two sequences are aligned
by name (Needleman-Wunsch) and each Lok Sabha booth inherits the village its
station actually belongs to. Against the official ECI totals, every one of the 19
candidates lands within 0.75%, the gap being postal votes, which Form 20 excludes
by design.

A village is published only if it clears two further tests: it must be anchored
by a name match, and its turnout must be within 35% of the same village's
assembly turnout. 30 villages failed and are withheld — town wards, which the
Lok Sabha sheet labels only with the town's name and so cannot be separated, and
those whose turnout gap indicates a bad alignment. Narwana and Tohana are not
published at all: their transcriptions carry no station names, leaving nothing to
anchor against.

**2019 (Dabwali).** The Lok Sabha sheet is a digital PDF and was parsed directly;
its rows carry either three or four figures after the candidate votes, because a
blank 'Rejected' cell is simply absent, so both readings are tried and the one
that satisfies the printed checksum is kept. The Vidhan Sabha sheet is a scan and
prints no station names at all — only serial numbers — so it cannot be aligned on
its own. Both 2019 sheets hold exactly 217 booths in the same order and were
polled five months apart, so the Lok Sabha sheet's station names identify the
booths for both. Every one of the 217 rows was read off the scan and checked
against both printed checksums, and all sixteen column totals match the sheet's
own 'Total EVM Votes' row exactly. Adding the printed postal row reproduces the
official ECI result to the vote (Amit Sihag 66,723 + 162 = 66,885).

## Tools and stack

- **Frontend:** hand-written HTML, CSS and vanilla JavaScript. No framework.
- **Charts:** hand-drawn SVG. No charting library.
- **Storage:** browser `localStorage` for accounts and saved villages.
- **Data:** one JSON file per constituency, fetched on demand.
- **Hosting:** Cloudflare Pages (static, free, no server).
- **Data pipeline:** Python — PyMuPDF for PDF parsing, openpyxl for spreadsheets,
  SQLite for the master database.
- **Email:** EmailJS for browser-side OTP delivery (no server required).
- **AI tools:** Claude (Cowork) for the pipeline, data verification and the app;
  Google Gemini for reading scanned Form 20s.

## Architecture and key decisions

**No backend.** The data never changes between elections, so it ships with the
app. The result loads instantly on a rural connection, costs nothing to host,
and cannot go down.

**Accounts live in the browser.** Since there is no server, sign-up stores a
salted-hash record in `localStorage`. That is honest prototype-grade auth: it is
real validation and a real session, but accounts do not sync across devices and
it is not production security. Moving to Supabase or Firebase auth is a
config-level change, not a rewrite.

**Verification is a feature.** Every constituency carries a data status. Sources
are cited. Where data is missing or provisional, the app says so on screen rather
than hiding it.

**Top 4, then Others.** A 20-candidate table is noise; four names answer the
question and the rest stay one tap away.

**Sort by votes or by share.** A village giving a candidate 120 of 125 votes is a
stronger signal than one giving 6,000 of 12,000. Both orderings ship because they
answer different questions.

## Setup

No build step, no dependencies.

```bash
git clone <this repo>
cd mivote
python -m http.server 8000      # any static server
# open http://localhost:8000
```

Deploying: upload the folder to Cloudflare Pages (or any static host).

```
index.html          the entire app
data/*.json         one file per constituency, plus _dir.json and sentiment.json
```

## Known limitations

- Shahbad has no booth-wise data — the government has not published it.
- Lok Sabha 2024 covers the Sirsa seat only; the other nine are still being
  digitised from scans. 2019 covers Dabwali only.
- Town wards have no Lok Sabha comparison, because that Form 20 labels every
  urban booth with the town's name alone.
- Accounts are per-browser, not synced across devices.
- Media sentiment is built but held back — automated tone analysis of Indian
  political coverage is unreliable and easily gamed, and it would borrow
  credibility from the verified election data sitting beside it.

## Roadmap

Four-election trend lines exist for Dabwali; extend 2019 to the rest of the Sirsa
seat, then the remaining nine Lok Sabha seats, then other states → Hindi
interface → interactive constituency map.

---

Built by **Nitish Chaudhary** — MA Political Science (CCSU, Meerut), MBA candidate
at MICA, Ahmedabad.
