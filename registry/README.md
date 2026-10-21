# registry/

The published registry of Cabo Verde home codes (engine/SPEC.md §7): **every code issued in the country, 175,630 of them**, with nothing left out. 174,234 lotes received their codes on 19 October 2026, in one run that froze every block; the 1,395 lotes with an official or presumed-official address (Platô, central Mindelo, numbered streets) received theirs in a second run on 20 October 2026, and one code was issued on demand for a building that was not yet on the map. No code has been renumbered. A code is `provisional` until people confirm it.

## Files

| File | One row per | Columns |
|---|---|---|
| `zones.csv` | zone (1,778) | zone, municipality, index, plate name, official name, plate rule, needs_council_choice, aliases, near, name key, name index, box, anchor |
| `names.csv` | name (1,360) | name key, name index, plate name, official names, digits, blocks (`zone:lo-hi`, in the order they were taken), reserve, aliases, needs_council_choice |
| `<KEY>.csv` | code, one file per municipality (`PR.csv`, `SV.csv`, ...) | machine code, home code, official name, zone, number, check digit, status, how and when issued, entrance (gate, door or centre) with its Plus Code, use, lote kind, structures, floor area, postcode, coverage (`official`, `official-pending` or empty) and the official address where the Câmara numbered the street |
| `lotes.csv.gz` | code | machine code, numbering anchor (latitude, longitude, full precision), entrance source (`map` or `people`), whether the lote is an enclosed site |
| `structures/<KEY>.csv.gz` | structure (192,272) | machine code, index, structure id, use, confidence and how it was found, status, footprint area, perimeter, height and its source, floors, floor area, name (never for a home), data source (`osm`, `ml`, `people`), footprint (WKT) |
| `MANIFEST.json` | | counts per municipality, the SHA-256 of every file (of the uncompressed CSV for the `.gz` files), export date, engine version, credit and licence |

Rows of `<KEY>.csv` are in name index and number order; `lotes.csv.gz` and the structure files are in machine-code order. Files are UTF-8, comma-separated, with LF line ends; a field is quoted only when it holds a comma, a quote or a line break. The `.gz` files are written without a name or a time stamp, so the same data always gives the same bytes.

Nothing in the registry is about the people in a home: no names, no household counts, no phone numbers.

## How it is made

The registry server (the N-Ways backend) is the single issuer of codes. It numbers the lotes that `tools/issue_registry.py` lists, keeps every code already issued and only adds new ones, so a rerun never renumbers. Every file here, `lotes.csv.gz` and `structures/` included, is written by its export in one step (`go run ./cmd/homecodes export -country CV -out <open-addresses-cv>/registry`), with the manifest. The `.gz` files are gzip at level 9; each SHA-256 is that of the uncompressed file, because two gzip implementations need not choose the same encoding of the same contents.

The registry server in [`../server/`](../server/README.md) loads these files, checks each against the manifest, serves them over an API and writes them back (`python3 -m server export`): the same contents byte for byte, so the same SHA-256.

## Checking it

```sh
python3 -m server import --registry registry --db /tmp/cv.sqlite   # checks every SHA-256 and every count
python3 tools/registry_vectors.py --check                          # the conformance vectors still derive from it
```

Data licence: ODbL 1.0 (LICENSE-DATA). Credit: "N-Ways Addressing for Cabo Verde, © N-WAYS LIMITED (nways.ng)".

The zone table and name register in `engine/data/` are the same register as it was frozen at first issue; `zones.csv` and `names.csv` here add every block taken since.
