#!/usr/bin/env python3
"""National name register for Cabo Verde home codes (SPEC.md §3.4, §3.7, §5).

Two rules shape the register. A home code "Name NNNN" is unique in the whole
country on its own, without a municipality or island after it: people give
their code with no context, so the code alone must decide. And the name in
the code is a short PLATE NAME, at most 12 characters and 2 words
(engine/reference/plate_names.py), short enough for a plate, a form field and
one breath; the full map name stays as the zone's OFFICIAL name, printed
small on the card and plate, never required.

  0. Plate name (SPEC.md §3.7): plate_names.derive() on the official name,
     Portuguese word lists plus the Cabo Verde lists below; documented short
     forms (KNOWN, each with a source); a plate name never equals a
     municipality, municipal seat, island, regional capital or country
     (AVOID, minus the zone's own municipality and seat), where it would read
     as that place; doubtful cases are flagged needsCouncilChoice with up to
     3 candidates, the first used provisionally until the Câmara Municipal
     chooses. A numeral is spelt out ("África 70" -> "África Setenta"); when
     the spelt form is over the limit the zone is flagged.
  1. Group zones by the national key of the PLATE name (cv_engine.name_key:
     case, accents, punctuation, articles and Kriolu spellings folded). Issue
     order inside a name: municipality index, then zone index (both frozen).
  2. Each zone gets a block of whole units (100 numbers in 3- and 4-digit
     ranges, 1000 in 5-digit ranges) holding 3 x its lotes.
  3. The name's length is the shortest (3, 4, 5 digits) whose range holds all
     its blocks plus 2 free units for zones of that name created later.
  4. A name that cannot fit 5 digits is split once by a qualifier people
     already say (cv_engine.QUALIFIERS); no name of the register needs one.
  5. Name index: 1.. in alphabetical order of the key; it enters the check
     digit. New names take the next index.
  6. Aliases: the official name, the map's other spellings and the written
     numeral form decode to the plate name. An alias that is the key of
     another plate name, or that two plate names would claim, is dropped and
     listed in droppedAliases.
  7. Two zones of one municipality with the same plate name record their
     nearest differently named zone as `near`, for the card.

The register is frozen at first issue: blocks are never renumbered.

  python3 tools/build_names.py           rebuilds the register from engine/data/zones.json
                                         in memory and checks that it reproduces
                                         engine/data/names.json exactly
  python3 tools/build_names.py --write   writes it (refused once codes are issued)

Called from building_stats.py after build_zones.py as well.
"""
import collections
import json
import math
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'engine', 'reference'))
import cv_engine as E  # noqa: E402
import plate_names as P  # noqa: E402

LANG = 'pt'
NAMES_STATUS = ('The national name register: plate names, name keys and indices, and the first-issue blocks and reserves, built '
                'by tools/build_names.py and frozen at first issue (2026-10-19). registry/names.csv publishes the same register '
                'with every block issued since. Plate names flagged needsCouncilChoice are provisional until the Câmara '
                'Municipal chooses; their numbers do not change.')
