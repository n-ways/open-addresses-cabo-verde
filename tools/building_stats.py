#!/usr/bin/env python3
"""Building-profile and lote (plot/compound) statistics for Cabo Verde.

Reads N-Ways' map data read-only and writes:
  model/building-stats.json     class mix, size distribution, heights, lotes
                                and gates, per municipality and island,
                                Praia in detail
  the zone table and name register (tools/build_zones.py, build_names.py):
                                engine/data/zones.json and names.json before
                                first issue; once codes are issued the
                                register is frozen, and the rebuilt tables go
                                to the work folder for comparison

Inputs (all read-only):
  postgres countries (the national border: OpenStreetMap admin_level 2),
           regions (CV municipalities), places (N-Ways POIs, by box)
  data/detail/countries/cape-verde/buildings-src.geojsonseq (OpenStreetMap)
  data/detail/ml/CV.parquet (Google Open Buildings / Microsoft, with h)
  data/valhalla/compounds.geojsonseq, gates.geojsonseq (routing build)

The border decides: a footprint, enclosure or gate whose point lies more
than 300 m outside the national border is dropped at extraction (load,
export_inputs), so no code can ever be planned in a neighbouring country,
whatever the zone or municipality outlines say.

One heavy step (duckdb, memory_limit 3GB, 4 threads); the rest is Python.

  NWAYS_DB=postgres://... python3 tools/building_stats.py --root /path/to/n-ways-data [--work DIR]
"""
import argparse
import collections
import csv
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile

csv.field_size_limit(1 << 30)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv_engine as E  # noqa: E402

sys.path.insert(0, REPO)
from server import geo  # noqa: E402  (standard-library WKT reader)

BOX = (-25.5, 14.7, -22.5, 17.3)
# The N-Ways database (read-only), e.g. NWAYS_DB='postgres:///<db>?host=<socket dir>'; needed only to extract.
DB = os.environ.get('NWAYS_DB', '')
TAG_KEYS = ['building', 'building:levels', 'height', 'amenity', 'shop', 'tourism', 'office', 'government', 'healthcare',
            'religion', 'man_made', 'aeroway', 'leisure', 'name', 'construction', 'ruins', 'disused', 'abandoned', 'craft',
            'addr:street', 'addr:housenumber', 'addr:postcode']


