"""The HTTP API: JSON under /v1, standard library only.

Every response is JSON. An error is {"error": {"code": "...", "message":
"..."}} with its HTTP status; a refused issue for a building that already has
a code carries that code's card as "card".
"""
import json
import re
import sys
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from . import engine as E
from .service import ApiError

MAX_BODY = 64 * 1024

ROUTES = [
    ('GET', r'/v1/health', 'health'),
    ('GET', r'/v1/info', 'info'),
    ('GET', r'/v1/find', 'find'),
    ('GET', r'/v1/at', 'at'),
    ('GET', r'/v1/near', 'near'),
    ('GET', r'/v1/verify', 'verify'),
    ('GET', r'/v1/spot', 'spot'),
    ('GET', r'/v1/spot/decode', 'spot_decode'),
    ('GET', r'/v1/zones', 'zones'),
    ('GET', r'/v1/zones/(?P<key>[^/]+)', 'zone'),
    ('GET', r'/v1/zones/(?P<key>[^/]+)/codes', 'zone_codes'),
    ('GET', r'/v1/areas', 'areas'),
    ('GET', r'/v1/areas/(?P<id>[^/]+)', 'area'),
    ('GET', r'/v1/codes/(?P<machine>[^/]+)', 'code'),
    ('POST', r'/v1/codes', 'issue'),
    ('PATCH', r'/v1/codes/(?P<machine>[^/]+)', 'change'),
]
ROUTES = [(m, re.compile('^' + p + '/?$'), h) for m, p, h in ROUTES]


def make_handler(svc, cors_origins=()):
    cors = [o.strip() for o in cors_origins if o.strip()]

    class Handler(BaseHTTPRequestHandler):
        server_version = 'n-ways-addresses-cv'
        sys_version = ''
        protocol_version = 'HTTP/1.1'

        def log_message(self, fmt, *args):
            sys.stderr.write('{} {}\n'.format(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), fmt % args))

        def _cors(self):
            origin = self.headers.get('Origin')
            if not origin or not cors:
                return
            if '*' in cors:
                self.send_header('Access-Control-Allow-Origin', '*')
            elif origin in cors:
                self.send_header('Access-Control-Allow-Origin', origin)
                self.send_header('Vary', 'Origin')

        def _send(self, status, body, cache=None):
            data = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', cache or 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self._cors()
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(data)

        def _error(self, status, code, message, **extra):
            body = {'error': {'code': code, 'message': message}}
            body.update(extra)
            self._send(status, body)

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
            self.send_header('Access-Control-Max-Age', '86400')
            self.send_header('Content-Length', '0')
            self.end_headers()

        def do_GET(self):
            self._dispatch('GET')

        def do_HEAD(self):
            self._dispatch('GET')

        def do_POST(self):
            self._dispatch('POST')

        def do_PATCH(self):
            self._dispatch('PATCH')

        def do_PUT(self):
            self._dispatch('PUT')

        def do_DELETE(self):
            self._dispatch('DELETE')

        def _body(self):
            n = int(self.headers.get('Content-Length') or 0)
            if n > MAX_BODY:
                raise ApiError(413, 'too_large', f'The request body is over {MAX_BODY // 1024} KB.')
            raw = self.rfile.read(n) if n else b''
            try:
                return json.loads(raw.decode('utf-8') or 'null')
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ApiError(400, 'bad_json', 'The request body is not valid JSON.') from None

        def _bearer(self):
            h = self.headers.get('Authorization', '')
            return h[7:].strip() if h.lower().startswith('bearer ') else ''

        def _dispatch(self, method):
            u = urlsplit(self.path)
            path = unquote(u.path)
            q = {k: v[-1] for k, v in parse_qs(u.query, keep_blank_values=True).items()}
            allowed = []
            for m, rx, name in ROUTES:
                mt = rx.match(path)
                if not mt:
                    continue
                if m != method:
                    allowed.append(m)
                    continue
                try:
                    status, body, cache = getattr(self, 'h_' + name)(q, **mt.groupdict())
                    self._send(status, body, cache)
                except ApiError as e:
                    self._error(e.status, e.code, e.message, **e.extra)
                except Exception:  # noqa: BLE001  (any other failure answers 500 and is logged)
                    traceback.print_exc()
                    self._error(500, 'internal', 'Something went wrong on the server.')
                finally:
                    svc.release()
                return
            if allowed:
                self._error(405, 'method_not_allowed', f'{method} is not allowed here. Allowed: {", ".join(sorted(set(allowed)))}.')
            else:
                self._error(404, 'not_found', f'There is no endpoint {path}. See /v1/info and docs/api.md.')

        # -- handlers: each returns (status, body, Cache-Control) --------------
        PUBLIC = 'public, max-age=60'

        def h_health(self, q):
            return 200, svc.health(), 'no-store'

        def h_info(self, q):
            return 200, svc.info(), self.PUBLIC

        def h_find(self, q):
            return 200, svc.find(q.get('q')), self.PUBLIC

        def h_at(self, q):
            return 200, svc.at(q.get('lat'), q.get('lng')), self.PUBLIC

        def h_near(self, q):
            return 200, svc.near(q.get('lat'), q.get('lng'), q.get('radius'), q.get('limit')), self.PUBLIC

        def h_verify(self, q):
            return 200, svc.verify(q.get('code')), self.PUBLIC

        def h_spot(self, q):
            return 200, svc.spot(q.get('lat'), q.get('lng')), self.PUBLIC

        def h_spot_decode(self, q):
            return 200, svc.spot_decode(q.get('code')), self.PUBLIC

        def h_zones(self, q):
            return 200, {'zones': [svc.muni_summary(E.MUNI[m[1]]) for m in E.MUNICIPALITIES]}, self.PUBLIC

        def h_zone(self, q, key):
            m = svc.municipality(key)
            out = svc.muni_summary(m)
            out['areaList'] = [svc.area_summary(z) for z in svc.zone_list if z['key'] == m['key']]
            return 200, out, self.PUBLIC

        def h_zone_codes(self, q, key):
            return 200, svc.zone_codes(key, q.get('after'), q.get('limit')), self.PUBLIC

        def h_areas(self, q):
            return 200, svc.find_areas(q.get('name') or ''), self.PUBLIC

        def h_area(self, q, id):
            return 200, svc.area(id), self.PUBLIC

        def h_code(self, q, machine):
            return 200, svc.get_card(machine), self.PUBLIC

        def h_issue(self, q):
            svc.key_id(self._bearer())  # refuse before reading the body
            return 201, svc.issue(self._body(), self._bearer()), 'no-store'

        def h_change(self, q, machine):
            svc.key_id(self._bearer())
            return 200, svc.change(machine, self._body(), self._bearer()), 'no-store'

    return Handler


def serve(svc, host, port, cors_origins=()):
    httpd = ThreadingHTTPServer((host, port), make_handler(svc, cors_origins))
    httpd.daemon_threads = True
    return httpd