# Documented short forms people already say (source for every entry).
KNOWN = {
    'Achada Santo António': ('ASA', ('Inforpress via Balai, "Praia: Tabanka de ASA com festividades de rua em homenagem ao santo '
                             'padroeiro" ("A Tabanka do bairro de Achada Santo António (ASA)"), '
                             'https://www.balai.cv/balai-kultural/praia-tabanka-de-asa-com-festividades-de-rua-em-homenagem-ao-santo-padroeiro/; '
                             'A Nação, 4 Feb 2026, https://www.anacao.cv/noticia/2026/02/04/praia-prisao-preventiva-para-o-principal-'
                             'suspeito-do-homicidio-de-jovem-de-17-anos-na-asa-em-2024/')),
    'Achada Grande Frente': ('AGF', ('Expresso das Ilhas, 9 Aug 2025, "CMP repudia roubo de plantas e promete levar à justiça os '
                             'infractores" ("na subida de Achada Grande Frente (AGF)"), https://expressodasilhas.cv/topico/achada-grande-frente')),
}
# "AGT" for Achada Grande Trás is in the map's alias list, but no published source was found:
# it stays an alias (tools/build_zones.py KNOWN_ALIASES), not the plate name.
GENERIC_EXTRA = ['condóminio', 'complexo', 'villagem', 'village']
# Cabo Verde words that are never a plate name on their own: adjectives and
# adverbs of place names (a trailing one is a qualifier: "Figueira Gorda" is
# not "Gorda", and never "Figueira" without the council).
WEAK_EXTRA = ['debaixo', 'fora', 'dentro', 'histórico', 'historico', 'antigo', 'antiga', 'colonial', 'paroquial', 'gorda', 'gordo',
              'formosa', 'formoso', 'torta', 'torto', 'queimada', 'queimado', 'curta', 'curto', 'muita', 'principal', 'pequenos',
              'pequenas', 'brancas', 'brancos', 'pretos', 'pretas', 'encostado', 'pelado', 'capado', 'selado', 'rachada', 'grosso',
              'grossa', 'pintado', 'salgadas', 'salgado', 'amargosa', 'selvagem', 'velhas', 'novas', 'boa', 'bom']
# Landform and settlement heads of Cabo Verde names, added to the Portuguese
# list (the first to go, never a plate name alone).
HEADS_EXTRA = {'curral', 'ribeirão', 'ribeirao', 'ribeirinha', 'ribeiro', 'covada', 'cabouco', 'cabouque', 'chão', 'chao', 'chā',
               'campo', 'cabeça', 'cabeca', 'horta', 'lombinho', 'fajã', 'faja', 'canto', 'casa', 'ilhéu', 'ilheu', 'ilha', 'ilhas',
               'estância', 'estancia', 'várzea', 'varzea', 'selada', 'quartel', 'recinto', 'cerrado', 'boca', 'ponte', 'tope',
               'pontinha', 'morrinho', 'montado'}
P.HEADS[LANG] = P.HEADS[LANG] | HEADS_EXTRA
ISLANDS = sorted({m['island'] for m in E.MUNI.values()} | {'Santa Luzia'})
# Names a plate name may not be on its own, because it would read as that
# place: the islands, the region's capitals and the Lusophone capitals, and
# the countries Cabo Verdean bairros are often named after (Brasil, Angola,
# Cuba...). The zone's own municipality and seat are allowed (avoid_for).
REGIONAL_CAPITALS = ['Dakar', 'Abidjan', 'Lomé', 'Cotonou', 'Accra', 'Lagos', 'Bamako', 'Ouagadougou', 'Conakry', 'Freetown',
                     'Bissau', 'Praia', 'Libreville', 'Yaoundé', 'Douala', 'Monrovia', 'Niamey', 'Nouakchott', 'Banjul', 'São Tomé',
                     'Lisboa', 'Santa Maria']  # Santa Maria: Sal's resort town, not a seat
COUNTRIES = ['Portugal', 'Espanha', 'França', 'Brasil', 'Angola', 'Cuba', 'Madeira', 'Genebra', 'Holanda', 'Itália']
# Automatic choices read by eye and refused: they go to the council, with the
# candidates given here when the automatic ones were wrong.
COUNCIL = {
    'Quatro Caminhos': ('the number word is part of the name ("Caminhos" alone is a road word)', None),
    'Colonato do Chão Bom': ('"Chão Bom" is the place; "Colonato" is a generic word', ['Chão Bom', 'Colonato']),
    'Achada do Chão Bom': ('"Chão Bom" is the place', ['Chão Bom']),
    "Fortim d'El-Rei": ('"El-Rei" alone is not said', None),
    'Ilha de Madeira': ('equals a well-known island elsewhere', None),
    'Pista de Aterragem': ('a generic description, not a name', None),
    'Campo de Aviaçāo': ('a generic description, not a name', None),
    'Atrás Cemitério': ('a generic description, not a name', None),
    'Lajedo dos Espargos': ('equals the seat of Sal: the council chooses', None),
    'Recinto Paroquial': ('a generic description, not a name', None),
    'Trás os Montes': ('"Montes" alone is a generic word', None),
    'Lombo Branco villagem/ Lomb Bronk': ('"villagem" is a generic word; two spellings given', ['Lombo Branco']),
}


