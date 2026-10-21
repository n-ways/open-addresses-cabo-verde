#!/usr/bin/env python3
"""Tests for the Cabo Verde reference engine (standard library only).

  python3 engine/reference/test_cv.py
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cv_engine as E  # noqa: E402

ENGINE = os.path.dirname(HERE)


class SelfTest(unittest.TestCase):
    def test_self_test(self):
        t = E.self_test()
        self.assertEqual(t['crossZoneCaught'], t['crossZoneSlips'])
        self.assertEqual(t['machineFormErrorsCaught'], t['machineFormErrors'])
        self.assertEqual(t['zonesDecoded'], len(E.zones()))

    def test_vectors_reproduce(self):
        want = E._json(os.path.join(ENGINE, 'test-vectors.json'))
        got = json.loads(json.dumps(E.vectors(), ensure_ascii=False))
        self.assertEqual(got, want)


class Border(unittest.TestCase):
    """The border decides (SPEC.md §3.2): no code more than 300 m outside it."""

    def test_shipped_outline(self):
        path = os.path.join(ENGINE, 'data', 'border.geojson')
        self.assertLess(os.path.getsize(path), 1 << 20)
        f = E._json(path)
        self.assertEqual(f['properties']['borderM'], E.BORDER_M)
        self.assertLess(f['properties']['deviationM'], 60)

    def test_inside_and_far_outside(self):
        self.assertEqual(E.border_distance_m(14.9177, -23.5372), 0.0)  # Praia
        self.assertTrue(E.within_border(14.9177, -23.5372))
        self.assertTrue(E.within_border(16.8870, -24.9900))            # Mindelo
        self.assertFalse(E.within_border(15.5, -27.0))                 # open sea, ~150 km beyond
        self.assertGreater(E.border_distance_m(15.5, -27.0), 100000)

    def _out(self, metres):
        """A point this far outside the middle of the outline's first edge."""
        polys, _ = E.border_outline()
        (x0, y0), (x1, y1) = polys[0][0][0], polys[0][0][1]
        lat, lon = (y0 + y1) / 2, (x0 + x1) / 2
        ky, kx = E._metres_per_degree(lat)
        ex, ey = (x1 - x0) * kx, (y1 - y0) * ky
        n = (ex * ex + ey * ey) ** 0.5
        for sgn in (1, -1):
            p = (lat + sgn * ex / n * metres / ky, lon - sgn * ey / n * metres / kx)
            if E.border_distance_m(*p) > 0:
                return p
        raise AssertionError('no outward side')

    def test_the_300_m_margin(self):
        _, dev = E.border_outline()
        polys = E.border_outline()[0]
        lat, lon = self._out(100)
        self.assertAlmostEqual(E.border_distance_m(lat, lon), 100, delta=1)
        self.assertTrue(E.within_border(lat, lon))
        # with the shipped outline the simplification's deviation comes off the 300 m
        lat, lon = self._out(300 - dev + 5)
        self.assertFalse(E.within_border(lat, lon))
        self.assertTrue(E.within_border(lat, lon, polys))  # a full outline counts the whole 300 m
        lat, lon = self._out(320)
        self.assertFalse(E.within_border(lat, lon, polys))


