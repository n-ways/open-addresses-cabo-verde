"""Plane geometry on building footprints, standard library only.

Footprints are WKT POLYGON or MULTIPOLYGON in longitude/latitude. Two
distances are used, each where the issuer uses it:

  dist_m        the issuer's rule distance (111,320 m per degree, longitude
                scaled by the cosine of the mean latitude): doors within
                80 m, entrance moves, zone anchors;
  geo_dist_m    the WGS 84 ellipsoid's local scale (meridian and prime
                vertical radii of curvature at the latitude), for the
                point-to-lote distances that decide "found" (12 m) and
                "already has a code" (3 m). Over such distances it agrees
                with a geodesic distance to well under a millimetre.
"""
import math
import re

M_PER_DEG = 111320.0


def dist_m(lat1, lng1, lat2, lng2):
    """Distance in metres between two points (local plane)."""
    dy = (lat2 - lat1) * M_PER_DEG
    dx = (lng2 - lng1) * M_PER_DEG * math.cos((lat1 + lat2) / 2 * math.pi / 180)
    return math.hypot(dx, dy)


_A = 6378137.0
_E2 = 6.69437999014e-3


def _scale(lat):
    """Metres per degree of latitude and of longitude on WGS 84 at a latitude."""
    p = math.radians(lat)
    w = 1 - _E2 * math.sin(p) ** 2
    m = _A * (1 - _E2) / w ** 1.5
    n = _A / math.sqrt(w)
    return m * math.pi / 180, n * math.cos(p) * math.pi / 180


def geo_dist_m(lat1, lng1, lat2, lng2):
    ky, kx = _scale((lat1 + lat2) / 2)
    return math.hypot((lng2 - lng1) * kx, (lat2 - lat1) * ky)


_NUM = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')


def parse_wkt(wkt):
    """WKT POLYGON / MULTIPOLYGON -> [polygon], polygon = [ring], ring =
    [(lng, lat)] with the closing point dropped. The first ring of each
    polygon is its outer boundary, the others are holes."""
    wkt = wkt.strip()
    if not wkt:
        return []
    head = wkt.split('(', 1)[0].strip().upper()
    body = wkt[len(head):].strip()
    if head == 'POLYGON':
        polys = [body]
    elif head == 'MULTIPOLYGON':
        inner = body[1:-1]
        polys, depth, start = [], 0, None
        for i, ch in enumerate(inner):
            if ch == '(':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    polys.append(inner[start:i + 1])
    else:
        raise ValueError(f'unsupported geometry {head}')
    out = []
    for p in polys:
        rings = []
        for r in re.findall(r'\(([^()]*)\)', p):
            vals = [float(x) for x in _NUM.findall(r)]
            pts = list(zip(vals[0::2], vals[1::2]))
            if len(pts) > 1 and pts[0] == pts[-1]:
                pts = pts[:-1]
            if len(pts) >= 3:
                rings.append(pts)
        if rings:
            out.append(rings)
    return out


def bbox(polys):
    xs = [x for poly in polys for ring in poly for x, _ in ring]
    ys = [y for poly in polys for ring in poly for _, y in ring]
    return min(xs), min(ys), max(xs), max(ys)


def _in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def contains(polys, lng, lat):
    """Whether a point lies inside a footprint (holes excluded)."""
    for poly in polys:
        if _in_ring(lng, lat, poly[0]) and not any(_in_ring(lng, lat, h) for h in poly[1:]):
            return True
    return False


def distance_m(polys, lat, lng):
    """Distance in metres from a point to a footprint (WGS 84 local scale):
    0 inside, else to the nearest edge."""
    if contains(polys, lng, lat):
        return 0.0
    ky, kx = _scale(lat)
    best = math.inf
    for poly in polys:
        for ring in poly:
            n = len(ring)
            for i in range(n):
                ax, ay = (ring[i][0] - lng) * kx, (ring[i][1] - lat) * ky
                bx, by = (ring[(i + 1) % n][0] - lng) * kx, (ring[(i + 1) % n][1] - lat) * ky
                dx, dy = bx - ax, by - ay
                L = dx * dx + dy * dy
                t = 0.0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
                best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def ring_area_m2(ring):
    """Area of a [(lng, lat)] ring in square metres (local plane at its
    first vertex), as the issuer measures a tapped outline."""
    if len(ring) < 3:
        return 0.0
    k = M_PER_DEG * math.cos(ring[0][1] * math.pi / 180)
    a = 0.0
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        xi, yi = ring[i][0] * k, ring[i][1] * M_PER_DEG
        xj, yj = ring[j][0] * k, ring[j][1] * M_PER_DEG
        a += xi * yj - xj * yi
    return abs(a) / 2


def ring_perimeter_m(ring):
    return sum(dist_m(ring[i][1], ring[i][0], ring[(i + 1) % len(ring)][1], ring[(i + 1) % len(ring)][0])
               for i in range(len(ring)))


def ring_wkt(ring):
    pts = list(ring) + [ring[0]]
    return 'POLYGON((' + ','.join(f'{x:.7f} {y:.7f}' for x, y in pts) + '))'


# Intersection area -----------------------------------------------------------
# Areas below are in square degrees, like PostGIS ST_Area on geometry; only
# their ratio is used.

def _signed(ring):
    a = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        a += x1 * y2 - x2 * y1
    return a / 2


def area(polys):
    return sum(abs(_signed(p[0])) - sum(abs(_signed(h)) for h in p[1:]) for p in polys)


def _clip(subject, tri):
    """Sutherland-Hodgman: subject ring (any simple ring) clipped by a
    counter-clockwise triangle. The clipped ring's area is exact even when
    the subject is not convex (overlapping degenerate edges cancel)."""
    out = subject
    for i in range(3):
        if not out:
            break
        ax, ay = tri[i]
        bx, by = tri[(i + 1) % 3]
        inp, out = out, []

        def side(p, ax=ax, ay=ay, bx=bx, by=by):
            return (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax)
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            sp, sq = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def _area_in_triangle(polys, tri):
    a = 0.0
    for poly in polys:
        for k, ring in enumerate(poly):
            c = _clip(ring, tri)
            v = abs(_signed(c)) if len(c) >= 3 else 0.0
            a += v if k == 0 else -v
    return a


def intersection_area(a_polys, b_polys):
    """Area of A ∩ B. A is written as a signed sum of triangles fanned from
    one point (each ring's orientation gives the sign: outer rings count +1,
    holes -1), and B is clipped by each triangle."""
    if not a_polys or not b_polys:
        return 0.0
    o = a_polys[0][0][0]
    total = 0.0
    for poly in a_polys:
        for k, ring in enumerate(poly):
            s = _signed(ring)
            want = 1 if k == 0 else -1
            r = ring if (s > 0) == (want > 0) else ring[::-1]
            for i in range(len(r)):
                p, q = r[i], r[(i + 1) % len(r)]
                tri = [o, p, q]
                ts = _signed(tri)
                if ts == 0:
                    continue
                if ts < 0:
                    tri = [o, q, p]
                total += (1 if ts > 0 else -1) * _area_in_triangle(b_polys, tri)
    return max(0.0, total)
