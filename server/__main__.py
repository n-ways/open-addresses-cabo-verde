"""Command line: import, serve, export.

  python3 -m server import --registry registry --db data/addresses.sqlite
  python3 -m server serve  --db data/addresses.sqlite --port 8080
  python3 -m server export --db data/addresses.sqlite --out exported/

Settings for `serve` come from the command line, else from the environment:
ADDRESSES_DB, HOST, PORT, ISSUE_KEYS (comma-separated bearer keys; none means
read-only), ISSUE_PER_DAY (codes per key per 24 hours, default 500),
CORS_ORIGINS (comma-separated origins, or *).
"""
import argparse
import os
import signal
import sys

from . import api, store
from .service import Service


def _stop(*_):
    raise KeyboardInterrupt  # docker stop: finish the request in hand, then close


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python3 -m server', description='N-Ways Addressing for Cabo Verde: registry server.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    env_db = os.environ.get('ADDRESSES_DB', 'data/addresses.sqlite')

    p = sub.add_parser('import', help='load a published registry into the database (checked against MANIFEST.json)')
    p.add_argument('--registry', default='registry')
    p.add_argument('--db', default=env_db)
    p.add_argument('--discard-local-changes', action='store_true',
                   help='replace a database that holds codes issued or changed by this deployment')

    p = sub.add_parser('serve', help='serve the API')
    p.add_argument('--db', default=env_db)
    p.add_argument('--host', default=os.environ.get('HOST', '0.0.0.0'))
    p.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8080')))

    p = sub.add_parser('export', help='write the registry in the published format')
    p.add_argument('--db', default=env_db)
    p.add_argument('--out', required=True)

    a = ap.parse_args(argv)
    if a.cmd == 'import':
        try:
            r = store.import_registry(a.registry, a.db, discard_local=a.discard_local_changes,
                                      log=lambda s: print(s, file=sys.stderr))
        except store.RegistryError as ex:
            sys.exit(f'import refused: {ex}')
        print(f"{r['codes']} codes, {r['structures']} structures, {r['zones']} areas, {r['names']} names", file=sys.stderr)
        return
    if not os.path.exists(a.db):
        sys.exit(f'{a.db} not found: run `python3 -m server import` first')
    if a.cmd == 'export':
        con = store.connect(a.db)
        try:
            r = store.export_registry(con, a.out)
        finally:
            con.close()
        print(f"{r['codes']} codes, {r['structures']} structures, {r['files']} files in {a.out}", file=sys.stderr)
        return
    keys = [k.strip() for k in os.environ.get('ISSUE_KEYS', '').split(',') if k.strip()]
    per_day = int(os.environ.get('ISSUE_PER_DAY', '500'))
    cors = os.environ.get('CORS_ORIGINS', '').split(',')
    svc = Service(a.db, issue_keys=keys, issue_per_day=per_day)
    httpd = api.serve(svc, a.host, a.port, cors)
    signal.signal(signal.SIGTERM, _stop)
    mode = f'issuing ({len(keys)} key(s), {per_day} per key per day)' if keys else 'read-only'
    print(f'serving {svc.health()["codes"]} codes on http://{a.host}:{a.port}/v1 ({mode})', file=sys.stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == '__main__':
    main()
