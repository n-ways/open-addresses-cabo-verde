"""Tests of the registry server on a real test registry (every code of Brava).

  python3 -m unittest server.test_server -v
"""
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

from server import api, geo, store
from server import engine as E
from server.service import Service

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, 'testdata', 'registry')
PARITY = os.path.join(HERE, 'testdata', 'parity.json')
KEY = 'test-issuer-key'


def quiet(*_):
    pass


class Server:
    """A server on a free port, in a thread."""

    def __init__(self, db, keys=(KEY,), per_day=10000):
        self.svc = Service(db, issue_keys=keys, issue_per_day=per_day)
        self.httpd = api.serve(self.svc, '127.0.0.1', 0, ['*'])
        self.httpd.RequestHandlerClass.log_message = quiet
        self.url = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.svc.close()

    def call(self, method, path, body=None, key=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(self.url + path, data=data, method=method)
        if data is not None:
            req.add_header('Content-Type', 'application/json')
        if key:
            req.add_header('Authorization', 'Bearer ' + key)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read())
            finally:
                e.close()


def fresh_db(tmp, name='t.sqlite'):
    db = os.path.join(tmp, name)
    store.import_registry(FIXTURE, db, log=quiet)
    return db


def export(db, out):
    con = store.connect(db)
    try:
        return store.export_registry(con, out)
    finally:
        con.close()


def q(s):
    return urllib.request.quote(s)


class ImportExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_round_trip_is_byte_identical(self):
        db = fresh_db(self.tmp)
        out = os.path.join(self.tmp, 'out')
        export(db, out)
        with open(os.path.join(FIXTURE, 'MANIFEST.json'), encoding='utf-8') as f:
            man = json.load(f)
        for name, sha in man['sha256'].items():
            p = os.path.join(out, name)
            opener = open if os.path.exists(p) else gzip.open
            with opener(p if os.path.exists(p) else p + '.gz', 'rb') as f:
                data = f.read()
            self.assertEqual(hashlib.sha256(data).hexdigest(), sha, name)
        with open(os.path.join(out, 'MANIFEST.json'), encoding='utf-8') as f:
            self.assertEqual(json.load(f), man)

    def test_rerun_is_safe(self):
        db = fresh_db(self.tmp)
        r = store.import_registry(FIXTURE, db, log=quiet)
        self.assertEqual(r['codes'], 2900)
        con = sqlite3.connect(db)
        self.assertEqual(con.execute('SELECT count(*) FROM codes').fetchone()[0], 2900)
        con.close()

    def _copy_fixture(self):
        d = os.path.join(self.tmp, 'reg')
        shutil.copytree(FIXTURE, d)
        return d

    def test_refuses_a_changed_file(self):
        d = self._copy_fixture()
        p = os.path.join(d, 'BR.csv.gz')
        with gzip.open(p) as f:
            data = f.read().replace(b'Baleia 10 02', b'Baleia 10 03', 1)
        with gzip.open(p, 'wb') as f:
            f.write(data)
        with self.assertRaisesRegex(store.RegistryError, 'SHA-256'):
            store.import_registry(d, os.path.join(self.tmp, 'x.sqlite'), log=quiet)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, 'x.sqlite')))

    def test_refuses_wrong_totals(self):
        d = self._copy_fixture()
        p = os.path.join(d, 'MANIFEST.json')
        with open(p, encoding='utf-8') as f:
            man = json.load(f)
        man['codes'] += 1
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(man, f)
        with self.assertRaisesRegex(store.RegistryError, 'manifest says'):
            store.import_registry(d, os.path.join(self.tmp, 'x.sqlite'), log=quiet)

    def test_refuses_a_missing_file(self):
        d = self._copy_fixture()
        os.remove(os.path.join(d, 'structures', 'BR.csv.gz'))
        with self.assertRaisesRegex(store.RegistryError, 'missing'):
            store.import_registry(d, os.path.join(self.tmp, 'x.sqlite'), log=quiet)

    def test_keeps_local_changes_unless_told(self):
        db = fresh_db(self.tmp)
        svc = Service(db, issue_keys=[KEY])
        svc.change('BR-0117-1002-4', {'status': 'confirmed'}, KEY)
        svc.close()
        with self.assertRaisesRegex(store.RegistryError, 'change'):
            store.import_registry(FIXTURE, db, log=quiet)
        store.import_registry(FIXTURE, db, discard_local=True, log=quiet)
        svc = Service(db)
        self.assertEqual(svc.get_card('BR-0117-1002-4')['status'], 'provisional')
        svc.close()

    def test_grid_index_gives_the_same_answers(self):
        db = fresh_db(self.tmp)
        orig = store.has_rtree
        store.has_rtree = lambda: False
        try:
            gdb = fresh_db(self.tmp, 'grid.sqlite')
        finally:
            store.has_rtree = orig
        a, b = Service(db), Service(gdb)
        self.assertEqual(b.meta('spatial'), 'grid')
        for lat, lng in ((14.8474514, -24.6824), (14.8682, -24.6994), (14.85, -24.70)):
            self.assertEqual(a.at(lat, lng), b.at(lat, lng))
            self.assertEqual(a.near(lat, lng, 200, 50), b.near(lat, lng, 200, 50))
        a.close()
        b.close()


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.db = fresh_db(cls.tmp)
        con = sqlite3.connect(cls.db)  # one official address, as in the full registry's Praia and Mindelo
        con.execute("UPDATE codes SET official_address = 'Rua da Saúde 7', coverage = 'official' WHERE machine = 'BR-0117-1006-2'")
        con.commit()
        con.close()
        cls.s = Server(cls.db)
        cls.ro = Server(cls.db, keys=())

    @classmethod
    def tearDownClass(cls):
        cls.s.close()
        cls.ro.close()
        shutil.rmtree(cls.tmp)

    def get(self, path, code=200, err=None, srv=None):
        status, body = (srv or self.s).call('GET', path)
        self.assertEqual(status, code, body)
        if err:
            self.assertEqual(set(body), {'error'})
            self.assertEqual(body['error']['code'], err)
            self.assertTrue(body['error']['message'])
        return body

    def test_health_and_info(self):
        h = self.get('/v1/health')
        self.assertEqual((h['status'], h['country'], h['codes']), ('ok', 'CV', 2900))
        i = self.get('/v1/info')
        self.assertEqual(i['counts']['codes'], 2900)
        self.assertEqual(len(i['zones']), 22)
        self.assertEqual(i['licences']['data'], 'ODbL-1.0')
        self.assertTrue(i['issuing'])
        self.assertFalse(self.get('/v1/info', srv=self.ro)['issuing'])

    def test_card(self):
        c = self.get('/v1/codes/BR-0117-1002-4')
        self.assertEqual((c['home'], c['check'], c['municipality'], c['island']), ('Baleia 10 02', 4, 'Brava', 'Brava'))
        self.assertEqual(c['postcode']['value'], '9110')
        self.assertEqual(c['written'], {'big': 'Baleia 10 02', 'small': 'Brava · Brava', 'machine': 'BR-0117-1002-4'})
        self.assertEqual(c['spoken'], 'Baleia, dez, zero dois')
        self.assertEqual(c['plusCode'], '796QR8W9+X2G')
        self.assertEqual(c['registry']['entrance_lat'], '14.8474370')
        self.assertEqual(set(c['registry']), set(store.CODE_COLS))
        self.assertEqual(c['structures'][0]['id'], 'nw:d16e12fc2d6d')
        self.assertEqual(c['lote'], {'use': 'residencial.moradia', 'kind': 'um_edificio', 'structures': 1,
                                     'floorAreaM2': 17.6, 'enclosed': False})
        self.get('/v1/codes/BR-0117-1002-5', 404, 'unknown_code')

    def test_find_remembered_form_as_typed(self):
        for typed in ('Baleia 10 02', 'baleia 1002', 'BALEIA   10 02', 'Baléia 10 02', '  baleia 10 02  '):
            b = self.get('/v1/find?q=' + q(typed))
            self.assertEqual((b['kind'], b['matches'][0]['machine']), ('home', 'BR-0117-1002-4'), typed)

    def test_find_machine_official_and_spot(self):
        self.assertEqual(self.get('/v1/find?q=br-0117-1002-4')['matches'][0]['home'], 'Baleia 10 02')
        b = self.get('/v1/find?q=' + q('rua da saude 7'))
        self.assertEqual((b['kind'], b['matches'][0]['machine']), ('official', 'BR-0117-1006-2'))
        b = self.get('/v1/find?q=' + q('796QR8W9+X2G'))
        self.assertEqual((b['kind'], b['spot']['at']['code']['machine']), ('spot', 'BR-0117-1002-4'))

    def test_find_errors(self):
        self.get('/v1/find?q=BR-0117-1002-5', 422, 'check_digit')
        self.get('/v1/find?q=' + q('Nowhereville 1234'), 404, 'unknown_name')
        self.get('/v1/find?q=' + q('Baleia 10 03'), 404, 'not_issued')
        self.get('/v1/find?q=' + q('Baleia 52 00'), 404, 'unknown_code')
        self.get('/v1/find?q=' + q('just words'), 400, 'bad_format')
        self.get('/v1/find', 400, 'bad_request')

    def test_at(self):
        b = self.get('/v1/at?lat=14.8474514&lng=-24.6824')  # inside the footprint of Baleia 10 02
        self.assertEqual((b['status'], b['code']['machine'], b['distanceM']), ('found', 'BR-0117-1002-4', 0))
        self.assertEqual(b['area']['key'], 'BR')
        b = self.get('/v1/at?lat=14.85&lng=-24.70')
        self.assertEqual((b['status'], b['area']['name'], b['canIssue']), ('none', 'Brava', True))
        self.assertEqual(self.get('/v1/at?lat=14.80&lng=-24.80')['status'], 'outside')
        self.get('/v1/at?lat=x&lng=1', 400, 'bad_request')
        self.get('/v1/at?lat=95&lng=1', 400, 'bad_request')

    def test_near(self):
        b = self.get('/v1/near?lat=14.8474&lng=-24.6824&radius=300&limit=5')
        self.assertEqual(len(b['codes']), 5)
        d = [c['distanceM'] for c in b['codes']]
        self.assertEqual(d, sorted(d))
        self.assertEqual(b['codes'][0]['machine'], 'BR-0117-1002-4')
        self.get('/v1/near?lat=14.8474&lng=-24.6824&radius=501', 400, 'bad_request')
        self.get('/v1/near?lat=14.8474&lng=-24.6824&limit=101', 400, 'bad_request')

    def test_verify(self):
        v = self.get('/v1/verify?code=BR-0117-1002-4')
        self.assertEqual((v['syntax'], v['checkDigit'], v['issued'], v['status']), (True, True, True, 'provisional'))
        v = self.get('/v1/verify?code=BR-0117-1002-5')
        self.assertEqual((v['checkDigit'], v['issued']), (False, False))
        c = __import__('server.engine', fromlist=['x']).check_digit(117, 1003)
        v = self.get(f'/v1/verify?code=BR-0117-1003-{c}')
        self.assertEqual((v['checkDigit'], v['issued']), (True, False))
        self.assertFalse(self.get('/v1/verify?code=hello')['syntax'])
        self.assertFalse(self.get('/v1/verify?code=XX-0117-1002-4')['syntax'])
        self.get('/v1/verify', 400, 'bad_request')

    def test_spot(self):
        s = self.get('/v1/spot?lat=14.847437&lng=-24.6824147')
        self.assertEqual((s['code'], s['municipality']), ('796QR8W9+X2G', 'Brava'))
        self.assertTrue(s['short'].endswith('Nova Sintra'))
        self.get('/v1/spot?lat=14.80&lng=-24.80', 422, 'outside')
        d = self.get('/v1/spot/decode?code=' + q('796QR8W9+X2G'))
        self.assertEqual(d['at']['code']['machine'], 'BR-0117-1002-4')
        d = self.get('/v1/spot/decode?code=' + q(s['short']))
        self.assertEqual(d['code'], '796QR8W9+X2')
        self.get('/v1/spot/decode?code=' + q('R8W9+X2 Atlantis'), 404, 'unknown_place')
        self.get('/v1/spot/decode?code=hello', 400, 'bad_format')
        self.get('/v1/spot/decode', 400, 'bad_request')

    def test_zones_and_areas(self):
        z = self.get('/v1/zones')['zones']
        self.assertEqual([x['key'] for x in z][:2], ['BR', 'BV'])
        self.assertEqual(z[0]['codes'], 2900)
        br = self.get('/v1/zones/br')
        self.assertEqual(len(br['areaList']), 36)
        self.get('/v1/zones/XX', 404, 'unknown_zone')
        a = self.get('/v1/areas/BR-034')
        self.assertEqual((a['plateName'], a['blocks'], a['codes']), ('Belem', [{'lo': 100, 'hi': 199}], 18))
        self.get('/v1/areas/BR-999', 404, 'unknown_area')
        f = self.get('/v1/areas?name=' + q('Achada do Poio Preto'))  # an official name, kept as an alias
        self.assertIn('BR-002', [x['id'] for x in f['areas']])
        f = self.get('/v1/areas?name=fazenda')
        self.assertEqual(len({x['nameIndex'] for x in f['areas']}), 1)
        self.get('/v1/areas', 400, 'bad_request')

    def test_paged_codes(self):
        p1 = self.get('/v1/zones/BR/codes?limit=3')
        self.assertEqual(len(p1['codes']), 3)
        p2 = self.get('/v1/zones/BR/codes?limit=3&after=' + p1['next'])
        self.assertGreater(p2['codes'][0]['machine'], p1['codes'][-1]['machine'])
        seen, after = 0, ''
        while True:
            p = self.get(f'/v1/zones/BR/codes?limit=1000&after={after}')
            seen += len(p['codes'])
            if not p['next']:
                break
            after = p['next']
        self.assertEqual(seen, 2900)
        self.get('/v1/zones/BR/codes?limit=0', 400, 'bad_request')

    def test_routing_errors(self):
        self.get('/v1/nothing', 404, 'not_found')
        status, body = self.s.call('DELETE', '/v1/codes/BR-0117-1002-4')
        self.assertEqual((status, body['error']['code']), (405, 'method_not_allowed'))


