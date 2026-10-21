#!/usr/bin/env python3
"""Zones for Cabo Verde home codes (SPEC.md §3.3).

A zone is the place word of a home code ("Palmarejo" in "Palmarejo 12 34"):
a frozen namespace built once from the N-Ways locality layer and the lotes
(plots/compounds) of tools/building_stats.py. Called from building_stats.py;
writes the zone table (engine/data/zones.json, which is frozen once codes are
issued: building_stats.py then writes the rebuilt table to its work folder for
comparison) and returns statistics.

Rules, in order:
  1. Candidates: OpenStreetMap city, town, suburb, neighbourhood, village
     (geo_names osm:*), and GeoNames localities that are not landforms
     (Ponta, Ilhéu, Baía, Pico, Morro, Cabo, Rocha, Lagoa, Furna, Boca,
     Serra, Praia de...). Squares and streets (Largo, Praça, Rua, Avenida,
     Rotunda) and school points (Escola ...) are never zones.
  2. Inside a municipality, the same name within 2 km is one candidate
     (OpenStreetMap preferred).
  3. In towns, a GeoNames locality within 1 km of an OSM suburb or
     neighbourhood is dropped: bairro names come from the town's own list;
     a city or town point with 3 or more bairros within 3 km is not a zone
     (its bairros are).
  4. Each lote goes to the nearest candidate in its own municipality.
  5. A candidate with fewer than 15 lotes is dropped (its lotes go to the
     next nearest) unless it is more than 1.5 km from every other one: an
     isolated povoação keeps its own name. Repeat until stable.
  6. The map name is kept as the zone's officialName. The name in the code
     is the short plate name (at most 12 characters and 2 words, SPEC.md
     §3.7), derived in tools/build_names.py; zones with the
     same plate name share one national number range, and the number tells
     them apart. Two of one municipality record their nearest differently
     named zone as `near`, for the card ("Calheta, perto de Morrinho").
  7. Index: 1.. in Hilbert order of the zone anchors over the municipality
     box. Digits and number blocks come from the national name register
     (tools/build_names.py), not from the zone alone.
"""
import collections
import json
import math
import os

M = 111320.0
ZONES_STATUS = ('The zones of Cabo Verde, built by tools/build_zones.py from the N-Ways map of 2026-10-17 and frozen at first '
                'issue (2026-10-19). registry/zones.csv publishes the same zones.')
COS = math.cos(math.radians(16.0))
LANDFORMS = ('ponta', 'ilhéu', 'ilheu', 'ilha ', 'baía', 'baia', 'pico', 'morro', 'cabo ', 'rocha', 'praia de', 'praia do',
             'praia da', 'lagoa', 'furna', 'boca ', 'serra')
# Spellings people use besides the map name (accents and apostrophes fold
# anyway). They decode to the zone; they are not the plate name unless
# tools/build_names.py KNOWN cites a source (ASA and AGF do; no published use
# of "AGT" was found, so Achada Grande Trás keeps it as an alias only).
KNOWN_ALIASES = {'Platô': ['Plateau', 'Plató'], 'Achada Santo António': ['ASA', 'Achada Sto António'],
                 'Ponta d\'Agua': ["Ponta d'Água", 'Pontadagua'], 'Cha d’Areia': ["Chã d'Areia", 'Chã de Areia'],
                 'Eugenio Lima': ['Eugénio Lima'], 'Achada Grande Trás': ['Achada Grande Tras', 'AGT'],
                 'Achada Grande Frente': ['AGF'], 'Lém-Ferreira': ['Lem Ferreira']}
STREETS = ('largo', 'praça', 'praca', 'rua ', 'avenida', 'rotunda', 'estrada', 'escola ')  # a school point is not a zone


def _d(a, b):
    return math.hypot((a['lon'] - b['lon']) * M * COS, (a['lat'] - b['lat']) * M)


def candidates(names, E):
    out = []
    for n in names:
        nm = n['name'].strip()
        alias = []
        if nm.startswith('(') and ')' in nm:  # "(Ribeira de) Craquinha" -> "Craquinha", alias the full name
            alias = [nm.replace('(', '').replace(')', '')]
            nm = nm.split(')', 1)[1].strip()
        lo = nm.lower()
        if lo.startswith(STREETS) or (n['id'].startswith('gn:') and lo.startswith(LANDFORMS)):
            continue
        lon, lat = float(n['lon']), float(n['lat'])
        m = E.municipality_at(lat, lon)
        if not m:
            continue
        out.append({'name': nm, 'official': (alias or [nm])[0], 'kind': n['kind'], 'osm': n['id'].startswith('osm'), 'srcId': n['id'], 'lat': lat, 'lon': lon,
                    'muni': m['iso'], 'key': m['key'], 'alias0': alias})
    ded = []
    for c in sorted(out, key=lambda c: (not c['osm'], c['srcId'])):
        if any(x['muni'] == c['muni'] and E.fold(x['name']) == E.fold(c['name']) and _d(x, c) < 2000 for x in ded):
            continue
        ded.append(c)
    subs = [c for c in ded if c['kind'] in ('suburb', 'neighbourhood')]
    ded = [c for c in ded if c['osm'] or not any(_d(c, s) < 1000 for s in subs)]
    # 3b. a city or town point inside its own bairros is not a zone: "Praia"
    # is the municipality, the bairros are the place words.
    return [c for c in ded if not (c['kind'] in ('city', 'town') and sum(1 for s in subs if _d(c, s) < 3000) >= 3)]