class NationalNames(unittest.TestCase):
    """'Name NNNN' is unique in the country on its own (SPEC.md §3.4)."""

    def test_same_name_two_places(self):
        a, b = E.parse('Fazenda 24 34'), E.parse('Fazenda 34 50')
        self.assertEqual(E.zref(a['zone']), 'PR-049')   # Praia
        self.assertEqual(E.zref(b['zone']), 'TA-022')   # Tarrafal
        self.assertNotEqual(a['zone']['anchor'], b['zone']['anchor'])

    def test_same_name_same_municipality(self):
        # three Achadinhas in Santa Catarina: no bracket, the number tells them apart
        refs = {E.zref(E.parse(f'Achadinha {n}')['zone']) for n in (1100, 1250, 1350)}
        self.assertEqual(refs, {'CA-028', 'CA-144', 'CA-194'})

    def test_spellings_fold(self):
        self.assertIs(E.names()[E.name_key('Chã de Baixo')], E.names()[E.name_key('Chã Baixo')])
        self.assertEqual(E.zref(E.parse('ACHADA STO ANTÓNIO 87 63')['zone']), 'PR-063')
        self.assertEqual(E.zref(E.parse('ASA 8763')['zone']), 'PR-063')
        self.assertEqual(E.zref(E.parse('Achada Santo António 87 63')['zone']), 'PR-063')

    def test_unused_number_refused(self):
        with self.assertRaises(ValueError):
            E.parse('Fazenda 52 29')  # in the reserve of Fazenda: no home

    def test_context_never_chooses(self):
        r = E.parse('Fazenda 24 34, Tarrafal')
        self.assertEqual(E.zref(r['zone']), 'PR-049')
        self.assertFalse(r['contextMatches'])
        self.assertTrue(E.parse('Fazenda 24 34, Praia')['contextMatches'])

    def test_cross_zone_slip_caught_by_check(self):
        c = E.check_digit(E.parse('Fazenda 24 34')['zone']['nameIndex'], 2434)
        with self.assertRaises(ValueError):
            E.parse('Fazenda 34 34', check=c)   # lands in Tarrafal's block
        self.assertTrue(E.parse('Fazenda 24 34', check=c)['checked'])

    def test_machine_form_round_trip_and_key(self):
        z = E.zone_by_ref('TA-022')
        m = E.format_machine(z, 3450)
        self.assertEqual(E.zref(E.parse(m)['zone']), 'TA-022')
        with self.assertRaises(ValueError):
            E.parse('PR' + m[2:])  # right name and number, wrong municipality

    def test_no_digits_in_names(self):
        for e in {id(v): v for v in E.names().values()}.values():
            self.assertNotRegex(e['name'], r'\d')

    def test_frozen_blocks_on_growth(self):
        ent = json.loads(json.dumps(E.names()['fazenda']))
        before = [dict(b) for b in ent['blocks']]
        E.new_zone(ent, 'SV-901', 40)
        E.take_block(ent, 'TA-022')
        self.assertEqual(ent['blocks'][:len(before)], before)
        spans = sorted((b['lo'], b['hi']) for b in ent['blocks'])
        self.assertTrue(all(spans[i][1] < spans[i + 1][0] for i in range(len(spans) - 1)))

    def test_max_five_digits(self):
        for e in {id(v): v for v in E.names().values()}.values():
            self.assertLessEqual(e['digits'], E.MAX_DIGITS)


class PlateNames(unittest.TestCase):
    """The name in the code is at most 12 characters and 2 words; the official
    name is kept and decodes too (SPEC.md §3.7)."""

    def test_long_official_name_to_plate(self):
        z = E.parse('São Filipe 21 30')['zone']
        self.assertEqual((E.zref(z), z['officialName']), ('PR-024', 'Lote Achada São Filipe'))
        self.assertTrue(z['needsCouncilChoice'])          # equals Fogo's São Filipe: the council confirms
        self.assertEqual(E.parse('Lote Achada São Filipe 21 30')['zone'], z)
        j = E.parse('Julião 24 30')['zone']
        self.assertEqual(j['officialName'], 'Casa Para Todos-Ribeira de Julião')
        self.assertEqual(E.parse('Casa Para Todos-Ribeira de Julião 24 30')['zone'], j)

    def test_collide_only_after_shortening(self):
        # Achada Fazenda (Santa Cruz) and Lugar de Fazenda (Tarrafal) are both
        # "Fazenda" now: one range, and each number decodes to its own place
        a, b = E.parse('Fazenda 12 34')['zone'], E.parse('Fazenda 31 00')['zone']
        self.assertEqual((a['officialName'], E.zref(a)), ('Achada Fazenda', 'CR-078'))
        self.assertEqual((b['officialName'], E.zref(b)), ('Lugar de Fazenda', 'TA-014'))
        self.assertEqual(a['nameIndex'], b['nameIndex'])

    def test_every_plate_fits_or_waits_for_council(self):
        for e in {id(v): v for v in E.names().values()}.values():
            self.assertTrue(E.plate_ok(e['name']) or e['needsCouncilChoice'], e['name'])
        for z in E.zones():
            if not z['needsCouncilChoice']:
                self.assertTrue(E.plate_ok(z['name']), z['name'])

    def test_over_long_name_refused(self):
        with self.assertRaises(ValueError):
            E.check_register_entry({'name': 'Lote Achada São Filipe'})

    def test_numeral_spelt_flagged(self):
        z = next(z for z in E.zones() if z['officialName'] == 'África 70')
        self.assertTrue(z['needsCouncilChoice'])           # África Setenta is 14 characters
        self.assertEqual(E.zref(E.parse(f"África 70 {z['block'][0]}")['zone']), E.zref(z))