class Issue(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = fresh_db(self.tmp)
        self.s = Server(self.db)

    def tearDown(self):
        self.s.close()
        shutil.rmtree(self.tmp)

    def post(self, body, code, err=None, key=KEY, srv=None):
        status, b = (srv or self.s).call('POST', '/v1/codes', body, key=key)
        self.assertEqual(status, code, b)
        if err:
            self.assertEqual(b['error']['code'], err)
        return b

    def test_parity_with_the_issuer(self):
        with open(PARITY, encoding='utf-8') as f:
            parity = json.load(f)
        n = 0
        for case in parity['cases']:
            for want in case['issues']:
                c = self.post(want['in'], 201)
                self.assertEqual((c['area']['id'], int(c['registry']['number']), c['machine'], c['home']),
                                 (want['zone'], want['number'], want['machine'], want['home']), case['name'])
                for k, v in want['lote'].items():
                    self.assertEqual(c['lote'][k], v, (want['machine'], k))
                if 'structure' in want:
                    for k, v in want['structure'].items():
                        self.assertEqual(c['structures'][0][k], v, (want['machine'], k))
                self.assertEqual((c['status'], c['issued']), ('provisional', 'on-demand'))
                n += 1
        self.assertEqual(n, 107)
        # the full Belem block took the next free unit of its name: an extension block
        a = self.s.svc.area('BR-034')
        self.assertEqual(a['blocks'], [{'lo': 100, 'hi': 199}, {'lo': 800, 'hi': 899}])
        for idx, blocks in parity['blocks'].items():
            self.assertEqual(__import__('server.engine', fromlist=['x']).names_by_index()[int(idx)]['blocks'], blocks)
        # the new codes and the new block are in the export, and the export imports again
        out = os.path.join(self.tmp, 'out')
        r = export(self.db, out)
        self.assertEqual(r['codes'], 2900 + 107)
        with open(os.path.join(out, 'names.csv'), encoding='utf-8') as f:
            names = f.read()
        self.assertIn('BR-034:100-199 CR-110:200-299 RB-057:300-699 SD-070:700-799 BR-034:800-899', names)
        again = store.import_registry(out, os.path.join(self.tmp, 'again.sqlite'), log=quiet)
        self.assertEqual(again['codes'], 3007)
        svc = Service(os.path.join(self.tmp, 'again.sqlite'))
        self.assertEqual(svc.get_card('BR-0143-856-1')['home'], 'Belem 856')
        svc.close()

    def test_already_has_a_code(self):
        b = self.post({'lat': 14.8474370 + 1 / 111320, 'lng': -24.6824147}, 409, 'exists')
        self.assertEqual(b['card']['machine'], 'BR-0117-1002-4')
        b = self.post({'lat': 14.8474514, 'lng': -24.6824}, 409, 'exists')  # inside its footprint
        self.assertEqual(b['card']['machine'], 'BR-0117-1002-4')

    def test_outline_checks(self):
        st = self.s.svc.con().execute("SELECT footprint FROM structures WHERE machine = 'BR-0117-1002-4'").fetchone()[0]
        ring = geo.parse_wkt(st)[0][0]
        # tapped 6 m east of the house, with the house's own outline
        lat, lng = 14.8474370, -24.6824147 + 6 / 107600
        self.post({'lat': lat, 'lng': lng, 'outline': [list(p) for p in ring]}, 409, 'exists')
        d = 1 / 111320
        small = [[lng, lat], [lng + d, lat], [lng + d, lat + d]]
        self.post({'lat': lat, 'lng': lng, 'outline': small}, 422, 'bad_outline')

    def test_doors(self):
        c = self.post({'lat': 14.8474370 + 15 / 110600, 'lng': -24.6824147, 'of': 'BR-0117-1002-4'}, 201)
        self.assertEqual((c['area']['id'], c['lote']['kind'], c['entrance']['kind']), ('BR-036', 'porta', 'door'))
        self.post({'lat': 14.8474370 + 100 / 110600, 'lng': -24.6824147, 'of': 'BR-0117-1002-4'}, 422, 'too_far')
        self.post({'lat': 14.8474370, 'lng': -24.6824147, 'of': 'BR-0117-9999-0'}, 404, 'unknown_code')

    def test_refusals(self):
        self.post({'lat': 14.80, 'lng': -24.80}, 422, 'outside')
        self.post({'lat': 14.85, 'lng': -24.70}, 401, 'unauthorized', key=None)
        self.post({'lat': 14.85, 'lng': -24.70}, 401, 'unauthorized', key='wrong')
        ro = Server(self.db, keys=())
        try:
            self.post({'lat': 14.85, 'lng': -24.70}, 403, 'read_only', srv=ro)
        finally:
            ro.close()
        status, b = self.s.call('POST', '/v1/codes', raw=b'{not json', key=KEY)
        self.assertEqual((status, b['error']['code']), (400, 'bad_json'))
        self.post({'lat': 'x'}, 400, 'bad_request')
        self.post([1, 2], 400, 'bad_request')

    def test_border_decides(self):
        # well across the border (about 150 km beyond it, in open sea): refused
        self.post({'lat': 15.5, 'lng': -27.0}, 422, 'outside')
        # refused even when the municipality and zone rules would take it
        brava = E.MUNI_BY_ISO['CV-BR']
        with mock.patch.object(E, 'municipality_at', return_value=brava):
            b = self.post({'lat': 15.5, 'lng': -27.0}, 422, 'outside')
            self.assertIn('national border', b['error']['message'])
            # inside the border, the same rules issue it
            c = self.post({'lat': 14.8682635, 'lng': -24.699435}, 201)
        self.assertEqual(c['area']['id'][:3], 'BR-')
        # a moved entrance is held to the same rule
        st, b = self.s.call('PATCH', '/v1/codes/BR-0117-1006-2', {'entrance': {'lat': 15.5, 'lng': -27.0, 'kind': 'gate'}}, key=KEY)
        self.assertEqual((st, b['error']['code']), (422, 'outside'))

    def test_daily_limit(self):
        lim = Server(self.db, per_day=1)
        try:
            self.post({'lat': 14.8682635, 'lng': -24.699435}, 201, srv=lim)
            self.post({'lat': 14.8682635 + 20 / 110600, 'lng': -24.699435}, 429, 'limit', srv=lim)
        finally:
            lim.close()

    def test_changes(self):
        m = 'BR-0117-1006-2'
        st, c = self.s.call('PATCH', f'/v1/codes/{m}', {'status': 'confirmed'}, key=KEY)
        self.assertEqual((st, c['status']), (200, 'confirmed'))
        lat, lng = c['entrance']['lat'] + 20 / 110600, c['entrance']['lng']
        st, c = self.s.call('PATCH', f'/v1/codes/{m}', {'entrance': {'lat': lat, 'lng': lng, 'kind': 'gate'}}, key=KEY)
        self.assertEqual((st, c['entrance']['kind'], c['entrance']['source']), (200, 'gate', 'people'))
        self.assertEqual(self.s.svc.at(lat, lng)['code']['machine'], m)
        st, b = self.s.call('PATCH', f'/v1/codes/{m}', {'entrance': {'lat': lat + 0.001, 'lng': lng}}, key=KEY)
        self.assertEqual((st, b['error']['code']), (422, 'too_far'))
        st, b = self.s.call('PATCH', f'/v1/codes/{m}', {'status': 'gone'}, key=KEY)
        self.assertEqual((st, b['error']['code']), (400, 'bad_request'))
        st, b = self.s.call('PATCH', f'/v1/codes/{m}', {'status': 'confirmed'})
        self.assertEqual((st, b['error']['code']), (401, 'unauthorized'))
        st, b = self.s.call('PATCH', '/v1/codes/BR-0117-9999-0', {'status': 'confirmed'}, key=KEY)
        self.assertEqual((st, b['error']['code']), (404, 'unknown_code'))
        st, c = self.s.call('PATCH', f'/v1/codes/{m}', {'status': 'retired'}, key=KEY)
        self.assertEqual(c['status'], 'retired')
        st, b = self.s.call('PATCH', f'/v1/codes/{m}', {'status': 'confirmed'}, key=KEY)
        self.assertEqual((st, b['error']['code']), (409, 'retired'))
        # a retired number is never given again, and a point no longer finds it
        self.assertNotEqual(self.s.svc.at(lat, lng).get('code', {}).get('machine'), m)


if __name__ == '__main__':
    unittest.main()