def run(cmd, data=None):
    r = subprocess.run(cmd, input=data, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        sys.exit(f'{cmd[0]} failed: {r.stderr.strip()[-2000:]}')
    return r.stdout


def read_text(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def write_text(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def geojsonseq(path):
    """The features of a GeoJSON sequence file, one per line."""
    with open(path, encoding='utf-8') as f:
        for line in f:
            yield json.loads(line.lstrip('\x1e'))


def border_polys(work):
    """The full national border (the work folder's border.wkt, exported from
    the countries table) as engine polygons; None when the work folder has
    none (an older extract): the shipped outline then decides, with its
    simplification's deviation taken off the 300 m (cv_engine.within_border)."""
    path = os.path.join(work, 'border.wkt')
    if not os.path.exists(path):
        print('no border.wkt in the work folder: using engine/data/border.geojson', file=sys.stderr)
        return None
    polys = geo.parse_wkt(read_text(path))
    if not polys:
        sys.exit(f'{path} holds no outline')
    return polys


def export_inputs(root, work):
    # the national border (OpenStreetMap admin_level 2); it decides which buildings are Cabo Verde's
    wkt = run(['psql', DB, '-Atc', "SELECT ST_AsText(geom) FROM countries WHERE code='CV'"]).strip()
    if not wkt:
        sys.exit('no national border for CV in the countries table')
    write_text(os.path.join(work, 'border.wkt'), wkt + '\n')
    border = border_polys(work)
    # municipalities
    sql = "COPY (SELECT code, ST_AsText(geom) FROM regions WHERE country='CV' ORDER BY code) TO STDOUT WITH CSV HEADER"
    write_text(os.path.join(work, 'regions.csv'), run(['psql', DB, '-Atc', sql]))
    # places inside the box
    sql = (f"COPY (SELECT id, category, ST_X(location::geometry) lon, ST_Y(location::geometry) lat FROM places "
           f"WHERE ST_Intersects(location::geometry, ST_MakeEnvelope({BOX[0]},{BOX[1]},{BOX[2]},{BOX[3]},4326))) TO STDOUT WITH CSV HEADER")
    write_text(os.path.join(work, 'places.csv'), run(['psql', DB, '-Atc', sql]))
    # locality names (zones, SPEC.md 3.3)
    sql = ("COPY (SELECT id, name, kind, ST_X(location::geometry) lon, ST_Y(location::geometry) lat FROM geo_names "
           "WHERE country='CV' AND kind IN ('locality','village','town','city','suburb','neighbourhood') ORDER BY id) TO STDOUT WITH CSV HEADER")
    write_text(os.path.join(work, 'names.csv'), run(['psql', DB, '-Atc', sql]))
    # compounds and gates in the box
    def inb(x, y):
        return BOX[0] <= x <= BOX[2] and BOX[1] <= y <= BOX[3]
    with open(os.path.join(work, 'compounds.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['cid', 'kind', 'name', 'wkt'])
        for ft in geojsonseq(os.path.join(root, 'data', 'valhalla', 'compounds.geojsonseq')):
            g = ft['geometry']
            first = g['coordinates'][0][0][0] if g['type'] == 'MultiPolygon' else g['coordinates'][0][0]
            if not inb(*first):
                continue
            polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
            outer = polys[0][0]
            cx, cy = sum(p[0] for p in outer) / len(outer), sum(p[1] for p in outer) / len(outer)
            if not E.within_border(cy, cx, border):
                continue  # an enclosure across the border is not Cabo Verde's
            wkt = 'MULTIPOLYGON(' + ','.join('(' + ','.join('(' + ','.join(f'{x} {y}' for x, y in ring[:]) + ')' for ring in p) + ')' for p in polys) + ')'
            p = ft['properties']
            w.writerow([p['id'], p.get('kind', ''), p.get('name', ''), wkt])
    with open(os.path.join(work, 'gates.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['gid', 'barrier', 'lon', 'lat'])
        for ft in geojsonseq(os.path.join(root, 'data', 'valhalla', 'gates.geojsonseq')):
            x, y = ft['geometry']['coordinates'][:2]
            if inb(x, y) and E.within_border(y, x, border):
                w.writerow([ft['properties']['id'], ft['properties'].get('barrier', ''), x, y])


def extract_features(root, work):
    osm = os.path.join(root, 'data', 'detail', 'countries', 'cape-verde', 'buildings-src.geojsonseq')
    ml = os.path.join(root, 'data', 'detail', 'ml', 'CV.parquet')
    out = os.path.join(work, 'features.csv')
    tag_sel = ', '.join(f"'{k}', json_extract_string(j, '$.properties.\"{k}\"')" for k in TAG_KEYS)
    sql = f"""
SET memory_limit='3GB'; SET threads=4; SET preserve_insertion_order=false;
INSTALL spatial; LOAD spatial;
CREATE TABLE r AS SELECT code, ST_GeomFromText(st_astext) AS g FROM read_csv('{work}/regions.csv', header=true);
CREATE TABLE p AS SELECT category, ST_Point(lon, lat) AS pt FROM read_csv('{work}/places.csv', header=true);
CREATE TABLE c AS SELECT cid, kind, name, ST_GeomFromText(wkt) AS g FROM read_csv('{work}/compounds.csv', header=true, quote='"');
CREATE TABLE gt AS SELECT gid, barrier, ST_Point(lon, lat) AS pt FROM read_csv('{work}/gates.csv', header=true);
CREATE TABLE raw AS SELECT ltrim(line, chr(30))::JSON AS j FROM read_csv('{osm}', columns={{'line': 'VARCHAR'}}, header=false,
    delim=chr(1), quote='', escape='', max_line_size=16000000) WHERE length(line) > 2;
CREATE TABLE b AS
  SELECT 'osm' AS src, json_extract_string(j, '$.properties."@type"') || '/' || json_extract_string(j, '$.properties."@id"') AS bid,
         ST_GeomFromGeoJSON(json_extract(j, '$.geometry')) AS g, to_json(json_object({tag_sel})) AS tags, NULL::DOUBLE AS h
  FROM raw
  UNION ALL
  -- ids in a fixed order: with preserve_insertion_order=false a bare OVER () numbered
  -- the footprints differently from run to run
  SELECT 'ml', 'ml/' || row_number() OVER (ORDER BY ST_X(ST_Centroid(geometry)), ST_Y(ST_Centroid(geometry)), h), geometry, NULL, h FROM '{ml}';
DROP TABLE raw;
CREATE TABLE f AS SELECT src, bid, g, tags, h, ST_Centroid(g) AS ctr,
  ST_Area_Spheroid(ST_FlipCoordinates(g)) AS area, ST_Perimeter_Spheroid(ST_FlipCoordinates(g)) AS perim FROM b;
DROP TABLE b;
CREATE TABLE fm AS SELECT f.*, r.code AS muni FROM f LEFT JOIN r ON ST_Contains(r.g, f.ctr);
CREATE TABLE fp AS SELECT fm.bid, string_agg(p.category, '|' ORDER BY p.category) AS cats FROM fm JOIN p ON ST_Contains(fm.g, p.pt) GROUP BY fm.bid;
CREATE TABLE fc AS SELECT bid, arg_min(cid, ST_Area(c.g)) AS cid FROM fm JOIN c ON ST_Contains(c.g, fm.ctr) GROUP BY bid;
CREATE TABLE cg AS SELECT c.cid, count(gt.gid) AS gates FROM c LEFT JOIN gt ON ST_DWithin(ST_Boundary(c.g), gt.pt, 0.0001) GROUP BY c.cid;
CREATE TABLE ca AS SELECT cid, kind, name, ST_Area_Spheroid(ST_FlipCoordinates(g)) AS carea FROM c;
COPY (
  SELECT fm.src, fm.bid, fm.muni, round(ST_X(fm.ctr), 7) AS lon, round(ST_Y(fm.ctr), 7) AS lat, round(fm.area, 1) AS area,
         round(fm.perim, 1) AS perim, fm.tags, fm.h, fp.cats, fc.cid, ca.kind AS ckind, ca.name AS cname, round(ca.carea) AS carea, cg.gates,
         ST_AsText(ST_ReducePrecision(fm.g, 0.0000001)) AS wkt  -- the footprint, for the registry (tools/issue_registry.py)
  FROM fm LEFT JOIN fp USING (bid) LEFT JOIN fc USING (bid) LEFT JOIN ca ON ca.cid = fc.cid LEFT JOIN cg ON cg.cid = fc.cid
  ORDER BY fm.src DESC, fm.bid  -- a fixed row order, so lotes and the sample are the same on every run
) TO '{out}' (HEADER, DELIMITER ',');
"""
    run(['duckdb', '-batch'], data=sql)
    return out


# ---------------------------------------------------------------- Python part
def load(path):
    """The extracted footprints, less any whose point lies more than 300 m
    outside the national border (the border decides; SPEC.md §3.2)."""
    border = border_polys(os.path.dirname(os.path.abspath(path)))
    rows, abroad = [], 0
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if not E.within_border(float(r['lat']), float(r['lon']), border):
                abroad += 1
                continue
            tags = {}
            if r['tags']:
                tags = {k: v for k, v in json.loads(r['tags']).items() if v is not None}
            rows.append({
                'src': r['src'], 'bid': r['bid'], 'muni': r['muni'] or None, 'lon': float(r['lon']), 'lat': float(r['lat']),
                'area': float(r['area']), 'perim': float(r['perim']), 'tags': tags,
                'h': float(r['h']) if r['h'] not in ('', None) else None,
                'cats': r['cats'].split('|') if r['cats'] else [], 'cid': r['cid'] or None, 'ckind': r['ckind'] or None,
                'cname': r['cname'] or None, 'carea': float(r['carea']) if r['carea'] else None,
                'gates': int(r['gates']) if r['gates'] else 0, 'wkt': r.get('wkt') or None})
    if abroad:
        print(f'{abroad} footprints more than {E.BORDER_M:.0f} m outside the national border dropped', file=sys.stderr)
    return rows


M_PER_DEG = 111320.0


def neighbours(rows, radius_m=100.0):
    """Count of footprints within radius (density) and nearest larger footprint."""
    cell = radius_m / M_PER_DEG
    grid = collections.defaultdict(list)
    for i, r in enumerate(rows):
        grid[(int(r['lon'] / cell), int(r['lat'] / cell))].append(i)
    coslat = math.cos(math.radians(16.0))
    for i, r in enumerate(rows):
        cx, cy = int(r['lon'] / cell), int(r['lat'] / cell)
        n = 0
        best = None
        ri = math.sqrt(r['area'] / math.pi)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((cx + dx, cy + dy), ()):
                    if j == i:
                        continue
                    s = rows[j]
                    d = math.hypot((s['lon'] - r['lon']) * M_PER_DEG * coslat, (s['lat'] - r['lat']) * M_PER_DEG)
                    if d <= radius_m:
                        n += 1
                    if s['area'] > r['area'] * 1.5 and s['area'] >= 40:
                        gap = d - ri - math.sqrt(s['area'] / math.pi)
                        if best is None or gap < best[0]:
                            best = (gap, j)
        r['density'] = n
        r['nearest_larger'] = best


URBAN_DENSITY = 40  # footprints within 100 m; Praia's town grid is ~60-150


def group_lotes(rows):
    """SPEC.md §7.1: group structures into lotes before numbering.
    Rule A (enclosure): footprints whose centre lies in the same mapped
    enclosure (N-Ways compounds: schools, hospitals, hotels, barracks...) form
    one lote; estates (resort or condominium sites over 2 ha with several
    houses) are kept as an estate with each house a lote.
    Rule B (annexe, rural only): a footprint under 30 m2 within 4 m of a
    larger one (>= 40 m2) joins it (kitchen, latrine, curral, water tank).
    Rule C (Cabo Verde specific): touching or near footprints are NOT merged
    in towns: terraced houses wall to wall are separate households.
    Everything else: one footprint, one lote."""
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_c = collections.defaultdict(list)
    estates = set()
    for i, r in enumerate(rows):
        if r['cid']:
            by_c[r['cid']].append(i)
    for cid, idx in by_c.items():
        r0 = rows[idx[0]]
        big = (r0['carea'] or 0) >= 20000
        if big and len(idx) >= 20 and r0['ckind'] in ('site', 'estate'):
            estates.add(cid)  # a resort or condominium: estate gate -> lotes
            continue
        for j in idx[1:]:
            union(idx[0], j)
    rule = ['single'] * len(rows)
    for cid, idx in by_c.items():
        if cid not in estates and len(idx) > 1:
            for j in idx:
                rule[j] = 'enclosure'
    for i, r in enumerate(rows):
        if r['cid'] and r['cid'] not in estates:
            continue
        nl = r['nearest_larger']
        if r['area'] < 30 and r['density'] < URBAN_DENSITY and nl and nl[0] <= 4.0:
            union(nl[1], i)
            rule[i] = 'annexe'
            r['annexe'] = True
            rule[nl[1]] = rule[nl[1]] if rule[nl[1]] != 'single' else 'annexe-host'
    groups = collections.defaultdict(list)
    for i in range(len(rows)):
        groups[find(i)].append(i)
    return list(groups.values()), rule, estates


def pct(n, d):
    return round(100.0 * n / d, 1) if d else None


def quantiles(xs):
    if not xs:
        return None
    xs = sorted(xs)
    q = lambda p: round(xs[min(len(xs) - 1, int(p * len(xs)))], 1)
    return {'p10': q(0.10), 'p25': q(0.25), 'median': q(0.5), 'p75': q(0.75), 'p90': q(0.9), 'p99': q(0.99),
            'mean': round(statistics.fmean(xs), 1)}


SIZE_BANDS = [(0, 12), (12, 25), (25, 50), (50, 100), (100, 200), (200, 500), (500, 2000), (2000, 1e12)]


def band_label(a, b):
    return f'{int(a)}-{int(b)}' if b < 1e11 else f'{int(a)}+'


def summarise(rows, groups, rule, estates):
    iso2 = {m['iso']: m for m in E.MUNI.values()}
    # building-level profile
    for r in rows:
        m = iso2.get(r['muni'])
        island = m['island'] if m else None
        h, hsrc = E.estimate_height(r['tags'], r['h'])
        floors = E.estimate_floors(r['tags'], h)
        cls, conf, src, status = E.classify(r['tags'], r['cats'], r['area'], h, island, r['density'] >= URBAN_DENSITY,
                                            annexe=r.get('annexe', False))
        r.update({'island': island, 'height': h, 'hsrc': hsrc, 'floors': floors, 'floorArea': r['area'] * floors,
                  'cls': cls, 'conf': conf, 'csrc': src, 'status': status})
    # lote-level
    lotes = []
    for g in groups:
        main = max(g, key=lambda i: rows[i]['area'])
        rm = rows[main]
        top = rows[main]['cls'].split('.')[0]
        if len(g) == 1:
            lcls = 'um_edificio'
        elif rule[main] == 'enclosure':
            lcls = 'recinto_' + top  # an enclosed site: school, hospital, barracks, hotel...
        else:
            lcls = 'lote_com_anexos'
        gate = bool(rm['cid'] and rm['cid'] not in estates and rm['gates'] > 0)
        cov, official = E.coverage_of(rm['tags'], rm['lat'], rm['lon'])
        lotes.append({'main': main, 'n': len(g), 'muni': rm['muni'], 'cls': lcls, 'gate': gate, 'coverage': cov, 'official': official,
                      'enclosed': bool(rm['cid'] and rm['cid'] not in estates),
                      'floorArea': sum(rows[i]['floorArea'] for i in g), 'lat': rm['lat'], 'lon': rm['lon'],
                      'members': g})

    def block(sel_rows, sel_lotes):
        n = len(sel_rows)
        cls = collections.Counter(r['cls'] for r in sel_rows)
        top = collections.Counter(r['cls'].split('.')[0] for r in sel_rows)
        srcs = collections.Counter(r['csrc'].split(':')[0] for r in sel_rows)
        conf = collections.Counter(('high' if r['conf'] >= 0.8 else 'medium' if r['conf'] >= 0.55 else 'low') for r in sel_rows)
        hs = [r['height'] for r in sel_rows if r['height']]
        hsrc = collections.Counter(r['hsrc'] or 'none' for r in sel_rows)
        floors = collections.Counter(min(r['floors'], 5) for r in sel_rows)
        bands = collections.Counter()
        for r in sel_rows:
            for a, b in SIZE_BANDS:
                if a <= r['area'] < b:
                    bands[band_label(a, b)] += 1
        multi = [l for l in sel_lotes if l['n'] > 1]
        in_multi = sum(l['n'] for l in multi)
        status = collections.Counter(r['status'] for r in sel_rows)
        return {
            'footprints': n,
            'sources': {'openstreetmap': sum(1 for r in sel_rows if r['src'] == 'osm'), 'googleMicrosoft': sum(1 for r in sel_rows if r['src'] == 'ml')},
            'classTop': {k: pct(v, n) for k, v in top.most_common()},
            'classDetail': {k: v for k, v in cls.most_common()},
            'classSource': {k: pct(v, n) for k, v in srcs.most_common()},
            'confidence': {k: pct(v, n) for k, v in conf.most_common()},
            'statusTagged': dict(status),
            'areaM2': quantiles([r['area'] for r in sel_rows]),
            'perimeterM': quantiles([r['perim'] for r in sel_rows]),
            'sizeBandsM2': {band_label(a, b): bands.get(band_label(a, b), 0) for a, b in SIZE_BANDS},
            'heightKnownPct': pct(len(hs), n),
            'mlHeightFiller': quantiles([r['h'] for r in sel_rows if r['h']]),
            'heightSource': dict(hsrc),
            'heightM': quantiles(hs),
            'floorsEstimated': {('5+' if k == 5 else str(k)): v for k, v in sorted(floors.items())},
            'floorAreaM2Total': round(sum(r['floorArea'] for r in sel_rows)),
            'lotes': {
                'count': len(sel_lotes),
                'footprintsPerLote': round(n / len(sel_lotes), 3) if sel_lotes else None,
                'multiStructure': len(multi),
                'footprintsInMultiStructurePct': pct(in_multi, n),
                'byRule': dict(collections.Counter(l['cls'] if l['n'] > 1 else 'um_edificio' for l in sel_lotes)),
                'enclosed': sum(1 for l in sel_lotes if l['enclosed']),
                'enclosedWithKnownGate': sum(1 for l in sel_lotes if l['gate']),
                'lotesWithKnownGatePct': round(100.0 * sum(1 for l in sel_lotes if l['gate']) / len(sel_lotes), 3) if sel_lotes else None,
                'enclosedWithKnownGatePct': pct(sum(1 for l in sel_lotes if l['gate']), sum(1 for l in sel_lotes if l['enclosed'])),
                'largestStructures': max((l['n'] for l in sel_lotes), default=0),
            },
            'poiMatchedPct': pct(sum(1 for r in sel_rows if r['cats']), n),
            'coverage': dict(collections.Counter(l['coverage'] for l in sel_lotes)),
        }

    out = {'built': '2026-10-18', 'notes': [
        'Footprints = OpenStreetMap buildings + Google Open Buildings / Microsoft footprints OSM lacks (Overture), as held by N-Ways on 2026-10-17.',
        'Classes are inferred (engine/reference/cv_engine.py classify); a footprint with no tag, no place and ordinary size falls to the census prior residencial.moradia.',
        'Heights: OSM height or building:levels x 3 m only. The ML h field is evenly spread 3.5-7.0 m (a filler, not a measurement): shown as mlHeightFiller, not used.',
        'Lotes: grouping of SPEC.md 7.1 (enclosures from the N-Ways routing build, rural annexes). Gate known = an enclosure with a mapped gate on its edge.',
        'Census 2021 (INE, preliminary results) for comparison: 150,016 buildings, 87.0 % of classic buildings homes only, 27.7 % unfinished.'],
        'country': block(rows, lotes), 'municipalities': {}, 'islands': {}}
    for iso in sorted(iso2):
        sel = [r for r in rows if r['muni'] == iso]
        out['municipalities'][iso] = block(sel, [l for l in lotes if l['muni'] == iso])
    for island in sorted({m['island'] for m in E.MUNI.values()}):
        isos = {m['iso'] for m in E.MUNI.values() if m['island'] == island}
        out['islands'][island] = block([r for r in rows if r['muni'] in isos], [l for l in lotes if l['muni'] in isos])
    out['unassigned'] = sum(1 for r in rows if not r['muni'])
    return out, lotes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.environ.get('NWAYS_ROOT'), help='the N-Ways data checkout (or NWAYS_ROOT)')
    ap.add_argument('--work', default=None)
    ap.add_argument('--skip-extract', action='store_true')
    a = ap.parse_args()
    work = a.work or tempfile.mkdtemp(prefix='cv-stats-')
    feats = os.path.join(work, 'features.csv')
    if not a.skip_extract:
        if not a.root or not DB:
            sys.exit('extracting needs --root (or NWAYS_ROOT) and NWAYS_DB; use --skip-extract with --work to reuse an extract')
        export_inputs(a.root, work)
        extract_features(a.root, work)
    rows = load(feats)
    neighbours(rows)
    groups, rule, estates = group_lotes(rows)
    stats, lotes = summarise(rows, groups, rule, estates)
    stats['estates'] = sorted(estates)
    import build_zones
    with open(os.path.join(work, 'names.csv'), encoding='utf-8') as f:
        names = list(csv.DictReader(f))
    boxes = {m['iso']: m['box'] for m in json.loads(read_text(os.path.join(REPO, 'model', 'regions.json')))}
    import build_names
    frozen = build_names.issued()
    zones_out = os.path.join(work if frozen else os.path.join(REPO, 'engine', 'data'), 'zones.json')
    _, stats['zones'], stats['names'] = build_zones.build(lotes, names, E, boxes, zones_out)
    if frozen:
        print(f'codes are issued: the register is frozen; the rebuilt zones and names are in {work}', file=sys.stderr)
    with open(os.path.join(REPO, 'model', 'building-stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    c = stats['country']
    print(f"{c['footprints']} footprints, {c['lotes']['count']} lotes, classes {c['classTop']}")


if __name__ == '__main__':
    main()
