#!/usr/bin/env python3
"""Copy Aegis's own trackable photos into photos/ and list them in data/photos.json.

Usage: python3 tools/import_photos.py FOLDER

FOLDER holds the files from Drive's Upload-ready folder (Claude > Projects > Geocaching >
Trackable Collection Missions > Photos > Upload-ready), named as they are there. Those files
already have their tracking numbers blurred. A file belongs to every trackable whose TB code
is in its name, so a group photo (TBA_TBB_TBC.jpg) shows on each of their pages.

For each file this writes two copies, with all metadata (including any GPS position) removed:
photos/<name>.jpg, at most 1600 px on its long side, and photos/<name>-card.jpg, at most
800 px, for the cards on the main page. Only photos of trackables in data/shoebox.json are
copied: run tools/import_sheet.py first.
"""
import json
import os
import re
import sys

from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS = os.path.join(ROOT, 'photos')
DATA = os.path.join(ROOT, 'data', 'shoebox.json')
OUT = os.path.join(ROOT, 'data', 'photos.json')
TB_RE = re.compile(r'TB[0-9A-Z]{4,7}')
EXTS = ('.jpg', '.jpeg', '.png')


def slug(name):
    base = os.path.splitext(name)[0]
    return re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-')


def save(img, path, longest, quality):
    im = img.copy()
    im.thumbnail((longest, longest), Image.LANCZOS)
    im.save(path, 'JPEG', quality=quality, optimize=True, progressive=True)  # no exif= : metadata dropped
    return im.size


def order_key(tb, name):
    base = os.path.splitext(name)[0]
    if base == tb:
        return (0, name)
    if base.startswith(tb) and len(TB_RE.findall(base)) == 1:
        return (1, name)
    if base.startswith(tb):
        return (2, name)
    return (3, name)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    folder = sys.argv[1]
    data = json.load(open(DATA, encoding='utf-8'))
    active = {t['tb'] for g in data['groups'] for t in g['trackables']}
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(EXTS))
    os.makedirs(PHOTOS, exist_ok=True)
    out, used, skipped = {}, set(), []
    for name in files:
        tbs = [tb for tb in dict.fromkeys(TB_RE.findall(name)) if tb in active]
        if not tbs:
            skipped.append(name)
            continue
        s = slug(name)
        with Image.open(os.path.join(folder, name)) as src:
            img = ImageOps.exif_transpose(src).convert('RGB')
        w, h = save(img, os.path.join(PHOTOS, s + '.jpg'), 1600, 82)
        cw, ch = save(img, os.path.join(PHOTOS, s + '-card.jpg'), 800, 78)
        used.add(s)
        for tb in tbs:
            out.setdefault(tb, []).append({'file': s + '.jpg', 'w': w, 'h': h,
                                           'card': s + '-card.jpg', 'cw': cw, 'ch': ch, 'source': name})
    for tb in out:
        out[tb].sort(key=lambda p: order_key(tb, p['source']))
    stale = [f for f in os.listdir(PHOTOS) if f.endswith('.jpg') and re.sub(r'-card$', '', f[:-4]) not in used]
    for f in stale:
        os.remove(os.path.join(PHOTOS, f))
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(dict(sorted(out.items())), fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print(f'{len(used)} photos for {len(out)} trackables written to photos/ and data/photos.json')
    if skipped:
        print('not for an activated trackable, so not copied: ' + ', '.join(skipped))
    missing = sorted(active - set(out))
    if missing:
        print('trackables with no photo: ' + ', '.join(missing))
    if stale:
        print(f'removed {len(stale)} photo files no longer in the folder')


if __name__ == '__main__':
    main()