def spell(name):
    return re.sub(r'\d+', lambda m: E._words(int(m.group()), 'pt').title(), name)


def avoid_for(z):
    own = {E.name_key(E.MUNI[z['key']]['name']), E.name_key(E.MUNI[z['key']]['seat'])}
    pool = [m['name'] for m in E.MUNI.values()] + [m['seat'] for m in E.MUNI.values()] + ISLANDS + REGIONAL_CAPITALS + COUNTRIES
    return {a for a in pool if E.name_key(a) not in own}


def _two_names(cleaned):
    """Exactly two content words and neither is a head or a weak word:
    "Figueira Gorda", "Bernardo Gomes", "Vista Pereira" - both are the name."""
    ws = P.content_words(cleaned, LANG)
    soft = {P.plain(x) for x in P.WEAK[LANG] | set(WEAK_EXTRA) | P.HEADS[LANG]}
    return len(ws) == 2 and all(P.plain(w) not in soft for w in ws)


def plate_for(z, freq):
    """-> plate record for one zone (see SPEC.md §3.7)."""
    official = z['officialName']
    kw = {'known': KNOWN, 'avoid': avoid_for(z), 'avoid_key': E.name_key, 'generic_extra': GENERIC_EXTRA, 'weak_extra': WEAK_EXTRA,
          'fold': E.name_key}
    spelt = spell(official)
    r = P.derive(spelt, LANG, freq, **kw)
    cl, _ = P.clean(spelt, LANG, GENERIC_EXTRA, WEAK_EXTRA, E.name_key)
    seats = {E.name_key(x) for m in E.MUNI.values() for x in (m['name'], m['seat'])}
    flag = None
    if re.search(r'\d', official) and not P.fits(cl, LANG):
        alt = P.derive(re.sub(r'\s*\d+\s*', ' ', official).strip(), LANG, freq, **kw)
        flag = ([alt['plate']] + [c for c in alt['candidates'] if c != alt['plate']],
                f'the numeral spelt out ({cl}) is {P.plate_length(cl)} characters')
    elif official in COUNCIL:
        why, cands = COUNCIL[official]
        flag = (cands or r['candidates'] or [r['plate']], why)
    elif r['rule'] == 'distinctive' and _two_names(cl):
        flag = (r['candidates'], 'no clear choice: both words are the name')
    elif r['rule'] == 'cleaned' and not P._strong(r['plate'], LANG, WEAK_EXTRA):
        inner = re.findall(r'\(([^)]*)\)', official)
        alt = P.derive(inner[0], LANG, freq, **kw) if inner else None
        flag = ([r['plate']] + ([alt['plate']] if alt and P.fits(alt['plate'], LANG) else []),
                'what is left after cleaning is only a weak word')
    elif r['rule'] in ('distinctive', 'cleaned', 'abbreviated') and E.name_key(cl) in seats and not r['needsCouncilChoice']:
        flag = ([r['plate']], 'the official name is a town: the council chooses its short form')
    if r['needsCouncilChoice']:
        r['rule'] = 'council'
    if flag:
        cands = []
        for c in flag[0]:
            if c and c not in cands:
                cands.append(c)
        r.update(needsCouncilChoice=True, rule='council', candidates=cands[:3], reason=flag[1])
        if cands:
            r['plate'] = cands[0]
    return r


