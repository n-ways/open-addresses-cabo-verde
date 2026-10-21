#!/usr/bin/env python3
"""The national border of Cabo Verde for the engine and the server
(engine/data/border.geojson, SPEC.md §3.2).

Input: the OpenStreetMap admin_level 2 boundary of Cabo Verde as WKT, as
tools/building_stats.py exports it to its work folder (border.wkt, from the
N-Ways countries table), or straight from NWAYS_DB.

The outline is simplified (Douglas-Peucker, 50 m in local metres) and the
largest distance between the simplified line and the full one is measured by
sampling both lines every 25 m. That distance is written as deviationM; the
engine then accepts a point with the shipped outline only within
300 m - deviationM of it (cv_engine.within_border), so the shipped file never
accepts what the full border refuses.

  python3 tools/build_border.py --wkt DIR/border.wkt
  NWAYS_DB=postgres://... python3 tools/build_border.py
"""
import argparse
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
from server import geo  # noqa: E402  (standard-library WKT reader)

TOLERANCE_M = 50.0
SAMPLE_M = 25.0
OUT = os.path.join(REPO, 'engine', 'data', 'border.geojson')
SQL = "SELECT ST_AsText(geom) FROM countries WHERE code = 'CV'"
LAT0 = 16.0
KY = geo.M_PER_DEG
KX = geo.M_PER_DEG * math.cos(math.radians(LAT0))


def border_wkt(path=None):
    """The full national border as WKT: from a file, else from NWAYS_DB."""
    if path:
        with open(path, encoding='utf-8') as f:
            return f.read().strip()
    db = os.environ.get('NWAYS_DB', '')
    if not db:
        sys.exit('give --wkt FILE or set NWAYS_DB')
    r = subprocess.run(['psql', db, '-Atc', SQL], capture_output=True, text=True, check=False)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit('no national border for CV in the countries table: ' + r.stderr.strip()[-500:])
    return r.stdout.strip()


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _xy(p):
    return p[0] * KX, p[1] * KY


def _dp(pts, tol):
    """Douglas-Peucker on an open polyline of (x, y) metres; keeps both ends."""
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        best, k = 0.0, None
        for i in range(a + 1, b):
            d = _seg_dist(*pts[i], *pts[a], *pts[b])
            if d > best:
                best, k = d, i
        if k is not None and best > tol:
            keep[k] = True
            stack += [(a, k), (k, b)]
    return keep


def simplify_ring(ring, tol):
    """A closed ring (no repeated end) simplified; never under 4 points."""
    pts = [_xy(p) for p in ring]
    far = max(range(len(pts)), key=lambda i: math.hypot(pts[i][0] - pts[0][0], pts[i][1] - pts[0][1]))
    a = _dp(pts[:far + 1], tol)
    b = _dp(pts[far:] + [pts[0]], tol)
    keep = a[:-1] + b[:-1]
    out = [ring[i] for i in range(len(ring)) if keep[i]]
    return out if len(out) >= 4 else list(ring)


def _samples(ring):
    n = len(ring)
    for i in range(n):
        ax, ay = _xy(ring[i])
        bx, by = _xy(ring[(i + 1) % n])
        steps = max(1, math.ceil(math.hypot(bx - ax, by - ay) / SAMPLE_M))
        for s in range(steps):
            yield ax + (bx - ax) * s / steps, ay + (by - ay) * s / steps


def _line_dist(x, y, polys):
    best = math.inf
    for poly in polys:
        for ring in poly:
            n = len(ring)
            for i in range(n):
                best = min(best, _seg_dist(x, y, *_xy(ring[i]), *_xy(ring[(i + 1) % n])))
    return best


def deviation_m(a, b):
    """The largest distance from a sample of either outline's line to the other's."""
    worst = 0.0
    for src, dst in ((a, b), (b, a)):
        for poly in src:
            for ring in poly:
                for x, y in _samples(ring):
                    worst = max(worst, _line_dist(x, y, dst))
    return worst


def build(wkt, tol=TOLERANCE_M):
    full = geo.parse_wkt(wkt)
    if not full:
        sys.exit('the national border is empty')
    simple = [[[(round(x, 6), round(y, 6)) for x, y in simplify_ring(r, tol)] for r in poly] for poly in full]
    dev = deviation_m(full, simple)
    coords = [[[list(p) for p in r] + [list(r[0])] for r in poly] for poly in simple]
    feat = {'type': 'Feature', 'properties': {
        'country': 'CV', 'source': 'OpenStreetMap admin_level 2 boundary of Cabo Verde', 'licence': 'ODbL-1.0',
        'borderM': 300, 'simplifyM': tol, 'deviationM': math.ceil(dev * 10) / 10,
        'pointsFull': sum(len(r) for p in full for r in p), 'pointsShipped': sum(len(r) for p in simple for r in p)},
        'geometry': {'type': 'MultiPolygon', 'coordinates': coords}}
    return feat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wkt', help='the border as WKT (the work folder\'s border.wkt); default: read NWAYS_DB')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    feat = build(border_wkt(a.wkt))
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(feat, f, separators=(',', ':'))
        f.write('\n')
    p = feat['properties']
    print(f"{a.out}: {p['pointsShipped']} of {p['pointsFull']} points, deviation {p['deviationM']} m, "
          f"{os.path.getsize(a.out)} bytes", file=sys.stderr)


if __name__ == '__main__':
    main()
