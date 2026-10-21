#!/usr/bin/env python3
"""N-Ways Addressing for Cabo Verde: reference engine (standard library only).

This is the readable reference for engine/SPEC.md, not the production engine.
It implements, for Cabo Verde only:

  * the home code people remember: a short PLATE NAME of the zone (bairro,
    povoação, zona; at most 12 characters and 2 words, so "Achada São
    Filipe" is said "São Filipe") + a 3- or 4-digit number, e.g.
    "Palmarejo 12 34"; the full official name is printed small on the card
    and the plate, and typed it decodes too;
    unique in the whole country ON ITS OWN: every zone with the same
    national name key shares one number range, cut into frozen blocks, so
    "Fazenda 24 33" is Praia and "Fazenda 34 48" is Tarrafal with nothing
    typed after them
  * the machine form that maps 1:1 to it: PR-0973-1234-0 (municipality key,
    national name index, number, Damm check digit over name index and
    number; the zone is bound by the frozen block table); the check digit
    is printed on plates and forms only, nobody has to remember it
  * zones: frozen namespaces built from the N-Ways locality layer
    (tools/build_zones.py -> engine/data/zones.json, frozen at first issue)
  * numbering: Hilbert order over lotes (plots/compounds) inside each zone,
    spread over the zone's block with headroom; insertion rule for new homes
    ("Add my home"); a full block takes a new block from its name's spare
    space, a full name range opens the next length
  * the spot layer: Open Location Code (Plus Codes), the grid Correios de
    Cabo Verde adopted for "Morada Certa" in 2016, clipped to land
  * point -> municipality -> island -> Correios postcode context, offline
  * Portuguese and Kriolu number words for the voice
  * the building-profile classifier shared with tools/building_stats.py

Run:  python3 engine/reference/cv_engine.py                 self-test + vectors
      python3 engine/reference/cv_engine.py 14.91992 -23.50709   a point
      python3 engine/reference/cv_engine.py "Fazenda 3448"       a code
      python3 engine/reference/test_cv.py                        the tests
"""
import json
import math
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plate_names  # noqa: E402  (same directory; the plate-name rule, SPEC.md §3.7)


def _json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)
DATA = os.path.join(os.path.dirname(HERE), 'data')

# --------------------------------------------------------------------------
# Municipalities (SPEC.md §3). The index is fixed forever (ISO 3166-2 order of
# the 22 municipalities); a new municipality gets the next index, never a
# reused one.
# postalPrefix: the first two digits observed on Correios codes for that
# municipality (UPU 2014 sheet + OpenStreetMap + Statoids; see SOURCES.md).
# Praia is the exception to "prefix = old concelho number": its codes are
# 7600-7602. Prefixes marked inferred are not confirmed by Correios.
# seat: reference point for short Plus Codes (the municipal seat).
# --------------------------------------------------------------------------
MUNICIPALITIES = [
    # index, key, ISO, name, island, island digit, postal prefix, prefix status, seat name, seat lat, seat lon
    (0, 'BR', 'CV-BR', 'Brava', 'Brava', 9, '91', 'observed 9110', 'Nova Sintra', 14.87107, -24.69565),
    (1, 'BV', 'CV-BV', 'Boa Vista', 'Boa Vista', 5, '51', 'observed 5110', 'Sal Rei', 16.17597, -22.91698),
    (2, 'CA', 'CV-CA', 'Santa Catarina', 'Santiago', 7, '72', 'inferred', 'Assomada', 15.10000, -23.68333),
    (3, 'CF', 'CV-CF', 'Santa Catarina do Fogo', 'Fogo', 8, '82', 'inferred', 'Cova Figueira', 14.88994, -24.29411),
    (4, 'CR', 'CV-CR', 'Santa Cruz', 'Santiago', 7, '73', 'inferred', 'Pedra Badejo', 15.13719, -23.53157),
    (5, 'MA', 'CV-MA', 'Maio', 'Maio', 6, '61', 'inferred', 'Vila do Maio', 15.13839, -23.21825),
    (6, 'MO', 'CV-MO', 'Mosteiros', 'Fogo', 8, '81', 'inferred', 'Mosteiros', 15.03473, -24.32774),
    (7, 'PA', 'CV-PA', 'Paul', 'Santo Antão', 1, '12', 'inferred', 'Vila das Pombas', 17.15026, -25.02007),
    (8, 'PN', 'CV-PN', 'Porto Novo', 'Santo Antão', 1, '13', 'inferred', 'Porto Novo', 17.01898, -25.06532),
    (9, 'PR', 'CV-PR', 'Praia', 'Santiago', 7, '76', 'official 7600 (UPU 2014)', 'Praia', 14.91628, -23.50951),
    (10, 'RB', 'CV-RB', 'Ribeira Brava', 'São Nicolau', 3, '31', 'inferred', 'Ribeira Brava', 16.61573, -24.29825),
    (11, 'RG', 'CV-RG', 'Ribeira Grande', 'Santo Antão', 1, '11', 'observed 1110-1139', 'Ponta do Sol', 17.20133, -25.09105),
    (12, 'RS', 'CV-RS', 'Ribeira Grande de Santiago', 'Santiago', 7, '74', 'inferred', 'Cidade Velha', 14.91488, -23.60477),
    (13, 'SD', 'CV-SD', 'São Domingos', 'Santiago', 7, '75', 'inferred', 'São Domingos', 15.02689, -23.56135),
    (14, 'SF', 'CV-SF', 'São Filipe', 'Fogo', 8, '82', 'observed 8220', 'São Filipe', 14.89530, -24.49694),
    (15, 'SL', 'CV-SL', 'Sal', 'Sal', 4, '41', 'observed 4110/4111', 'Espargos', 16.75780, -22.94315),
    (16, 'SM', 'CV-SM', 'São Miguel', 'Santiago', 7, '76', 'inferred', 'Calheta de São Miguel', 15.18420, -23.59150),
    (17, 'SO', 'CV-SO', 'São Lourenço dos Órgãos', 'Santiago', 7, '73', 'inferred', 'João Teves', 15.06706, -23.58918),
    (18, 'SS', 'CV-SS', 'São Salvador do Mundo', 'Santiago', 7, '72', 'inferred', 'Picos', 15.08427, -23.63224),
    (19, 'SV', 'CV-SV', 'São Vicente', 'São Vicente', 2, '21', 'observed 2110', 'Mindelo', 16.88731, -24.98641),
    (20, 'TA', 'CV-TA', 'Tarrafal', 'Santiago', 7, '71', 'observed 7110', 'Tarrafal', 15.27842, -23.75229),
    (21, 'TS', 'CV-TS', 'Tarrafal de São Nicolau', 'São Nicolau', 3, '31', 'inferred', 'Tarrafal de São Nicolau', 16.56648, -24.35680),
]
FIELDS = ('index', 'key', 'iso', 'name', 'island', 'islandDigit', 'postalPrefix', 'postalStatus', 'seat', 'seatLat', 'seatLon')
MUNI = {m[1]: dict(zip(FIELDS, m)) for m in MUNICIPALITIES}
MUNI_BY_ISO = {m[2]: MUNI[m[1]] for m in MUNICIPALITIES}

# Postcodes seen with a source (SOURCES.md). Shown beside a code as context,
# never derived from it.
KNOWN_POSTCODES = {
    '7600': ('Praia', 'UPU addressing sheet 04/2014; Correios HQ address'),
    '7601': ('Praia', 'OpenStreetMap addr:postcode'),
    '7602': ('Praia', 'N-Ways research via Nominatim, 2026-10-17'),
    '2110': ('Mindelo', 'OpenStreetMap addr:postcode'),
    '4110': ('Espargos', 'N-Ways research via Nominatim, 2026-10-17'),
    '4111': ('Santa Maria', 'OpenStreetMap addr:postcode'),
    '5110': ('Sal Rei', 'OpenStreetMap addr:postcode'),
    '8220': ('São Filipe', 'N-Ways research via Nominatim, 2026-10-17'),
    '9110': ('Nova Sintra', 'OpenStreetMap addr:postcode'),
    '7110': ('Tarrafal', 'third-party listing (unverified)'),
}
# The area postcode shown beside a code that has no verified postcode of its
# own: the municipality's main Correios code, where one is known with a source.
MUNICIPAL_POSTCODE = {'PR': '7600', 'SV': '2110', 'BV': '5110', 'SF': '8220', 'BR': '9110'}


def postcode_for(postcode, key):
    """(value, source) of the area postcode to show for a code, or None: its
    own postcode when it is a known one, else its municipality's."""
    if postcode and postcode in KNOWN_POSTCODES:
        return postcode, KNOWN_POSTCODES[postcode][1]
    v = MUNICIPAL_POSTCODE.get(key)
    return (v, KNOWN_POSTCODES[v][1]) if v else None


# --------------------------------------------------------------------------
# Check digit: the Damm algorithm (SPEC.md §4), one decimal digit that
# detects EVERY single-digit substitution and EVERY adjacent transposition.
# (ISO/IEC 7064 MOD 11,10, the other common choice, misses about 2 % of
# adjacent swaps: 12/21, 56/65, 09/90 ...)
# Data string = national name index (4 digits) + number. The area is bound
# through the register: inside a name every number has exactly one owning
# zone, frozen at issue, so name + number fix the zone; a machine form whose
# zone does not own the number is refused outright. Keeping the zone digits
# out of the string is what makes a one-digit slip that lands in another zone
# of the same name always detectable (with them in, 90.6 % were caught).
# --------------------------------------------------------------------------
DAMM = ('0317598642', '7092154863', '4206871359', '1750983426', '6123045978',
        '3674209581', '5869720134', '8945362017', '9438617205', '2581436790')