class RegistryVectors(unittest.TestCase):
    """Real issued codes (engine/test-vectors-registry.json, from registry/ by
    tools/registry_vectors.py): every form comes from the register alone."""

    @classmethod
    def setUpClass(cls):
        cls.v = E._json(os.path.join(ENGINE, 'test-vectors-registry.json'))
        E.use_published_registry(os.path.join(os.path.dirname(ENGINE), 'registry'))

    @classmethod
    def tearDownClass(cls):
        E.use_register(E._json(os.path.join(E.DATA, 'zones.json'))['zones'], E._json(os.path.join(E.DATA, 'names.json'))['names'])

    def test_codes_decode_and_format(self):
        for s in self.v['sample'] + self.v['sameName'] + self.v['official']:
            r = E.parse(s['home'])
            z, n = r['zone'], r['number']
            self.assertEqual((E.zref(z), E.format_machine(z, n)), (s['zone'], s['machine']), s['home'])
            self.assertEqual(E.check_digit(z['nameIndex'], n), s['check'])
            self.assertEqual(E.format_plate(z, n), s['plate'])
            self.assertEqual(E.format_home(z, n, full=True), s['full'])
            self.assertEqual((E.spoken(z, n, 'pt'), E.spoken(z, n, 'kea')), (s['spokenPt'], s['spokenKea']))
            self.assertEqual(E.olc_encode(s['entrance'][0], s['entrance'][1], 11), s['plusCode'])
            self.assertEqual(E.zref(E.parse(s['machine'])['zone']), s['zone'])

    def test_same_name_codes_are_distinct_places(self):
        by = {}
        for s in self.v['sameName']:
            by.setdefault(s['name'], set()).add(s['zone'])
        for name, refs in by.items():
            self.assertGreater(len(refs), 1, name)

    def test_insertion(self):
        i = self.v['insertion']
        z = E.zone_by_ref(i['zone'])
        issued = {n: m for n, m, _ in i['issued']}
        anchors = {m: tuple(a) for _, m, a in i['issued']}
        entry = json.loads(json.dumps(E.names()[z['nameKey']]))
        n = E.insert_lote(issued, i['point'][0], i['point'][1], i['box'], anchors, entry, i['zone'])
        self.assertEqual((n, E.format_home(z, n), E.format_machine(z, n)), (i['number'], i['home'], i['machine']))
        self.assertNotIn(n, issued)


class FrozenRegister(unittest.TestCase):
    def test_register_reproduces_from_its_rules(self):
        import subprocess
        tool = os.path.join(os.path.dirname(ENGINE), 'tools', 'build_names.py')
        r = subprocess.run([sys.executable, tool], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_register_matches_published_registry(self):
        import csv
        reg = os.path.join(os.path.dirname(ENGINE), 'registry')
        with open(os.path.join(reg, 'names.csv'), encoding='utf-8', newline='') as f:
            pub = {int(r['name_index']): r for r in csv.DictReader(f)}
        for e in {id(v): v for v in E.names().values()}.values():
            p = pub[e['index']]
            self.assertEqual((p['name_key'], p['plate_name']), (e['key'], e['name']))
            first = ' '.join(f"{b['zone']}:{b['lo']}-{b['hi']}" for b in e['blocks'])
            self.assertTrue(p['blocks'].startswith(first), e['key'])  # blocks issued since come after


if __name__ == '__main__':
    unittest.main(verbosity=1)
