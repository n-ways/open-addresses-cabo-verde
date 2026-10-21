# open-addresses-cabo-verde: N-Ways Addressing for Cabo Verde

**Status: in force.** Every building in Cabo Verde has its home code: 175,630 codes, issued on 19 and 20 October 2026 across the 22 municipalities of the nine inhabited islands, all published in [`registry/`](registry/README.md) with nothing left out. Codes are provisional until people confirm them (the agreement of independent phones, one of them at the lote). In the N-Ways app, "Get my code" finds the code already issued for a building; only a building not yet on the map, or an extra door, gets a new code, issued on demand by the same rules.

This repository holds Cabo Verde's addressing model, its engine and specification, the full registry, a ready-made registry server with its API, and the research papers.

## The format

A **home code** is the short name of your bairro, zona or povoação and a short number:

> **Palmarejo 12 34** · Praia, Santiago  ·  **São Filipe 21 29** · *Lote Achada São Filipe*, Praia  ·  **Fazenda 34 48** · Tarrafal  ·  **João Vaz 214** · Paul, Santo Antão

- **Short plate names.** The name in the code has at most 12 characters and 2 words (`São Filipe`, `ASA`, `Julião`); the full official name (*Lote Achada São Filipe*, *Achada Santo António*, *Casa Para Todos-Ribeira de Julião*) is printed small for context and still decodes when typed. 306 of the 1,778 plate names are provisional until their Câmara Municipal chooses (`needsCouncilChoice`); the choice changes the name, never the number.
- **Unique nationally on its own.** Plate names repeat (254 names in 672 zones), so all zones with the same plate name share one national number range, cut into frozen blocks: `Fazenda 24 33` is Praia and `Fazenda 34 48` is Tarrafal with nothing typed after them. The official name, municipality and island are printed for information only.
- Numbers have 3 or 4 digits (never more than 5); the length belongs to the name. A 4-digit number is said as two pairs ("doze, trinta e quatro").
- A machine form, `PR-0973-1234-0` (municipality, national name index, number, check digit), is for systems and the QR code on a plate. Its check digit appears nowhere else: plates and forms show the name and number only, and nobody has to remember it.
- One code covers one **lote** (plot or compound). It leads to the lote's gate or front door.
- Every structure carries a **building profile**: use, size, entrances and status, each with a source and a confidence.
- Spot addresses are **Plus Codes**, the grid Correios de Cabo Verde adopted in 2016.
- The Correios postcode, the municipal street address and the cadastral NIP are shown beside the code and never replaced.

## What is where

| Path | What |
|---|---|
| [registry/](registry/README.md) | **The registry**: every issued code, per municipality, with the zone and name tables, numbering anchors, building profiles and footprints, and a manifest of SHA-256 sums |
| [server/](server/README.md) | **The registry server**: a ready-made HTTP service and JSON API (`docker compose up`) that serves the registry and, on the designated issuer's deployment, issues codes by the same rules |
| [docs/api.md](docs/api.md), [server/openapi.yaml](server/openapi.yaml) | The API, with a real request and response for every endpoint; OpenAPI 3.1 |
| [engine/SPEC.md](engine/SPEC.md) | Engine specification |
| [engine/reference/](engine/reference/) | Reference engine, Python standard library only: [cv_engine.py](engine/reference/cv_engine.py), the plate-name rule [plate_names.py](engine/reference/plate_names.py), tests [test_cv.py](engine/reference/test_cv.py) |
| [engine/test-vectors.json](engine/test-vectors.json), [test-vectors-registry.json](engine/test-vectors-registry.json) | Conformance vectors: the engine's own, and real issued codes from the registry |
| [engine/data/](engine/data/) | Municipality outlines; the national border (`border.geojson`: no code more than 300 m outside it); the zone table and national name register as frozen at first issue |
| [docs/model.md](docs/model.md) | The model and why each choice fits Cabo Verde |
| [docs/existing-systems.md](docs/existing-systems.md) | Postcodes (area-level, not door-level), Morada Certa, municipal door numbers, cadastre, census |
| [docs/paper.md](docs/paper.md), [paper.pt.md](docs/paper.pt.md), [paper.fr.md](docs/paper.fr.md) | The research paper in English, Portuguese and French, with PDFs ([en](docs/n-ways-addressing-cabo-verde-en.pdf), [pt](docs/n-ways-addressing-cabo-verde-pt.pdf), [fr](docs/n-ways-addressing-cabo-verde-fr.pdf)) |
| [docs/paper/](docs/paper/), [docs/figures/](docs/figures/) | How the papers are typeset (pandoc and LaTeX), their verified references (`references.bib`), and the figures as TikZ/pgfplots sources with their data tables |
| [model/](model/) | The model, machine-readable (`design.json`, with the building-profile schema); municipalities and building counts (`regions.json`, `country.json`); statistics (`building-stats.json`) |
| [tools/](tools/) | How the data was built ([tools/README.md](tools/README.md)): statistics, zones and plate names from N-Ways data (`building_stats.py`, `build_zones.py`, `build_names.py`), the national border (`build_border.py`), the lote list for issue (`issue_registry.py`), the registry vectors (`registry_vectors.py`), the data tables of the paper's figures (`paper_figures.py`) |
| [doors/](doors/README.md) | Confirmed doors and gates, once people have agreed on them |
| [GOVERNANCE.md](GOVERNANCE.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) | Rules, the one-issuer rule, how to propose changes, how to report a problem |
| [SOURCES.md](SOURCES.md), [LICENSING.md](LICENSING.md), [NOTICE](NOTICE), [CITATION.cff](CITATION.cff) | Sources, licences and how to credit N-Ways, how to cite the paper |

