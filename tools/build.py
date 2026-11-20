#!/usr/bin/env python3
"""Build the site from data/shoebox.json and data/photos.json.

Usage: python3 tools/build.py

Writes index.html (every trackable, as cards) and <TB code>/index.html (one page per
trackable), from the templates tools/page.html and tools/trackable.html, which share
tools/style.css and tools/topo.svg. Every word about a trackable comes from
data/shoebox.json, which tools/import_sheet.py makes from the collection sheet, and every
photo from data/photos.json, which tools/import_photos.py makes from Aegis's own files.
Never edit the built pages by hand.
"""
import datetime as dt
import hashlib
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
DATA = os.path.join(ROOT, 'data', 'shoebox.json')
PHOTOS = os.path.join(ROOT, 'data', 'photos.json')
TB_DIR = re.compile(r'TB[0-9A-Z]{4,7}')

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


def esc(s):
    return html.escape(s, quote=True)


def read(name):
    return open(os.path.join(TOOLS, name), encoding='utf-8').read()


def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return f'{MONTHS[d.month - 1]} {d.day}, {d.year}'


def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return 'group-' + (s or 'x')


def note_html(text):
    """The sheet's note, with *starred* words in italics, as the sheet shows them."""
    out = []
    for p in (x.strip() for x in text.split('\n')):
        if p:
            out.append('<p>' + re.sub(r'\*([^*\n]+)\*', r'<em>\1</em>', esc(p)) + '</p>')
    return '\n'.join(out)


def fill(page, fills, what):
    for k, v in fills.items():
        if page.count(k) != 1:
            raise SystemExit(f'{what} should hold {k} exactly once')
        page = page.replace(k, v)
    return page


def ids_html(t):
    ids = [f'<dt>TB code</dt><dd><a class="mono" href="https://coord.info/{esc(t["tb"])}">{esc(t["tb"])}</a></dd>']
    if t['tracking']:
        ids.append('<dt>Tracking code</dt><dd>'
                   f'<span class="mono code">{esc(t["tracking"])}</span>'
                   f'<button class="btn small copy" type="button" data-code="{esc(t["tracking"])}" '
                   f'aria-label="Copy the tracking code for {esc(t["name"])}">Copy</button></dd>')
    if t['released']:
        ids.append(f'<dt>Released</dt><dd><time datetime="{esc(t["released"])}">{esc(nice_date(t["released"]))}</time></dd>')
    return f'<dl class="ids">{"".join(ids)}</dl>'


def blocks_html(t):
    out = []
    if t['mission']:
        out.append(f'<div class="block"><span class="lbl">Your mission</span><p class="txt">{esc(t["mission"])}</p></div>')
    if t['goal']:
        out.append(f'<div class="block"><span class="lbl">Its goal</span><p class="txt">{esc(t["goal"])}</p></div>')
    return ''.join(out)


def card(t, group, photos):
    s = ' '.join(x for x in (t['name'], t['tb'], t['tracking'], group, t['mission'], t['goal'], t['about']) if x)
    if photos:
        p = photos[0]
        ph = (f'<figure class="ph"><img src="photos/{esc(p["card"])}" width="{p["cw"]}" height="{p["ch"]}" '
              f'alt="{esc(t["name"])}" loading="lazy" decoding="async"></figure>')
    else:
        ph = '<div class="ph none"><span>No photo yet</span></div>'
    about = (f'\n      <details class="about"><summary class="lbl">About</summary><p class="txt">{esc(t["about"])}</p></details>'
             if t['about'] else '')
    return (f'    <article class="tb" id="{esc(t["tb"])}" data-s="{esc(s)}">\n'
            f'      {ph}\n'
            f'      <div class="body">\n'
            f'      <h3><a href="{esc(t["tb"])}/">{esc(t["name"])}</a></h3>\n'
            f'      {ids_html(t)}\n'
            f'      {blocks_html(t)}{about}\n'
            f'      </div>\n'
            f'    </article>')


def gallery(t, photos):
    if not photos:
        return '      <div class="main none"><span>No photo yet</span></div>'
    p = photos[0]
    out = [f'      <figure class="main"><img id="ph-main" src="../photos/{esc(p["file"])}" width="{p["w"]}" '
           f'height="{p["h"]}" alt="{esc(t["name"])}"></figure>']
    if len(photos) > 1:
        out.append('      <ul class="thumbs">')
        for i, q in enumerate(photos, 1):
            out.append(f'        <li><a href="../photos/{esc(q["file"])}" data-w="{q["w"]}" data-h="{q["h"]}" '
                       f'aria-current="{"true" if i == 1 else "false"}" aria-label="Photo {i} of {len(photos)}">'
                       f'<img src="../photos/{esc(q["card"])}" alt="" loading="lazy" decoding="async"></a></li>')
        out.append('      </ul>')
    return '\n'.join(out)


