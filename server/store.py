"""The SQLite store: import of the published registry, queries, export.

The database holds exactly what registry/ publishes, plus what this
deployment has done since (codes it issued, blocks it took, status and
entrance changes), so `export` writes a registry in the published format.
"""
import csv
import gzip
import hashlib
import io
import json
import math
import os
import sqlite3
import time

from . import engine as E
from . import geo

ZONE_COLS = ['zone', 'municipality', 'index', 'plate_name', 'official_name', 'plate_rule', 'needs_council_choice',
             'aliases', 'near', 'name_key', 'name_index', 'box', 'anchor']
NAME_COLS = ['name_key', 'name_index', 'plate_name', 'official_names', 'digits', 'blocks', 'reserve', 'aliases',
             'needs_council_choice']
CODE_COLS = ['machine', 'home', 'official_name', 'zone', 'number', 'check', 'status', 'issued', 'issued_at',
             'entrance_lat', 'entrance_lng', 'entrance_kind', 'plus_code', 'use', 'lote_kind', 'structures',
             'floor_area_m2', 'postcode', 'coverage', 'official_address']
LOTE_COLS = ['machine', 'anchor_lat', 'anchor_lng', 'entrance_source', 'enclosed']
STRUCTURE_COLS = ['machine', 'index', 'structure_id', 'use', 'confidence', 'class_source', 'status', 'footprint_m2',
                  'perimeter_m', 'height_m', 'height_source', 'floors', 'floor_area_m2', 'name', 'data', 'footprint']

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE zones (
  ref TEXT PRIMARY KEY, municipality TEXT NOT NULL, idx INTEGER NOT NULL, plate_name TEXT NOT NULL,
  official_name TEXT NOT NULL, plate_rule TEXT NOT NULL, needs_council_choice TEXT NOT NULL, aliases TEXT NOT NULL,
  near TEXT NOT NULL, name_key TEXT NOT NULL, name_index INTEGER NOT NULL, box TEXT NOT NULL, anchor TEXT NOT NULL,
  seq INTEGER NOT NULL);
CREATE INDEX zones_name ON zones (name_index);
CREATE INDEX zones_plate ON zones (plate_name COLLATE NOCASE);
CREATE TABLE names (
  name_index INTEGER PRIMARY KEY, name_key TEXT NOT NULL UNIQUE, plate_name TEXT NOT NULL, official_names TEXT NOT NULL,
  digits INTEGER NOT NULL, reserve TEXT NOT NULL, aliases TEXT NOT NULL, needs_council_choice TEXT NOT NULL);
CREATE TABLE blocks (
  name_index INTEGER NOT NULL, seq INTEGER NOT NULL, zone TEXT NOT NULL, lo INTEGER NOT NULL, hi INTEGER NOT NULL,
  local INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (name_index, lo));
CREATE INDEX blocks_zone ON blocks (zone);
CREATE TABLE codes (
  id INTEGER PRIMARY KEY, machine TEXT NOT NULL UNIQUE, home TEXT NOT NULL, home_key TEXT NOT NULL,
  official_name TEXT NOT NULL, zone TEXT NOT NULL, muni TEXT NOT NULL, name_index INTEGER NOT NULL,
  number INTEGER NOT NULL, check_digit INTEGER NOT NULL, status TEXT NOT NULL, issued TEXT NOT NULL,
  issued_at TEXT NOT NULL, entrance_lat REAL NOT NULL, entrance_lng REAL NOT NULL, entrance_kind TEXT NOT NULL,
  plus_code TEXT NOT NULL, use TEXT NOT NULL, lote_kind TEXT NOT NULL, structures INTEGER NOT NULL,
  floor_area_m2 TEXT NOT NULL, postcode TEXT NOT NULL, coverage TEXT NOT NULL, official_address TEXT NOT NULL,
  anchor_lat REAL NOT NULL, anchor_lng REAL NOT NULL, entrance_source TEXT NOT NULL, enclosed INTEGER NOT NULL,
  issued_key TEXT, status_at TEXT,
  UNIQUE (name_index, number));
