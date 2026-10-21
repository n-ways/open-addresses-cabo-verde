#!/usr/bin/env python3
"""The lotes of Cabo Verde for issuing home codes (engine/SPEC.md §7.1).

Reads N-Ways' map data read-only, as tools/building_stats.py does, groups the
structures into lotes (rules A, A2, B, C), takes each lote's anchor (its gate
when a mapped gate is on its enclosure, else its main structure), puts it in
its FROZEN zone (the nearest zone anchor of engine/data/zones.json in
its own municipality: zones are never rebuilt once codes exist) and marks its
coverage (official address, official-pending, or N-Ways).

The border decides: footprints, enclosures and gates more than 300 m outside
the national border never reach the lotes (tools/building_stats.py), and a
lote whose anchor still lies there is dropped and counted as "abroad".

It writes one JSON line per lote (gzip). NUMBERS ARE NOT GIVEN HERE: the
registry server numbers the lotes (the N-Ways backend, `homecodes issue`),
which keeps every number already issued and only adds new ones, so a rerun
never renumbers a code.

  python3 tools/issue_registry.py --root /path/to/n-ways-data --work DIR [--skip-extract] [--muni PR] --out lotes.jsonl.gz

Extracting needs NWAYS_DB (read-only) and duckdb (memory limit 3 GB).

Each line: {"key": stable id of the main structure, "muni": "PR", "zone": "PR-024",
"anchor": [lat, lon], "anchorKind": "gate"|"centre", "gate": [lat, lon]|null,
"coverage": "nways"|"official"|"official-pending", "official": address|null,
"enclosed": bool, "rule": "single"|"enclosure"|"annexe-host"|..., "structures": [
{"id", "src": "osm"|"ml", "lat", "lon", "areaM2", "perimeterM", "tags": {...}, "mlHeight",
"places": [...], "annexe": bool, "urban": bool, "wkt"}]} (main structure first).

Structure ids are stable across map updates: OpenStreetMap "osm:way/<id>" or
"osm:relation/<id>"; a Google/Microsoft footprint "nw:" + the first 12 hex
characters of the SHA-1 of its centre to 1e-6 degrees and its area to 1 m2.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import building_stats as BS  # noqa: E402
import cv_engine as E  # noqa: E402

M = 111320.0
COS = math.cos(math.radians(16.0))


def structure_id(r):
    if r['src'] == 'osm':
        return 'osm:' + r['bid']
    h = hashlib.sha1(f"{r['lat']:.6f},{r['lon']:.6f},{round(r['area'])}".encode()).hexdigest()[:12]
    return 'nw:' + h


def compound_gates(work):
    """The mapped gate on each enclosure's edge (within about 11 m), the
    lowest gate id when there are several: one per compound."""
    out = os.path.join(work, 'compound_gates.csv')
    sql = f"""
SET memory_limit='2GB'; SET threads=4;
INSTALL spatial; LOAD spatial;
CREATE TABLE c AS SELECT cid, ST_GeomFromText(wkt) AS g FROM read_csv('{work}/compounds.csv', header=true, quote='"');
CREATE TABLE gt AS SELECT gid, ST_Point(lon, lat) AS pt FROM read_csv('{work}/gates.csv', header=true);
COPY (SELECT c.cid, arg_min(gt.gid, gt.gid) AS gid, arg_min(ST_Y(gt.pt), gt.gid) AS lat, arg_min(ST_X(gt.pt), gt.gid) AS lon
      FROM c JOIN gt ON ST_DWithin(ST_Boundary(c.g), gt.pt, 0.0001) GROUP BY c.cid ORDER BY c.cid) TO '{out}' (HEADER, DELIMITER ',');
"""
    r = subprocess.run(['duckdb', '-batch'], input=sql, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        sys.exit('duckdb failed: ' + r.stderr[-2000:])
    gates = {}
    with open(out, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            gates[row['cid']] = (float(row['lat']), float(row['lon']))
    return gates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=os.environ.get('NWAYS_ROOT'), help='the N-Ways data checkout (or NWAYS_ROOT)')
    ap.add_argument('--work', default=None)
    ap.add_argument('--skip-extract', action='store_true')
    ap.add_argument('--muni', action='append', help='only these municipality keys (PR, SV...); default: the whole country')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    work = a.work or tempfile.mkdtemp(prefix='cv-issue-')
    feats = os.path.join(work, 'features.csv')
    if not a.skip_extract:
        if not a.root or not BS.DB:
            sys.exit('extracting needs --root (or NWAYS_ROOT) and NWAYS_DB; use --skip-extract with --work to reuse an extract')
        BS.export_inputs(a.root, work)
        BS.extract_features(a.root, work)
    gates = compound_gates(work)
    rows = BS.load(feats)
    BS.neighbours(rows)
    groups, rule, estates = BS.group_lotes(rows)
    _, lotes = BS.summarise(rows, groups, rule, estates)
    border = BS.border_polys(work)
    zones = E.zones()
    by_muni = collections.defaultdict(list)
    for z in zones:
        by_muni[z['iso']].append(z)
    want = {('CV-' + k.upper()) for k in (a.muni or [])}
    counts = collections.Counter()
    seen = set()
    with gzip.open(a.out, 'wt', encoding='utf-8') as out:
        for l in lotes:
            iso = l['muni']
            if not iso or (want and iso not in want):
                continue
            rm = rows[l['main']]
            gate = gates.get(rm['cid']) if l['enclosed'] and rm['cid'] else None
            anchor = gate or (rm['lat'], rm['lon'])
            if not E.within_border(anchor[0], anchor[1], border):
                counts['abroad'] += 1  # never coded: outside Cabo Verde's border
                continue
            cs = by_muni.get(iso) or []
            if not cs:
                counts['noZone'] += 1
                continue
            # the zone of the lote's main structure, as at zone building
            # (tools/build_zones.py _assign): nearest zone anchor
            zz = min(cs, key=lambda c: ((c['anchor'][1] - rm['lon']) * COS) ** 2 + (c['anchor'][0] - rm['lat']) ** 2)
            members = [l['main']] + sorted((i for i in l['members'] if i != l['main']), key=lambda i: (-rows[i]['area'], rows[i]['bid']))
            sts = []
            for i in members:
                r = rows[i]
                sts.append({'id': structure_id(r), 'src': r['src'], 'lat': r['lat'], 'lon': r['lon'], 'areaM2': r['area'],
                            'perimeterM': r['perim'], 'tags': r['tags'], 'mlHeight': r['h'], 'places': r['cats'],
                            'annexe': bool(r.get('annexe')), 'urban': r['density'] >= BS.URBAN_DENSITY, 'wkt': r.get('wkt')})
            key = sts[0]['id']
            if key in seen:
                counts['duplicateKey'] += 1
                continue
            seen.add(key)
            rec = {'key': key, 'muni': iso[3:], 'zone': E.zref(zz), 'anchor': [round(anchor[0], 7), round(anchor[1], 7)],
                   'anchorKind': 'gate' if gate else 'centre', 'gate': [round(gate[0], 7), round(gate[1], 7)] if gate else None,
                   'coverage': l['coverage'], 'official': l['official'], 'enclosed': l['enclosed'],
                   'rule': rule[l['main']], 'structures': sts}
            out.write(json.dumps(rec, ensure_ascii=False, separators=(',', ':')) + '\n')
            counts[l['coverage']] += 1
            counts['lotes'] += 1
            counts['structures'] += len(sts)
    print(json.dumps(dict(counts)), file=sys.stderr)


if __name__ == '__main__':
    main()