## Run the reference engine

Python 3.9 or later, no packages to install (see [requirements.txt](requirements.txt)):

```sh
python3 engine/reference/cv_engine.py                      # self-test, then prints the test vectors
python3 engine/reference/cv_engine.py 14.91992 -23.50709   # a point: Plus Code, municipality, island, postcode context
python3 engine/reference/cv_engine.py "Palmarejo 12 34"    # a home code -> machine form
python3 engine/reference/cv_engine.py "fazenda 3448"       # a repeated name: still exactly one place (Tarrafal)
python3 engine/reference/cv_engine.py "Lote Achada São Filipe 21 29"   # an official name: decodes to São Filipe 21 29
python3 engine/reference/cv_engine.py "PR-0973-1234-0"     # a machine form, check digit verified
python3 engine/reference/test_cv.py                        # the engine tests
python3 tools/test_tools.py                                # the build tools' border rule
python3 tools/build_names.py                               # the name register reproduces from its rules
python3 tools/registry_vectors.py --check                  # the registry vectors reproduce from registry/
```

## Run the server

```sh
docker compose -f server/docker-compose.yml up -d          # imports the registry on first start, then serves on :8080
curl -s 'http://localhost:8080/v1/find?q=Palmarejo%2012%2034'
```

or without Docker:

```sh
python3 -m server import --registry registry --db data/addresses.sqlite
python3 -m server serve --db data/addresses.sqlite --port 8080
python3 -m unittest server.test_server                     # the server tests
```

A deployment is read-only unless the State of Cabo Verde or N-WAYS LIMITED has designated it as the issuer: one issuer per country keeps every code unique. Deployment, configuration, backups, updates and the issuer rule: [server/README.md](server/README.md). Every endpoint: [docs/api.md](docs/api.md).

## Build the papers

The papers are pandoc Markdown with TeX mathematics; the PDFs are typeset with LaTeX. Install pandoc 3, tectonic and poppler (`brew install pandoc tectonic poppler`, or the equivalent packages), then:

```sh
python3 tools/paper_figures.py           # recompute the figures' data tables from registry/ (--check to compare)
sh docs/paper/build.sh                   # compile docs/figures/*.tex to PDF and SVG, then the three PDFs in docs/
```

## Rebuild the data

The statistics, zones and plate names were built from N-Ways map data with duckdb. The border decides: a building more than 300 m outside Cabo Verde's national border (OpenStreetMap admin_level 2) is dropped at extraction and never coded ([tools/README.md](tools/README.md)). The zone table and name register are frozen now that codes are issued; the tools rebuild them for comparison only:

```sh
NWAYS_DB=postgres://... python3 tools/building_stats.py --root /path/to/n-ways-data --work DIR   # add --skip-extract to reuse DIR
```

## Build on it

Everything here is open for developers, couriers, municipalities and researchers: https://github.com/n-ways/open-addresses-cabo-verde

- **Run the server.** One command gives you the whole registry behind a JSON API: look codes up, find what is at a point, list a municipality's codes, check machine codes (*Run the server* above).
- **Run the engine.** `engine/reference/cv_engine.py` parses a home code or a machine form, verifies its check digit, formats the plate and the spoken form, places a point in its municipality and island, and gives its Plus Code. `engine/test-vectors.json` and `engine/test-vectors-registry.json` are the conformance suite for an implementation in any language (SPEC.md §11).
- **Use the data.** `registry/` holds every issued code with its lote, entrance, building profile and footprint; `engine/data/` the zone table and name register that make `Name NNNN` decode offline; `model/` the statistics and the building-profile schema.
- **Look codes up live.** The N-Ways app and API decode every issued code to its gate or front door (N-Ways Maps Platform, nways.ng/developers).
- **Credit N-Ways.** Show "Home codes by N-Ways Addressing · © N-WAYS LIMITED (nways.ng)" wherever a code appears, keep [NOTICE](NOTICE) with the code, and credit the data as [LICENSING.md](LICENSING.md) says.

## Licence

Code (`engine/`, `server/`, `tools/`): Apache License 2.0 ([LICENSE](LICENSE), [NOTICE](NOTICE)). Data (`registry/`, `doors/`, `engine/data/`, `model/*.json`): ODbL 1.0 ([LICENSE-DATA](LICENSE-DATA)). Documents (`docs/` and the other Markdown files): CC BY 4.0 ([LICENSE-DOCS](LICENSE-DOCS)). How to credit N-Ways: [LICENSING.md](LICENSING.md).

© N-WAYS LIMITED (nways.ng).
