# Tools

How the data of N-Ways Addressing for Cabo Verde is built. The tools read N-Ways map data read-only (an `NWAYS_DB` Postgres connection and an N-Ways data checkout, `--root`) and write to this repository or to a work folder. The engine and the server never need them.

| Tool | What it does |
|---|---|
| `building_stats.py` | Extracts footprints, enclosures, gates, places and locality names (duckdb, memory limit 3 GB), groups the lotes (SPEC.md §7.1) and writes `model/building-stats.json`; calls `build_zones.py` and `build_names.py` |
| `build_zones.py` | The zone table (SPEC.md §3.3), frozen once codes are issued |
| `build_names.py` | The national name register (SPEC.md §3.4, §3.7); run alone, checks that it reproduces from its rules |
| `build_border.py` | The national border shipped with the engine, `engine/data/border.geojson` (SPEC.md §3.2) |
| `issue_registry.py` | The lotes for issue, one JSON line each, numbered by the registry server |
| `registry_vectors.py` | `engine/test-vectors-registry.json` from the published registry (`--check` to compare) |
| `paper_figures.py` | The data tables behind the paper's figures (`--check` to compare) |
| `test_tools.py` | Tests of the border rule in the tools |

## The border decides

A Cabo Verde code is only ever issued for a building whose entrance lies inside Cabo Verde's national border, the OpenStreetMap admin_level 2 boundary, or within 300 m of it. Zone and municipality outlines, and outlines from other sources (geoBoundaries, GADM and the like), may spill over a border; they never decide. The tools enforce this so that nobody re-running them can code a building in a neighbouring country:

1. `building_stats.py` exports the national border with the other inputs: `border.wkt` in the work folder, the admin_level 2 relation of Cabo Verde as held in the N-Ways `countries` table (`SELECT ST_AsText(geom) FROM countries WHERE code='CV'`).
2. At extraction it drops every enclosure whose centre and every gate that lies more than 300 m outside that border, and, when it loads the footprints, every footprint whose centre does (it reports how many). Nothing beyond the border reaches the lotes, the zones or the statistics.
3. `issue_registry.py` checks each lote's anchor (its gate or its main structure) once more and drops any beyond the border, counting it as `abroad`.
4. A work folder without `border.wkt` (an extract made before this rule) falls back to `engine/data/border.geojson`, with the 300 m reduced by its measured deviation.

The distance is measured on the WGS 84 local scale at the point to the nearest edge of the border, 0 inside it (`cv_engine.border_distance_m`, `cv_engine.within_border`).

`build_border.py` writes `engine/data/border.geojson` from the same border: simplified with Douglas-Peucker at 50 m, then the largest distance between the simplified line and the full one is measured by sampling both lines every 25 m and stored as `deviationM`. The engine and the server accept a point with the shipped outline only within 300 m less `deviationM`, so the shipped file never accepts a point the full border refuses. The registry server refuses an issue or an entrance move beyond it with `422 outside`.

```sh
NWAYS_DB=postgres://... python3 tools/building_stats.py --root /path/to/n-ways-data --work DIR   # add --skip-extract to reuse DIR
python3 tools/build_border.py --wkt DIR/border.wkt          # or with NWAYS_DB set and no --wkt
NWAYS_DB=postgres://... python3 tools/issue_registry.py --root /path/to/n-ways-data --work DIR --skip-extract --out lotes.jsonl.gz
python3 tools/test_tools.py
```

Against the published registry: 175,630 codes, none more than 300 m outside the national border (every entrance lies inside it).