def _assign(lotes, alive):
    z = collections.defaultdict(list)
    for i, l in enumerate(lotes):
        cs = alive.get(l['muni']) or []
        if cs:
            best = min(cs, key=lambda c: ((c['lon'] - l['lon']) * COS) ** 2 + (c['lat'] - l['lat']) ** 2)
            z[id(best)].append(i)
    return z


def build(lotes, names, E, regions_box, out_path):
    cand = candidates(names, E)
    alive = collections.defaultdict(list)
    for c in cand:
        alive[c['muni']].append(c)
    for _ in range(6):
        z = _assign(lotes, alive)
        changed = False
        for k, cs in alive.items():
            keep = []
            for c in cs:
                n = len(z.get(id(c), []))
                iso = min((_d(c, o) for o in cs if o is not c), default=1e9)
                if n >= 15 or (n >= 1 and iso > 1500):
                    keep.append(c)
                else:
                    changed = True
            alive[k] = keep
        if not changed:
            break
    z = _assign(lotes, alive)
    zones = []
    for muni, cs in sorted(alive.items()):
        cs = [c for c in cs if z.get(id(c))]
        # rule 6: the map name is the official name; plate name and `near`
        # come from tools/build_names.py
        for c in cs:
            c['display'] = c['name']
            c['aliases'] = list(c.get('alias0', [])) + KNOWN_ALIASES.get(c['name'], [])
            c['near'] = None
        box = regions_box[muni]
        cs.sort(key=lambda c: (E.hilbert_of(c['lat'], c['lon'], box), c['srcId']))
        for i, c in enumerate(cs, start=1):
            idx = z[id(c)]
            lats = [lotes[j]['lat'] for j in idx]
            lons = [lotes[j]['lon'] for j in idx]
            pad = 300.0 / M
            zbox = [round(min(lons) - pad / COS, 5), round(min(lats) - pad, 5), round(max(lons) + pad / COS, 5), round(max(lats) + pad, 5)]
            zones.append({'key': c['key'], 'iso': muni, 'index': i, 'name': c['display'], 'officialName': c['official'], 'aliases': c['aliases'],
                          'near': c['near'], 'source': c['srcId'], 'kind': c['kind'], 'anchor': [round(c['lat'], 6), round(c['lon'], 6)],
                          'box': zbox, 'lotes': len(idx), '_members': idx})
    for zz in zones:
        for j in zz['_members']:
            lotes[j]['zone'] = zz
    import build_names
    names_stats = build_names.build(zones, os.path.join(os.path.dirname(out_path), 'names.json'))
    pub = [{k: v for k, v in zz.items() if not k.startswith('_')} for zz in zones]
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'status': ZONES_STATUS, 'rules': 'tools/build_zones.py', 'zones': pub}, f, ensure_ascii=False, indent=0)
    # statistics
    digits = collections.Counter(zz['digits'] for zz in zones)
    lotes_by_digits = collections.Counter()
    for zz in zones:
        lotes_by_digits[zz['digits']] += zz['lotes']
    sizes = sorted(zz['lotes'] for zz in zones)
    per_muni = collections.defaultdict(list)
    for zz in zones:
        per_muni[zz['iso']].append(zz)
    stats = {
        'zones': len(zones), 'candidates': len(cand),
        'zonesByDigits': {str(k): v for k, v in sorted(digits.items())},
        'lotesByDigits': {str(k): v for k, v in sorted(lotes_by_digits.items())},
        'lotesPerZone': {'min': sizes[0], 'median': sizes[len(sizes) // 2], 'p90': sizes[int(len(sizes) * 0.9)], 'max': sizes[-1]},
        'largestZones': [{'name': zz['name'], 'officialName': zz['officialName'], 'iso': zz['iso'], 'lotes': zz['lotes'], 'digits': zz['digits'], 'block': zz['block']}
                         for zz in sorted(zones, key=lambda q: -q['lotes'])[:12]],
        'perMunicipality': {iso: {'zones': len(v), 'maxLotes': max(q['lotes'] for q in v),
                                  'threeDigit': sum(1 for q in v if q['digits'] == 3), 'fourDigit': sum(1 for q in v if q['digits'] == 4)}
                            for iso, v in sorted(per_muni.items())},
        'praiaZones': [{'index': zz['index'], 'name': zz['name'], 'officialName': zz['officialName'], 'lotes': zz['lotes'], 'digits': zz['digits'], 'block': zz['block']}
                       for zz in sorted(per_muni.get('CV-PR', []), key=lambda q: -q['lotes'])],
    }
    return zones, stats, names_stats