def apply_plates(zones):
    """Step 0: name = plate name; officialName kept; aliases completed."""
    for z in zones:
        z.setdefault('officialName', z['name'])
    freq = P.word_freq([spell(z['officialName']) for z in zones], LANG)
    for z in zones:
        r = plate_for(z, freq)
        z['name'] = r['plate']
        z['plateRule'] = r['rule']
        z['needsCouncilChoice'] = bool(r['needsCouncilChoice'])
        for k in ('plateCandidates', 'plateReason', 'plateSource'):
            z.pop(k, None)
        if r['needsCouncilChoice']:
            z['plateCandidates'] = r['candidates']
            z['plateReason'] = r.get('reason')
        if r.get('source'):
            z['plateSource'] = r['source']
        al = [z['officialName']] + ([spell(z['officialName'])] if re.search(r'\d', z['officialName']) else []) + z.get('aliases', [])
        out = []
        for a in al:
            if E.name_key(a) != E.name_key(z['name']) and a not in out and a not in z.get('droppedAliases', []):
                out.append(a)
        z['aliases'] = out


def set_near(zones):
    """Step 7: the card hint for zones sharing a plate name in one municipality."""
    by = collections.defaultdict(list)
    for z in zones:
        by[(z['iso'], E.name_key(z['name']))].append(z)
    for z in zones:
        z['near'] = None
        if len(by[(z['iso'], E.name_key(z['name']))]) > 1:
            cos = math.cos(math.radians(z['anchor'][0]))
            others = [o for o in zones if o['iso'] == z['iso'] and E.name_key(o['name']) != E.name_key(z['name'])]
            if others:
                o = min(others, key=lambda o: ((o['anchor'][1] - z['anchor'][1]) * cos) ** 2 + (o['anchor'][0] - z['anchor'][0]) ** 2)
                z['near'] = o['name']


def build(zones, out_path):
    """zones: the zone dicts of build_zones (mutated: name, officialName,
    plate fields, aliases, near, nameKey, nameIndex, digits, block). Writes
    the register; returns stats."""
    before = plan_by(zones, lambda z: E.name_key(spell(z.get('officialName', z['name']))))
    apply_plates(zones)
    by_key = collections.defaultdict(list)
    for z in zones:
        q = E.QUALIFIERS.get(E.name_key(z['name']), {}).get(E.zref(z))
        if q:
            z['aliases'] = [z['name']] + z.get('aliases', [])
            z['name'] = q
        z['nameKey'] = E.name_key(z['name'])
        by_key[z['nameKey']].append(z)
    # step 6: aliases claimed by another plate name or by two of them are dropped
    claim = collections.defaultdict(set)
    for z in zones:
        for a in z['aliases']:
            claim[E.name_key(a)].add(z['nameKey'])
    dropped = []
    for k, owners in sorted(claim.items()):
        if (k in by_key and owners - {k}) or len(owners) > 1:
            names_ = sorted({by_key[o][0]['name'] for o in owners})
            for z in zones:
                bad = [a for a in z['aliases'] if E.name_key(a) == k]
                if bad:
                    z['aliases'] = [a for a in z['aliases'] if E.name_key(a) != k]
                    z['droppedAliases'] = sorted(set(z.get('droppedAliases', []) + bad))
            dropped.append({'alias': k, 'claimedBy': names_ + ([by_key[k][0]['name']] if k in by_key and by_key[k][0]['name'] not in names_ else []),
                            'why': 'the name of another plate' if k in by_key else 'claimed by two plate names'})
    set_near(zones)
    entries = []
    for i, key in enumerate(sorted(by_key), start=1):
        zs = sorted(by_key[key], key=lambda z: (E.MUNI[z['key']]['index'], z['index']))
        d, blocks, reserve = E.plan_name([(E.zref(z), z['lotes']) for z in zs])
        aliases = []
        for z in zs:
            for a in [z['name']] + z.get('aliases', []):
                if a != zs[0]['name'] and a not in aliases:
                    aliases.append(a)
        officials = []
        for z in zs:
            if z['officialName'] not in officials:
                officials.append(z['officialName'])
        e = {'key': key, 'index': i, 'name': zs[0]['name'], 'aliases': aliases, 'officialNames': officials,
             'needsCouncilChoice': any(z['needsCouncilChoice'] for z in zs), 'fits': P.fits(zs[0]['name'], LANG), 'digits': d,
             'blocks': [{'zone': E.zref(z), 'lo': blocks[E.zref(z)][0], 'hi': blocks[E.zref(z)][1]} for z in zs],
             'reserve': reserve, 'zones': len(zs), 'lotes': sum(z['lotes'] for z in zs)}
        entries.append(e)
        for z in zs:
            z['nameIndex'] = i
            z['digits'] = d
            z['block'] = blocks[E.zref(z)]
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'status': NAMES_STATUS,
                   'rules': 'tools/build_names.py; SPEC.md 3.4, 3.7 and 5', 'unit': {'3': 100, '4': 100, '5': 1000},
                   'plate': {'maxChars': P.MAX_CHARS, 'maxWords': P.MAX_WORDS, 'rules': 'engine/reference/plate_names.py'},
                   'reserveUnits': E.RESERVE_UNITS, 'qualifiers': E.QUALIFIERS, 'droppedAliases': dropped, 'names': entries},
                  f, ensure_ascii=False, indent=0)
    return stats(zones, entries, before, dropped)