def _damm(digits):
    i = 0
    for d in digits:
        i = int(DAMM[i][d])
    return i


def data_digits(name_index, number):
    return [int(c) for c in f'{name_index:04d}{number}']


def check_digit(name_index, number):
    return _damm(data_digits(name_index, number))


def check_ok(name_index, number, check):
    return _damm(data_digits(name_index, number) + [check]) == 0


# --------------------------------------------------------------------------
# National name ranges (SPEC.md §5): "Name NNNN" is unique in the whole
# country on its own, with no municipality or island after it, because
# people give their code without context (on the phone, on a form, to a
# courier from another island). Every zone whose name folds to the same NAME KEY draws
# from ONE national number range for that name. The range is cut into blocks
# of whole UNITS; each zone owns one or more blocks; at least RESERVE_UNITS
# units stay free for zones of that name created later. Blocks are frozen at
# issue and never renumbered.
#
#   length  numbers       unit   units          the unit is read from
#   3       100-999       100    1..9   (9)     the first digit   (2 14)
#   4       1000-9999     100    10..99 (90)    the first pair    (12 34)
#   5       10000-99999   1000   10..99 (90)    the first pair    (12 345)
#
# Numbers never have a leading zero (people drop it) and never more than 5
# digits; a name whose zones cannot fit 5 digits is split once, by a
# qualifier people already say (QUALIFIERS).
# --------------------------------------------------------------------------
RANGES = {3: (100, 999), 4: (1000, 9999), 5: (10000, 99999)}
UNITS = {3: (1, 9, 100), 4: (10, 99, 100), 5: (10, 99, 1000)}  # first unit, last unit, unit size
HEADROOM = 3.0      # a zone's blocks hold at least 3 x its lotes at first issue
RESERVE_UNITS = 2   # units of a name's range kept free for future zones of that name
MAX_DIGITS = 5

# Names whose zones together would not fit 5 digits are split ONCE, before
# first issue, by an established qualifier people already say (the way
# "Achada Santo António" is said, not "Achada"). name key -> {zone ref:
# qualified name}. No name of the issued register needs one: the largest
# shared range is Bela Vista (3 zones, 49 units = 4 digits). The table stays
# in the model so the rule is mechanical when a name outgrows 5 digits.
QUALIFIERS = {}

_ARTICLES = {'de', 'da', 'do', 'das', 'dos', 'd', 'o', 'a', 'os', 'as'}
_ABBREV = {'sto': 'santo', 'sta': 'santa', 's': 'sao', 'sr': 'senhor', 'sra': 'senhora', 'n': 'nossa', 'na': 'nossa',
           'nsa': 'nossa'}


def _plain(s):
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    s = s.lower().replace('’', "'").replace('`', "'").replace('ª', 'a').replace('º', 'o')
    return s


def name_key(s):
    """The national normalisation of a place name (Portuguese and Kriolu,
    SPEC.md §3.4). Two zones with the same key share one number range.
    - case and accents fold: Platô = plato, Lém = lem;
    - apostrophes, hyphens, dots and slashes are spaces: Lém-Ferreira = Lem Ferreira;
    - articles and the prepositions de/da/do/das/dos/d' drop: Chã de Baixo =
      Chã Baixo, Pé do Monte = Pé de Monte, As Hortas = Hortas, Ponta d'Água = Ponta Água;
    - abbreviations expand: Sto/Sta/S. = Santo/Santa/São;
    - ALUPEC (Kriolu) spellings fold to the Portuguese ones: tx/tch = ch,
      dj = j, k = c before a/o/u and qu before e/i (Txada = Chada, Kaza = Caza);
    - a bracketed part is kept (Cidade das Pombas (Eito de Baixo) is its own name)."""
    s = _plain(s)
    s = re.sub(r"[\'\.\-/,]", ' ', s).replace('(', ' ( ').replace(')', ' ) ')
    s = re.sub(r'tch|tx', 'ch', s)
    s = re.sub(r'dj', 'j', s)
    s = re.sub(r'k(?=[aou])', 'c', s)
    s = re.sub(r'k(?=[ei])', 'qu', s)
    s = s.replace('k', 'c')
    out = []
    for w in s.split():
        w = _ABBREV.get(w, w)
        if w in _ARTICLES:
            continue
        out.append(w)
    return re.sub(r'\(\s*', '(', re.sub(r'\s*\)', ')', ' '.join(out))).strip()


def name_keys_typed(s):
    """Keys to try for something typed: the key itself, plus the reading of
    a run-together "d" ('Ponta dagua' = 'Ponta d'Água')."""
    keys = [name_key(s)]
    alt = name_key(re.sub(r"\bd(?=[aeiou])", "d' ", _plain(s)))
    if alt not in keys:
        keys.append(alt)
    return keys


def units_needed(lotes, digits):
    _u0, _u1, size = UNITS[digits]
    return max(1, math.ceil(lotes * HEADROOM / size))


def digits_for_name(lotes_per_zone):
    """Shortest length whose range holds every zone of the name at x3 headroom
    plus RESERVE_UNITS free units. None: the name needs a qualifier."""
    for d in (3, 4, 5):
        u0, u1, _ = UNITS[d]
        if sum(units_needed(n, d) for n in lotes_per_zone) + RESERVE_UNITS <= u1 - u0 + 1:
            return d
    return None


def digits_for(lotes):
    """Digits a zone that is alone with its name needs at first issue."""
    return digits_for_name([lotes])


def unit_range(digits, unit):
    _, _, size = UNITS[digits]
    return unit * size, unit * size + size - 1


def plan_name(zone_lotes):
    """First-issue blocks of one name. zone_lotes: [(zone ref, lotes)] in issue
    order (municipality index, then zone index). Returns (digits, {zone ref:
    [lo, hi]}, reserve [lo, hi]); blocks are contiguous runs of units from the
    bottom of the range, the reserve is the rest."""
    d = digits_for_name([n for _, n in zone_lotes])
    if d is None:
        raise ValueError('name needs a qualifier (QUALIFIERS) before first issue')
    u, _, size = UNITS[d]
    blocks = {}
    for ref, n in zone_lotes:
        k = units_needed(n, d)
        blocks[ref] = [u * size, (u + k) * size - 1]
        u += k
    return d, blocks, [u * size, RANGES[d][1]]


def group(number):
    """How the number is written and said: 3 digits whole, 4 as two pairs,
    5 as a pair and a door number (12 345)."""
    s = str(number)
    if len(s) in (4, 5):
        return s[:2] + ' ' + s[2:]
    return s


# --------------------------------------------------------------------------
# Zones (SPEC.md §3.3) and the national name register (§3.4, §5). Loaded from
# engine/data/zones.json and engine/data/names.json (built by
# tools/build_zones.py and tools/build_names.py, frozen at first issue; the
# published registry's zones.csv and names.csv hold the same register with
# every block issued since).
# --------------------------------------------------------------------------
_ZONES = None
_NAMES = None


def fold(s):
    """Fold a place name for matching inside the zone builder: no accents, no
    apostrophe variants, lower case, single spaces."""
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    s = s.lower().replace('’', "'").replace('`', "'")
    s = re.sub(r"[\'\.\-]", '', s)
    return re.sub(r'\s+', ' ', s).strip()


def zref(z):
    return f"{z['key']}-{z['index']:03d}"


def zones():
    global _ZONES
    if _ZONES is None:
        p = os.path.join(DATA, 'zones.json')
        _ZONES = _json(p)['zones'] if os.path.exists(p) else []
    return _ZONES


def plate_ok(name):
    """A plate name fits the limit (SPEC.md §3.7): at most 12
    characters (a letter, space, hyphen, apostrophe or dot each counts one)
    and 2 words (de, da, do... do not count), and no digit."""
    return plate_names.fits(name, 'pt')


def check_register_entry(e):
    """A register name over the limit is refused unless it is a
    provisional name waiting for the municipality (needsCouncilChoice): its
    codes are issued provisional with the provisional name, and the numbers stay
    when the Câmara chooses."""
    if not plate_ok(e['name']) and not e.get('needsCouncilChoice'):
        raise ValueError(f"plate name {e['name']!r} is over {plate_names.MAX_CHARS} characters or {plate_names.MAX_WORDS} words")


def _index_names(entries):
    out = {}
    for e in entries:
        check_register_entry(e)
        for k in [e['key']] + [name_key(a) for a in e.get('aliases', [])]:
            if out.get(k, e) is not e:
                raise ValueError(f'alias {k!r} is claimed by two names')
            out[k] = e
    return out


def names():
    """name key -> register entry {key, index, name, aliases, officialNames,
    needsCouncilChoice, fits, digits, blocks: [{zone, lo, hi}], reserve,
    zones}; aliases (the official names among them) map to the same entry."""
    global _NAMES
    if _NAMES is None:
        p = os.path.join(DATA, 'names.json')
        _NAMES = _index_names(_json(p)['names']) if os.path.exists(p) else {}
    return _NAMES


