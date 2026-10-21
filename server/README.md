# server/: the registry server

A ready-made HTTP service for the Cabo Verde home-code registry. It serves exactly the codes published in [`registry/`](../registry/README.md), answers the same questions as the N-Ways app and API (what is this code, what is at this point, which codes are near), and, on the deployment designated as the issuer, issues new codes by the issuer's own rules. A ministry, a municipality, Correios, an emergency service or a developer can run it without touching the code.

- Python 3.9 or later, standard library only. The code rules (parsing, check digits, forms, plate names, Plus Codes, municipalities, Hilbert numbering, blocks) come from the reference engine in [`engine/reference/`](../engine/reference/); nothing is reimplemented here.
- The data is a single SQLite file (WAL mode) with an R\*Tree spatial index (an integer grid where SQLite lacks R\*Tree).
- The API is described in [`docs/api.md`](../docs/api.md), with a real request and response for every endpoint, and in [`openapi.yaml`](openapi.yaml) (OpenAPI 3.1).

## Deploy with Docker

From the repository root:

```sh
docker compose -f server/docker-compose.yml up -d
curl -s http://localhost:8080/v1/health
# {"status":"ok","country":"CV","codes":175630,"exported":"2026-10-20T02:31:15Z"}
```

That is the whole deployment. The image holds the engine, the server and the published registry. On first start the container finds its database volume empty, checks every registry file against `MANIFEST.json`, loads it (about ten seconds), then serves on port 8080. Later starts reuse the volume. The container runs as an unprivileged user on a read-only root file system, and Docker checks `/v1/health` every 30 seconds.

Settings go in the environment, or in a `.env` file next to `docker-compose.yml`:

```sh
HOST_PORT=8080          # the port on the host
ISSUE_KEYS=             # leave empty unless this deployment is the designated issuer
ISSUE_PER_DAY=500       # codes per issuer key per 24 hours
CORS_ORIGINS=*          # or https://maps.example.cv,https://other.example.cv
```

## Run with plain Python

```sh
python3 -m server import --registry registry --db data/addresses.sqlite
python3 -m server serve --db data/addresses.sqlite --port 8080
```

Run both from the repository root. `import` checks the SHA-256 of every file against `MANIFEST.json` and every count against its total, and refuses the registry if anything differs. It builds a new database file and swaps it in only once all of it has loaded, so an interrupted or refused import leaves the old database as it was, and running it again is safe.

For a service that starts at boot, a systemd unit is enough:

```ini
[Unit]
Description=Cabo Verde home-code registry
After=network.target

[Service]
User=addresses
WorkingDirectory=/opt/open-addresses-cabo-verde
Environment=ADDRESSES_DB=/var/lib/addresses/addresses.sqlite PORT=8080
ExecStart=/usr/bin/python3 -m server serve
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `ADDRESSES_DB` | `data/addresses.sqlite` | The database file (`--db` overrides it) |
| `HOST` | `0.0.0.0` | Address to listen on |
| `PORT` | `8080` | Port to listen on (`--port` overrides it) |
| `ISSUE_KEYS` | empty | Comma-separated bearer keys allowed to issue and change codes. Empty: read-only. |
| `ISSUE_PER_DAY` | `500` | Codes one key may issue in any 24 hours |
| `CORS_ORIGINS` | empty | Origins allowed to call the API from a browser, comma-separated, or `*` |

Make a key with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`. Keys are compared by their SHA-256; the server never logs them.

## Behind a reverse proxy with TLS

Serve the API over HTTPS only. With Caddy, which obtains and renews the certificate itself:

```
addresses.example.cv {
    reverse_proxy 127.0.0.1:8080
}
```

With nginx and a certificate from Let's Encrypt (certbot):

```nginx
server {
    listen 443 ssl http2;
    server_name addresses.example.cv;
    ssl_certificate     /etc/letsencrypt/live/addresses.example.cv/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/addresses.example.cv/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        client_max_body_size 64k;
    }
}
```

Publish the container port on 127.0.0.1 only (`ports: ["127.0.0.1:8080:8080"]`) when the proxy runs on the same host. The server answers each request in its own thread. Measured on a laptop with eight concurrent clients, one instance answers about 1,200 card lookups and 120 point lookups per second in central Praia; a cache in the proxy (GET responses carry `Cache-Control: public, max-age=60`) takes repeated requests.

## Back up

A read-only deployment holds nothing that is not in the published registry: rebuilding it is `import` again. A deployment that issues holds codes that exist nowhere else until they are published, so back it up daily and before every upgrade:

```sh
sqlite3 data/addresses.sqlite ".backup 'backup/addresses-$(date +%F).sqlite'"   # a consistent copy while it serves
python3 -m server export --db data/addresses.sqlite --out backup/registry-$(date +%F)
```

In Docker: `docker compose exec addresses python3 -m server export --db /data/addresses.sqlite --out /tmp/registry` and `docker compose cp addresses:/tmp/registry ./registry-backup`.

