# adequate-shoebox — standing instructions

This repository is **public**, and GitHub Pages publishes it to the open internet at
https://adequatefootwear.github.io/adequate-shoebox/ from the `main` branch, root folder.
It holds **Adequate's Shoebox**: a main page listing AdequateFootwear's trackable collection, and a page
of its own for each trackable at `…/adequate-shoebox/<TB code>/`, with its photos, TB code, tracking
code, release date, mission, goal, About text and mission checklist. The QR code Aegis hands out points
here. Aegis uses **it/its** pronouns.

## The sheet is the source
- Every word on the page about a trackable comes from Aegis's collection sheet ("AdequateFootwear
  Trackable Collection and Missions"). A research chat drafts that text and keeps the sheet; Aegis
  decides what is published. This repository only builds the page from it.
- `tools/import_sheet.py` turns a snapshot of the sheet into `data/shoebox.json`;
  `tools/import_photos.py` copies Aegis's own photos into `photos/` and lists them in
  `data/photos.json`; and `tools/build.py` turns both into `index.html` and every `<TB code>/index.html`.
  Never edit any of those outputs by hand: change the sheet or the photos, then rebuild. The pages'
  own labels, layout and script live in `tools/page.html`, `tools/trackable.html`, `tools/style.css`
  and `tools/topo.svg`.
- **Photos** are Aegis's own files from Drive's Upload-ready folder (Claude › Projects › Geocaching ›
  Trackable Collection Missions › Photos › Upload-ready), where tracking numbers are already blurred.
  A file belongs to every trackable whose TB code is in its name. The importer strips all metadata
  (GPS included). Never link photos from geocaching.com's image host.
- Text goes on the page as plain text. Never add links, names or words that aren't in the sheet.
  If a web address shows up in the sheet's text, ask Aegis before it goes public.

## The mission checklist
- Each trackable's page shows its checklist from the sheet's column L, **Checklist**: one item per
  line, taken only from that row's mission. The research chat drafts it and Aegis approves it.
- Tags go at the end of a line, and the importer stops on any tag it doesn't know:
  `[GC code]` (the log holds a GC code), `[GC codes: N]` (N different GC codes), `[mentions: a, b]`
  (any of those words or phrases, as whole words, ignoring case and accents), `[words: N]` (the log
  is at least N words), `[photo]` (never lights; the cacher's own photo shows beside it) and `[bonus]`
  (optional). A line can carry several; when it has more than one that can light, all must be met.
- **Nothing ever marks an item as failing** (Aegis's rule, 2026-11-19). A cacher ticks items
  themselves; when their log newly covers a tagged item, its box lights and ticks, and the page never
  unticks one. Keep it that way: no red, no crosses, no "missing".
- The cacher's ticks and draft log stay in their own browser (`localStorage`, one key per trackable);
  photos they add are shown from their device and never stored or sent. Nothing else is kept.

## What stays off the page
- Hidden rows (drafts for coins not yet in hand) and rows with no TB code (not yet activated).
- AdequateTires's tracking code: people have to find it in the field to log it. The importer holds
  it back by TB code (`WITHHELD_TRACKING`); never publish it anywhere in this repository.
- Every other tracking code is public on purpose (Aegis's decision, 2026-11-13): the mission is what
  a discover costs, and Aegis deletes discover logs that fall short of it.
- No tracking, no analytics, no sign-in, and nothing collected from visitors (the checklist keeps a
  cacher's own ticks and draft log in their browser, nowhere else). The only thing the
  pages load from elsewhere is Google Fonts; TB codes link to `https://coord.info/<TB code>`.
- **Never read geocaching.com automatically.** Its Terms of Use forbid using "any robot, spider,
  scraper, or other means to access, display, or collect data from our services without our express
  written permission". Release dates, photos and anything else come from the sheet and Aegis's own
  files. (Log checking for Aegis uses the log emails geocaching.com sends to Aegis, in a session,
  never on these pages.)
- Geocaching only. Nothing from Aegis's legal work or any client data, ever.

## Refreshing the page
1. Read the sheet with the Google Sheets connector's `get_spreadsheet`, with the grid data, range
   and fields that the top of `tools/import_sheet.py` lists, and save the result to a file outside
   this repository. (The sheet's address is in the collection handoff; ask Aegis.)
2. `python3 tools/import_sheet.py <that file> --read <the day you read it, YYYY-MM-DD>`. Read what it
   reports: rows left out, and trackables with no Released date, checklist or photo.
3. If photos changed: copy the Upload-ready folder's files to a folder outside this repository and run
   `python3 tools/import_photos.py <that folder>`. Look at any new photo of AdequateTires before it
   goes in: its tracking code must not be readable.
4. `python3 tools/build.py`
5. Look at the pages at phone width (~375 px) and desktop width, in light and dark mode.
6. Work on a branch and open a pull request. Aegis reviews and merges; never push to `main` and
   never merge.

When a trackable is activated, whoever fills in its TB code also fills in column K, **Released**,
with the date its trackable page shows as "Released" (YYYY-MM-DD).

## Never break a link
- Never rename this repository or move `index.html`. Printed QR codes point here, and GitHub
  doesn't redirect Pages URLs.
- Each trackable's page is at `…/adequate-shoebox/<TB code>/`, and each card on the main page keeps its
  TB code as its id, so `…/adequate-shoebox/#TBXXXXX` still opens that card. Keep both: QR codes on
  individual tags may point at either.

## Look
- It must read well on a phone and on a desktop: one column of cards on a phone, more side by side
  on a wider screen. Check both, with the keyboard too.
- It shares the AdequateFootwear house look with Tools of the Trade
  (https://adequatefootwear.github.io/adequate-footwear/): the forest-green-and-brass tokens on
  `:root` (light, dark and `[data-theme]` blocks), the compass-needle favicon and the green masthead
  with the brass contour lines. Green is for actions and highlights, red only for things that went
  wrong, brass for small labels. Keep text at 4.5:1 contrast or better.