CREATE INDEX codes_home ON codes (home_key);
CREATE INDEX codes_official ON codes (official_address) WHERE official_address <> '';
CREATE INDEX codes_zone ON codes (zone, number);
CREATE INDEX codes_muni ON codes (muni, name_index, number);
CREATE INDEX codes_number ON codes (number);
CREATE INDEX codes_issued_key ON codes (issued_key, issued_at) WHERE issued_key IS NOT NULL;
CREATE TABLE structures (
  id INTEGER PRIMARY KEY, machine TEXT NOT NULL, idx INTEGER NOT NULL, structure_id TEXT NOT NULL, use TEXT NOT NULL,
  confidence TEXT NOT NULL, class_source TEXT NOT NULL, status TEXT NOT NULL, footprint_m2 TEXT NOT NULL,
  perimeter_m TEXT NOT NULL, height_m TEXT NOT NULL, height_source TEXT NOT NULL, floors TEXT NOT NULL,
  floor_area_m2 TEXT NOT NULL, name TEXT NOT NULL, data TEXT NOT NULL, footprint TEXT NOT NULL,
  UNIQUE (machine, idx));
"""

# Spatial index: an R*Tree when SQLite has it, else an integer grid of
# 0.001 degree cells (about 110 m).
RTREE = """
CREATE VIRTUAL TABLE codes_rtree USING rtree(id, min_lng, max_lng, min_lat, max_lat);
CREATE VIRTUAL TABLE structures_rtree USING rtree(id, min_lng, max_lng, min_lat, max_lat);
"""
GRID = """
CREATE TABLE codes_grid (cell INTEGER NOT NULL, id INTEGER NOT NULL);
CREATE INDEX codes_grid_cell ON codes_grid (cell);
CREATE TABLE structures_grid (cell INTEGER NOT NULL, id INTEGER NOT NULL);
CREATE INDEX structures_grid_cell ON structures_grid (cell);
"""
CELL = 0.001


class RegistryError(Exception):
    pass


def has_rtree():
    c = sqlite3.connect(':memory:')
    try:
        c.execute('CREATE VIRTUAL TABLE t USING rtree(id, a, b, c, d)')
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        c.close()


def connect(path, readonly=False):
    if readonly:
        con = sqlite3.connect(f'file:{path}?mode=ro', uri=True, check_same_thread=False)
    else:
        con = sqlite3.connect(path, check_same_thread=False, timeout=30)
        if con.execute('PRAGMA journal_mode').fetchone()[0] != 'wal':
            con.execute('PRAGMA journal_mode=WAL')  # once per file; it stays
        con.execute('PRAGMA synchronous=NORMAL')
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def home_key(home):
    """The remembered form folded for lookup: no accents, case or spaces."""
    return E.name_key(home).replace(' ', '')


# --------------------------------------------------------------------------
# Import
# --------------------------------------------------------------------------

def _rows(data, cols, name):
    text = data.decode('utf-8')
    r = csv.reader(io.StringIO(text, newline=''))
    header = next(r, None)
    if header != cols:
        raise RegistryError(f'{name}: columns are {header}, expected {cols}')
    for row in r:
        if len(row) != len(cols):
            raise RegistryError(f'{name}: a row has {len(row)} fields, expected {len(cols)}')
        yield row


def _read(registry, name, man):
    """The uncompressed bytes of a registry file, checked against the
    manifest (the hash is over the uncompressed CSV)."""
    path = os.path.join(registry, name)
    gz = path + '.gz'
    if os.path.exists(path):
        with open(path, 'rb') as f:
            data = f.read()
    elif os.path.exists(gz):
        with gzip.open(gz, 'rb') as f:
            data = f.read()
    else:
        raise RegistryError(f'{name}: missing from {registry}')
    want = man['sha256'].get(name)
    got = hashlib.sha256(data).hexdigest()
    if want != got:
        raise RegistryError(f'{name}: SHA-256 {got} does not match the manifest ({want})')
    return data


def _cell(lat, lng):
    return math.floor(lat / CELL) * 1000000 + math.floor(lng / CELL)


def _cells(min_lat, min_lng, max_lat, max_lng):
    for y in range(math.floor(min_lat / CELL), math.floor(max_lat / CELL) + 1):
        for x in range(math.floor(min_lng / CELL), math.floor(max_lng / CELL) + 1):
            yield y * 1000000 + x


def _fill(con, registry, man, log):
    """Load every registry file into an empty database, checking each one."""
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    rtree = has_rtree()
    con.executescript(SCHEMA + (RTREE if rtree else GRID))
    zones = list(_rows(_read(registry, 'zones.csv', man), ZONE_COLS, 'zones.csv'))
    con.executemany('INSERT INTO zones VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    [r[:2] + [int(r[2])] + r[3:10] + [int(r[10])] + r[11:] + [i] for i, r in enumerate(zones)])
    zone_refs = {r[0] for r in zones}
    names = list(_rows(_read(registry, 'names.csv', man), NAME_COLS, 'names.csv'))
    blocks = []
    for r in names:
        ni = int(r[1])
        con.execute('INSERT INTO names VALUES (?,?,?,?,?,?,?,?)', (ni, r[0], r[2], r[3], int(r[4]), r[6], r[7], r[8]))
        for seq, b in enumerate(r[5].split()):
            zone, rng = b.rsplit(':', 1)
            lo, hi = rng.split('-')
            if zone not in zone_refs:
                raise RegistryError(f'names.csv: block {b} names an unknown zone')
            blocks.append((ni, seq, zone, int(lo), int(hi)))
    con.executemany('INSERT INTO blocks (name_index, seq, zone, lo, hi) VALUES (?,?,?,?,?)', blocks)
    log(f'{len(zones)} zones, {len(names)} names, {len(blocks)} blocks')

    # anchors, entrance sources and enclosure, by machine code
    extra = {}
    if 'lotes.csv' in man['sha256']:
        for r in _rows(_read(registry, 'lotes.csv', man), LOTE_COLS, 'lotes.csv'):
            extra[r[0]] = (float(r[1]), float(r[2]), r[3], 1 if r[4] == 'true' else 0)
        if len(extra) != man.get('lotes', len(extra)):
            raise RegistryError(f"lotes.csv has {len(extra)} rows, the manifest says {man.get('lotes')}")

    total = 0
    zone_muni = {r[0]: r[1] for r in zones}
    zone_ni = {r[0]: int(r[10]) for r in zones}
    for key, want in man['byMunicipality'].items():
        n = 0
        batch = []
        for r in _rows(_read(registry, f'{key}.csv', man), CODE_COLS, f'{key}.csv'):
            machine, zone = r[0], r[3]
            if zone_muni.get(zone) != key or not machine.startswith(key + '-'):
                raise RegistryError(f'{key}.csv: {machine} is in zone {zone}, not in {key}')
            number, check = int(r[4]), int(r[5])
            ni = zone_ni[zone]
            if not E.check_ok(ni, number, check):
                raise RegistryError(f'{key}.csv: {machine} has a wrong check digit')
            lat, lng = float(r[9]), float(r[10])
            a = extra.get(machine, (lat, lng, 'map', 0))
            batch.append((machine, r[1], home_key(r[1]), r[2], zone, key, ni, number, check, r[6], r[7], r[8], lat, lng,
                          r[11], r[12], r[13], r[14], int(r[15]), r[16], r[17], r[18], r[19], a[0], a[1], a[2], a[3]))
            n += 1
        con.executemany('''INSERT INTO codes (machine, home, home_key, official_name, zone, muni, name_index, number,
            check_digit, status, issued, issued_at, entrance_lat, entrance_lng, entrance_kind, plus_code, use, lote_kind,
            structures, floor_area_m2, postcode, coverage, official_address, anchor_lat, anchor_lng, entrance_source,
            enclosed) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', batch)
        if n != want:
            raise RegistryError(f'{key}.csv has {n} codes, the manifest says {want}')
        total += n
    if total != man['codes']:
        raise RegistryError(f"the registry has {total} codes, the manifest says {man['codes']}")
    log(f'{total} codes')

    # structures and their footprints
    nst = 0
    for key, want in (man.get('structuresByMunicipality') or {}).items():
        n = 0
        batch = []
        for r in _rows(_read(registry, f'structures/{key}.csv', man), STRUCTURE_COLS, f'structures/{key}.csv'):
            batch.append((r[0], int(r[1])) + tuple(r[2:]))
            n += 1
        con.executemany('''INSERT INTO structures (machine, idx, structure_id, use, confidence, class_source, status,
            footprint_m2, perimeter_m, height_m, height_source, floors, floor_area_m2, name, data, footprint)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', batch)
        if n != want:
            raise RegistryError(f'structures/{key}.csv has {n} structures, the manifest says {want}')
        nst += n
    if nst != man.get('structures', 0):
        raise RegistryError(f"the registry has {nst} structures, the manifest says {man.get('structures')}")
    orphan = con.execute('SELECT count(*) FROM structures s LEFT JOIN codes c ON c.machine = s.machine WHERE c.id IS NULL').fetchone()[0]
    if orphan:
        raise RegistryError(f'{orphan} structures belong to no code')
    log(f'{nst} structures')

    _index_all(con, rtree)
    meta = {'country': man['country'], 'exported': man['exported'], 'engine': man['engine'], 'credit': man['credit'],
            'licence': man['licence'], 'imported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'local_changes': '0', 'spatial': 'rtree' if rtree else 'grid'}
    con.executemany('INSERT INTO meta VALUES (?,?)', list(meta.items()))
    con.commit()
    return {'codes': total, 'structures': nst, 'zones': len(zones), 'names': len(names)}, meta


def import_registry(registry, db_path, discard_local=False, log=print):
    """Load a published registry into a new database file and swap it in.
    Every file is checked against MANIFEST.json and every count against its
    total; nothing is swapped in unless all of it is right."""
    man_path = os.path.join(registry, 'MANIFEST.json')
    if not os.path.exists(man_path):
        raise RegistryError(f'{man_path} not found')
    with open(man_path, encoding='utf-8') as f:
        man = json.load(f)
    if man.get('country') != E.COUNTRY:
        raise RegistryError(f"the registry is for {man.get('country')!r}, this server serves {E.COUNTRY}")
    if os.path.exists(db_path) and not discard_local:
        try:
            old = connect(db_path, readonly=True)
            n = old.execute("SELECT value FROM meta WHERE key = 'local_changes'").fetchone()
            old.close()
        except sqlite3.DatabaseError:
            n = None
        if n and int(n[0]) > 0:
            raise RegistryError(f'{db_path} holds {n[0]} change(s) made by this deployment (codes issued, status or '
                                'entrance changes). Export them first; re-run with --discard-local-changes to replace them.')
    os.makedirs(os.path.dirname(os.path.abspath(db_path)) or '.', exist_ok=True)
    tmp = db_path + '.import'
    for p in (tmp, tmp + '-wal', tmp + '-shm'):
        if os.path.exists(p):
            os.remove(p)
    con = sqlite3.connect(tmp)
    t0 = time.time()
    try:
        result, meta_ = _fill(con, registry, man, log)
        con.execute('ANALYZE')
        con.close()
    except BaseException:
        con.close()
        os.remove(tmp)
        raise
    for p in (db_path + '-wal', db_path + '-shm'):
        if os.path.exists(p):
            os.remove(p)
    os.replace(tmp, db_path)
    connect(db_path).close()  # switch the new file to WAL
    log(f'imported into {db_path} in {time.time() - t0:.0f} s ({meta_["spatial"]} spatial index)')
    return result


def _index_all(con, rtree):
    rows = con.execute('SELECT id, entrance_lat, entrance_lng FROM codes').fetchall()
    if rtree:
        con.executemany('INSERT INTO codes_rtree VALUES (?,?,?,?,?)', [(i, lng, lng, lat, lat) for i, lat, lng in rows])
    else:
        con.executemany('INSERT INTO codes_grid VALUES (?,?)', [(_cell(lat, lng), i) for i, lat, lng in rows])
    batch = []
    for sid, wkt in con.execute('SELECT id, footprint FROM structures WHERE footprint <> ""'):
        x0, y0, x1, y1 = geo.bbox(geo.parse_wkt(wkt))
        if rtree:
            batch.append((sid, x0, x1, y0, y1))
        else:
            batch.extend((c, sid) for c in _cells(y0, x0, y1, x1))
    if rtree:
        con.executemany('INSERT INTO structures_rtree VALUES (?,?,?,?,?)', batch)
    else:
        con.executemany('INSERT INTO structures_grid VALUES (?,?)', batch)


def index_code(con, code_id, lat, lng, replace=False):
    rtree = meta(con, 'spatial') == 'rtree'
    if rtree:
        con.execute('INSERT OR REPLACE INTO codes_rtree VALUES (?,?,?,?,?)', (code_id, lng, lng, lat, lat))
    else:
        if replace:
            con.execute('DELETE FROM codes_grid WHERE id = ?', (code_id,))
        con.execute('INSERT INTO codes_grid VALUES (?,?)', (_cell(lat, lng), code_id))


def index_structure(con, sid, polys):
    x0, y0, x1, y1 = geo.bbox(polys)
    if meta(con, 'spatial') == 'rtree':
        con.execute('INSERT INTO structures_rtree VALUES (?,?,?,?,?)', (sid, x0, x1, y0, y1))
    else:
        con.executemany('INSERT INTO structures_grid VALUES (?,?)', [(c, sid) for c in _cells(y0, x0, y1, x1)])


def meta(con, key):
    r = con.execute('SELECT value FROM meta WHERE key = ?', (key,)).fetchone()
    return r[0] if r else None


def codes_in_box(con, min_lat, min_lng, max_lat, max_lng):
    """Codes whose entrance lies in a box."""
    if meta(con, 'spatial') == 'rtree':
        return con.execute('''SELECT c.* FROM codes_rtree r JOIN codes c ON c.id = r.id
            WHERE r.min_lng <= ? AND r.max_lng >= ? AND r.min_lat <= ? AND r.max_lat >= ?''',
                           (max_lng, min_lng, max_lat, min_lat)).fetchall()
    cells = list(_cells(min_lat, min_lng, max_lat, max_lng))
    out = []
    for i in range(0, len(cells), 500):
        part = cells[i:i + 500]
        out += con.execute(f'''SELECT c.* FROM codes_grid g JOIN codes c ON c.id = g.id
            WHERE g.cell IN ({','.join('?' * len(part))}) AND c.entrance_lat BETWEEN ? AND ? AND c.entrance_lng BETWEEN ? AND ?''',
                           part + [min_lat, max_lat, min_lng, max_lng]).fetchall()
    return out


def structures_in_box(con, min_lat, min_lng, max_lat, max_lng):
    """Structures whose footprint's bounding box meets a box."""
    if meta(con, 'spatial') == 'rtree':
        return con.execute('''SELECT s.* FROM structures_rtree r JOIN structures s ON s.id = r.id
            WHERE r.min_lng <= ? AND r.max_lng >= ? AND r.min_lat <= ? AND r.max_lat >= ?''',
                           (max_lng, min_lng, max_lat, min_lat)).fetchall()
    cells = list(_cells(min_lat, min_lng, max_lat, max_lng))
    seen, out = set(), []
    for i in range(0, len(cells), 500):
        part = cells[i:i + 500]
        for r in con.execute(f'''SELECT s.* FROM structures_grid g JOIN structures s ON s.id = g.id
                WHERE g.cell IN ({','.join('?' * len(part))})''', part):
            if r['id'] not in seen:
                seen.add(r['id'])
                out.append(r)
    return out


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------