`export` writes the registry in the published format: the same files, columns, row order, number formats and compression, with a fresh `MANIFEST.json`. Exporting a database that was imported and not changed gives files whose contents are identical, byte for byte once uncompressed, to the published ones (the checksums in `MANIFEST.json` match; the tests check this). Codes this deployment issued, the blocks it opened and every status or entrance change are in the export.

## Update to a newer registry

A read-only deployment follows the published registry:

```sh
git pull                                    # the new registry/
python3 -m server import --registry registry --db data/addresses.sqlite
# then restart the server
```

With Docker, rebuild the image and start it on an empty volume: `docker compose build && docker compose down -v && docker compose up -d`.

`import` refuses to replace a database that holds changes made by this deployment (codes issued, status or entrance changes), because those would be lost. Export them first; `--discard-local-changes` replaces the database anyway.

## One issuer

**A code is issued by one issuer per country.** A deployment issues codes only if the State of Cabo Verde or N-WAYS LIMITED has designated it as the issuer; every other deployment runs read-only, with no `ISSUE_KEYS`, and answers `403 read_only` to `POST` and `PATCH`.

The reason is arithmetic. A new code takes the free number between its neighbours in the zone's block, or the next free unit of the name's national range. Two issuers that start from the same registry see the same free numbers, so the first new building each of them numbers in the same zone gets the same number: two homes with one code, which no later step can repair without renumbering one of them, and a code is never renumbered. One issuer, and a registry published from it, keeps every code unique. A deployment that needs to issue (a municipality's front desk, for instance) does so through the issuer's API with a key of its own, so that its codes are numbered in the one place where every number is known.

The designated issuer publishes its registry (with `export`, or from the N-Ways registry server) after each round of issuing, and every other deployment updates from it.

## How a code is issued

`POST /v1/codes` follows the N-Ways issuer for Cabo Verde rule for rule (engine/SPEC.md §7.4):

1. The border decides: the point must lie inside Cabo Verde's national border (the OpenStreetMap admin_level 2 boundary) or within 300 m of it, whatever the other rules allow; a point further out is refused with `422 outside`. The server checks against `engine/data/border.geojson`, the border simplified to 50 m, and takes the simplification's measured deviation off the 300 m, so it never accepts a point the full border refuses. A moved entrance (`PATCH`) is held to the same rule.
2. The point must be on land in one of the 22 municipalities.
3. A new building is refused when a live code's footprint holds the point or its entrance or footprint is within 3 m (`409 exists`, with that code's card), or when the tapped outline and an existing footprint share more than half of the smaller of the two. An outline must be between 12 m² and 2 ha.
4. Another door (`of`) must be within 80 m of that lote's entrance and takes its zone.
5. A new building takes the zone of the nearest live code within 3 km in the same municipality, else the zone whose anchor is nearest.
6. The number is the middle free number between the point's Hilbert neighbours among the zone's codes (retired codes included: their numbers are never given again), else the nearest free number of the zone's blocks, else a new block, the lowest free unit of the name's national range, at the point's relative position. A name whose range is full opens the next length.
7. The code is `provisional`, `on-demand`, with the machine, remembered and written forms of the engine and a building profile from the outline. New blocks are stored and appear in `export`.

The tests replay 107 issues in Brava (filling the block of Belem until it opens an extension block, inserting into the dense block of Nova Sintra, adding a door) against the numbers the N-Ways issuer computes from the same state, and match every zone, number, form and profile.

## The data it holds

`registry/` publishes, for every code, its row in `<KEY>.csv` and, in two companion files written with it, what makes point lookups and the duplicate checks give the issuer's answers: `lotes.csv.gz` (each code's numbering anchor, where its entrance came from, whether the lote is an enclosed site) and `structures/<KEY>.csv.gz` (every structure's building profile and footprint). The server loads all of it.

## Tests

```sh
python3 -m unittest server.test_server -v
```

They run on [`testdata/registry/`](testdata/registry/), every real code of Brava with the full zone and name tables (built by `testdata/make_fixture.py`), and cover the import checks and the byte-identical export, every endpoint with its errors, issue parity ([`testdata/parity.json`](testdata/parity.json)), extension blocks, the duplicate checks, the border, the daily limit and status and entrance changes.

## Files

| File | What |
|---|---|
| `__main__.py` | The command line: `import`, `serve`, `export` |
| `store.py` | The SQLite schema, import with its checks, spatial queries, export |
| `service.py` | Cards, lookups, points, issue and changes |
| `api.py` | The HTTP layer: routes, JSON, errors, CORS |
| `engine.py` | Loads the reference engine with the database's frozen register |
| `geo.py` | Footprints: point in polygon, distances, outline areas, overlaps |
| `Dockerfile`, `docker-compose.yml`, `docker-entrypoint.sh` | The container |
| `openapi.yaml` | The API, OpenAPI 3.1 |
| `test_server.py`, `testdata/` | Tests and their data |

Licence: Apache-2.0 for the code, ODbL 1.0 for the data it serves ([LICENSING.md](../LICENSING.md)). Show "Home codes by N-Ways Addressing · © N-WAYS LIMITED (nways.ng)" wherever a code from it appears.