def use_register(zone_list, name_list):
    """Decode against a frozen register (the zones and names of a published
    registry, with every block issued since) instead of the one in
    engine/data. Zones need key, index, name, officialName, aliases, near,
    anchor, box, nameKey and nameIndex; names need key, index, name,
    aliases, officialNames, needsCouncilChoice, digits, blocks and reserve."""
    global _ZONES, _NAMES, _BY_REF, _BY_INDEX
    names_ = _index_names(name_list)
    _ZONES, _NAMES, _BY_REF, _BY_INDEX = list(zone_list), names_, None, None


_BY_REF = None
_BY_INDEX = None


def use_published_registry(registry_dir):
    """Decode against the register of a published registry folder (its
    zones.csv and names.csv), which holds every block issued since first
    issue."""
    import csv
    with open(os.path.join(registry_dir, 'names.csv'), encoding='utf-8', newline='') as f:
        nrows = list(csv.DictReader(f))
    with open(os.path.join(registry_dir, 'zones.csv'), encoding='utf-8', newline='') as f:
        zrows = list(csv.DictReader(f))
    first, entries = {}, []
    for r in nrows:
        blocks = []
        for b in r['blocks'].split():
            zone, rng = b.rsplit(':', 1)
            lo, hi = (int(x) for x in rng.split('-'))
            blocks.append({'zone': zone, 'lo': lo, 'hi': hi})
            first.setdefault(zone, [lo, hi])
        e = {'key': r['name_key'], 'index': int(r['name_index']), 'name': r['plate_name'],
             'aliases': [a for a in r['aliases'].split('|') if a], 'officialNames': [a for a in r['official_names'].split('|') if a],
             'needsCouncilChoice': r['needs_council_choice'] == 'true', 'digits': int(r['digits']), 'blocks': blocks,
             'reserve': [int(x) for x in r['reserve'].split('-')]}
        for b in blocks:  # lengths a name has opened since first issue (SPEC.md §5.3)
            d = len(str(b['lo']))
            if d != e['digits'] and d not in e.get('lengths', []):
                e.setdefault('lengths', [e['digits']]).append(d)
        entries.append(e)
    zl = [{'key': r['municipality'], 'iso': 'CV-' + r['municipality'], 'index': int(r['index']), 'name': r['plate_name'],
           'officialName': r['official_name'], 'aliases': [a for a in r['aliases'].split('|') if a], 'near': r['near'] or None,
           'plateRule': r['plate_rule'], 'needsCouncilChoice': r['needs_council_choice'] == 'true', 'nameKey': r['name_key'],
           'nameIndex': int(r['name_index']), 'box': [float(x) for x in r['box'].split()],
           'anchor': [float(x) for x in r['anchor'].split()], 'block': first.get(r['zone'])} for r in zrows]
    use_register(zl, entries)


def names_by_index():
    global _BY_INDEX
    if _BY_INDEX is None or len(_BY_INDEX) == 0:
        _BY_INDEX = {e['index']: e for e in names().values()}
    return _BY_INDEX


def zone_by_ref(ref):
    key, idx = ref.split('-')
    return zone_by_index(key, int(idx))


def zone_by_index(key, index):
    global _BY_REF
    if _BY_REF is None:
        _BY_REF = {(z['key'], z['index']): z for z in zones()}
    z = _BY_REF.get((key, index))
    if z is None:
        raise KeyError(f'{key}-{index:03d}')
    return z


def owning_zone(entry, number):
    """The one zone of a name that owns a number, or None (unused)."""
    for b in entry['blocks']:
        if b['lo'] <= number <= b['hi']:
            return b['zone']
    return None


def _check(z, number):
    return check_digit(z['nameIndex'], number)


def format_machine(z, number, structure=None):
    """KEY-NAME INDEX-NUMBER-CHECK, e.g. PR-0690-1234-6: municipality key,
    national name index (4 digits), number, check digit. The zone is not in
    it: name + number decode to the zone, and the key must agree with it."""
    s = f"{z['key']}-{z['nameIndex']:04d}-{number}-{_check(z, number)}"
    return s + (f'.{structure}' if structure and structure > 1 else '')


def format_home(z, number, structure=None, full=False):
    """The remembered form, e.g. 'Palmarejo 12 34': unique in the whole
    country on its own. full adds the context lines of the UPU layout, which
    are information, never part of the code: the official name when the
    plate name is shorter, then municipality and island."""
    s = f"{z['name']} {group(number)}" + (f'.{structure}' if structure and structure > 1 else '')
    if full:
        m = MUNI[z['key']]
        off = z.get('officialName')
        s += (f" · {off}" if off and off != z['name'] else '') + f" · {m['name']}, {m['island']}"
    return s


def format_plate(z, number):
    """What a door plate or a form prints: the home code in large type and a
    context line (official name when it differs, municipality and island,
    printed to inform; the big line alone decodes). People never see the
    check digit: it exists only in the machine form, which the plate carries
    in its QR code for systems."""
    m = MUNI[z['key']]
    off = z.get('officialName')
    out = {'big': f"{z['name']} {group(number)}", 'small': f"{m['name']} · {m['island']}",
           'machine': format_machine(z, number)}
    if off and off != z['name']:
        out['official'] = off
    return out


MACHINE_RE = re.compile(r'^\s*([A-Za-z]{2})\s*-?\s*(\d{4})\s*-?\s*(\d{3,5})\s*-?\s*(\d)\s*(?:\.(\d{1,2}))?\s*$')
HOME_RE = re.compile(r'^\s*(.*?\D)\s*((?:\d\s?){3,5})(?:\.(\d{1,2}))?\s*(?:[,·]\s*(.*))?$')
HOME_RE_GREEDY = re.compile(r'^\s*(.*\D)\s*((?:\d\s?){3,5})(?:\.(\d{1,2}))?\s*(?:[,·]\s*(.*))?$')


def parse(text, check=None):
    """Read a machine form ('PR-0690-1234-6') or a home form ('Fazenda 1234',
    'fazenda 12 34'). Returns ONE result: a home code names exactly one zone
    in the country, found from the name's national range (SPEC.md §3.4).
    check: the check digit from a plate or form, if the person has it.
    Anything after a comma (a municipality or island) is not part of the code:
    it is compared with the decoded zone and reported, never used to choose."""
    m = MACHINE_RE.match(text)
    if m:
        key, ni, num, chk = m.group(1).upper(), int(m.group(2)), int(m.group(3)), int(m.group(4))
        if key not in MUNI:
            raise ValueError(f'unknown municipality key {key}')
        if not check_ok(ni, num, chk):
            raise ValueError('check digit does not match: a digit is wrong or two are swapped')
        entry = names_by_index().get(ni)
        ref = owning_zone(entry, num) if entry else None
        if ref is None:
            raise ValueError(f'{ni:04d}-{num} is not an issued block')
        if not ref.startswith(key + '-'):
            raise ValueError(f'{entry["name"]} {group(num)} is in {MUNI[ref[:2]]["name"]}, not {MUNI[key]["name"]}')
        return {'zone': zone_by_ref(ref), 'number': num, 'structure': int(m.group(5) or 1), 'checked': True}
    h = HOME_RE.match(text)
    if not h:
        raise ValueError('a home code is a place name and a number, e.g. "Palmarejo 12 34"')
    # an official name with a numeral typed in full ("África 70 230"): when
    # the shortest reading of the name does not own the number, the name may
    # end in the numeral
    g = HOME_RE_GREEDY.match(text)
    if g and g.group(1) != h.group(1):
        e2 = next((names()[k] for k in name_keys_typed(g.group(1)) if k in names()), None)
        n2 = int(g.group(2).replace(' ', ''))
        e1 = next((names()[k] for k in name_keys_typed(h.group(1)) if k in names()), None)
        n1 = int(h.group(2).replace(' ', ''))
        if e2 and owning_zone(e2, n2) and not (e1 and owning_zone(e1, n1)):
            h = g
    num = int(h.group(2).replace(' ', ''))
    if len(str(num)) < 3 or len(str(num)) > MAX_DIGITS:
        raise ValueError('numbers have 3 to 5 digits and no leading zero')
    entry = next((names()[k] for k in name_keys_typed(h.group(1)) if k in names()), None)
    if entry is None:
        raise ValueError(f'no zone called {h.group(1).strip()!r}')
    ref = owning_zone(entry, num)
    if ref is None:
        raise ValueError(f'{entry["name"]} {group(num)} is not a home code: the number is outside every block of {entry["name"]}')
    z = zone_by_ref(ref)
    out = {'zone': z, 'number': num, 'structure': int(h.group(3) or 1), 'checked': False}
    if check is not None:
        if not check_ok(z['nameIndex'], num, int(check)):
            raise ValueError('check digit does not match: a digit is wrong or two are swapped')
        out['checked'] = True
    if h.group(4):
        ctx = name_key(h.group(4))
        mu = MUNI[z['key']]
        out['contextMatches'] = any(name_key(x).startswith(ctx) for x in (mu['name'], mu['island']))
    return out


# Portuguese / Kriolu number words for the voice (SPEC.md §2.3).
_PT_UNITS = ['zero', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove', 'dez', 'onze', 'doze',
             'treze', 'catorze', 'quinze', 'dezasseis', 'dezassete', 'dezoito', 'dezanove']
_PT_TENS = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
_PT_HUNDREDS = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos',
                'oitocentos', 'novecentos']
# Kriolu (Santiago), ALUPEC spelling; to be confirmed with speakers.
_KEA_UNITS = ['zeru', 'un', 'dos', 'tres', 'kuatu', 'sinku', 'seis', 'seti', 'oitu', 'novi', 'dés', 'onzi', 'dozi',
              'trezi', 'katorzi', 'kinzi', 'dizaseis', 'dizaseti', 'dizoitu', 'dizanovi']
