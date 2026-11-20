# adequate-shoebox
The place for Adequate's collection of trackables and other shiny things picked up along the way, which others may discover if they complete the associated missions.

**The page:** https://adequatefootwear.github.io/adequate-shoebox/

Each trackable has a card on the main page and a page of its own, with its photos, TB code (linked to
its page on geocaching.com), tracking code, release date, the mission to complete before logging it as
discovered, its goal, and its story. Its page also has the mission as a checklist: write or paste your
log there, and the items it covers light up (your log, photos and ticks stay on your device). A
trackable's page is at its TB code:
`https://adequatefootwear.github.io/adequate-shoebox/TBBE9T1/`.

## How it's made
The pages are built from Adequate's collection sheet and Adequate's own photos, never edited by hand:
`tools/import_sheet.py` reads a snapshot of the sheet into `data/shoebox.json`, `tools/import_photos.py`
copies the photos into `photos/`, and `tools/build.py` builds the main page and each trackable's page.
See `CLAUDE.md` for the full steps and what stays off the pages.
