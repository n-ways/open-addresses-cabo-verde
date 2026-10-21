# Licensing

N-Ways Addressing for Cabo Verde is open. Build on it, and credit N-Ways.

| Part | Licence | File |
|---|---|---|
| Code: the engine, the registry server and the tools (`engine/reference/`, `engine/*.json` test vectors, `server/`, `tools/`) | Apache License 2.0 | [LICENSE](LICENSE), [NOTICE](NOTICE) |
| Data: the registry (codes, lotes, building profiles and footprints), doors, zones, name register and model (`registry/`, `doors/`, `engine/data/`, `model/*.json`, `server/testdata/`, and the figures' data tables in `docs/figures/data/`) | Open Database License (ODbL) 1.0 | [LICENSE-DATA](LICENSE-DATA) |
| Documents: the model, the research papers and their PDFs, the figures and their TikZ sources, the verification of existing systems (`docs/`), and this repository's other Markdown files | Creative Commons Attribution 4.0 (CC BY 4.0) | [LICENSE-DOCS](LICENSE-DOCS) |
| Typesetting of the papers (`docs/paper/`): `template.tex` is adapted from pandoc's default LaTeX template; `ieee.csl` is the Citation Style Language IEEE style | pandoc templates: BSD 3-Clause (or GPL 2+); `ieee.csl`: CC BY-SA 3.0, as stated in the file | the file headers |

Licensor: **N-WAYS LIMITED** (nways.ng). Source: https://github.com/n-ways/open-addresses-cabo-verde

## How to credit N-Ways

Copy the line that fits. Link it to https://github.com/n-ways/open-addresses-cabo-verde where you can.

**An app, a website or an API that shows, decodes or issues home codes:**

> Home codes by N-Ways Addressing · © N-WAYS LIMITED (nways.ng)

Put it next to the code, or on the screen that shows it, and in your about or licences screen. If you ship or change the engine, also keep [NOTICE](NOTICE) (Apache 2.0, section 4(d)).

**A map, a dataset or a database built from the data:**

> © N-WAYS LIMITED, N-Ways Addressing; contains OpenStreetMap data © OpenStreetMap contributors (ODbL) and the other sources in SOURCES.md

A database you make from it and share is shared under ODbL 1.0 too (share-alike). A map image or a printed plate made from it is a "produced work": it carries the line above, and needs no share-alike.

**A paper, an article, a slide or a translation that uses the documents:**

> N-Ways Addressing for Cabo Verde, © N-WAYS LIMITED (nways.ng), CC BY 4.0. https://github.com/n-ways/open-addresses-cabo-verde

Say what you changed, if you changed anything.

## Sources inside the data

The data is built from open sources (full list in [SOURCES.md](SOURCES.md)). Their own terms travel with it, and the data credit above names them:

| Source | Licence | What you owe it |
|---|---|---|
| OpenStreetMap (buildings and their footprints, places, boundaries, gates and enclosures derived from it) | ODbL 1.0 | "© OpenStreetMap contributors"; share-alike, which is why the data is ODbL |
| Microsoft building footprints, via Overture Maps (in `registry/structures/`) | ODbL 1.0 | credit Microsoft and the Overture Maps Foundation |
| Google Open Buildings, via Overture Maps (in `registry/structures/`) | CC BY 4.0 | credit Google and the Overture Maps Foundation; compatible with redistribution inside an ODbL database |
| GeoNames (localities, zone names) | CC BY 4.0 | credit GeoNames (geonames.org) |
| N-Ways places (POIs used only to classify buildings: OSM, Overture, Foursquare OS Places, All The Places) | per source (ODbL, CDLA-Permissive-2.0, Apache-2.0, CC0) | only categories are used, no POI records are redistributed |

**Correios postcodes.** Correios de Cabo Verde publishes no licence for its postcodes. Only postcodes from open sources (OpenStreetMap `addr:postcode`) or given with Correios' permission enter the data. They are shown as context and never derived from a home code.

**Official addresses.** Where a Câmara Municipal numbers a street, its address is used as it writes it (SPEC.md §3.6). The municipality's own register keeps its own terms; a public body that takes over the registry may relicense its own additions.

## Trademarks

"N-Ways" and the N-Ways logo are trade marks of N-WAYS LIMITED. The licences above cover the code, data and documents, not the marks: you may say your product uses N-Ways Addressing, but not that it is N-Ways or is endorsed by N-Ways.
