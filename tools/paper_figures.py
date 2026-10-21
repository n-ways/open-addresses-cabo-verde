#!/usr/bin/env python3
"""Data tables behind the paper's figures (docs/figures/*.tex).

Every number is computed from the published registry (registry/) and the
municipality outlines (engine/data/municipalities.geojson), so a reader can
recompute each figure. Writes small whitespace-separated tables to
docs/figures/data/; the figures read them with pgfplots.

  python3 tools/paper_figures.py           write the tables
  python3 tools/paper_figures.py --check   rebuild them and compare

Standard library only.
"""
import argparse
import collections
import csv
import gzip
import io
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import cv_engine as E  # noqa: E402

REG = os.path.join(REPO, 'registry')
OUT = os.path.join(REPO, 'docs', 'figures', 'data')
csv.field_size_limit(1 << 30)
RING = re.compile(r'\(([^()]+)\)')  # every ring of a WKT POLYGON or MULTIPOLYGON

# Map projection for the national figures: equirectangular about 16 deg N,
# in kilometres. At this scale (about 300 km across) the distortion against
# the national Lambert grid (EPSG:4826) is well under one per cent.
LAT0, LON0 = 16.0, -24.0
KX = 111.320 * math.cos(math.radians(LAT0))
KY = 110.574

# The worked example of the paper (§5): its zone and the area of the spot
# grid figure, a block of the Platô around the Correios headquarters.
EXAMPLE_ZONE = 'PR-004'
EXAMPLE_CODE = 'PR-0973-1922-6'
SPOT_CODE = 'PR-1052-1132-2'
SPOT_HALF_M = 75.0
RANGE_NAMES = ('fazenda', 'figueira', 'bela vista')
# Where each island's label sits on the map, from its area-weighted centre (km).
LABEL = {'Santo Antão': (-8, 20, 'south'), 'São Vicente': (0, -14, 'north'), 'São Nicolau': (0, 14, 'south'),
         'Sal': (12, 0, 'west'), 'Boa Vista': (0, -22, 'north'), 'Maio': (14, 0, 'west'),
         'Santiago': (34, -24, 'north'), 'Fogo': (-18, 6, 'east'), 'Brava': (0, -10, 'north')}


def registry_rows():
    out = []
    for key in sorted(E.MUNI):
        with open(os.path.join(REG, f'{key}.csv'), encoding='utf-8', newline='') as f:
            out += list(csv.DictReader(f))
    return out


