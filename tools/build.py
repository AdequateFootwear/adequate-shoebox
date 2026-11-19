#!/usr/bin/env python3
"""Build index.html from data/shoebox.json and tools/page.html.

Usage: python3 tools/build.py
Every word on the page about a trackable comes from data/shoebox.json, which
tools/import_sheet.py makes from the collection sheet. Never edit index.html by hand.
"""
import datetime as dt
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data', 'shoebox.json')
TEMPLATE = os.path.join(ROOT, 'tools', 'page.html')
OUT = os.path.join(ROOT, 'index.html')

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


def esc(s):
    return html.escape(s, quote=True)


def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return f'{MONTHS[d.month - 1]} {d.day}, {d.year}'


def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return 'group-' + (s or 'x')


def note_html(text):
    """The sheet's note, with *starred* words in italics, as the sheet shows them."""
    paras = [p for p in (x.strip() for x in text.split('\n')) if p]
    out = []
    for p in paras:
        p = esc(p)
        p = re.sub(r'\*([^*\n]+)\*', r'<em>\1</em>', p)
        out.append(f'<p>{p}</p>')
    return '\n'.join(out)


def card(t, group):
    s = ' '.join(x for x in (t['name'], t['tb'], t['tracking'], group, t['mission'], t['goal'], t['about']) if x)
    if t['photo']:
        ph = (f'<figure class="ph"><img src="{esc(t["photo"])}" alt="{esc(t["name"])}" '
              'loading="lazy" decoding="async"></figure>')
    else:
        ph = '<div class="ph none"><span>No photo yet</span></div>'
    ids = [f'<dt>TB code</dt><dd><a class="mono" href="https://coord.info/{esc(t["tb"])}">{esc(t["tb"])}</a></dd>']
    if t['tracking']:
        ids.append('<dt>Tracking code</dt><dd>'
                   f'<span class="mono code">{esc(t["tracking"])}</span>'
                   f'<button class="btn small copy" type="button" data-code="{esc(t["tracking"])}" '
                   f'aria-label="Copy the tracking code for {esc(t["name"])}">Copy</button></dd>')
    if t['released']:
        ids.append(f'<dt>Released</dt><dd><time datetime="{esc(t["released"])}">{esc(nice_date(t["released"]))}</time></dd>')
    blocks = []
    if t['mission']:
        blocks.append(f'<div class="block"><span class="lbl">Your mission</span><p class="txt">{esc(t["mission"])}</p></div>')
    if t['goal']:
        blocks.append(f'<div class="block"><span class="lbl">Its goal</span><p class="txt">{esc(t["goal"])}</p></div>')
    about = (f'\n      <details class="about"><summary class="lbl">About</summary><p class="txt">{esc(t["about"])}</p></details>'
             if t['about'] else '')
    return (f'    <article class="tb" id="{esc(t["tb"])}" data-s="{esc(s)}">\n'
            f'      {ph}\n'
            f'      <div class="body">\n'
            f'      <h3>{esc(t["name"])}</h3>\n'
            f'      <dl class="ids">{"".join(ids)}</dl>\n'
            f'      {"".join(blocks)}{about}\n'
            f'      </div>\n'
            f'    </article>')


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    groups = [g for g in data['groups'] if g['trackables']]
    n = sum(len(g['trackables']) for g in groups)
    used = set()
    parts, jumps = [], []
    for g in groups:
        gid = slug(g['name'])
        while gid in used:
            gid += '-'
        used.add(gid)
        jumps.append(f'    <a href="#{gid}">{esc(g["name"])}</a>')
        cards = '\n'.join(card(t, g['name']) for t in g['trackables'])
        parts.append(f'  <section class="group" id="{gid}" aria-labelledby="{gid}-h">\n'
                     f'    <h2 id="{gid}-h">{esc(g["name"])} <span class="n">{len(g["trackables"])}</span></h2>\n'
                     f'    <div class="cards">\n{cards}\n    </div>\n'
                     f'  </section>')
    notes = ''.join(f'  <div class="note">{note_html(x)}</div>\n' for x in data.get('notes', []))
    page = open(TEMPLATE, encoding='utf-8').read()
    fills = {
        '{{STATS}}': f'{n} trackables · {len(groups)} groups',
        '{{NOTES}}': notes.rstrip('\n'),
        '{{JUMP}}': '\n'.join(jumps),
        '{{GROUPS}}': '\n'.join(parts),
        '{{READ}}': esc(nice_date(data['read'])),
    }
    for k, v in fills.items():
        if page.count(k) != 1:
            raise SystemExit(f'tools/page.html should hold {k} exactly once')
        page = page.replace(k, v)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'index.html: {n} trackables in {len(groups)} groups, {len(page.encode()) // 1024} KB')


if __name__ == '__main__':
    main()