def facts(t):
    out = [f'      {ids_html(t)}',
           f'      <p class="log"><a class="btn primary" href="https://coord.info/{esc(t["tb"])}">Open its page on geocaching.com</a></p>',
           f'      {blocks_html(t)}']
    if t['about']:
        out.append(f'      <div class="about-full"><span class="lbl">About</span><p class="txt">{esc(t["about"])}</p></div>')
    return '\n'.join(out)


def checklist_html(t):
    """The mission checklist: the cacher ticks items; a pasted log lights the tagged ones (never fails any)."""
    items = t.get('checklist') or []
    if not items:
        return ''
    sig = hashlib.sha1(json.dumps(items, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    lis = []
    for n, it in enumerate(items):
        attrs = ''
        if it.get('gc'):
            attrs += f' data-gc="{int(it["gc"])}"'
        if it.get('words'):
            attrs += f' data-words="{it["words"]}"'
        if it.get('mentions'):
            attrs += f' data-mentions="{esc(json.dumps(it["mentions"], ensure_ascii=False))}"'
        if it.get('photo'):
            attrs += ' data-photo="1"'
        chips = []
        if it.get('bonus'):
            chips.append('<span class="chip bonus">Bonus</span>')
        if it.get('photo'):
            chips.append('<span class="chip photo">Photo</span>')
        if attrs.replace(' data-photo="1"', ''):
            chips.append('<span class="chip lit" hidden>In your log</span>')
        lis.append(f'        <li class="ck{" bonus" if it.get("bonus") else ""}"{attrs}>'
                   f'<input type="checkbox" id="ck-{n}"><label for="ck-{n}">{esc(it["text"])}</label>'
                   + (f'<span class="chips">{"".join(chips)}</span>' if chips else '')
                   + ('<span class="mine" hidden></span>' if it.get('photo') else '') + '</li>')
    photo = any(it.get('photo') for it in items)
    work = ['        <label class="lbl" for="ck-log">Your log</label>',
            '        <textarea id="ck-log" rows="9" spellcheck="true" placeholder="Write or paste your log here"></textarea>',
            '        <div class="ck-row"><span class="ck-words" id="ck-words">0 words</span>'
            '<button class="btn small" type="button" id="ck-copy">Copy log</button></div>']
    if photo:
        work += ['        <label class="lbl" for="ck-file">Your photos</label>',
                 '        <input type="file" id="ck-file" accept="image/*" multiple>',
                 '        <div class="ck-yours" id="ck-yours"></div>']
    work += ['        <p class="ck-note">Your log, photos and ticks stay on this device. Nothing is sent anywhere.</p>',
             '        <div class="ck-row"><a class="btn primary" href="https://coord.info/' + esc(t['tb']) + '">Log it on geocaching.com</a>'
             '<button class="btn small" type="button" id="ck-clear">Clear</button></div>']
    return ('  <section class="check" id="checklist" aria-labelledby="ck-h" data-tb="' + esc(t['tb']) + f'" data-sig="{sig}">\n'
            '    <h2 id="ck-h">Mission checklist</h2>\n'
            '    <p class="ck-intro">Tick each item as you do it. Write or paste your log, and items your words cover '
            'light up. Tick the rest yourself: a photo can show what words don\'t.</p>\n'
            '    <div class="ck-grid">\n'
            '      <div class="ck-list">\n'
            '      <ol class="cks">\n' + '\n'.join(lis) + '\n      </ol>\n'
            '      <p class="ck-sum" id="ck-sum" aria-live="polite"></p>\n'
            '      </div>\n'
            '      <div class="ck-work">\n' + '\n'.join(work) + '\n      </div>\n'
            '    </div>\n'
            '  </section>')


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    photos = json.load(open(PHOTOS, encoding='utf-8')) if os.path.exists(PHOTOS) else {}
    groups = [g for g in data['groups'] if g['trackables']]
    style, topo, read_on = read('style.css'), read('topo.svg').rstrip('\n'), esc(nice_date(data['read']))
    order = [(t, g['name']) for g in groups for t in g['trackables']]
    n = len(order)

    # the main page
    used, parts, jumps = set(), [], []
    for g in groups:
        gid = slug(g['name'])
        while gid in used:
            gid += '-'
        used.add(gid)
        jumps.append(f'    <a href="#{gid}">{esc(g["name"])}</a>')
        cards = '\n'.join(card(t, g['name'], photos.get(t['tb'], [])) for t in g['trackables'])
        parts.append(f'  <section class="group" id="{gid}" aria-labelledby="{gid}-h">\n'
                     f'    <h2 id="{gid}-h">{esc(g["name"])} <span class="n">{len(g["trackables"])}</span></h2>\n'
                     f'    <div class="cards">\n{cards}\n    </div>\n'
                     f'  </section>')
    notes = ''.join(f'  <div class="note">{note_html(x)}</div>\n' for x in data.get('notes', []))
    page = fill(read('page.html'), {
        '{{STYLE}}': style, '{{TOPO}}': topo,
        '{{STATS}}': f'{n} trackables · {len(groups)} groups',
        '{{NOTES}}': notes.rstrip('\n'),
        '{{JUMP}}': '\n'.join(jumps),
        '{{GROUPS}}': '\n'.join(parts),
        '{{READ}}': read_on,
    }, 'tools/page.html')
    with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page)

    # one page per trackable
    tmpl, made = read('trackable.html'), set()
    for i, (t, gname) in enumerate(order):
        prev_t, next_t = order[i - 1][0], order[(i + 1) % n][0]
        prevnext = (f'    <a class="prev" href="../{esc(prev_t["tb"])}/">← {esc(prev_t["name"])}</a>\n'
                    f'    <a class="all" href="../#{esc(t["tb"])}">All trackables</a>\n'
                    f'    <a class="next" href="../{esc(next_t["tb"])}/">{esc(next_t["name"])} →</a>')
        desc = t['mission'] or t['about'] or t['name']
        pg = fill(tmpl, {
            '{{TITLE}}': esc(t['name']),
            '{{DESCRIPTION}}': esc(desc if len(desc) <= 160 else desc[:157].rstrip() + '…'),
            '{{STYLE}}': style, '{{TOPO}}': topo,
            '{{GROUP}}': esc(gname),
            '{{NAME}}': esc(t['name']),
            '{{SUBLINE}}': esc(t['tb']),
            '{{GALLERY}}': gallery(t, photos.get(t['tb'], [])),
            '{{FACTS}}': facts(t),
            '{{CHECKLIST}}': checklist_html(t),
            '{{PREVNEXT}}': prevnext,
            '{{READ}}': read_on,
        }, 'tools/trackable.html')
        d = os.path.join(ROOT, t['tb'])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(pg)
        made.add(t['tb'])

    # A trackable no longer on the list keeps its address, since printed QR codes may point at it,
    # but its page says only that it isn't listed now: none of its old text stays up.
    gone = []
    for name in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, name)
        if TB_DIR.fullmatch(name) and name not in made and os.path.isdir(p) and os.listdir(p) == ['index.html']:
            pg = fill(tmpl, {
                '{{TITLE}}': esc(name),
                '{{DESCRIPTION}}': esc(f"{name} isn't listed in Adequate's Shoebox right now."),
                '{{STYLE}}': style, '{{TOPO}}': topo,
                '{{GROUP}}': 'Not listed',
                '{{NAME}}': esc(name),
                '{{SUBLINE}}': 'Not listed right now',
                '{{GALLERY}}': '      <div class="main none"><span>Not listed right now</span></div>',
                '{{FACTS}}': (f'      <p class="txt">This trackable isn\'t listed in Adequate\'s Shoebox right now.</p>\n'
                              f'      <p class="log"><a class="btn primary" href="../">See all trackables</a></p>\n'
                              f'      <p><a href="https://coord.info/{esc(name)}">Its page on geocaching.com</a></p>'),
                '{{CHECKLIST}}': '',
                '{{PREVNEXT}}': '    <a class="all" href="../">All trackables</a>',
                '{{READ}}': read_on,
            }, 'tools/trackable.html')
            with open(os.path.join(p, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(pg)
            gone.append(name)
    print(f'index.html and {len(made)} trackable pages built ({len(page.encode()) // 1024} KB main page)'
          + (f'; kept a not-listed page for {", ".join(gone)}' if gone else ''))


if __name__ == '__main__':
    main()