def plan_by(zones, keyf):
    """Collisions and number lengths if zones were grouped by keyf (used for
    the 'before plate names' figures)."""
    by = collections.defaultdict(list)
    for z in zones:
        by[keyf(z)].append(z)
    digits = {}
    for zs in by.values():
        d, _, _ = E.plan_name([(E.zref(z), z['lotes']) for z in zs])
        for z in zs:
            digits[E.zref(z)] = d
    rep = {k: v for k, v in by.items() if len(v) > 1}
    big = max(rep.items(), key=lambda kv: (len(kv[1]), sum(z['lotes'] for z in kv[1])))
    return {'names': len(by), 'namesShared': len(rep), 'zonesInSharedNames': sum(len(v) for v in rep.values()),
            'mostZonesForOneName': {'key': big[0], 'zones': len(big[1])},
            'zonesByDigits': {str(k): v for k, v in sorted(collections.Counter(digits.values()).items())}}


def stats(zones, entries, before=None, dropped=()):
    rep = [e for e in entries if e['zones'] > 1]
    within = collections.Counter((z['iso'], z['nameKey']) for z in zones)
    zbd = collections.Counter(z['digits'] for z in zones)
    lbd = collections.Counter()
    for z in zones:
        lbd[z['digits']] += z['lotes']

    def used(e):
        return sum(b['hi'] - b['lo'] + 1 for b in e['blocks'])

    def code(z):
        return f"{z['name']} {E.group(z['block'][1])}"

    top = sorted(rep, key=lambda e: (-e['digits'], -used(e), e['key']))
    off = [z['officialName'] for z in zones]
    longest = max(zones, key=lambda z: (P.plate_length(code(z)), code(z)))
    longest_ok = max((z for z in zones if not z['needsCouncilChoice']), key=lambda z: (P.plate_length(code(z)), code(z)))
    flagged = [z for z in zones if z['needsCouncilChoice']]
    after_only = [e for e in rep if len({E.name_key(spell(o)) for o in e['officialNames']}) > 1]
    plates = {
        'zones': len(zones),
        'officialOverChars': sum(1 for n in off if P.plate_length(spell(n)) > P.MAX_CHARS),
        'officialOverWords': sum(1 for n in off if P.word_count(spell(n), LANG) > P.MAX_WORDS),
        'officialOverLimit': sum(1 for n in off if not P.fits(spell(n), LANG)),
        'byRule': dict(collections.Counter(z['plateRule'] for z in zones).most_common()),
        'needsCouncilChoice': len(flagged),
        'flaggedStillOverLimit': sum(1 for z in flagged if not P.fits(z['name'], LANG)),
        'stillOverLimit': sum(1 for z in zones if not P.fits(z['name'], LANG)),
        'known': [{'official': z['officialName'], 'plate': z['name'], 'source': z['plateSource']} for z in zones if z.get('plateSource')],
        'namesSharedOnlyAfterShortening': len(after_only),
        'droppedAliases': len(dropped),
        'longestCode': {'code': code(longest), 'chars': P.plate_length(code(longest)), 'official': longest['officialName'],
                        'needsCouncilChoice': longest['needsCouncilChoice']},
        'longestCodeNotFlagged': {'code': code(longest_ok), 'chars': P.plate_length(code(longest_ok)), 'official': longest_ok['officialName']},
        'before': before,
    }
    return {
        'names': len(entries),
        'namesRepeated': len(rep),
        'zonesWithRepeatedNames': sum(e['zones'] for e in rep),
        'mostZonesForOneName': [{'name': e['name'], 'zones': e['zones']} for e in sorted(rep, key=lambda e: (-e['zones'], e['key']))[:4]],
        'zonesSharingANameInsideAMunicipality': sum(v for v in within.values() if v > 1),
        'repeatedNamesByDigits': {str(k): v for k, v in sorted(collections.Counter(e['digits'] for e in rep).items())},
        'zonesByDigits': {str(k): v for k, v in sorted(zbd.items())},
        'lotesByDigits': {str(k): v for k, v in sorted(lbd.items())},
        'qualifiersNeeded': len(E.QUALIFIERS),
        'plateNames': plates,
        'largestSharedRanges': [{'name': e['name'], 'zones': e['zones'], 'lotes': e['lotes'], 'digits': e['digits'],
                                 'numbersInBlocks': used(e), 'reserve': e['reserve'],
                                 'blocks': e['blocks']} for e in top[:6]],
    }


