#!/usr/bin/env python3
"""Conformance vectors from the published registry (engine/SPEC.md §11).

Writes engine/test-vectors-registry.json: real issued codes with every form
an implementation must reproduce from the register alone (remembered,
machine, plate and spoken forms, check digit, spot code of the entrance),
the codes of every zone of four repeated names, codes with official
addresses, and an insertion computed on a real zone's issued state.

  python3 tools/registry_vectors.py           write the vectors from registry/
  python3 tools/registry_vectors.py --check   rebuild them and compare

Standard library only; reads registry/ and engine/data/ only.
"""
import argparse
import csv
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import cv_engine as E  # noqa: E402

REG = os.path.join(REPO, 'registry')
OUT = os.path.join(REPO, 'engine', 'test-vectors-registry.json')
SAME_NAMES = ('fazenda', 'achadinha', 'sao pedro', 'bela vista')
# A zone of moderate size whose whole issued state goes into the vector, and
# an empty spot in it (no footprint and no entrance within 3 m), as a new
# building would be.
INSERT_ZONE = 'BR-034'
INSERT_POINT = (14.8664528, -24.6885324)


def rows(key):
    with open(os.path.join(REG, f'{key}.csv'), encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def anchors():
    with gzip.open(os.path.join(REG, 'lotes.csv.gz'), 'rt', encoding='utf-8', newline='') as f:
        return {r['machine']: (float(r['anchor_lat']), float(r['anchor_lng'])) for r in csv.DictReader(f)}


def card(r):
    z = E.zone_by_ref(r['zone'])
    n = int(r['number'])
    lat, lng = float(r['entrance_lat']), float(r['entrance_lng'])
    return {'home': r['home'], 'machine': r['machine'], 'check': int(r['check']), 'zone': r['zone'],
            'officialName': z['officialName'], 'municipality': E.MUNI[z['key']]['name'], 'island': E.MUNI[z['key']]['island'],
            'plate': E.format_plate(z, n), 'full': E.format_home(z, n, full=True), 'spokenPt': E.spoken(z, n, 'pt'),
            'spokenKea': E.spoken(z, n, 'kea'), 'entrance': [lat, lng], 'plusCode': r['plus_code'], 'use': r['use'],
            'status': r['status']}


def build():
    E.use_published_registry(REG)
    with open(os.path.join(REG, 'MANIFEST.json'), encoding='utf-8') as f:
        man = json.load(f)
    by_muni = {k: rows(k) for k in man['byMunicipality']}
    sample = []
    for rs in by_muni.values():
        ok = [r for r in rs if E.plate_ok(E.zone_by_ref(r['zone'])['name'])]
        for r in (ok[0], ok[len(ok) // 2], ok[-1]):
            sample.append(card(r))
    all_rows = [r for rs in by_muni.values() for r in rs]
    first = {}
    for r in all_rows:
        if r['zone'] not in first or int(r['number']) < int(first[r['zone']]['number']):
            first[r['zone']] = r
    same = []
    for key in SAME_NAMES:
        e = E.names()[key]
        for b in e['blocks']:
            if b['zone'] in first:
                c = card(first[b['zone']])
                c.update(name=e['name'], block=[b['lo'], b['hi']], near=E.zone_by_ref(b['zone']).get('near'))
                same.append(c)
    official = [dict(card(r), coverage=r['coverage'], officialAddress=r['official_address'])
                for r in all_rows if r['coverage'] == 'official'][:4]
    official += [dict(card(r), coverage=r['coverage']) for r in all_rows if r['coverage'] == 'official-pending'][:2]
    # insertion on the real issued state of one zone
    anc = anchors()
    z = E.zone_by_ref(INSERT_ZONE)
    zr = [r for r in by_muni[z['key']] if r['zone'] == INSERT_ZONE]
    issued = {int(r['number']): r['machine'] for r in zr}
    lat, lng = INSERT_POINT
    entry = json.loads(json.dumps(E.names()[z['nameKey']]))
    n = E.insert_lote(issued, lat, lng, z['box'], {m: anc[m] for m in issued.values()}, entry, INSERT_ZONE)
    insertion = {'zone': INSERT_ZONE, 'box': z['box'], 'blocks': E.zone_blocks(entry, INSERT_ZONE),
                 'issued': [[int(r['number']), r['machine'], list(anc[r['machine']])] for r in zr],
                 'point': [lat, lng], 'number': n, 'home': E.format_home(z, n),
                 'machine': E.format_machine(z, n),
                 'rule': "the middle free number between the point's Hilbert neighbours in the zone's block (SPEC.md §7.4)"}
    return {'about': 'Real codes of the published registry (registry/), with every form derived from the register alone; '
                     'an implementation reproduces each value (SPEC.md §11).',
            'registryExported': man['exported'], 'codes': man['codes'], 'sample': sample, 'sameName': same,
            'official': official, 'insertion': insertion}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    v = build()
    text = json.dumps(v, ensure_ascii=False, indent=1) + '\n'
    if a.check:
        with open(OUT, encoding='utf-8') as f:
            same = f.read() == text
        print(f'{OUT}: reproduced from the registry: {same}')
        sys.exit(0 if same else 1)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"{len(v['sample'])} sample codes, {len(v['sameName'])} same-name codes, {len(v['official'])} official, "
          f"insertion {v['insertion']['home']}", file=sys.stderr)


if __name__ == '__main__':
    main()
