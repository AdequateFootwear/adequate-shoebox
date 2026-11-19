# adequate-shoebox — standing instructions

This repository is **public**, and GitHub Pages publishes it to the open internet at
https://adequatefootwear.github.io/adequate-shoebox/ from the `main` branch, root folder.
It holds **Adequate's Shoebox**: one page listing AdequateFootwear's trackable collection, with each
trackable's name, photo, TB code, tracking code, release date, mission, goal and About text. The QR
code Aegis hands out points here. Aegis uses **it/its** pronouns.

## The sheet is the source
- Every word on the page about a trackable comes from Aegis's collection sheet ("AdequateFootwear
  Trackable Collection and Missions"). A research chat drafts that text and keeps the sheet; Aegis
  decides what is published. This repository only builds the page from it.
- `tools/import_sheet.py` turns a snapshot of the sheet into `data/shoebox.json`, and
  `tools/build.py` turns that into `index.html`. Never edit either output by hand: change the sheet,
  then rebuild. The page's own labels, layout and script live in `tools/page.html`.
- Text goes on the page as plain text. Never add links, names or words that aren't in the sheet.
  If a web address shows up in the sheet's text, ask Aegis before it goes public.

## What stays off the page
- Hidden rows (drafts for coins not yet in hand) and rows with no TB code (not yet activated).
- AdequateTires's tracking code: people have to find it in the field to log it. The importer holds
  it back by TB code (`WITHHELD_TRACKING`); never publish it anywhere in this repository.
- Every other tracking code is public on purpose (Aegis's decision, 2026-11-13): the mission is what
  a discover costs, and Aegis deletes discover logs that fall short of it.
- No tracking, no analytics, no sign-in, and nothing collected from visitors. The only things the
  page loads from elsewhere are Google Fonts and the trackables' own photos on geocaching.com's
  image host; TB codes link to `https://coord.info/<TB code>`.
- Geocaching only. Nothing from Aegis's legal work or any client data, ever.

## Refreshing the page
1. Read the sheet with the Google Sheets connector's `get_spreadsheet`, with the grid data, range
   and fields that the top of `tools/import_sheet.py` lists, and save the result to a file outside
   this repository. (The sheet's address is in the collection handoff; ask Aegis.)
2. `python3 tools/import_sheet.py <that file> --read <the day you read it, YYYY-MM-DD>`. Read what it
   reports: rows left out, and trackables with no photo or no Released date.
3. `python3 tools/build.py`
4. Look at the page at phone width (~375 px) and desktop width, in light and dark mode.
5. Work on a branch and open a pull request. Aegis reviews and merges; never push to `main` and
   never merge.

When a trackable is activated, whoever fills in its TB code also fills in column K, **Released**,
with the date its trackable page shows as "Released" (YYYY-MM-DD).

## Never break a link
- Never rename this repository or move `index.html`. Printed QR codes point here, and GitHub
  doesn't redirect Pages URLs.
- Each card's id is its TB code, so `…/adequate-shoebox/#TBXXXXX` opens one trackable. Keep it so.

## Look
- It must read well on a phone and on a desktop: one column of cards on a phone, more side by side
  on a wider screen. Check both, with the keyboard too.
- It shares the AdequateFootwear house look with Tools of the Trade
  (https://adequatefootwear.github.io/adequate-footwear/): the forest-green-and-brass tokens on
  `:root` (light, dark and `[data-theme]` blocks), the compass-needle favicon and the green masthead
  with the brass contour lines. Green is for actions and highlights, red only for things that went
  wrong, brass for small labels. Keep text at 4.5:1 contrast or better.
