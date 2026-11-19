# adequate-shoebox
The place for Adequate's collection of trackables and other shiny things picked up along the way, which others may discover if they complete the associated missions.

**The page:** https://adequatefootwear.github.io/adequate-shoebox/

Each trackable's card shows its photo, TB code (linked to its page on geocaching.com), tracking code,
release date, the mission to complete before logging it as discovered, its goal, and its story.
Link straight to one trackable with its TB code: `https://adequatefootwear.github.io/adequate-shoebox/#TBBE9T1`.

## How it's made
The page is built from Adequate's collection sheet, never edited by hand:
`tools/import_sheet.py` reads a snapshot of the sheet into `data/shoebox.json`, and `tools/build.py`
turns that into `index.html`. See `CLAUDE.md` for the full steps and what stays off the page.