def table(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def simplify(pts, tol):
    """Douglas-Peucker on a list of (x, y)."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = math.hypot(dx, dy)
    far, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        if norm < 1e-9:  # a closed ring: split at the point farthest from its start
            d = math.hypot(p[0] - a[0], p[1] - a[1])
        else:
            d = abs(dy * (p[0] - a[0]) - dx * (p[1] - a[1])) / norm
        if d > far:
            far, idx = d, i
    if far <= tol:
        return [a, b]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def shade(density):
    """Map shade for a density of codes per km2: logarithmic between the
    sparsest municipality (about 8 per km2) and Praia (about 320)."""
    t = (math.log10(max(density, 5)) - math.log10(5)) / (math.log10(400) - math.log10(5))
    return round(12 + 80 * min(max(t, 0), 1))


def km(lat, lon):
    return (lon - LON0) * KX, (lat - LAT0) * KY


def fmt(v, nd=3):
    return f'{v:.{nd}f}'


def write(files, name, header, lines, comment):
    buf = io.StringIO()
    buf.write(f'# {comment}\n')
    buf.write(' '.join(header) + '\n')
    for ln in lines:
        buf.write((' '.join(str(x) for x in ln) if ln else '') + '\n')
    files[name] = buf.getvalue()


def build():
    files = {}
    rows = registry_rows()
    zones = {z['zone']: z for z in table(os.path.join(REG, 'zones.csv'))}
    names = {n['name_index']: n for n in table(os.path.join(REG, 'names.csv'))}
    per_zone = collections.Counter(r['zone'] for r in rows)
    per_muni = collections.Counter(r['machine'][:2] for r in rows)

    # 1. Map of the municipalities, shaded by codes per km2.
    with open(os.path.join(REPO, 'engine', 'data', 'municipalities.geojson'), encoding='utf-8') as f:
        gj = json.load(f)
    feats = sorted(gj['features'], key=lambda ft: ft['properties']['iso'])
    ring_lines, muni_lines, isles = [], [], {}
    for i, ft in enumerate(feats):
        key = ft['properties']['iso'][3:]
        geom = ft['geometry']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        area = 0.0
        sx = sy = 0.0
        for poly in polys:
            for j, ring in enumerate(poly):
                pts = [km(lat, lon) for lon, lat in ring]
                a = 0.5 * sum(pts[k][0] * pts[k + 1][1] - pts[k + 1][0] * pts[k][1] for k in range(len(pts) - 1))
                if j == 0:
                    area += abs(a)
                    sx += abs(a) * sum(p[0] for p in pts) / len(pts)
                    sy += abs(a) * sum(p[1] for p in pts) / len(pts)
                if j > 0 or abs(a) < 0.05:
                    continue  # holes and islets under 5 ha are not drawn
                simple = simplify(pts, 0.12)
                if len(simple) < 4:
                    continue
                ring_lines += [(i, fmt(x, 2), fmt(y, 2)) for x, y in simple]
                ring_lines.append((i, 'nan', 'nan'))
        codes = per_muni[key]
        dens = codes / area
        muni_lines.append((i, key, E.MUNI[key]['island'].replace(' ', '~'), codes, fmt(area, 1),
                           fmt(dens, 1), shade(dens), fmt(sx / area, 2), fmt(sy / area, 2)))
        isl = isles.setdefault(E.MUNI[key]['island'], [0, 0.0, 0.0, 0.0])
        isl[0] += codes
        isl[1] += area
        isl[2] += sx
        isl[3] += sy
    write(files, 'map.dat', ('id', 'x', 'y'), ring_lines,
          'municipality outlines, km east and north of 16N 24W; a nan row ends each ring')
    write(files, 'municipalities.dat', ('id', 'key', 'island', 'codes', 'km2', 'density', 'shade', 'cx', 'cy'),
          muni_lines, 'codes per municipality (registry/), land area of the outline, and the map shade (per cent of ink)')
    write(files, 'islands.dat', ('island', 'codes', 'label', 'labelsp', 'km2', 'lx', 'ly', 'anchor'),
          [(k.replace(' ', '~'), v[0], f'{v[0]:,}', f'{v[0]:,}'.replace(',', '~'), fmt(v[1], 1), fmt(v[2] / v[1] + LABEL[k][0], 2), fmt(v[3] / v[1] + LABEL[k][1], 2), LABEL[k][2].replace(' ', '~'))
           for k, v in sorted(isles.items())],
          'codes and land area per island, written with a comma or a space between thousands; label position (km) and anchor')

    # 2. Codes per zone: histogram on log-spaced bins, by the digits of the zone's name.
    edges = [round(10 ** (k / 4)) for k in range(15)]
    edges = sorted(set(edges))
    hist = {d: [0] * (len(edges) - 1) for d in ('3', '4')}
    for ref, z in zones.items():
        n = per_zone[ref]
        d = names[z['name_index']]['digits']
        for k in range(len(edges) - 1):
            if edges[k] <= n < edges[k + 1] or (k == len(edges) - 2 and n >= edges[k]):
                hist[d][k] += 1
                break
    lines = [(edges[k], hist['3'][k], hist['4'][k]) for k in range(len(edges) - 1)]
    lines.append((edges[-1], 0, 0))
    write(files, 'zone-sizes.dat', ('lo', 'three', 'four'), lines,
          'zones by number of codes (bin lower edge), split by the digits of the name range')

    # 3. The worked example's zone: every code at its numbering anchor, by number.
    anchors = {}
    with gzip.open(os.path.join(REG, 'lotes.csv.gz'), 'rt', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            if r['machine'].startswith('PR-'):
                anchors[r['machine']] = (float(r['anchor_lat']), float(r['anchor_lng']))
    z = zones[EXAMPLE_ZONE]
    box = tuple(map(float, z['box'].split()))
    la0, lo0 = (box[1] + box[3]) / 2, (box[0] + box[2]) / 2
    kx = 111320 * math.cos(math.radians(la0))
    pts = []
    for r in rows:
        if r['zone'] != EXAMPLE_ZONE:
            continue
        la, lo = anchors[r['machine']]
        pts.append((int(r['number']), fmt((lo - lo0) * kx, 1), fmt((la - la0) * 110574, 1),
                    1 if r['machine'] == EXAMPLE_CODE else 0, 1 if r['coverage'] else 0))
    pts.sort()
    write(files, 'palmarejo.dat', ('number', 'x', 'y', 'example', 'official'), pts,
          f'codes of zone {EXAMPLE_ZONE} (Palmarejo, Praia) at their numbering anchors, metres from the box centre')

    # 4. National ranges of three repeated names: blocks and reserve.
    lines = []
    by_key = {n['name_key']: n for n in names.values()}
    for row, key in enumerate(RANGE_NAMES):
        n = by_key[key]
        blocks = n['blocks'].split()
        for pos, b in enumerate(blocks):
            ref, span = b.split(':')
            lo, hi = map(int, span.split('-'))
            zz = zones[ref]
            label = zz['official_name'].replace(' ', '~') + ',~' + E.MUNI[zz['municipality']]['name'].replace(' ', '~')
            lines.append((row, n['plate_name'].replace(' ', '~'), lo, hi + 1, per_zone[ref], pos, len(blocks), label))
    write(files, 'ranges.dat', ('row', 'name', 'lo', 'hi', 'codes', 'pos', 'n', 'zone'), lines,
          'blocks of three national name ranges (registry/names.csv); hi is exclusive; pos of n blocks in the range')

    # 5. The spot grid around the Correios headquarters, Platô.
    pr = {r['machine']: r for r in rows if r['machine'].startswith('PR-')}
    c = pr[SPOT_CODE]
    cla, clo = float(c['entrance_lat']), float(c['entrance_lng'])
    step = 0.000125
    g_la = math.floor((cla + 90) / step) * step - 90
    g_lo = math.floor((clo + 180) / step) * step - 180
    kx = 111320 * math.cos(math.radians(cla))
    ky = 110574.0

    def m(lat, lon):
        return (lon - g_lo) * kx, (lat - g_la) * ky

    polys = []
    with gzip.open(os.path.join(REG, 'structures', 'PR.csv.gz'), 'rt', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            for ring in RING.findall(r['footprint']):
                xy = [m(float(p.split()[1]), float(p.split()[0])) for p in ring.split(',')]
                if any(abs(x - 6.7) <= SPOT_HALF_M and abs(y - 6.9) <= SPOT_HALF_M for x, y in xy):
                    polys.append((r['machine'], r['index'], xy))
    lines = []
    for i, (mach, _, xy) in enumerate(sorted(polys)):
        ex = 1 if mach == SPOT_CODE else 0
        lines += [(i, ex, fmt(x, 1), fmt(y, 1)) for x, y in xy]
        lines.append((i, ex, 'nan', 'nan'))
    write(files, 'plato-footprints.dat', ('id', 'example', 'x', 'y'), lines,
          'footprints near the Correios headquarters, metres east and north of the corner of its 10-character Plus Code cell')
    cells = []
    for i in range(-5, 7):
        for j in range(-5, 7):
            la = g_la + (j + 0.5) * step
            lo = g_lo + (i + 0.5) * step
            code = E.olc_encode(la, lo, 10)
            x, y = m(la, lo)
            cells.append((i, j, fmt(x, 1), fmt(y, 1), code[4:]))
    write(files, 'plato-cells.dat', ('i', 'j', 'x', 'y', 'code'), cells,
          'centres of 10-character Plus Code cells; cell width ' + fmt(step * kx, 2) + ' m, height ' + fmt(step * ky, 2) + ' m')
    ex, ey = m(cla, clo)
    write(files, 'plato-entrance.dat', ('x', 'y', 'code', 'plus'), [(fmt(ex, 1), fmt(ey, 1), c['home'].replace(' ', '~'), c['plus_code'])],
          'the entrance of the Correios headquarters')

    # 6. Footprint sources by island.
    island_of = {k: E.MUNI[k]['island'] for k in E.MUNI}
    src = collections.defaultdict(collections.Counter)
    for key in E.MUNI:
        with gzip.open(os.path.join(REG, 'structures', f'{key}.csv.gz'), 'rt', encoding='utf-8', newline='') as f:
            for r in csv.DictReader(f):
                src[island_of[key]][r['data']] += 1
    isl_codes = collections.Counter()
    for k, v in per_muni.items():
        isl_codes[island_of[k]] += v
    order = sorted(src, key=lambda i: src[i]['osm'] + src[i]['ml'])
    lines = [(i.replace(' ', '~'), src[i]['osm'], src[i]['ml'], isl_codes[i]) for i in order]
    write(files, 'sources.dat', ('island', 'osm', 'ml', 'codes'), lines,
          'footprints in registry/structures by source: OpenStreetMap, or machine-learned (Google Open Buildings, Microsoft, via Overture)')
    # 7. The order-3 Hilbert curve, cell by cell, with the engine's own index.
    pos = {E.hilbert_index(x, y, 3): (x, y) for x in range(8) for y in range(8)}
    write(files, 'hilbert.dat', ('d', 'x', 'y'), [(d, pos[d][0], pos[d][1]) for d in range(64)],
          'cells of an 8 x 8 grid in the order of hilbert_index(x, y, order=3)')
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='rebuild and compare with docs/figures/data/')
    args = ap.parse_args()
    files = build()
    if args.check:
        bad = []
        for name, text in files.items():
            p = os.path.join(OUT, name)
            if not os.path.exists(p):
                bad.append(name)
                continue
            with open(p, encoding='utf-8') as f:
                if f.read() != text:
                    bad.append(name)
        if bad:
            print('differ:', ', '.join(bad))
            sys.exit(1)
        print(f'{len(files)} tables reproduce')
        return
    os.makedirs(OUT, exist_ok=True)
    for name, text in files.items():
        with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
            f.write(text)
    print(f'wrote {len(files)} tables to {os.path.relpath(OUT, REPO)}')


if __name__ == '__main__':
    main()
