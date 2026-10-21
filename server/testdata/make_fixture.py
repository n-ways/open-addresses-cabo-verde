#!/usr/bin/env python3
"""Build the test registry: the real rows of one municipality (Brava, BR)
from registry/, with the full zone and name tables, gzip-compressed, and a
manifest of its own.

  python3 server/testdata/make_fixture.py
"""
import gzip
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(REPO, 'registry')
OUT = os.path.join(HERE, 'registry')
KEY = 'BR'


def raw(name):
    p = os.path.join(SRC, name)
    if os.path.exists(p):
        with open(p, 'rb') as f:
            return f.read()
    with gzip.open(p + '.gz', 'rb') as f:
        return f.read()


def put(name, data, sha):
    p = os.path.join(OUT, name + '.gz')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f, gzip.GzipFile(filename='', mode='wb', fileobj=f, mtime=0, compresslevel=9) as g:
        g.write(data)
    sha[name] = hashlib.sha256(data).hexdigest()


def main():
    with open(os.path.join(SRC, 'MANIFEST.json'), encoding='utf-8') as f:
        man = json.load(f)
    sha = {}
    for name in ('zones.csv', 'names.csv', f'{KEY}.csv', f'structures/{KEY}.csv'):
        put(name, raw(name), sha)
    lines = raw('lotes.csv').decode('utf-8').splitlines(keepends=True)
    lotes = [lines[0]] + [ln for ln in lines[1:] if ln.startswith(KEY + '-')]
    put('lotes.csv', ''.join(lotes).encode('utf-8'), sha)
    fix = {'byMunicipality': {KEY: man['byMunicipality'][KEY]}, 'codes': man['byMunicipality'][KEY],
           'country': man['country'], 'credit': man['credit'], 'engine': man['engine'], 'exported': man['exported'],
           'licence': man['licence'], 'lotes': len(lotes) - 1, 'sha256': sha,
           'structures': man['structuresByMunicipality'][KEY], 'structuresByMunicipality': {KEY: man['structuresByMunicipality'][KEY]}}
    with open(os.path.join(OUT, 'MANIFEST.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(fix, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
