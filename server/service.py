"""What the API answers: cards, lookups, points, issue and changes.

The rules are those of the N-Ways issuer for Cabo Verde (engine/SPEC.md §7):
a point finds the lote whose footprint holds it, else the nearest entrance or
footprint within 12 m; a new code goes to the zone of the nearest issued code
in the same municipality (within 3 km), else to the zone whose anchor is
nearest; its number is the free number between its Hilbert neighbours, else
the nearest free number of the zone's blocks, else a new block from the
name's spare space. No issued number ever changes or is given twice.
The border decides: a new code or a moved entrance more than 300 m outside
Cabo Verde's national border is refused (422 outside), whatever the
municipality, zone or spot rules would allow.
"""
import copy
import hashlib
import math
import re
import struct
import threading
import time
import unicodedata

from . import engine as E
from . import geo
from . import store as S

FOUND_M = 12.0          # a point finds a lote within this distance of its entrance or footprint
SAME_BUILDING_M = 3.0   # a new code is refused this close to an issued lote
ZONE_SEARCH_M = 3000.0  # a new code takes the zone of the nearest issued code within this distance
DOOR_MAX_M = 80.0       # another door of a lote is within this distance of its entrance
MOVE_MAX_M = 80.0       # an entrance moves at most this far
MIN_AREA_M2 = 12.0      # a tapped outline is between 12 m² and 2 ha
MAX_AREA_M2 = 20000.0
NEAR_MAX_M = 500.0
NEAR_MAX_RESULTS = 100
STATUSES = ('provisional', 'confirmed', 'retired')


class ApiError(Exception):
    def __init__(self, status, code, message, **extra):
        super().__init__(message)
        self.status, self.code, self.message, self.extra = status, code, message, extra


def go_round(x):
    """Round half away from zero, exactly (as Go's math.Round)."""
    t = math.trunc(x)
    if abs(x - t) >= 0.5:
        t += math.copysign(1, x)
    return float(t)


def r1(x):
    return go_round(x * 10) / 10


def fold(s):
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^\w]+', ' ', s.lower()).split())


def _num(x):
    if x is None or x == '':
        return None
    v = float(x)
    return int(v) if v.is_integer() and abs(v) < 1e15 else v


SPOT_FULL = re.compile(r'^[23456789CFGHJMPQRVWX]{8}\+[23456789CFGHJMPQRVWX]{2,3}$')
SPOT_SHORT = re.compile(r'^([23456789CFGHJMPQRVWX]{2,6}\+[23456789CFGHJMPQRVWX]{2,3})[\s,]+(.+)$')