def _csv_bytes(header, rows):
    """CSV as the published registry writes it: comma, LF line ends, a field
    quoted only when it holds a comma, a quote, a line break or starts with
    white space."""
    def cell(v):
        if v and (any(c in v for c in ',"\r\n') or v[0].isspace()):
            return '"' + v.replace('"', '""') + '"'
        return v
    return ''.join(','.join(cell(v) for v in r) + '\n' for r in [header] + rows).encode('utf-8')


def _num(x):
    """Shortest decimal that reads back as the same double ('14.847437')."""
    r = repr(float(x))
    return r.removesuffix('.0')


def _gz(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=9) as g:
        g.write(data)


def export_registry(con, out):
    """Write the registry in the published format (same files, columns,
    order and number formats) with a fresh MANIFEST.json."""
    os.makedirs(out, exist_ok=True)
    sha = {}

    def plain(name, header, rows):
        data = _csv_bytes(header, rows)
        with open(os.path.join(out, name), 'wb') as f:
            f.write(data)
        sha[name] = hashlib.sha256(data).hexdigest()

    zr = [[r['ref'], r['municipality'], str(r['idx']), r['plate_name'], r['official_name'], r['plate_rule'],
           r['needs_council_choice'], r['aliases'], r['near'], r['name_key'], str(r['name_index']), r['box'], r['anchor']]
          for r in con.execute('SELECT * FROM zones ORDER BY seq')]
    plain('zones.csv', ZONE_COLS, zr)
    blocks = {}
    for b in con.execute('SELECT name_index, zone, lo, hi FROM blocks ORDER BY name_index, seq'):
        blocks.setdefault(b[0], []).append(f'{b[1]}:{b[2]}-{b[3]}')
    nr = [[r['name_key'], str(r['name_index']), r['plate_name'], r['official_names'], str(r['digits']),
           ' '.join(blocks.get(r['name_index'], [])), r['reserve'], r['aliases'], r['needs_council_choice']]
          for r in con.execute('SELECT * FROM names ORDER BY name_index')]
    plain('names.csv', NAME_COLS, nr)

    counts, total = {}, 0
    for m in E.MUNICIPALITIES:
        key = m[1]
        rows = [[r['machine'], r['home'], r['official_name'], r['zone'], str(r['number']), str(r['check_digit']),
                 r['status'], r['issued'], r['issued_at'], f"{r['entrance_lat']:.7f}", f"{r['entrance_lng']:.7f}",
                 r['entrance_kind'], r['plus_code'], r['use'], r['lote_kind'], str(r['structures']), r['floor_area_m2'],
                 r['postcode'], r['coverage'], r['official_address']]
                for r in con.execute('SELECT * FROM codes WHERE muni = ? ORDER BY name_index, number', (key,))]
        if not rows:
            continue
        plain(f'{key}.csv', CODE_COLS, rows)
        counts[key] = len(rows)
        total += len(rows)

    lotes = [[r['machine'], _num(r['anchor_lat']), _num(r['anchor_lng']), r['entrance_source'],
              'true' if r['enclosed'] else 'false'] for r in con.execute('SELECT * FROM codes ORDER BY machine')]
    data = _csv_bytes(LOTE_COLS, lotes)
    _gz(os.path.join(out, 'lotes.csv.gz'), data)
    sha['lotes.csv'] = hashlib.sha256(data).hexdigest()
    st_counts = {}
    for m in E.MUNICIPALITIES:
        key = m[1]
        rows = [[r['machine'], str(r['idx']), r['structure_id'], r['use'], r['confidence'], r['class_source'], r['status'],
                 r['footprint_m2'], r['perimeter_m'], r['height_m'], r['height_source'], r['floors'], r['floor_area_m2'],
                 r['name'], r['data'], r['footprint']]
                for r in con.execute('''SELECT * FROM structures WHERE machine >= ? AND machine < ?
                    ORDER BY machine, idx''', (key + '-', key + '.'))]
        if not rows:
            continue
        data = _csv_bytes(STRUCTURE_COLS, rows)
        _gz(os.path.join(out, 'structures', f'{key}.csv.gz'), data)
        sha[f'structures/{key}.csv'] = hashlib.sha256(data).hexdigest()
        st_counts[key] = len(rows)

    changed = int(meta(con, 'local_changes') or 0) > 0
    man = {'byMunicipality': counts, 'codes': total, 'country': meta(con, 'country'), 'credit': meta(con, 'credit'),
           'engine': meta(con, 'engine'),
           'exported': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) if changed else meta(con, 'exported'),
           'licence': meta(con, 'licence'), 'lotes': len(lotes), 'sha256': sha, 'structures': sum(st_counts.values()),
           'structuresByMunicipality': st_counts}
    with open(os.path.join(out, 'MANIFEST.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(man, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    return {'codes': total, 'structures': man['structures'], 'files': len(sha)}
