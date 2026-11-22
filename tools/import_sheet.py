#!/usr/bin/env python3
"""Turn a snapshot of the collection sheet into data/shoebox.json.

The snapshot is what the Google Sheets connector's get_spreadsheet returns for
the sheet "AdequateFootwear Trackable Collection and Missions" (its address
is in the collection handoff) with
  includeGridData: true
  ranges: ["A1:L300"]
  fields: ["sheets.data.rowMetadata.hiddenByUser",
           "sheets.data.rowData.values.userEnteredValue",
           "sheets.data.rowData.values.formattedValue"]
saved to a file, with or without the connector's {"content": ...} wrapper.

Usage: python3 tools/import_sheet.py SNAPSHOT.json [--read YYYY-MM-DD]

The sheet is the source. Nothing here adds or rewrites words: it picks rows and
cells, and leaves out what must never be public (see CLAUDE.md).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'shoebox.json')

SHEET_NAME = 'AdequateFootwear Trackable Collection and Missions'
FIRST_GROUP = 'Top personal items'  # rows above the first group heading have no heading in the sheet
# Tracking codes that stay off every public page: AdequateTires (people find the car to log it).
WITHHELD_TRACKING = {'TBATY0Z'}

# Columns, by letter, with the header each must carry. A changed header stops the import,
# so a moved column can't put the wrong words on the page.
COLS = {
    'tracking': ('B', lambda h: h == 'Tracking No.'),
    'tb':       ('C', lambda h: h == 'TB Code'),
    'name':     ('D', lambda h: h == 'Name'),
    'mission':  ('F', lambda h: h.startswith('Your Mission (')),
    'about':    ('H', lambda h: h == 'TB Description'),
    'goal':     ('I', lambda h: h.startswith('TB Mission')),
    'photo':    ('J', lambda h: h == 'Photo'),
    'released': ('K', lambda h: h == 'Released'),
    'checklist': ('L', lambda h: h == 'Checklist'),
}
TB_RE = re.compile(r'TB[0-9A-Z]{4,7}')
PHOTO_RE = re.compile(r'=IMAGE\(\s*"(https://s3\.amazonaws\.com/gs-geo-images/[0-9a-f-]{36}_l\.(?:jpe?g|png|gif))"\s*\)', re.I)


def col(letter):
    return ord(letter) - ord('A')


def cell_text(cell):
    if not cell:
        return ''
    if 'formattedValue' in cell:
        return str(cell['formattedValue'])
    uv = cell.get('userEnteredValue', {})
    for k in ('stringValue', 'numberValue', 'boolValue'):
        if k in uv:
            return str(uv[k])
    return ''


def clean(s):
    return '\n'.join(line.rstrip() for line in s.replace('\r\n', '\n').split('\n')).strip()


def parse_date(cell):
    """Released: an ISO date, a date the sheet formats, or a sheet serial number."""
    if not cell:
        return ''
    uv = cell.get('userEnteredValue', {})
    if 'numberValue' in uv:  # days since 1899-12-30
        return (dt.date(1899, 12, 30) + dt.timedelta(days=int(uv['numberValue']))).isoformat()
    s = cell_text(cell).strip()
    if not s:
        return ''
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y', '%A, %B %d, %Y'):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    raise SystemExit(f'Released date not understood: {s!r}')


CHECK_LINE = re.compile(r'(.*?)((?:\s*\[[^\[\]]*\])*)')
CHECK_TAG = re.compile(r'\[([^\[\]]*)\]')


def parse_checklist(text, row):
    """Checklist: one item per line, tags at the end of the line (see CLAUDE.md)."""
    items = []
    for line in clean(text).split('\n'):
        line = line.strip()
        if not line:
            continue
        m = CHECK_LINE.fullmatch(line)
        body = m.group(1).strip()
        if '[' in body or ']' in body or not body:
            raise SystemExit(f'Row {row}: a Checklist line needs its text first and its tags at the end: {line!r}')
        item, lights = {'text': body}, set()
        for tag in CHECK_TAG.findall(m.group(2)):
            tag = tag.strip()
            kind = 'GC code' if tag.startswith('GC code') else tag.split(':')[0].strip()
            if kind in ('GC code', 'words', 'mentions'):
                if kind in lights:  # each must be met on its own, so a repeat would weaken or overwrite one
                    raise SystemExit(f'Row {row}: a Checklist line can carry each of [GC code(s)], [words] and '
                                     f'[mentions] only once; put all the words in one [mentions: …]: {line!r}')
                lights.add(kind)
            words = re.fullmatch(r'words:\s*(\d+)', tag)
            mentions = re.fullmatch(r'mentions:\s*(.*\S)', tag)
            codes = re.fullmatch(r'GC codes:\s*(\d+)', tag)
            if tag == 'GC code':
                item['gc'] = 1
            elif codes and int(codes.group(1)) >= 1:
                item['gc'] = int(codes.group(1))
            elif tag == 'photo':
                item['photo'] = True
            elif tag == 'bonus':
                item['bonus'] = True
            elif tag == 'reminder':
                item['reminder'] = True
            elif tag == 'alternate':
                item['alternate'] = True
            elif words:
                item['words'] = int(words.group(1))
            elif mentions:
                found = [w.strip() for w in mentions.group(1).split(',') if w.strip()]
                item['mentions'] = list(dict.fromkeys(item.get('mentions', []) + found))
            else:
                raise SystemExit(f'Row {row}: Checklist tag not understood: [{tag}] in {line!r}')
        kinds = [k for k in ('bonus', 'reminder', 'alternate') if item.get(k)]
        if len(kinds) > 1 or (item.get('reminder') and item.get('photo')):
            raise SystemExit(f'Row {row}: a Checklist line can be only one of bonus, reminder or alternate, '
                             f'and a reminder takes no [photo]: {line!r}')
        items.append(item)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('snapshot')
    ap.add_argument('--read', default=dt.date.today().isoformat(), help='the day the sheet was read (YYYY-MM-DD)')
    a = ap.parse_args()

    snap = json.load(open(a.snapshot, encoding='utf-8'))
    snap = snap.get('content', snap)
    data = snap['sheets'][0]['data'][0]
    rows = [r.get('values', []) for r in data.get('rowData', [])]
    hidden = [bool(m.get('hiddenByUser')) for m in data.get('rowMetadata', [])]
    hidden += [False] * (len(rows) - len(hidden))

    def get(r, key):
        return r[col(COLS[key][0])] if len(r) > col(COLS[key][0]) else {}

    header = rows[0]
    for key, (letter, ok) in COLS.items():
        h = cell_text(get(header, key)).strip()
        if not ok(h):
            raise SystemExit(f'Column {letter} should be the {key} column, but its header is {h!r}. '
                             'The sheet changed: update COLS in tools/import_sheet.py.')

    # A row counts as an item only if it is visible: a hidden row never shapes or reaches the page.
    has_item = [bool(clean(cell_text(get(r, 'name')))) and not hidden[i] for i, r in enumerate(rows)]
    groups, notes = [], []
    current = {'name': FIRST_GROUP, 'trackables': []}
    left_out = {'hidden': [], 'not_activated': []}
    for i, r in enumerate(rows[1:], start=1):
        name = clean(cell_text(get(r, 'name')))
        label = clean(cell_text(get(r, 'tracking')))
        if hidden[i]:  # every hidden row stays off: items, group headings and notes alike
            left_out['hidden'].append(name or f'row {i + 1}')
            continue
        if not name:
            if label and any(has_item[i + 1:]):
                if current['trackables']:
                    groups.append(current)
                current = {'name': label, 'trackables': []}
            elif label:
                notes.append(label)
            continue
        tb = clean(cell_text(get(r, 'tb'))).upper()
        if not tb:
            left_out['not_activated'].append(name)
            continue
        if not TB_RE.fullmatch(tb):
            raise SystemExit(f'Row {i + 1}: TB code not understood: {tb!r}')
        formula = get(r, 'photo').get('userEnteredValue', {}).get('formulaValue', '')
        m = PHOTO_RE.fullmatch(formula.strip()) if formula else None
        if formula and not m:
            raise SystemExit(f'Row {i + 1}: Photo isn\'t an IMAGE() of an S3 _l link: {formula[:80]!r}')
        tracking = clean(cell_text(get(r, 'tracking'))).upper()
        current['trackables'].append({
            'name': name,
            'tb': tb,
            'tracking': '' if tb in WITHHELD_TRACKING else tracking,
            'released': parse_date(get(r, 'released')),
            'mission': clean(cell_text(get(r, 'mission'))),
            'goal': clean(cell_text(get(r, 'goal'))),
            'about': clean(cell_text(get(r, 'about'))),
            'photo': m.group(1) if m else '',
            'checklist': parse_checklist(cell_text(get(r, 'checklist')), i + 1),
        })
    if current['trackables']:
        groups.append(current)

    out = {'sheet': SHEET_NAME, 'read': a.read, 'notes': notes, 'groups': groups}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    n = sum(len(g['trackables']) for g in groups)
    print(f'{n} trackables in {len(groups)} groups written to data/shoebox.json')
    for k, names in left_out.items():
        if names:
            print(f'left out ({k.replace("_", " ")}): {", ".join(names)}')
    missing = [t['name'] for g in groups for t in g['trackables'] if not t['released']]
    if missing:
        print('no Released date yet: ' + ', '.join(missing))
    nolist = [t['name'] for g in groups for t in g['trackables'] if not t['checklist']]
    if nolist:
        print('no checklist: ' + ', '.join(nolist))
    nophoto = [t['name'] for g in groups for t in g['trackables'] if not t['photo']]
    if nophoto:
        print('no photo: ' + ', '.join(nophoto))


if __name__ == '__main__':
    main()