class Service:
    def __init__(self, db_path, issue_keys=(), issue_per_day=500):
        self.db_path = db_path
        self.local = threading.local()
        self.write_lock = threading.Lock()
        self.reg_lock = threading.Lock()
        self.issue_keys = {hashlib.sha256(k.encode()).hexdigest()[:16]: k for k in issue_keys if k}
        self.issue_per_day = issue_per_day
        con = self.con()
        if S.meta(con, 'country') != E.COUNTRY:
            raise RuntimeError(f'{db_path} is not a {E.COUNTRY} registry database (run the import first)')
        self.load_register()

    # -- database and register ------------------------------------------------
    def con(self):
        c = getattr(self.local, 'con', None)
        if c is None:
            c = S.connect(self.db_path)
            self.local.con = c
        return c

    def release(self):
        """Close this thread's connection (the server calls it after each
        request: every request runs in a thread of its own)."""
        c = getattr(self.local, 'con', None)
        if c is not None:
            c.close()
            self.local.con = None

    close = release

    def load_register(self):
        """Give the reference engine the frozen register of this database:
        every zone and name, with every block issued so far."""
        con = self.con()
        blocks = {}
        for b in con.execute('SELECT name_index, zone, lo, hi FROM blocks ORDER BY name_index, seq'):
            blocks.setdefault(b['name_index'], []).append({'zone': b['zone'], 'lo': b['lo'], 'hi': b['hi']})
        names, first = [], {}
        for r in con.execute('SELECT * FROM names ORDER BY name_index'):
            bl = blocks.get(r['name_index'], [])
            e = {'key': r['name_key'], 'index': r['name_index'], 'name': r['plate_name'],
                 'aliases': [a for a in r['aliases'].split('|') if a],
                 'officialNames': [a for a in r['official_names'].split('|') if a],
                 'needsCouncilChoice': r['needs_council_choice'] == 'true', 'digits': r['digits'], 'blocks': bl,
                 'reserve': [int(x) for x in r['reserve'].split('-')]}
            for b in bl:  # lengths a name has opened since first issue (SPEC §5.3)
                d = len(str(b['lo']))
                if d != e['digits'] and d not in e.get('lengths', []):
                    e.setdefault('lengths', [e['digits']]).append(d)
                first.setdefault(b['zone'], [b['lo'], b['hi']])
            names.append(e)
        zones = []
        for r in con.execute('SELECT * FROM zones ORDER BY seq'):
            zones.append({'key': r['municipality'], 'iso': 'CV-' + r['municipality'], 'index': r['idx'],
                          'name': r['plate_name'], 'officialName': r['official_name'],
                          'aliases': [a for a in r['aliases'].split('|') if a], 'near': r['near'] or None,
                          'plateRule': r['plate_rule'], 'needsCouncilChoice': r['needs_council_choice'] == 'true',
                          'nameKey': r['name_key'], 'nameIndex': r['name_index'],
                          'box': [float(x) for x in r['box'].split()], 'anchor': [float(x) for x in r['anchor'].split()],
                          'block': first.get(r['ref'])})
        with self.reg_lock:
            E.use_register(zones, names)
            self.zone_list = zones
            self.zone_by_ref = {E.zref(z): z for z in zones}
            self.official = {}
            for r in con.execute("SELECT machine, official_address FROM codes WHERE official_address <> ''"):
                self.official.setdefault(fold(r['official_address']), []).append(r['machine'])
            self.counts = None

    def meta(self, key):
        return S.meta(self.con(), key)

    def zone_counts(self):
        if self.counts is None:
            c = {}
            for r in self.con().execute('SELECT zone, status, count(*) n FROM codes GROUP BY zone, status'):
                c.setdefault(r['zone'], {})[r['status']] = r['n']
            self.counts = c
        return self.counts

    # -- municipalities ("zones" of the API) and places ("areas") -----------------
    def muni_box(self, iso):
        for i, _, (x0, y0, x1, y1) in E._cv._load_polys():
            if i == iso:
                return [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)]
        return None

    def area_of_muni(self, m):
        return {'key': m['key'], 'name': m['name'], 'island': m['island'], 'bbox': self.muni_box(m['iso'])}

    def muni_summary(self, m):
        counts = {}
        for ref, c in self.zone_counts().items():
            if ref.startswith(m['key'] + '-'):
                for k, v in c.items():
                    counts[k] = counts.get(k, 0) + v
        return {'key': m['key'], 'iso': m['iso'], 'name': m['name'], 'island': m['island'],
                'postcode': self.postcode('', m['key']), 'seat': m['seat'], 'bbox': self.muni_box(m['iso']),
                'codes': sum(counts.values()), 'byStatus': counts,
                'areas': sum(1 for z in self.zone_list if z['key'] == m['key'])}

    def municipality(self, key):
        m = E.MUNI.get(key.upper().replace('CV-', ''))
        if m is None:
            raise ApiError(404, 'unknown_zone', f'There is no municipality {key!r}. The keys are '
                           + ', '.join(E.MUNI) + '.')
        return m

    def area_summary(self, z):
        ref = E.zref(z)
        c = self.zone_counts().get(ref, {})
        return {'id': ref, 'municipality': z['key'], 'plateName': z['name'], 'officialName': z['officialName'],
                'nameIndex': z['nameIndex'], 'needsCouncilChoice': z['needsCouncilChoice'], 'codes': sum(c.values())}

    def area(self, ref):
        z = self.zone_by_ref.get(ref.upper())
        if z is None:
            raise ApiError(404, 'unknown_area', f'There is no area {ref!r}. Area ids look like PR-024.')
        e = E.names_by_index()[z['nameIndex']]
        ref = E.zref(z)
        c = self.zone_counts().get(ref, {})
        m = E.MUNI[z['key']]
        return {'id': ref, 'municipality': {'key': m['key'], 'name': m['name'], 'island': m['island']},
                'plateName': z['name'], 'officialName': z['officialName'], 'plateRule': z['plateRule'],
                'needsCouncilChoice': z['needsCouncilChoice'], 'aliases': z['aliases'], 'near': z['near'],
                'nameKey': z['nameKey'], 'nameIndex': z['nameIndex'], 'box': z['box'], 'anchor': z['anchor'],
                'blocks': [{'lo': lo, 'hi': hi} for lo, hi in E.zone_blocks(e, ref)],
                'name': {'plateName': e['name'], 'digits': e['digits'], 'reserve': e['reserve'],
                         'blocks': e['blocks'], 'officialNames': e['officialNames']},
                'codes': sum(c.values()), 'byStatus': c}

    def find_areas(self, name, limit=50):
        q = name.strip()
        if not q:
            raise ApiError(400, 'bad_request', 'Give a place name: /v1/areas?name=Palmarejo')
        keys = set(E.name_keys_typed(q))
        f = fold(q)
        out = []
        for z in self.zone_list:
            names_ = [z['name'], z['officialName']] + z['aliases']
            if z['nameKey'] in keys or any(E.name_key(n) in keys for n in names_) or any(fold(n) == f for n in names_):
                out.append(self.area_summary(z))
        if not out:  # then names that start with what was typed
            for z in self.zone_list:
                if any(fold(n).startswith(f) for n in [z['name'], z['officialName']] + z['aliases']):
                    out.append(self.area_summary(z))
        return {'name': q, 'areas': out[:limit], 'count': len(out)}

    # -- cards ----------------------------------------------------------------
    def postcode(self, postcode, key):
        p = E.postcode_for(postcode, key)
        return {'value': p[0], 'kind': 'area', 'source': p[1]} if p else None

    def row(self, machine):
        return self.con().execute('SELECT * FROM codes WHERE machine = ?', (machine,)).fetchone()

    def card(self, r):
        z = self.zone_by_ref[r['zone']]
        m = E.MUNI[z['key']]
        n = r['number']
        sts = []
        for s in self.con().execute('SELECT * FROM structures WHERE machine = ? ORDER BY idx', (r['machine'],)):
            st = {'index': s['idx'], 'id': s['structure_id'], 'use': s['use'], 'confidence': _num(s['confidence']),
                  'source': s['class_source'], 'status': s['status'], 'footprintM2': _num(s['footprint_m2']),
                  'perimeterM': _num(s['perimeter_m'])}
            if s['height_m']:
                st['heightM'] = _num(s['height_m'])
            if s['height_source']:
                st['heightSource'] = s['height_source']
            st.update({'floors': int(s['floors']), 'floorAreaM2': _num(s['floor_area_m2'])})
            if s['name'] and not E.residential(s['use']):
                st['name'] = s['name']
            st['data'] = s['data']
            sts.append(st)
        pc = self.postcode(r['postcode'], r['muni'])
        full = E.format_home(z, n, full=True) + (f" · {pc['value']}" if pc else '')
        card = {
            'country': E.COUNTRY, 'machine': r['machine'], 'home': r['home'], 'check': r['check_digit'],
            'name': z['name'], 'officialName': z['officialName'] if z['officialName'] != z['name'] else None,
            'nameProvisional': z['needsCouncilChoice'], 'near': z['near'],
            'area': {'id': r['zone'], 'plateName': z['name'], 'officialName': z['officialName']},
            'municipality': m['name'], 'municipalityKey': m['key'], 'island': m['island'],
            'coverage': r['coverage'] or None, 'officialAddress': r['official_address'] or None,
            'postcode': pc, 'fullLine': full, 'written': E.format_plate(z, n),
            'spoken': E.spoken(z, n, 'pt'), 'spokenKea': E.spoken(z, n, 'kea'),
            'status': r['status'], 'issued': r['issued'], 'issuedAt': r['issued_at'],
            'entrance': {'lat': r['entrance_lat'], 'lng': r['entrance_lng'], 'kind': r['entrance_kind'],
                         'source': r['entrance_source']},
            'location': {'lat': r['entrance_lat'], 'lng': r['entrance_lng']},
            'plusCode': r['plus_code'],
            'plusCodeShort': self.short_spot(r['entrance_lat'], r['entrance_lng'], m),
            'lote': {'use': r['use'], 'kind': r['lote_kind'], 'structures': r['structures'],
                     'floorAreaM2': _num(r['floor_area_m2']), 'enclosed': bool(r['enclosed'])},
            'structures': sts,
            'registry': {c: self._registry_value(r, c) for c in S.CODE_COLS},
            'credit': E.CREDIT, 'creditUrl': E.CREDIT_URL,
        }
        return {k: v for k, v in card.items() if v is not None}

    @staticmethod
    def _registry_value(r, c):
        if c == 'check':
            return str(r['check_digit'])
        if c in ('entrance_lat', 'entrance_lng'):
            return f'{r[c]:.7f}'
        v = r[c]
        return str(v) if isinstance(v, int) else v

    def short_spot(self, lat, lng, m):
        return f"{E.olc_short(E.olc_encode(lat, lng, 10), m['seatLat'], m['seatLon'])} {m['seat']}"

    def get_card(self, machine):
        r = self.row(machine.strip().upper())
        if r is None:
            raise ApiError(404, 'unknown_code', f'There is no code {machine}.')
        return self.card(r)

    # -- find -----------------------------------------------------------------
    def find(self, q):
        text = ' '.join((q or '').split())
        if not text:
            raise ApiError(400, 'bad_request', 'Give something to find: /v1/find?q=Palmarejo 12 34')
        if E.MACHINE_RE.match(text):
            return {'query': text, 'kind': 'machine', 'matches': [self._decode(text, machine=True)]}
        up = text.upper()
        if SPOT_FULL.match(up) or SPOT_SHORT.match(up):
            return {'query': text, 'kind': 'spot', 'spot': self.spot_decode(text)}
        hits = self.official.get(fold(text))
        if hits:
            return {'query': text, 'kind': 'official', 'matches': [self.card(self.row(m)) for m in sorted(hits)]}
        return {'query': text, 'kind': 'home', 'matches': [self._decode(text, machine=False)]}

    def _decode(self, text, machine):
        try:
            p = E.parse(text)
        except ValueError as ex:
            msg = str(ex)
            if 'check digit' in msg:
                raise ApiError(422, 'check_digit', 'The check digit does not match: a digit is wrong or two are swapped. '
                               'Read the machine code again, or scan the QR code.') from None
            if 'not an issued block' in msg or 'outside every block' in msg:
                raise ApiError(404, 'unknown_code', msg[0].upper() + msg[1:] + '.') from None
            if msg.startswith('no zone called'):
                raise ApiError(404, 'unknown_name', f"No place in Cabo Verde has that name: {msg[len('no zone called '):]}.") from None
            if ' is in ' in msg:
                raise ApiError(422, 'wrong_municipality', msg + '.') from None
            msg = msg[0].upper() + msg[1:].rstrip('.') + '.'
            if 'place name and a number' not in msg:
                msg += ' A Cabo Verde code is a place name and a number, like Palmarejo 12 34, or a machine form like PR-0973-1234-0.'
            raise ApiError(400, 'bad_format', msg) from None
        z, n = p['zone'], p['number']
        r = self.con().execute('SELECT * FROM codes WHERE name_index = ? AND number = ?', (z['nameIndex'], n)).fetchone()
        if r is None:
            raise ApiError(404, 'not_issued', f"No home has {E.format_home(z, n)} yet (the number is in the range of "
                           f"{z['name']}, {E.MUNI[z['key']]['name']}).")
        c = self.card(r)
        if r['status'] == 'retired':
            c['note'] = 'This code is retired: there is no home there any more. Its number is never given again.'
        if p.get('contextMatches') is False:
            c['note'] = 'The place typed after the code does not match it; the code alone decides.'
        return c

    # -- points ---------------------------------------------------------------
    def code_at(self, lat, lng, max_m):
        """The live code of the lote a point is in, else the one whose
        entrance or footprint is nearest within max_m: (row, distance)."""
        con = self.con()
        d = 0.0005
        inside = []
        for s in S.structures_in_box(con, lat - d, lng - d, lat + d, lng + d):
            polys = geo.parse_wkt(s['footprint'])
            if polys and geo.contains(polys, lng, lat):
                inside.append(s['machine'])
        if inside:
            rows = con.execute(f"SELECT * FROM codes WHERE machine IN ({','.join('?' * len(inside))}) "
                               "AND status <> 'retired' ORDER BY machine LIMIT 1", inside).fetchall()
            if rows:
                return rows[0], 0.0
        fp = {}
        for s in S.structures_in_box(con, lat - 0.001, lng - 0.001, lat + 0.001, lng + 0.001):
            polys = geo.parse_wkt(s['footprint'])
            if polys:
                v = geo.distance_m(polys, lat, lng)
                if v < fp.get(s['machine'], math.inf):
                    fp[s['machine']] = v
        reach = max_m + 150
        dlat = reach / geo.M_PER_DEG
        dlng = reach / (geo.M_PER_DEG * math.cos(lat * math.pi / 180))
        best = None
        for r in S.codes_in_box(con, lat - dlat, lng - dlng, lat + dlat, lng + dlng):
            if r['status'] == 'retired':
                continue
            de = geo.geo_dist_m(r['entrance_lat'], r['entrance_lng'], lat, lng)
            if de > reach:
                continue
            dd = min(de, fp.get(r['machine'], 1e9))
            if dd <= max_m and (best is None or (dd, r['machine']) < (best[1], best[0]['machine'])):
                best = (r, dd)
        return best if best else (None, None)

    def check_point(self, lat, lng):
        try:
            lat, lng = float(lat), float(lng)
        except (TypeError, ValueError):
            raise ApiError(400, 'bad_request', 'lat and lng are required, in decimal degrees (lat=14.9177&lng=-23.5372).') from None
        if not (math.isfinite(lat) and math.isfinite(lng)) or not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ApiError(400, 'bad_request', 'lat must be between -90 and 90 and lng between -180 and 180.')
        return lat, lng

    @staticmethod
    def check_border(lat, lng):
        """The border decides (SPEC.md §3.2): no code more than 300 m outside the national border."""
        if not E.within_border(lat, lng):
            raise ApiError(422, 'outside', f'That spot is more than {E.BORDER_M:.0f} m outside the national border of Cabo Verde, '
                           'so it cannot have a Cabo Verde code.')

    def at(self, lat, lng):
        lat, lng = self.check_point(lat, lng)
        m = E.municipality_at(lat, lng)
        if m is None:
            return {'status': 'outside', 'note': 'At sea or outside Cabo Verde: no code is issued here.'}
        r, d = self.code_at(lat, lng, FOUND_M)
        if r is not None:
            return {'status': 'found', 'code': self.card(r), 'distanceM': go_round(d), 'area': self.area_of_muni(m)}
        return {'status': 'none', 'canIssue': True, 'building': False, 'area': self.area_of_muni(m),
                'spot': E.olc_encode(lat, lng, 11)}

    def near(self, lat, lng, radius=None, limit=None):
        lat, lng = self.check_point(lat, lng)
        try:
            radius = 100.0 if radius in (None, '') else float(radius)
            limit = 20 if limit in (None, '') else int(limit)
        except ValueError:
            raise ApiError(400, 'bad_request', 'radius is in metres and limit is a whole number.') from None
        if not (0 < radius <= NEAR_MAX_M):
            raise ApiError(400, 'bad_request', f'radius is between 1 and {NEAR_MAX_M:.0f} metres.')
        if not (1 <= limit <= NEAR_MAX_RESULTS):
            raise ApiError(400, 'bad_request', f'limit is between 1 and {NEAR_MAX_RESULTS}.')
        dlat = radius / geo.M_PER_DEG
        dlng = radius / (geo.M_PER_DEG * math.cos(lat * math.pi / 180))
        hits = []
        for r in S.codes_in_box(self.con(), lat - dlat, lng - dlng, lat + dlat, lng + dlng):
            if r['status'] == 'retired':
                continue
            d = geo.dist_m(r['entrance_lat'], r['entrance_lng'], lat, lng)
            if d <= radius:
                hits.append((d, r['machine'], r))
        hits.sort(key=lambda t: (t[0], t[1]))
        return {'lat': lat, 'lng': lng, 'radiusM': radius, 'count': len(hits),
                'codes': [{'machine': r['machine'], 'home': r['home'], 'distanceM': round(d, 1), 'status': r['status'],
                           'use': r['use'], 'entrance': {'lat': r['entrance_lat'], 'lng': r['entrance_lng'],
                                                         'kind': r['entrance_kind']}, 'plusCode': r['plus_code']}
                          for d, _, r in hits[:limit]]}

    def verify(self, code):
        text = ' '.join((code or '').split())
        if not text:
            raise ApiError(400, 'bad_request', 'Give a machine code: /v1/verify?code=PR-0973-1234-0')
        out = {'code': text, 'syntax': False, 'checkDigit': None, 'issued': False}
        m = E.MACHINE_RE.match(text)
        if not m:
            out['reason'] = 'Not a machine code: KEY-NNNN-NUMBER-C, like PR-0973-1234-0.'
            return out
        out['syntax'] = True
        key, ni, num, chk = m.group(1).upper(), int(m.group(2)), int(m.group(3)), int(m.group(4))
        if key not in E.MUNI:
            out['syntax'] = False
            out['reason'] = f'{key} is not a municipality key.'
            return out
        out['checkDigit'] = E.check_ok(ni, num, chk)
        if not out['checkDigit']:
            out['reason'] = 'The check digit does not match: a digit is wrong or two are swapped.'
            return out
        canon = f'{key}-{ni:04d}-{num}-{chk}'
        out['machine'] = canon
        r = self.row(canon)
        if r is None:
            out['reason'] = 'Well formed, but no code with this number has been issued.'
            return out
        out.update({'issued': True, 'status': r['status'], 'home': r['home'], 'issuedAt': r['issued_at']})
        return out

    def spot(self, lat, lng):
        lat, lng = self.check_point(lat, lng)
        d = E.describe_point(lat, lng)
        if not d['land']:
            raise ApiError(422, 'outside', 'At sea or outside Cabo Verde: no spot code is issued here.')
        lo_lat, lo_lng, hi_lat, hi_lng = E.olc_decode(d['plusCode'])
        return {'lat': lat, 'lng': lng, 'code': d['plusCode'], 'code10': E.olc_encode(lat, lng, 10),
                'short': d['plusCodeShort'], 'municipality': d['municipality'], 'municipalityKey': d['key'],
                'island': d['island'], 'postcode': self.postcode('', d['key']),
                'bounds': {'south': lo_lat, 'west': lo_lng, 'north': hi_lat, 'east': hi_lng}}

    def spot_decode(self, code):
        text = ' '.join((code or '').split()).upper()
        if not text:
            raise ApiError(400, 'bad_request', 'Give a spot code: /v1/spot/decode?code=796RWF8Q+2V8')
        if SPOT_FULL.match(text):
            full = text
        else:
            m = SPOT_SHORT.match(text)
            if not m:
                raise ApiError(400, 'bad_format', 'A spot code is a full Plus Code (796RWF8Q+2V8) or a short one with its '
                               'town (WF8Q+2V Praia).')
            place = fold(m.group(2))
            ref = next((x for x in E.MUNI.values() if place in (fold(x['seat']), fold(x['name']))), None)
            if ref is None:
                raise ApiError(404, 'unknown_place', f'{m.group(2).title()} is not a municipality or its seat.')
            full = E.olc_recover(m.group(1), ref['seatLat'], ref['seatLon'])
        try:
            lo_lat, lo_lng, hi_lat, hi_lng = E.olc_decode(full)
        except ValueError:
            raise ApiError(400, 'bad_format', f'{text} is not a valid Plus Code.') from None
        lat, lng = (lo_lat + hi_lat) / 2, (lo_lng + hi_lng) / 2
        m = E.municipality_at(lat, lng)
        if m is None:
            raise ApiError(422, 'outside', f'{full} is at sea or outside Cabo Verde.')
        return {'code': full, 'lat': round(lat, 7), 'lng': round(lng, 7),
                'bounds': {'south': lo_lat, 'west': lo_lng, 'north': hi_lat, 'east': hi_lng},
                'municipality': m['name'], 'municipalityKey': m['key'], 'island': m['island'],
                'at': self.at(lat, lng)}

    # -- listing --------------------------------------------------------------
    def zone_codes(self, key, after=None, limit=None):
        m = self.municipality(key)
        try:
            limit = 100 if limit in (None, '') else int(limit)
        except ValueError:
            raise ApiError(400, 'bad_request', 'limit is a whole number.') from None
        if not 1 <= limit <= 1000:
            raise ApiError(400, 'bad_request', 'limit is between 1 and 1000.')
        rows = self.con().execute('''SELECT machine, home, zone, number, status, entrance_lat, entrance_lng, plus_code, use
            FROM codes WHERE muni = ? AND machine > ? ORDER BY machine LIMIT ?''',
                                  (m['key'], (after or '').upper(), limit + 1)).fetchall()
        more = len(rows) > limit
        rows = rows[:limit]
        return {'zone': m['key'], 'count': len(rows), 'next': rows[-1]['machine'] if more else None,
                'codes': [{'machine': r['machine'], 'home': r['home'], 'area': r['zone'], 'number': r['number'],
                           'status': r['status'], 'lat': r['entrance_lat'], 'lng': r['entrance_lng'],
                           'plusCode': r['plus_code'], 'use': r['use']} for r in rows]}

    # -- issue ----------------------------------------------------------------
    def key_id(self, bearer):
        if not self.issue_keys:
            raise ApiError(403, 'read_only', 'This deployment is read-only: it serves the published codes and does not '
                           'issue. Codes are issued by the designated issuer for Cabo Verde.')
        if not bearer:
            raise ApiError(401, 'unauthorized', 'Issuing needs an issuer key: Authorization: Bearer <key>.')
        kid = hashlib.sha256(bearer.encode()).hexdigest()[:16]
        if kid not in self.issue_keys:
            raise ApiError(401, 'unauthorized', 'That issuer key is not valid here.')
        return kid

    def issue(self, body, bearer):
        kid = self.key_id(bearer)
        if not isinstance(body, dict):
            raise ApiError(400, 'bad_request', 'Send a JSON object: {"lat": 14.92, "lng": -23.53}.')
        lat, lng = self.check_point(body.get('lat'), body.get('lng'))
        outline, of = body.get('outline'), body.get('of')
        if of is not None and not isinstance(of, str):
            raise ApiError(400, 'bad_request', 'of is the machine code of the lote this is another door of.')
        ring = []
        if outline is not None:
            try:
                ring = [(float(p[0]), float(p[1])) for p in outline]
            except (TypeError, ValueError, IndexError):
                raise ApiError(400, 'bad_request', 'outline is a list of [lng, lat] points.') from None
        self.check_border(lat, lng)
        m = E.municipality_at(lat, lng)
        if m is None:
            raise ApiError(422, 'outside', 'That spot is at sea or outside Cabo Verde, so it cannot have a code.')
        con = self.con()
        since = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 86400))
        n = con.execute('SELECT count(*) FROM codes WHERE issued_key = ? AND issued_at >= ?', (kid, since)).fetchone()[0]
        if n >= self.issue_per_day:
            raise ApiError(429, 'limit', f'This key has issued {n} codes in the last 24 hours, its daily limit. Try again later.')
        with self.write_lock:
            return self._issue(con, kid, lat, lng, ring, (of or '').strip().upper(), m)

    def _issue(self, con, kid, lat, lng, ring, of, m):
        area = per = 0.0
        wkt = ''
        if not of:
            r, _ = self.code_at(lat, lng, SAME_BUILDING_M)
            if r is not None:
                raise ApiError(409, 'exists', f"This building already has its code: {r['home']}.", card=self.card(r))
            if len(ring) >= 3:
                if ring[0] == ring[-1]:
                    ring = ring[:-1]
                area, per = geo.ring_area_m2(ring), geo.ring_perimeter_m(ring)
                if len(ring) < 3 or area < MIN_AREA_M2 or area > MAX_AREA_M2:
                    raise ApiError(422, 'bad_outline', f'That outline is {area:.0f} m², but a building is between 12 m² and 2 ha.')
                wkt = geo.ring_wkt(ring)
                r = self.overlap(con, [[ring]])
                if r is not None:
                    raise ApiError(409, 'exists', f"This building already has its code: {r['home']}.", card=self.card(r))
        if of:
            o = self.row(of)
            if o is None:
                raise ApiError(404, 'unknown_code', f'There is no code {of} to add a door to.')
            if geo.dist_m(o['entrance_lat'], o['entrance_lng'], lat, lng) > DOOR_MAX_M:
                raise ApiError(422, 'too_far', f"That door is more than {DOOR_MAX_M:.0f} m from {o['home']}.")
            ref = o['zone']
        else:
            ref = self.nearest_zone(m, lat, lng)
        z = self.zone_by_ref.get(ref)
        if z is None:
            raise ApiError(422, 'outside', 'There is no area for this spot.')
        e = copy.deepcopy(E.names_by_index()[z['nameIndex']])
        nb = len(e['blocks'])
        issued, anchors = {}, {}
        for r in con.execute('SELECT machine, number, anchor_lat, anchor_lng FROM codes WHERE zone = ?', (ref,)):
            issued[r['number']] = r['machine']
            anchors[r['machine']] = (r['anchor_lat'], r['anchor_lng'])
        if not issued:
            n = E.number_zone([('new', lat, lng)], z['box'], z['block'])['new']
        else:
            n = E.insert_lote(issued, lat, lng, z['box'], anchors, e, ref)
        new_blocks = e['blocks'][nb:]
        machine, home = E.format_machine(z, n), E.format_home(z, n)
        sts = []
        if area > 0:
            cls, conf, src, status = E.classify({}, [], area, None, m['island'], True, False)
            h, _hsrc = E.estimate_height({}, None)
            floors = E.estimate_floors({}, h)
            sts.append({'idx': 1, 'id': 'people:' + machine, 'use': cls, 'confidence': conf, 'source': src, 'status': status,
                        'fp': r1(area), 'per': r1(per), 'floors': floors, 'fa': r1(area * floors), 'wkt': wkt})
        floor_area = r1(area * sts[0]['floors']) if sts else 0.0
        use = sts[0]['use'] if sts else ''
        kind = 'porta' if of else ('um_edificio' if len(sts) == 1 else 'lote_com_anexos')
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        try:
            con.execute('BEGIN IMMEDIATE')
            for b in new_blocks:
                seq = con.execute('SELECT coalesce(max(seq) + 1, 0) FROM blocks WHERE name_index = ?', (e['index'],)).fetchone()[0]
                con.execute('INSERT INTO blocks (name_index, seq, zone, lo, hi, local) VALUES (?,?,?,?,?,1)',
                            (e['index'], seq, b['zone'], b['lo'], b['hi']))
            cur = con.execute('''INSERT INTO codes (machine, home, home_key, official_name, zone, muni, name_index, number,
                check_digit, status, issued, issued_at, entrance_lat, entrance_lng, entrance_kind, plus_code, use, lote_kind,
                structures, floor_area_m2, postcode, coverage, official_address, anchor_lat, anchor_lng, entrance_source,
                enclosed, issued_key, status_at) VALUES (?,?,?,?,?,?,?,?,?,'provisional','on-demand',?,?,?,?,?,?,?,?,?,'','','',?,?,'map',0,?,?)''',
                              (machine, home, S.home_key(home), z['officialName'], ref, z['key'], z['nameIndex'], n,
                               E.check_digit(z['nameIndex'], n), now, lat, lng, 'door' if of else 'centre',
                               E.olc_encode(lat, lng, 11), use, kind, len(sts), f'{floor_area:.1f}', lat, lng, kid, now))
            S.index_code(con, cur.lastrowid, lat, lng)
            for s in sts:
                cur = con.execute('''INSERT INTO structures (machine, idx, structure_id, use, confidence, class_source, status,
                    footprint_m2, perimeter_m, height_m, height_source, floors, floor_area_m2, name, data, footprint)
                    VALUES (?,?,?,?,?,?,?,?,?,'','',?,?,'','people',?)''',
                                  (machine, s['idx'], s['id'], s['use'], _fmt(s['confidence'], 100), s['source'], s['status'],
                                   _fmt(s['fp'], 10), _fmt(s['per'], 10), str(s['floors']), _fmt(s['fa'], 10), s['wkt']))
                S.index_structure(con, cur.lastrowid, geo.parse_wkt(s['wkt']))
            con.execute("UPDATE meta SET value = CAST(value AS INTEGER) + 1 WHERE key = 'local_changes'")
            con.execute('COMMIT')
        except Exception as ex:
            con.execute('ROLLBACK')
            if 'UNIQUE' in str(ex):
                raise ApiError(409, 'busy', 'That number was taken at the same moment. Try again.') from None
            raise
        if new_blocks:
            self.load_register()
        else:
            self.counts = None
        return self.card(self.row(machine))

    def overlap(self, con, polys):
        """A live code with a structure that covers more than half of the
        smaller of it and the outline (the issuer's test for one building)."""
        x0, y0, x1, y1 = geo.bbox(polys)
        a = geo.area(polys)
        hits = []
        for s in S.structures_in_box(con, y0, x0, y1, x1):
            fp = geo.parse_wkt(s['footprint'])
            if fp and geo.intersection_area(fp, polys) > 0.5 * min(geo.area(fp), a):
                hits.append(s['machine'])
        if not hits:
            return None
        return con.execute(f"SELECT * FROM codes WHERE machine IN ({','.join('?' * len(hits))}) AND status <> 'retired' "
                           "ORDER BY machine LIMIT 1", hits).fetchone()

    def nearest_zone(self, m, lat, lng):
        r, _ = self.code_at(lat, lng, ZONE_SEARCH_M)
        if r is not None and r['muni'] == m['key']:
            return r['zone']
        best, bd = '', math.inf
        for z in self.zone_list:
            if z['key'] != m['key']:
                continue
            d = geo.dist_m(z['anchor'][0], z['anchor'][1], lat, lng)
            if d < bd:
                best, bd = E.zref(z), d
        return best

    # -- changes --------------------------------------------------------------
    def change(self, machine, body, bearer):
        self.key_id(bearer)
        if not isinstance(body, dict) or not ({'status', 'entrance'} & set(body)):
            raise ApiError(400, 'bad_request', 'Send {"status": "confirmed"} or {"entrance": {"lat": .., "lng": .., "kind": "gate"}}.')
        con = self.con()
        with self.write_lock:
            r = self.row(machine.strip().upper())
            if r is None:
                raise ApiError(404, 'unknown_code', f'There is no code {machine}.')
            if r['status'] == 'retired':
                raise ApiError(409, 'retired', f"{r['home']} is retired. A retired code stays retired and its number is never given again.")
            sets, args = [], []
            now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            if 'status' in body:
                st = body['status']
                if st not in STATUSES:
                    raise ApiError(400, 'bad_request', 'status is provisional, confirmed or retired.')
                sets += ['status = ?', 'status_at = ?']
                args += [st, now]
            new_pt = None
            if 'entrance' in body:
                en = body['entrance']
                if not isinstance(en, dict):
                    raise ApiError(400, 'bad_request', 'entrance is {"lat": .., "lng": .., "kind": "gate" or "door"}.')
                lat, lng = self.check_point(en.get('lat'), en.get('lng'))
                self.check_border(lat, lng)
                kind = en.get('kind', 'gate')
                if kind not in ('gate', 'door', 'centre'):
                    raise ApiError(400, 'bad_request', 'entrance kind is gate, door or centre.')
                d = geo.dist_m(r['entrance_lat'], r['entrance_lng'], lat, lng)
                if d > MOVE_MAX_M:
                    raise ApiError(422, 'too_far', f'The new entrance is {d:.0f} m away; an entrance moves at most {MOVE_MAX_M:.0f} m.')
                sets += ['entrance_lat = ?', 'entrance_lng = ?', 'entrance_kind = ?', 'entrance_source = ?', 'plus_code = ?']
                args += [lat, lng, kind, 'people', E.olc_encode(lat, lng, 11)]
                new_pt = (lat, lng)
            con.execute('BEGIN IMMEDIATE')
            try:
                con.execute(f"UPDATE codes SET {', '.join(sets)} WHERE id = ?", args + [r['id']])
                if new_pt:
                    S.index_code(con, r['id'], new_pt[0], new_pt[1], replace=True)
                con.execute("UPDATE meta SET value = CAST(value AS INTEGER) + 1 WHERE key = 'local_changes'")
                con.execute('COMMIT')
            except Exception:
                con.execute('ROLLBACK')
                raise
            self.counts = None
            return self.card(self.row(r['machine']))

    # -- info -----------------------------------------------------------------
    def health(self):
        n = self.con().execute('SELECT count(*) FROM codes').fetchone()[0]
        return {'status': 'ok', 'country': E.COUNTRY, 'codes': n, 'exported': self.meta('exported')}

    def info(self):
        con = self.con()
        by = {r[0]: r[1] for r in con.execute('SELECT status, count(*) FROM codes GROUP BY status')}
        return {'country': E.COUNTRY, 'name': E.COUNTRY_NAME,
                'zones': [self.muni_summary(E.MUNI[m[1]]) for m in E.MUNICIPALITIES],
                'counts': {'codes': sum(by.values()), 'byStatus': by,
                           'structures': con.execute('SELECT count(*) FROM structures').fetchone()[0],
                           'areas': len(self.zone_list), 'names': con.execute('SELECT count(*) FROM names').fetchone()[0]},
                'registry': {'exported': self.meta('exported'), 'importedAt': self.meta('imported_at'),
                             'localChanges': int(self.meta('local_changes') or 0)},
                'licences': E.LICENCES, 'credit': E.CREDIT, 'dataCredit': E.DATA_CREDIT, 'creditUrl': E.CREDIT_URL,
                'engine': self.meta('engine'), 'spec': E.SPEC, 'issuing': bool(self.issue_keys),
                'example': {'home': 'Palmarejo 12 34', 'machine': 'PR-0973-1234-0'}}


def _fmt(x, scale):
    """A value as the registry stores it: rounded like the code card."""
    f = struct.unpack('f', struct.pack('f', float(x)))[0]
    v = int(f * scale + 0.5) / scale
    r = repr(v)
    return r.removesuffix('.0')