def issued():
    """Whether codes have been issued (the published registry holds codes):
    from then on the register is frozen."""
    p = os.path.join(REPO, 'registry', 'MANIFEST.json')
    if not os.path.exists(p):
        return False
    with open(p, encoding='utf-8') as f:
        return json.load(f).get('codes', 0) > 0


def main():
    import argparse
    import tempfile
    ap = argparse.ArgumentParser(description='Rebuild the national name register and check it, or write it before first issue.')
    ap.add_argument('--write', action='store_true', help='write engine/data/names.json and the name fields of zones.json')
    a = ap.parse_args()
    zp = os.path.join(REPO, 'engine', 'data', 'zones.json')
    np_ = os.path.join(REPO, 'engine', 'data', 'names.json')
    with open(zp, encoding='utf-8') as f:
        doc = json.load(f)
    if a.write:
        if issued():
            sys.exit('codes are issued: the register is frozen and is not rewritten (SPEC.md §3.4)')
        st = build(doc['zones'], np_)
        with open(zp, 'w', encoding='utf-8') as f:
            f.write(json.dumps(doc, ensure_ascii=False, indent=0))
        sp = os.path.join(REPO, 'model', 'building-stats.json')
        with open(sp, encoding='utf-8') as f:
            bs = json.load(f)
        bs['zones'].update({k: v for k, v in st.items() if k in ('zonesByDigits', 'lotesByDigits')})
        bs['names'] = st
        with open(sp, 'w', encoding='utf-8') as f:
            json.dump(bs, f, ensure_ascii=False, indent=1)
    else:
        before = json.dumps(doc, ensure_ascii=False, sort_keys=True)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, 'names.json')
            st = build(doc['zones'], out)
            with open(out, encoding='utf-8') as f:
                rebuilt = json.load(f)
        with open(np_, encoding='utf-8') as f:
            frozen = json.load(f)
        same_names = rebuilt['names'] == frozen['names']
        same_zones = json.dumps(doc, ensure_ascii=False, sort_keys=True) == before
        print(f"rebuilt register: {len(rebuilt['names'])} names; names.json reproduced: {same_names}; "
              f"zones.json reproduced: {same_zones}")
        if not (same_names and same_zones):
            sys.exit(1)
    print(json.dumps({k: v for k, v in st.items() if k not in ('largestSharedRanges', 'plateNames')}, ensure_ascii=False))
    print(json.dumps({k: v for k, v in st['plateNames'].items() if k != 'known'}, ensure_ascii=False))
    for e in st['largestSharedRanges']:
        print(e['name'], e['zones'], 'zones', e['lotes'], 'lotes', e['digits'], 'digits', e['numbersInBlocks'], 'numbers', e['blocks'])


if __name__ == '__main__':
    main()