_KEA_TENS = ['', '', 'vinti', 'trinta', 'korenta', 'sinkuenta', 'sesenta', 'setenta', 'oitenta', 'noventa']
_KEA_HUNDREDS = ['', 'senti', 'duzentu', 'trezentu', 'kuatusentu', 'kinhentu', 'seisentu', 'setisentu', 'oitusentu',
                 'novisentu']


def _words(n, lang):
    U, T, H, AND = ((_PT_UNITS, _PT_TENS, _PT_HUNDREDS, ' e ') if lang == 'pt' else (_KEA_UNITS, _KEA_TENS, _KEA_HUNDREDS, ' i '))
    if n < 20:
        return U[n]
    if n < 100:
        return T[n // 10] + (AND + U[n % 10] if n % 10 else '')
    if n == 100:
        return 'cem' if lang == 'pt' else 'sen'
    return H[n // 100] + (AND + _words(n % 100, lang) if n % 100 else '')


def spoken(z, number, lang='pt'):
    """'Palmarejo, doze, trinta e quatro'. 3 digits are said as a door
    number; 4 digits as two pairs, the way phone numbers are said; a pair
    starting with 0 is said digit by digit ('zero cinco')."""
    s = str(number)
    if len(s) == 3:
        parts = [_words(number, lang)]
    else:
        parts = []
        for pair in (s[:2], s[2:]):
            if len(pair) == 2 and pair[0] == '0':
                parts.append(' '.join(_words(int(c), lang) for c in pair))
            elif len(pair) == 3:
                parts.append(_words(int(pair), lang))
            else:
                parts.append(_words(int(pair), lang))
    return z['name'] + ', ' + ', '.join(parts)


# --------------------------------------------------------------------------
# Open Location Code (SPEC.md §6): encode/decode, short codes. Implemented here
# from the public specification (github.com/google/open-location-code).
# --------------------------------------------------------------------------
OLC_ALPHABET = '23456789CFGHJMPQRVWX'
OLC_SEP = '+'


def olc_encode(lat, lon, length=10):
    """Full Plus Code of a point; length 10 (~14 m) or 11 (~3.5 x 2.8 m)."""
    lat = min(max(lat, -90.0), 90.0)
    lon = ((lon + 180.0) % 360.0) - 180.0
    lat_val = math.floor(round((lat + 90.0) * 25000000, 6))   # 8000 * 5**5 per degree
    lon_val = math.floor(round((lon + 180.0) * 8192000, 6))   # 8000 * 4**5 per degree
    if lat_val >= 180 * 25000000:
        lat_val = 180 * 25000000 - 1
    code = ''
    if length > 10:
        for _ in range(5):
            code = OLC_ALPHABET[(lat_val % 5) * 4 + (lon_val % 4)] + code
            lat_val //= 5
            lon_val //= 4
    else:
        lat_val //= 5 ** 5
        lon_val //= 4 ** 5
    for _ in range(5):
        code = OLC_ALPHABET[lon_val % 20] + code
        code = OLC_ALPHABET[lat_val % 20] + code
        lat_val //= 20
        lon_val //= 20
    return code[:8] + OLC_SEP + code[8:length]


def olc_decode(code):
    """Return (lat_lo, lon_lo, lat_hi, lon_hi) of a full code."""
    c = code.upper().replace(OLC_SEP, '')
    lat, lon = -90.0, -180.0
    res = 20.0
    pairs, grid = c[:10], c[10:]
    for i in range(0, len(pairs), 2):
        lat += OLC_ALPHABET.index(pairs[i]) * res
        lon += OLC_ALPHABET.index(pairs[i + 1]) * res
        last_lat = last_lon = res
        res /= 20.0
    lat_res, lon_res = last_lat, last_lon
    for ch in grid:
        v = OLC_ALPHABET.index(ch)
        lat_res /= 5.0
        lon_res /= 4.0
        lat += (v // 4) * lat_res
        lon += (v % 4) * lon_res
    return lat, lon, lat + lat_res, lon + lon_res


def olc_short(code, ref_lat, ref_lon):
    """Shorten a full code against a reference point, as the OLC reference
    libraries do: drop 6 digits if the reference is within 0.015 degrees of
    the code's centre, else 4 digits if within 0.3 degrees."""
    lo_lat, lo_lon, hi_lat, hi_lon = olc_decode(code)
    rng = max(abs((lo_lat + hi_lat) / 2 - ref_lat), abs((lo_lon + hi_lon) / 2 - ref_lon))
    for removal, precision in ((6, 0.05), (4, 1.0)):
        if rng < precision * 0.3:
            return code[removal:]
    return code


def olc_recover(short, ref_lat, ref_lon):
    """The full code nearest a reference point for a short code (the OLC
    recoverNearest rule), e.g. '8W9+X2G' near Nova Sintra."""
    short = short.strip().upper()
    sep = short.index(OLC_SEP)
    pad = 8 - sep
    if pad <= 0:
        return short
    resolution = 20.0 ** (2 - pad / 2)
    half = resolution / 2
    digits = len(short) - 1 + pad
    lo_lat, lo_lon, hi_lat, hi_lon = olc_decode(olc_encode(ref_lat, ref_lon, 10)[:pad] + short)
    lat, lon = (lo_lat + hi_lat) / 2, (lo_lon + hi_lon) / 2
    if ref_lat + half < lat and lat - resolution >= -90:
        lat -= resolution
    elif ref_lat - half > lat and lat + resolution <= 90:
        lat += resolution
    if ref_lon + half < lon:
        lon -= resolution
    elif ref_lon - half > lon:
        lon += resolution
    return olc_encode(lat, lon, digits)


# --------------------------------------------------------------------------
# Point -> municipality (SPEC.md §3.2), from the shipped simplified outlines.
# --------------------------------------------------------------------------
_POLYS = None


def _load_polys():
    global _POLYS
    if _POLYS is None:
        fc = _json(os.path.join(DATA, 'municipalities.geojson'))
        _POLYS = []
        for f in fc['features']:
            g = f['geometry']
            polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
            xs = [p[0] for poly in polys for ring in poly for p in ring]
            ys = [p[1] for poly in polys for ring in poly for p in ring]
            _POLYS.append((f['properties']['iso'], polys, (min(xs), min(ys), max(xs), max(ys))))
    return _POLYS


def _in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def municipality_at(lat, lon):
    for iso, polys, (x0, y0, x1, y1) in _load_polys():
        if not (x0 <= lon <= x1 and y0 <= lat <= y1):
            continue
        for poly in polys:
            if _in_ring(lon, lat, poly[0]) and not any(_in_ring(lon, lat, h) for h in poly[1:]):
                return MUNI_BY_ISO[iso]
    return None


# --------------------------------------------------------------------------
# National border (SPEC.md §3.2): the border decides. A home code is only
# ever issued for an entrance inside Cabo Verde's national border (the
# OpenStreetMap admin_level 2 boundary) or within BORDER_M of it; no other
# outline (municipality, zone, box) ever overrides it.
# --------------------------------------------------------------------------
BORDER_M = 300.0
_BORDER = None
_WGS_A = 6378137.0
_WGS_E2 = 6.69437999014e-3


def border_outline():
    """(polygons, deviationM) of data/border.geojson: the national border
    simplified, and how far at most its line lies from the full one."""
    global _BORDER
    if _BORDER is None:
        f = _json(os.path.join(DATA, 'border.geojson'))
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        _BORDER = (polys, float(f['properties']['deviationM']))
    return _BORDER


def _metres_per_degree(lat):
    """Metres per degree of latitude and of longitude (WGS 84, local scale)."""
    p = math.radians(lat)
    w = 1 - _WGS_E2 * math.sin(p) ** 2
    return (_WGS_A * (1 - _WGS_E2) / w ** 1.5 * math.pi / 180,
            _WGS_A / math.sqrt(w) * math.cos(p) * math.pi / 180)


def border_distance_m(lat, lon, polys=None):
    """How far a point lies outside the national border, in metres: 0 inside
    (holes excluded), else the distance to the nearest edge. polys: an outline
    as [polygon], polygon = [ring], ring = [[lon, lat], ...]; default the
    shipped one."""
    if polys is None:
        polys = border_outline()[0]
    for poly in polys:
        if _in_ring(lon, lat, poly[0]) and not any(_in_ring(lon, lat, h) for h in poly[1:]):
            return 0.0
    ky, kx = _metres_per_degree(lat)
    best = math.inf
    for poly in polys:
        for ring in poly:
            n = len(ring)
            for i in range(n):
                ax, ay = (ring[i][0] - lon) * kx, (ring[i][1] - lat) * ky
                bx, by = (ring[(i + 1) % n][0] - lon) * kx, (ring[(i + 1) % n][1] - lat) * ky
                dx, dy = bx - ax, by - ay
                L = dx * dx + dy * dy
                t = 0.0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
                best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def within_border(lat, lon, polys=None):
    """Whether a home code may be issued at this entrance. With the full
    border (polys) the limit is BORDER_M; with the shipped, simplified one it
    is BORDER_M less the simplification's deviation, so the shipped outline
    never accepts a point the full border would refuse."""
    if polys is None:
        polys, dev = border_outline()
        return border_distance_m(lat, lon, polys) <= BORDER_M - dev
    return border_distance_m(lat, lon, polys) <= BORDER_M


def describe_point(lat, lon):
    """What the app shows for a point when no lote is known (offline)."""
    m = municipality_at(lat, lon)
    if m is None:
        return {'land': False, 'note': 'at sea or outside Cabo Verde: no spot code is issued'}
    full = olc_encode(lat, lon, 11)
    return {'land': True, 'plusCode': full, 'plusCodeShort': f"{olc_short(olc_encode(lat, lon, 10), m['seatLat'], m['seatLon'])} {m['seat']}",
            'municipality': m['name'], 'key': m['key'], 'island': m['island'],
            'postalPrefix': m['postalPrefix'], 'postalStatus': m['postalStatus']}



# --------------------------------------------------------------------------
# Coverage mask (SPEC.md §3.6): official addresses first. Where a Câmara
# Municipal (or a future national register) has given a street name and a door
# number, that address is THE address, shown exactly as written, and no N-Ways
# number is issued. N-Ways numbers exist only where nothing official exists;
# when official numbering arrives, the N-Ways code becomes an alias.
# --------------------------------------------------------------------------
# Areas presumed to have municipal numbering whose register is not shared yet
# (approximate boxes). Their lotes have home codes like every other; the door
# number is shown first once the Câmara shares its register.
PRESUMED_OFFICIAL = [
    {'iso': 'CV-PR', 'name': 'Platô (historic centre, Praia)', 'box': [-23.5115, 14.9135, -23.5025, 14.9235]},
    {'iso': 'CV-SV', 'name': 'Mindelo historic centre', 'box': [-24.9950, 16.8840, -24.9860, 16.8920]},
]


def coverage_of(tags, lat, lon):
    # -> ('official', address) | ('official-pending', None) | ('nways', None)
    tags = tags or {}
    if tags.get('addr:street') and tags.get('addr:housenumber'):
        return 'official', f"{tags['addr:street']} {tags['addr:housenumber']}"
    for a in PRESUMED_OFFICIAL:
        x0, y0, x1, y1 = a['box']
        if x0 <= lon <= x1 and y0 <= lat <= y1:
            return 'official-pending', None
    return 'nways', None


def resolve(lote):
    # What the app shows as the address of a lote record: the official
    # address first where there is one, with the lote's home code beside it.
    if lote.get('official'):
        aliases = list(lote.get('nwaysAliases', []))
        if lote.get('home') and lote['home'] not in aliases:
            aliases.append(lote['home'])
        return {'address': lote['official'], 'system': 'official', 'aliases': aliases}
    return {'address': lote['home'], 'system': 'nways', 'aliases': []}


def hand_over(lote, official_address):
    # The municipality numbers a street that had N-Ways codes: the official
    # address becomes the address; the N-Ways code stays as an alias that
    # resolves to it, and its number is never given to anyone else.
    out = dict(lote)
    out['official'] = official_address
    out['nwaysAliases'] = list(lote.get('nwaysAliases', [])) + ([lote['home']] if lote.get('home') else [])
    out['nwaysStatus'] = 'alias'
    return out


# --------------------------------------------------------------------------
# Hilbert order and numbering inside a zone (SPEC.md §7).
# --------------------------------------------------------------------------
HILBERT_ORDER = 16  # 65,536 x 65,536 grid over the zone box


def hilbert_index(x, y, order=HILBERT_ORDER):
    n = 1 << order
    d = 0
    s = n >> 1
    while s > 0:
        rx = 1 if (x & s) else 0
        ry = 1 if (y & s) else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x = n - 1 - x
                y = n - 1 - y
            x, y = y, x
        s >>= 1
    return d


def hilbert_of(lat, lon, box):
    x0, y0, x1, y1 = box
    n = (1 << HILBERT_ORDER) - 1
    x = round((lon - x0) / (x1 - x0) * n)
    y = round((lat - y0) / (y1 - y0) * n)
    return hilbert_index(min(max(x, 0), n), min(max(y, 0), n))



def number_zone(lotes, box, block):
    """First issue in one zone. lotes: [(lote_id, lat, lon)] of each lote's
    anchor (its gate if known, else its main structure); block: the zone's
    [lo, hi] in its name's national range. Values are spread over the block
    so Hilbert neighbours keep free numbers between them for homes built
    later. Returns {lote_id: number}."""
    lo, hi = block
    span = hi - lo + 1
    order = sorted(lotes, key=lambda t: (hilbert_of(t[1], t[2], box), str(t[0])))
    n = len(order)
    if n * HEADROOM > span:
        raise ValueError('block too small: the name plan gives every zone 3 x its lotes')
    return {lid: lo + int((k + 0.5) * span / n) for k, (lid, _, _) in enumerate(order)}


def _used_units(entry):
    used = set()
    for bl in entry['blocks']:
        d = len(str(bl['lo']))
        size = UNITS[d][2]
        used |= {(d, u) for u in range(bl['lo'] // size, bl['hi'] // size + 1)}
    return used


def take_block(entry, ref, units=1):
    """A new block for zone ref from its name's spare space: the lowest free
    run of `units` units in the name's open lengths; if none is left, the
    name opens the next length (its range there is all free). Existing
    blocks are never moved or renumbered. Mutates and returns the entry's
    new block {zone, lo, hi}."""
    used = _used_units(entry)
    lengths = entry.setdefault('lengths', [entry['digits']])
    while True:
        for d in lengths:
            u0, u1, size = UNITS[d]
            for u in range(u0, u1 - units + 2):
                if all((d, x) not in used for x in range(u, u + units)):
                    bl = {'zone': ref, 'lo': u * size, 'hi': (u + units) * size - 1}
                    entry['blocks'].append(bl)
                    return bl
        if lengths[-1] >= MAX_DIGITS:
            raise ValueError('name range full at 5 digits: split the name with a qualifier')
        lengths.append(lengths[-1] + 1)


def new_zone(entry, ref, lotes):
    """A zone created after first issue whose name already exists (a new
    Achadinha): it gets its own block, 3 x its lotes, from the name's spare
    space (SPEC.md §5.3)."""
    d = entry.setdefault('lengths', [entry['digits']])[-1]
    return take_block(entry, ref, units_needed(lotes, d))


def zone_blocks(entry, ref):
    return [(b['lo'], b['hi']) for b in entry['blocks'] if b['zone'] == ref]


def insert_lote(issued, lat, lon, box, anchors, entry, ref):
    """A home added after first issue ("Add my home", a new building) in zone
    ref of name entry. issued: {number: lote_id} of that zone; anchors:
    {lote_id: (lat, lon)}.
    1. find its Hilbert neighbours among the zone's issued lotes; 2. take the
    middle free number between them; 3. if none is free, the nearest free
    number in the zone's blocks; 4. if the zone's blocks are full, the zone
    takes a new block from its name's spare space, at the same relative
    position; 5. if the name's range is full, the name opens the next
    length. No issued number changes, and the number never lands in another
    zone's block."""
    h = hilbert_of(lat, lon, box)
    for lo, hi in zone_blocks(entry, ref):
        by_h = sorted((hilbert_of(*anchors[l], box), v) for v, l in issued.items() if lo <= v <= hi)
        if len(by_h) >= hi - lo + 1:
            continue
        prev_v, next_v = lo - 1, hi + 1
        for hv, v in by_h:
            if hv <= h:
                prev_v = v
            else:
                next_v = v
                break
        a, b = min(prev_v, next_v), max(prev_v, next_v)
        # Hilbert neighbours aren't always number neighbours once lotes have
        # been inserted, so the midpoint may already be taken.
        if b - a > 1:
            mid = (a + b) // 2
            if mid not in issued:
                return mid
            a = b = mid
        for d in range(1, hi - lo + 2):
            for v in (a - d, b + d):
                if lo <= v <= hi and v not in issued:
                    return v
    bl = take_block(entry, ref)
    pos = h / float(1 << (2 * HILBERT_ORDER))
    v = bl['lo'] + int(pos * (bl['hi'] - bl['lo'] + 1))
    while v in issued:
        v += 1
    return v


# --------------------------------------------------------------------------
# Building profile: use classes (SPEC.md §8). Rules in priority order; the
# first that fires sets class, confidence and source.
# --------------------------------------------------------------------------
STOREY_M = 3.0
ML_HEIGHT_TRUSTED = False

OSM_BUILDING = {
    'house': ('residencial.moradia', 0.85), 'detached': ('residencial.moradia', 0.85),
    'semidetached_house': ('residencial.moradia', 0.85), 'terrace': ('residencial.moradia', 0.85),
    'bungalow': ('residencial.moradia', 0.85), 'hut': ('residencial.precaria', 0.75),
    'shed': ('anexo', 0.75), 'garage': ('anexo', 0.8), 'garages': ('anexo', 0.8), 'roof': ('anexo', 0.6),
    'apartments': ('residencial.predio', 0.85), 'residential': ('residencial', 0.7), 'dormitory': ('residencial.predio', 0.8),
    'commercial': ('comercio', 0.75), 'retail': ('comercio.loja', 0.8), 'kiosk': ('comercio.quiosque', 0.85),
    'supermarket': ('comercio.loja', 0.85), 'office': ('servicos.escritorio', 0.8), 'warehouse': ('comercio.armazem', 0.85),
    'industrial': ('industria', 0.85), 'factory': ('industria', 0.85),
    'hotel': ('turismo.hotel', 0.85), 'school': ('educacao', 0.9), 'university': ('educacao', 0.9),
    'college': ('educacao', 0.9), 'kindergarten': ('educacao', 0.9), 'hospital': ('saude', 0.9),
    'clinic': ('saude', 0.85), 'church': ('religioso', 0.95), 'chapel': ('religioso', 0.95),
    'cathedral': ('religioso', 0.95), 'mosque': ('religioso', 0.95), 'religious': ('religioso', 0.85),
    'government': ('governo', 0.9), 'public': ('governo', 0.6), 'civic': ('governo', 0.7),
    'transportation': ('transporte', 0.85), 'train_station': ('transporte', 0.85),
    'farm': ('agricola', 0.75), 'farm_auxiliary': ('agricola', 0.8), 'barn': ('agricola', 0.8), 'stable': ('agricola', 0.8),
    'cowshed': ('agricola', 0.85), 'sty': ('agricola', 0.85), 'greenhouse': ('agricola', 0.85),
    'sports_hall': ('desporto', 0.85), 'stadium': ('desporto', 0.85), 'grandstand': ('desporto', 0.85),
    'service': ('utilidade', 0.6), 'water_tower': ('utilidade', 0.85), 'toilets': ('anexo', 0.75),
    'construction': ('residencial', 0.3), 'ruins': ('desconhecido', 0.5), 'military': ('governo.defesa', 0.85),
}
STATUS_TAGS = {'construction': 'em_construcao', 'ruins': 'ruina', 'abandoned': 'abandonado', 'collapsed': 'ruina'}

POI_CLASS = {  # N-Ways places categories -> class
    'school': ('educacao', 0.75), 'hospital': ('saude', 0.75), 'pharmacy': ('comercio.loja', 0.6),
    'church': ('religioso', 0.8), 'mosque': ('religioso', 0.8), 'hotel': ('turismo.hotel', 0.7),
    'police': ('governo.seguranca', 0.8), 'bank': ('servicos.escritorio', 0.7), 'office': ('servicos.escritorio', 0.55),
    'market': ('comercio.mercado', 0.75), 'supermarket': ('comercio.loja', 0.7), 'shop': ('comercio.loja', 0.6),
    'food': ('restauracao', 0.6), 'bar': ('restauracao', 0.6), 'cafe': ('restauracao', 0.6), 'fastfood': ('restauracao', 0.6),
    'salon': ('comercio.loja', 0.55), 'mechanic': ('industria.oficina', 0.6), 'petrol': ('transporte.combustivel', 0.75),
    'motorpark': ('transporte', 0.6), 'phones': ('comercio.loja', 0.55), 'carwash': ('servicos', 0.55),
}
# Classes a POI turns into mixed use when the building otherwise looks like a
# home (the CV "loja em baixo, casa em cima" pattern; census: 6.5 % of
# buildings mostly residential with another use).
SHOPFRONT = {'comercio.loja', 'restauracao', 'servicos.escritorio', 'servicos', 'industria.oficina'}

TOURISM_ISLANDS = {'Sal', 'Boa Vista'}


def classify(tags, poi_categories, area_m2, height_m, island, urban, annexe=False):
    """-> (class, confidence, source, status). tags: OSM tags of the footprint
    (empty for Google/Microsoft footprints); poi_categories: N-Ways places
    categories found inside the footprint; urban: True where the local
    density says town (SPEC.md §8.2)."""
    tags = tags or {}
    status = 'em_uso'
    b = tags.get('building', '')
    for t in ('construction', 'ruins', 'abandoned', 'collapsed'):
        if b == t or tags.get(t) == 'yes' or tags.get('disused') == 'yes' and t == 'abandoned':
            status = STATUS_TAGS[t]
    # 1. explicit OSM use tags on the footprint
    for k, mapping in (('amenity', {'school': 'educacao', 'kindergarten': 'educacao', 'university': 'educacao',
                                     'college': 'educacao', 'hospital': 'saude', 'clinic': 'saude', 'doctors': 'saude',
                                     'pharmacy': 'comercio.loja', 'place_of_worship': 'religioso',
                                     'townhall': 'governo', 'courthouse': 'governo', 'police': 'governo.seguranca',
                                     'fire_station': 'governo.seguranca', 'post_office': 'governo', 'bank': 'servicos.escritorio',
                                     'marketplace': 'comercio.mercado', 'restaurant': 'restauracao', 'bar': 'restauracao',
                                     'cafe': 'restauracao', 'fuel': 'transporte.combustivel', 'bus_station': 'transporte',
                                     'ferry_terminal': 'transporte', 'community_centre': 'governo', 'library': 'educacao'}),
                       ('office', {'government': 'governo'}), ('government', None), ('healthcare', None),
                       ('tourism', {'hotel': 'turismo.hotel', 'guest_house': 'turismo.pensao', 'hostel': 'turismo.pensao',
                                    'apartment': 'turismo.hotel', 'museum': 'cultura'}),
                       ('shop', None), ('aeroway', {'terminal': 'transporte'}), ('man_made', {'water_works': 'utilidade',
                                                                                               'reservoir_covered': 'utilidade'})):
        v = tags.get(k)
        if not v:
            continue
        if mapping is None:
            cls = {'government': 'governo', 'healthcare': 'saude', 'shop': 'comercio.loja'}[k]
        else:
            cls = mapping.get(v) or ({'office': 'servicos.escritorio'}.get(k))
        if cls:
            return cls, 0.9, 'osm:' + k, status
    if b in OSM_BUILDING:
        cls, conf = OSM_BUILDING[b]
        if b == 'hotel' or (b in ('apartments', 'commercial') and island in TOURISM_ISLANDS and tags.get('tourism')):
            cls = 'turismo.hotel'
        if status != 'em_uso' and cls == 'desconhecido':
            return cls, conf, 'osm:building', status
        return cls, conf, 'osm:building', status
    # 2. N-Ways places inside the footprint
    best = None
    for c in poi_categories or []:
        if c in POI_CLASS and (best is None or POI_CLASS[c][1] > best[1]):
            best = POI_CLASS[c]
    if best:
        cls, conf = best
        if cls in SHOPFRONT and height_m and height_m >= 2 * STOREY_M and area_m2 < 400:
            return 'misto', 0.55, 'places+height', status  # shop below, home above
        return cls, conf, 'places', status
    # 3. size and context (Google/Microsoft footprints mostly land here)
    floors = estimate_floors(tags, height_m)
    if annexe:
        return 'anexo', 0.55, 'lote:annexe', status  # small structure beside a house (SPEC.md §7.1 rule B)
    if area_m2 < 12:
        return 'anexo', 0.45, 'size', status
    if island in TOURISM_ISLANDS and area_m2 >= 150 and not urban and floors <= 3:
        return 'turismo.hotel', 0.35, 'size+island', status
    if area_m2 >= 2500 and floors <= 2:
        return 'comercio.armazem', 0.35, 'size', status
    if area_m2 >= 400 and floors >= 4:
        return 'residencial.predio', 0.45, 'size+height', status
    if floors >= 3:
        return 'residencial.predio', 0.5, 'height', status
    if area_m2 < 25:
        return 'residencial.moradia', 0.4, 'size', status  # one-room house or a store; ask people
    # 4. prior: census 2021, 87.0 % of classic buildings are homes only
    return 'residencial.moradia', 0.6 if floors <= 2 else 0.5, 'prior:census2021', status


def estimate_height(tags, ml_h):
    tags = tags or {}
    h = tags.get('height')
    if h:
        try:
            return float(str(h).replace('m', '').strip()), 'osm:height'
        except ValueError:
            pass
    lv = tags.get('building:levels')
    if lv:
        try:
            return float(lv) * STOREY_M, 'osm:building:levels'
        except ValueError:
            pass
    # The machine-learned height field of the footprint dataset is spread
    # evenly between 3.5 and 7.0 m for every footprint in Cabo Verde: a
    # rendering filler, not a measurement. It is not used (ML_HEIGHT_TRUSTED
    # False) until a measured source exists (SPEC.md §8.3).
    if ML_HEIGHT_TRUSTED and ml_h is not None and ml_h > 0:
        return float(ml_h), 'ml:h'
    return None, None


def estimate_floors(tags, height_m):
    tags = tags or {}
    lv = tags.get('building:levels')
    if lv:
        try:
            return max(1, round(float(lv)))
        except ValueError:
            pass
    if height_m:
        return max(1, round(height_m / STOREY_M))
    return 1


# --------------------------------------------------------------------------
# Self-test and test vectors.
# --------------------------------------------------------------------------
REAL_POINTS = [
    ('Praia, Platô', 14.91992, -23.50709),
    ('Mindelo, São Vicente', 16.88731, -24.98641),
    ('Santa Maria, Sal', 16.59869, -22.90503),
    ('São Filipe, Fogo', 14.89530, -24.49694),
    ('Nova Sintra, Brava', 14.87107, -24.69565),
    ('Tarrafal, Santiago', 15.27842, -23.75229),
    ('Tarrafal de São Nicolau', 16.56648, -24.35680),
    ('Atlantic, 5 km off Praia', 14.87, -23.47),
]

# The toy registry (six lotes and an insertion) runs in the real Palmarejo
# zone of the register (PR-004, its block and name index), over a small box
# inside it.
TOY_BOX = [-23.5420, 14.9180, -23.5260, 14.9300]


def _toy_zone():
    return dict(zone_by_ref('PR-004'), box=TOY_BOX)


def _copy(entry):
    return json.loads(json.dumps(entry))


def self_test():
    # OLC: the published example (Zurich) must round-trip
    assert olc_encode(47.365590, 8.524997) == '8FVC9G8F+6X'
    assert olc_encode(47.365590, 8.524997, 11) == '8FVC9G8F+6XQ'
    lo_lat, lo_lon, hi_lat, hi_lon = olc_decode('8FVC9G8F+6X')
    assert lo_lat <= 47.365590 < hi_lat and lo_lon <= 8.524997 < hi_lon
    # check digit: the published Damm example, then every single substitution
    # and every adjacent transposition of the number, exhaustively for 3- and
    # 4-digit numbers under four name indices and for a sample of 5-digit ones
    assert _damm([5, 7, 2]) == 4 and _damm([5, 7, 2, 4]) == 0
    for ni in (690, 76, 1, 1547):
        for num in list(range(100, 10000)) + list(range(10000, 100000, 97)):
            c = check_digit(ni, num)
            assert check_ok(ni, num, c)
            s = str(num)
            for i in range(len(s)):
                for d in '0123456789':
                    if d != s[i] and not (i == 0 and d == '0'):
                        assert not check_ok(ni, int(s[:i] + d + s[i + 1:]), c)
            for i in range(len(s) - 1):
                if s[i] != s[i + 1] and not (i == 0 and s[1] == '0'):
                    assert not check_ok(ni, int(s[:i] + s[i + 1] + s[i] + s[i + 2:]), c)
    # national normalisation
    for x, y in (("Chã de Baixo", 'Chã Baixo'), ("Pé do Monte", 'Pé de Monte'), ('As Hortas', 'Hortas'),
                 ('Lém-Ferreira', 'lem ferreira'), ("Ponta d'Água", 'ponta agua'), ('Achada Sto António', 'Achada Santo Antonio'),
                 ('Txada Grandi', 'Chada Grandi'), ('PLATÔ', 'plato')):
        assert name_key(x) == name_key(y), (x, y)
    assert name_key('Palmarejo') != name_key('Palmarejo Grande')
    assert 'ponta agua' in name_keys_typed('Ponta dagua')
    # number lengths: one zone alone with its name; 2 units stay in reserve
    assert digits_for(233) == 3 and digits_for(234) == 4 and digits_for(2933) == 4 and digits_for(2934) == 5
    assert digits_for_name([100, 100]) == 3 and digits_for_name([150, 150]) == 4 and digits_for_name([30, 30, 30]) == 3
    assert digits_for_name([29333]) == 5 and digits_for_name([29334]) is None
    # numbering keeps order and spacing inside the block
    pts = [(f'l{i}', 14.918 + (i % 10) * 0.001, -23.542 + (i // 10) * 0.0015) for i in range(100)]
    vals = number_zone(pts, TOY_BOX, (1000, 3899))
    assert len(set(vals.values())) == 100 and all(1000 <= v <= 3899 for v in vals.values())
    # plate names (SPEC.md §3.7): the limit, and the engine refuses a name over it
    assert plate_ok('São Filipe') and plate_ok('Sto António') and plate_ok('Lém-Ferreira') and plate_ok('Chã de Areia') and not plate_ok('Chã de Alecrim')
    assert not plate_ok('Achada São Filipe') and not plate_ok('África Setenta') and not plate_ok('Lombo Branco Novo')
    assert not plate_ok('África 70')
    for bad in ({'name': 'Lote Achada São Filipe'}, {'name': 'Madeiralzinho', 'needsCouncilChoice': False}):
        try:
            check_register_entry(bad)
            raise AssertionError('over-long plate name accepted')
        except ValueError:
            pass
    check_register_entry({'name': 'Madeiralzinho', 'needsCouncilChoice': True})  # provisional, not issuable
    if not names():
        return None
    # the register: every name decodes each of its numbers to exactly one zone;
    # blocks of one name never overlap; same-named zones decode apart
    seen = 0
    for e in {id(v): v for v in names().values()}.values():
        spans = sorted((b['lo'], b['hi']) for b in e['blocks'])
        assert all(spans[i][1] < spans[i + 1][0] for i in range(len(spans) - 1)), e['key']
        assert spans[-1][1] < e['reserve'][0] and len(str(spans[0][0])) == e['digits'] <= MAX_DIGITS
        for b in e['blocks']:
            r = parse(f"{e['name']} {b['lo']}")
            assert zref(r['zone']) == b['zone'] and r['zone']['nameIndex'] == e['index']
            seen += 1
    # every plate name fits or waits for the council; every official name
    # kept as an alias decodes to its own zone's plate name
    officials = 0
    for z in zones():
        e = names()[z['nameKey']]
        assert plate_ok(e['name']) or e['needsCouncilChoice'], e['name']
        if z['officialName'] in z.get('aliases', []):
            assert names()[name_key(z['officialName'])] is e
            r = parse(f"{z['officialName']} {z['block'][0]}")
            assert zref(r['zone']) == zref(z)
            officials += 1
    # a slip in the number that lands in ANOTHER zone of the same name (every
    # single-digit substitution and adjacent swap, from 25 numbers of every
    # block of every repeated name), entered with the plate's check digit:
    # caught, or unused, or reported
    cross = caught = unused = 0
    for e in {id(v): v for v in names().values()}.values():
        if len(e['blocks']) < 2:
            continue
        for b in e['blocks']:
            z = zone_by_ref(b['zone'])
            step = max(1, (b['hi'] - b['lo']) // 25)
            for num in range(b['lo'], b['hi'] + 1, step):
                c = _check(z, num)
                s = str(num)
                slips = {int(s[:i] + d + s[i + 1:]) for i in range(len(s)) for d in '0123456789' if d != s[i] and not (i == 0 and d == '0')}
                slips |= {int(s[:i] + s[i + 1] + s[i] + s[i + 2:]) for i in range(len(s) - 1) if s[i] != s[i + 1] and not (i == 0 and s[1] == '0')}
                for w in slips:
                    o = owning_zone(e, w)
                    if o is None:
                        unused += 1
                    elif o != b['zone']:
                        cross += 1
                        caught += not check_ok(e['index'], w, c)
    assert caught == cross
    # a machine form with one wrong character: any single substitution in the
    # name index or the number, any adjacent swap, or the wrong municipality
    # key; every one must be refused
    mz = mcaught = 0
    for z in zones()[::7]:
        b = names()[z['nameKey']]['blocks']
        num = next(x['lo'] for x in b if x['zone'] == zref(z)) + 37
        good = format_machine(z, num)
        key, ni, nn, c = good.split('-')
        body = ni + nn
        bad = set()
        for i in range(len(body)):
            for d in '0123456789':
                if d != body[i]:
                    bad.add(body[:i] + d + body[i + 1:])
            if i < len(body) - 1 and body[i] != body[i + 1]:
                bad.add(body[:i] + body[i + 1] + body[i] + body[i + 2:])
        tries = [f"{key}-{x[:4]}-{x[4:]}-{c}" for x in bad if x[4] != '0']
        tries += [f"{k}-{ni}-{nn}-{c}" for k in MUNI if k != key]
        for t in tries:
            mz += 1
            try:
                parse(t)
            except ValueError:
                mcaught += 1
    assert mcaught == mz
    return {'zonesDecoded': seen, 'officialNamesDecoded': officials, 'crossZoneSlips': cross, 'crossZoneCaught': caught, 'slipsToUnusedNumbers': unused,
            'machineFormErrors': mz, 'machineFormErrorsCaught': mcaught}


def vectors():
    z = _toy_zone()
    out = {'zone': {k: z[k] for k in ('key', 'index', 'name', 'nameIndex', 'digits', 'block')}, 'codes': [], 'sameName': [],
           'points': [], 'arithmetic': []}
    for num in (1000, 1234, 2050, 3899):
        out['codes'].append({'home': format_home(z, num), 'full': format_home(z, num, full=True),
                             'machine': format_machine(z, num), 'plate': format_plate(z, num),
                             'spokenPt': spoken(z, num, 'pt'), 'spokenKea': spoken(z, num, 'kea')})
    z3 = zone_by_ref('PA-011')  # João Vaz (official Chã de João Vaz), a 3-digit zone
    for num in (100, 214, 299):
        out['codes'].append({'home': format_home(z3, num), 'full': format_home(z3, num, full=True),
                             'machine': format_machine(z3, num), 'spokenPt': spoken(z3, num, 'pt'), 'spokenKea': spoken(z3, num, 'kea')})
    out['codes'].append({'home': format_home(z, 1234, structure=2), 'machine': format_machine(z, 1234, structure=2),
                         'note': 'second structure of the lote (a shop in the front wall, an annexe)'})
    # same name, different places: each code decodes alone to one zone
    for typed in ('Fazenda 12 34', 'Fazenda 20 50', 'Fazenda 24 34', 'Fazenda 29 50', 'Fazenda 31 00', 'Fazenda 32 50',
                  'Fazenda 34 50', 'fazenda 3450', 'Achadinha 15 00', 'Achadinha 25 10', 'Achadinha 11 00', 'Achadinha 12 50',
                  'Cutelo 22 00', 'Cutelo 10 50', 'Bela Vista 30 00', 'Bela Vista 55 50', 'Tarrafal 11 00', 'Tarrafal 15 00',
                  'Tarrafal 30 00', 'São Filipe 21 30', 'São Filipe 45 00'):
        r = parse(typed)
        zz, m = r['zone'], MUNI[r['zone']['key']]
        out['sameName'].append({'typed': typed, 'zone': zref(zz), 'officialName': zz['officialName'], 'municipality': m['name'], 'island': m['island'],
                                'near': zz.get('near'), 'machine': format_machine(zz, r['number']),
                                'check': _check(zz, r['number']), 'anchor': zz['anchor']})
    e = names()['fazenda']
    out['sameNameRegister'] = {'name': e['name'], 'index': e['index'], 'digits': e['digits'], 'blocks': e['blocks'], 'reserve': e['reserve']}
    for bad in ('Fazenda 52 29', 'Fazenda 12 34, Tarrafal'):
        try:
            r = parse(bad)
            out.setdefault('rejected', []).append({'typed': bad, 'zone': zref(r['zone']), 'contextMatches': r.get('contextMatches')})
        except ValueError as ex:
            out.setdefault('rejected', []).append({'typed': bad, 'error': str(ex)})
    # a slip that lands in another Fazenda, caught by the plate's check digit
    zp = zone_by_ref('PR-049')
    c = _check(zp, 2434)
    try:
        parse('Fazenda 34 34', check=c)
        slip = 'not caught'
    except ValueError as ex:
        slip = str(ex)
    out['crossZoneSlip'] = {'meant': 'Fazenda 24 34 (Praia), check ' + str(c), 'typed': 'Fazenda 34 34 + check ' + str(c),
                            'lands': owning_zone(names()['fazenda'], 3434) + ' (Tarrafal)', 'result': slip}
    # plate names (SPEC.md §3.7): (a) long official names -> plate name; the
    # official name typed decodes to the same zone; (b) zones whose official
    # names differ and whose plate names collide only after shortening share
    # one range and decode apart
    out['plateNames'] = []
    for ref in ('PR-024', 'PR-063', 'PR-003', 'SV-053', 'SV-009', 'PA-017', 'SL-023', 'PA-011'):
        zz = zone_by_ref(ref)
        num = 2130 if ref == 'PR-024' else zz['block'][0] + 30  # São Filipe 21 30: inside PR-024's block
        rec = {'zone': ref, 'officialName': zz['officialName'], 'plate': zz['name'], 'plateRule': zz['plateRule'],
               'needsCouncilChoice': zz['needsCouncilChoice'], 'home': format_home(zz, num), 'full': format_home(zz, num, full=True),
               'plateLayout': format_plate(zz, num), 'machine': format_machine(zz, num)}
        if zz.get('plateCandidates'):
            rec['plateCandidates'] = zz['plateCandidates']
            rec['plateReason'] = zz['plateReason']
        if zz.get('plateSource'):
            rec['plateSource'] = zz['plateSource']
        try:
            rec['officialTyped'] = zref(parse(f"{zz['officialName']} {group(num)}")['zone'])
        except ValueError as ex:
            rec['officialTyped'] = str(ex)
        out['plateNames'].append(rec)
    out['collideAfterShortening'] = []
    for ref, num in (('CR-078', 1234), ('TA-014', 3100), ('PA-005', 2050)):
        zz = zone_by_ref(ref)
        r = parse(f"{zz['name']} {group(num)}")
        m = MUNI[r['zone']['key']]
        out['collideAfterShortening'].append({'officialName': zz['officialName'], 'typed': f"{zz['name']} {group(num)}",
                                              'zone': zref(r['zone']), 'municipality': m['name'], 'island': m['island'],
                                              'machine': format_machine(r['zone'], num)})
    try:
        check_register_entry({'name': 'Lote Achada São Filipe'})
        out['overLimitRefused'] = 'accepted'
    except ValueError as ex:
        out['overLimitRefused'] = str(ex)
    for n in (40, 233, 234, 1971, 2933, 2934):
        d = digits_for(n)
        _, blocks, reserve = plan_name([('X', n)])
        out['arithmetic'].append({'lotes': n, 'needed': int(n * HEADROOM), 'digits': d, 'block': blocks['X'], 'reserve': reserve,
                                  'spacing': round((blocks['X'][1] - blocks['X'][0] + 1) / n, 2)})
    fz = [(b['zone'], zone_by_ref(b['zone'])['lotes']) for b in names()['fazenda']['blocks']]
    out['arithmetic'].append({'name': 'Fazenda', 'zones': fz, 'plan': plan_name(fz)})
    # registry toy: six lotes in Palmarejo's block, then "Add my home"
    toy = [('a', 14.9190, -23.5410), ('b', 14.9195, -23.5402), ('c', 14.9230, -23.5350),
           ('d', 14.9260, -23.5300), ('e', 14.9290, -23.5280), ('f', 14.9205, -23.5390)]
    vals = number_zone(toy, z['box'], z['block'])
    issued = {v: k for k, v in vals.items()}
    anchors = {k: (la, lo) for k, la, lo in toy}
    new = (14.9232, -23.5348)
    pv = insert_lote(issued, new[0], new[1], z['box'], anchors, _copy(names()['palmarejo']), 'PR-004')
    out['registryToy'] = {'lotes': [{'id': k, 'lat': la, 'lon': lo, 'hilbert': hilbert_of(la, lo, z['box']),
                                     'number': vals[k], 'home': format_home(z, vals[k]), 'machine': format_machine(z, vals[k])}
                                    for k, la, lo in toy],
                          'addMyHome': {'lat': new[0], 'lon': new[1], 'hilbert': hilbert_of(new[0], new[1], z['box']),
                                        'number': pv, 'home': format_home(z, pv), 'machine': format_machine(z, pv)}}
    # growth 1: Fazenda of Tarrafal (TA-022) is full; it takes the next free
    # unit of the name Fazenda; no other number changes
    ft = zone_by_ref('TA-022')
    ent = _copy(names()['fazenda'])
    lo, hi = ft['block']
    full = {v: f'x{v}' for v in range(lo, hi + 1)}
    anch = {f'x{v}': (15.27 + (v - lo) * 0.00002, -23.75) for v in range(lo, hi + 1)}
    ov = insert_lote(full, 15.271, -23.75, ft['box'], anch, ent, 'TA-022')
    out['overflow'] = {'zone': f'Fazenda TA-022 (Tarrafal), all {hi - lo + 1} numbers of its block {lo}-{hi} issued', 'newBlock': ent['blocks'][-1],
                       'newNumber': ov, 'home': format_home(ft, ov), 'machine': format_machine(ft, ov),
                       'decodes': zref(zone_by_ref(owning_zone(ent, ov)))}
    # growth 2: a new zone named Fazenda (40 lotes) gets its own block from the spare space
    nb = new_zone(ent, 'SV-901', 40)
    out['newZoneSameName'] = {'zone': 'SV-901 (hypothetical new Fazenda, São Vicente, 40 lotes)', 'block': nb}
    # growth 3: a 3-digit name whose 9 units are all taken opens 4 digits
    e3 = {'key': 'x', 'index': 1, 'digits': 3, 'blocks': [{'zone': 'PA-011', 'lo': 100, 'hi': 999}], 'reserve': [1000, 999]}
    out['nameOpensNextLength'] = {'before': '9 units of 100-999 used', 'newBlock': take_block(e3, 'PA-011')}
    # coverage mask: an official address is used as is, shown first, and the
    # lote has its home code too (its real code in the registry); a
    # handed-over N-Ways code resolves to the official address
    off = {'official': 'Rua Barragem de Figueira Gorda 142, Praia', 'home': 'Cidadela 10 88', 'machine': 'PR-0364-1088-2'}
    nw = {'home': format_home(z, 3283), 'machine': format_machine(z, 3283)}
    later = hand_over(nw, 'Rua Exemplo 12, Palmarejo, Praia (hypothetical future municipal number)')
    out['coverage'] = {'officialLote': {'record': off, 'resolves': resolve(off),
                                        'mask': coverage_of({'addr:street': 'Rua Barragem de Figueira Gorda', 'addr:housenumber': '142'}, 14.906469, -23.540511)},
                       'presumedOfficial': {'point': [14.91992, -23.50709], 'mask': coverage_of({}, 14.91992, -23.50709)},
                       'nwaysArea': {'point': [14.9235, -23.5340], 'mask': coverage_of({}, 14.9235, -23.5340), 'resolves': resolve(nw)},
                       'handOver': {'after': later, 'resolves': resolve(later)}}
    for name, lat, lon in REAL_POINTS:
        d = describe_point(lat, lon)
        d.update({'name': name, 'lat': lat, 'lon': lon})
        out['points'].append(d)
    return out


if __name__ == '__main__':
    if len(sys.argv) == 3:
        print(json.dumps(describe_point(float(sys.argv[1]), float(sys.argv[2])), ensure_ascii=False, indent=2))
        sys.exit(0)
    if len(sys.argv) == 2:
        r = parse(sys.argv[1])
        zz = r['zone']
        print(format_home(zz, r['number'], r['structure'], full=True), '=', format_machine(zz, r['number'], r['structure']))
        sys.exit(0)
    t = self_test()
    print('self-test ok;', json.dumps(t), file=sys.stderr)
    if t:
        print(f"same-name slips with the check digit: {t['crossZoneCaught']}/{t['crossZoneSlips']} caught; "
              f"{t['slipsToUnusedNumbers']} slips land on unused numbers; machine-form errors refused "
              f"{t['machineFormErrorsCaught']}/{t['machineFormErrors']}", file=sys.stderr)
    print(json.dumps(vectors(), ensure_ascii=False, indent=2))
