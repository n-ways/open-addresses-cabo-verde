# N-Ways Addressing for Cabo Verde: engine specification

Specification version 0.4, the version recorded in every registry manifest (`"engine": "... (SPEC v0.4)"`). Every code of Cabo Verde was issued under it on 19 and 20 October 2026. Licence: Apache-2.0, see [`../LICENSING.md`](../LICENSING.md).

This engine is for Cabo Verde only. The reference implementation is [`reference/cv_engine.py`](reference/cv_engine.py) (Python standard library only). Its outputs are [`test-vectors.json`](test-vectors.json) and, from the published registry, [`test-vectors-registry.json`](test-vectors-registry.json); its tests are [`reference/test_cv.py`](reference/test_cv.py). The zone table is [`data/zones.json`](data/zones.json) and the national name register [`data/names.json`](data/names.json), both frozen at first issue; the published registry ([`../registry/`](../registry/README.md)) holds the same register with every block issued since. The registry server in [`../server/`](../server/README.md) serves and issues codes by this specification.

The key words MUST, SHOULD and MAY are used as in RFC 2119.

## 0. Design order

The first criterion is that **people can remember their code and get it without effort**. Everything else follows from that: being beside the official systems, pointing to the door, working offline, staying stable, and protecting privacy. That criterion is why the code people use is a **short place word they already say plus a short number**, and why every letter and the check digit sit outside what anyone has to remember. Two hard constraints follow from it. **The remembered code is unique in the whole country on its own**: no municipality, island, phone position or saved place is needed to decode it, because people give their code without context (§3.4). And the place word is a **plate name** of at most 12 characters and 2 words, short enough for a plate, a form field and one breath (§3.7).

## 1. What the engine does

| Function | Input | Output | Offline |
|---|---|---|---|
| `parse` | "Palmarejo 12 34", "fazenda 3448", "Lote Achada São Filipe 21 29", "PR-0973-1234-0" | exactly one zone and number; check verified when given | yes |
| `name_key` | a place name | its national key (§3.4) | yes |
| `plate_ok` / `check_register_entry` | a plate name / a register entry | within 12 characters and 2 words; refused if not and not flagged (§3.7) | yes |
| `format_home` / `format_machine` / `format_plate` | zone, number | remembered form, machine form, plate layout | yes |
| `spoken` | zone, number, language | words for the voice (pt, kea) | yes |
| `describe_point` | latitude, longitude | land or sea; Plus Code; municipality, island; postcode context | yes |
| `lookup` | home or machine code | lote record (structures, entrances, profile) | yes, for downloaded municipalities |
| `plan_name` | the zones of one name and their lotes | length, blocks, reserve | registry build |
| `number_zone` | lotes of one zone, its block | first-issue numbers | registry build |
| `insert_lote` / `take_block` / `new_zone` | anchor of a new home / a full block / a new zone of an existing name | provisional number; new block | registry server |
| `use_register` / `use_published_registry` | a register, or a published registry folder | decode against it (with every block issued since) | yes |
| `classify` | footprint tags, places, size, context | use class, confidence, source, status | yes |
| `coverage_of` / `resolve` / `hand_over` | lote tags and position / lote record | official, official-pending or N-Ways; the address to show first, with the home code beside it | yes |

## 2. The home code

### 2.1 Forms

| Form | Example | Who uses it |
|---|---|---|
| **Home (remembered)** | `Palmarejo 12 34` | residents, callers, couriers on the phone |
| Full address line | `Palmarejo 12 34 · Praia, Santiago · 7600`; with a shortened name `São Filipe 21 29 · Lote Achada São Filipe · Praia, Santiago` | letters, forms, the app card |
| Plate | big: `Palmarejo 12 34`; small: `Praia · Santiago · 0`; the official name in small type when it differs; QR | the gate or door |
| **Machine** | `PR-0973-1234-0` | APIs, partner systems, the QR link `nways.ng/a/PR-0973-1234-0` |
| Structure | `Palmarejo 12 34.2` / `PR-0973-1234-0.2` | a second building in the lote (a shop in the front wall, an annexe) |
| Unit | `Palmarejo 12 34, 2.º Esq.` | a flat; the floor and side follow Portuguese usage (R/C, 1.º Esq., 1.º Dto.) |

Home and machine forms map 1:1. The machine form is municipality key, **national name index** (4 digits), number, then check digit. The zone is not written in it: name + number decode to the zone (§3.4), and the key MUST equal the owning zone's municipality, else the code is refused. The official name, municipality and island on the full line and the plate are information only; the big line alone decodes.

### 2.2 Numbers

- 3 digits, **100–999**, or 4 digits, **1000–9999**; 5 digits, **10000–99999**, only if a name ever needs them; never more (§5). The length belongs to the name, not to the zone.
- There is never a leading zero, because people drop it.
- A 4-digit number is written and said as **two pairs**: `12 34`, "doze, trinta e quatro". That is how Cabo Verde reads phone numbers. A 3-digit number is said like a door number: "duzentos e catorze".
- A pair starting with zero is said digit by digit: `10 05` is "dez, zero cinco".

### 2.3 Spoken forms

| Code | pt | kea (Santiago, to confirm with speakers) |
|---|---|---|
| Palmarejo 12 34 | Palmarejo, doze, trinta e quatro | Palmarejo, dozi, trinta i kuatu |
| Palmarejo 40 50 | Palmarejo, quarenta, cinquenta | Palmarejo, korenta, sinkuenta |
| João Vaz 214 | João Vaz, duzentos e catorze | João Vaz, duzentu i katorzi |
| João Vaz 100 | João Vaz, cem | João Vaz, sen |

`cv_engine._words` implements Portuguese (European norm: dezasseis, catorze) and Kriolu number words up to 999. The Kriolu table MUST be checked with Santiago (Badiu) and São Vicente speakers before the voice ships.

### 2.4 Why no letters

A 16-character alphanumeric code was considered and rejected. Portuguese letter names rhyme in two large families: bê, cê, dê, gê, pê, quê, tê, vê, zê; and efe, ele, eme, ene, erre, esse. Kriolu's ALUPEC spelling has no c or q. Letters belong to no address anyone in Cabo Verde already remembers. Digits read the same in Portuguese and Kriolu, are typed the same on every phone, and look like the door and phone numbers people already keep in their heads.

## 3. Places: municipality, island, zone

### 3.1 Municipality keys

The 22 ISO 3166-2:CV suffixes are BR, BV, CA, CF, CR, MA, MO, PA, PN, PR, RB, RG, RS, SD, SF, SL, SM, SO, SS, SV, TA, TS. Each has a fixed index, 0–21 in ISO order of 2026; indices are never reused. The key appears only in the machine form, where it must match the zone that owns the number. It is not in the check digit (§4) and is never needed to decode a home code.

### 3.2 Point to municipality and island

The engine ships `data/municipalities.geojson`: the 22 OpenStreetMap outlines simplified to 0.0003° (142 kB). Lookup is a box test, then even-odd ray casting on each polygon, holes excluded. A point inside no outline is "at sea or outside Cabo Verde": no spot code is issued there, except at ports and marinas listed in the registry. Near a boundary (within 50 m) the app SHOULD offer both municipalities. The island comes from the municipality and is always displayed.

**The border decides.** A home code MUST only be issued for an entrance inside Cabo Verde's national border, the OpenStreetMap admin_level 2 boundary, or within 300 m of it (`BORDER_M`). No other outline decides: municipality outlines, zone boxes and anchors, and outlines from other sources (geoBoundaries, GADM and the like, which often spill over a border) may place a point in Cabo Verde, but a point more than 300 m outside the national border is refused whatever they say, and a building there is never coded, so that no building in a neighbouring country can ever get a Cabo Verde code. Distance is measured on the WGS 84 local scale at the point to the nearest edge of the border (0 inside it, holes excluded).

The engine ships `data/border.geojson`: the national border simplified (Douglas-Peucker, 50 m) by `tools/build_border.py`, which also measures the largest distance between the simplified line and the full one by sampling both every 25 m and records it as `deviationM` (20.8 m for the outline shipped). With the shipped outline, `within_border` accepts a point only within 300 m less `deviationM`, so it never accepts a point the full border refuses; with the full border (the build tools) the limit is the whole 300 m. The registry server refuses an issue or an entrance move beyond it with `422 outside` (§7.4).

### 3.3 Zones

A zone is the place word. It is a **frozen record** holding the municipality, index, official name, plate name (§3.7), aliases, source, anchor, its name key and name index, its block(s) in the name's national range, and the Hilbert box used to number its lotes. A zone is a list of lotes, not a boundary. Zones are built once per municipality before first issue, by `tools/build_zones.py`:

1. **Candidates.** OSM city, town, suburb, neighbourhood and village points in N-Ways' `geo_names`, plus GeoNames localities that are not landforms. Excluded first words: Ponta, Ilhéu, Ilha, Baía, Pico, Morro, Cabo, Rocha, Lagoa, Furna, Boca, Serra, and "Praia de/do/da" (a beach). Squares, streets and school points (Largo, Praça, Rua, Avenida, Rotunda, Estrada, Escola) are never zones.
2. **One per name.** Within a municipality, the same folded name within 2 km is one candidate; OSM wins.
3. **Towns.** A GeoNames locality within 1 km of an OSM suburb or neighbourhood is dropped. A city or town point with 3 or more bairros within 3 km is not a zone itself: in Praia, the bairros are the place words, not "Praia".
4. **Assignment.** Each lote's anchor goes to the nearest candidate in its own municipality.
5. **Pruning.** A candidate with fewer than 15 lotes is dropped and its lotes go to the next nearest, unless it is more than 1.5 km from every other candidate, so an isolated povoação keeps its own name. This repeats until stable.
6. **Same plate name twice in one municipality.** Both keep the bare plate name; their blocks tell them apart (§3.4). Each records its nearest differently named zone, by plate name, as `near`, shown on the card only ("Achadinha, perto de Mancanha"; set by `tools/build_names.py`). Brackets in the name (`Achadinha (Mancanha)`) were rejected: they make the code longer to say and are left out in speech. The Câmara Municipal MAY rename a zone at any time (§3.4).
7. **Index** 1… in Hilbert order (§7.2) of the zone anchors over the municipality box. **Digits and blocks** come from the name register (§3.4, §5), built by `tools/build_names.py`.

Result: **1,778 zones** (64 in Praia); official names under 1,547 keys, plate names under **1,360**. 1,349 zones have 3 digits and 429 have 4; 77,467 lotes (44 %) get 3-digit numbers and 98,162 get 4. The median zone holds 50 lotes; the largest is Achada Santo António (`ASA`) in Praia with 2,855.

### 3.4 Names: one national range per name

**Rule:** a home code `Name NNNN` MUST decode to exactly one zone in the whole country with nothing else given. Context (the phone's position, saved places, a municipality or island after a comma) MUST NOT be needed and MUST NOT be used to choose. A code is given on the phone, on a form or to a courier from another island, where context is missing or wrong; a code that needed it (`Achadinha 214, Paul`) would fail exactly there.

**Name key.** `name_key()` folds a **plate name** (§3.7) for the national comparison (Portuguese and Kriolu):
1. NFKD, combining marks removed, lower case (Platô = plato);
2. `' . - / ,` become spaces (Lém-Ferreira = lem ferreira);
3. ALUPEC to Portuguese: `tch`, `tx` → `ch`; `dj` → `j`; `k` → `c` before a, o, u, `qu` before e, i;
4. abbreviations expand: `sto` santo, `sta` santa, `s` são, `sr`/`sra` senhor/senhora, `n`/`na`/`nsa` nossa;
5. the words `de da do das dos d o a os as` are dropped (Chã de Baixo = Chã Baixo; As Hortas = Hortas; Ponta d'Água = ponta agua);
6. a bracketed part is kept as part of the key (plate names have none: brackets are dropped in §3.7).

A typed name is also tried with a run-together `d` read as `d'` (`ponta dagua` = `ponta agua`). Rule 5 joins 10 pairs of names that differ only by an article or a preposition. A plate name never contains digits: `tools/build_names.py` spells a numeral out (`África 70` → `África Setenta`) and keeps the written form as an alias; a spelt form over the limit is flagged (§3.7).

**Register.** All zones whose plate names have one key form a **name**, with:
- `index`: national name index, 1… in key order at first issue; new names take the next index; never reused. It is in the machine form and the check digit.
- `digits`: the length of the name's range (§5).
- `blocks`: `[{zone, lo, hi}]`, contiguous runs of whole units (100 numbers for 3 and 4 digits, 1,000 for 5), each holding at least 3 × the zone's lotes. Order at first issue: municipality index, then zone index, from the bottom of the range.
- `reserve`: the rest of the range; at least `RESERVE_UNITS` = 2 units at first issue.
- `aliases`: the official names and other spellings; an alias MUST NOT equal another name's key and MUST NOT be claimed by two names (it is dropped and listed in `droppedAliases`);
- `officialNames`, `needsCouncilChoice` (any zone flagged), `fits` (§3.7).

**Decoding.** `parse("Name NNNN")`: key → name → the one block with lo ≤ NNNN ≤ hi → zone. A number in no block is refused ("not a home code"). If a municipality or island is typed after a comma, it is compared with the decoded zone and the result flagged `contextMatches`; it never changes the answer.

**Frozen blocks.** Blocks are fixed at first issue and never renumbered or moved. Growth only adds blocks (§5.3). A municipal boundary change, a renamed zone or a merge changes no block. If a zone is renamed, the new name becomes its official name; if the new plate name already exists, the old plate name stays in the code and the new one is shown on the card only, so two ranges never collide.

**Qualifiers.** A name whose blocks plus reserve would not fit 5 digits MUST be split before first issue by one established qualifier per affected zone (as "Achada Santo António" is said, not "Achada"), listed in `cv_engine.QUALIFIERS` and `names.json → qualifiers`. The register needs none.

**Counts** (`model/building-stats.json → names`):

| | |
|---|---|
| names (plate-name keys) | 1,360 (official-name keys: 1,547) |
| names with 2 or more zones | 254, in 672 zones (64,872 lotes); keyed on official names it would be 163 in 394 |
| … shared only after shortening | 130 |
| across municipalities / across islands / inside one municipality only | 207 / 132 / 47 |
| zones sharing a name with another zone of the same municipality | 208 |
| zones per repeated name | 2: 162; 3: 56; 4: 23; 5: 3; 6: 2; 7: 5; 8: 2; 10: 1 (Figueira) |
| repeated names by length | 3 digits: 152; 4: 102; 5: 0 |
| largest shared range | Bela Vista: PR-007 `1000–5499` (1,473 lotes), SL-013 `5500–5599` (17), SV-038 `5600–5899` (72); 4,900 numbers in blocks, 4 digits |
| qualifiers | 0 |

**Test vectors** (`test-vectors.json → sameName`): `Fazenda 12 34` → CR-078 (Achada Fazenda, Santa Cruz), `20 50` → PA-005 (Chã de Fazenda, Paul), `24 34` → PR-049 (Praia), `29 50` → SM-062 (São Miguel), `31 00` → TA-014 (Lugar de Fazenda), `32 50` → TA-021 (Porto Fazenda), `34 50` → TA-022 (Tarrafal); `Achadinha 11 00`, `12 50`, `13 50` → CA-028, CA-144, CA-194 (three zones of Santa Catarina), `Achadinha 15 00` → PR-048, `25 10` → TA-046; `Tarrafal 11 00`, `15 00`, `30 00` → PN-001, RG-104, TA-020; `São Filipe 21 30`, `45 00` → PR-024, PR-026; `Fazenda 52 29` is refused. `test-vectors-registry.json → sameName` gives the first issued code of every zone of Fazenda (four of its seven zones share it only after shortening), Achadinha, São Pedro and Bela Vista, each with its `officialName` and every form.

**Renamed or disputed bairros.** The code never changes. A new official name becomes the zone's `officialName` and the old one stays an alias (subject to the collision rule above). A boundary dispute changes nothing, because a lote's zone is fixed in the registry at issue.

**New settlements.** 15 or more new lotes more than 1.5 km from every zone form a new zone with the next index, named with the residents and the Câmara Municipal. If its name exists, `new_zone()` gives it a block from that name's spare units.

### 3.5 Postcode context

Each municipality has a postal prefix (the first two digits seen on Correios codes) and there is a table of known postcodes with sources. A lote's postcode is set in the registry from a verified source: Correios, the municipality, or an OSM `addr:postcode`. It is never computed from the N-Ways code. Praia's postcodes are 7600–7602, not the "74" the national geographic code would suggest.

### 3.6 Coverage mask: official addresses first, a home code everywhere

**Rule:** where the government already has an address, N-Ways uses it as written and shows it first. **Every building still has its home code**, the officially numbered ones included, so one kind of code works for every home in the country and an official address and a home code never compete. In Cabo Verde the government address is the **street name and door number given by a Câmara Municipal** (Decreto-Lei 5/2012), or a future national address register. The Correios 4-digit postcode is area-level and does not count. The door-level model still applies under it and maps to it (§3.5).

Every lote has a `coverage` value:

| Value | Meaning | What the app shows | Home code |
|---|---|---|---|
| `official` | the lote's entrance is on a street the municipality has named and numbered, and its number is known | the official address **exactly as the municipality writes it** first, `Rua Barragem de Figueira Gorda 142, Praia · 7600`, with the home code beside it, `Cidadela 10 88` | issued |
| `official-pending` | the area is known or presumed to be municipally numbered, but the register is not yet shared | the home code, `Platô 12 78`; the door number joins it once the Câmara shares its register | issued |
| `nways` | nothing official exists | the home code `Palmarejo 19 22` | issued |

**How the boundary is drawn.** The unit is the street frontage, not the zone. Sources, best first:
1. the Câmara Municipal's register of streets and door numbers, or a national register, when shared;
2. door plates photographed in the app and agreed by two or more people, where the number follows the municipal numbering of that street;
3. OpenStreetMap `addr:street` + `addr:housenumber` as evidence, until 1 or 2 confirms it.

A street becomes `official` when source 1 covers it, or when sources 2–3 show municipal numbering along it. Every lote fronting it then follows the mask, including lotes whose number is not yet known: those are asked for the number on their door. Areas presumed numbered (Platô in Praia, the historic centre of Mindelo; boxes in `PRESUMED_OFFICIAL`) are `official-pending` until the Câmara confirms. Every lote, whatever its coverage, has its home code.

**How it grows.** The mask is published with the registry: `coverage` and `official_address` are columns of every `registry/<KEY>.csv`. It is rebuilt with every release. When a municipality numbers a street or a bairro that already has N-Ways codes, `hand_over()` applies:
- the official address becomes the lote's address and is shown first;
- the home code stays and resolves to the same door (a plate, a saved contact or a parcel label with it still works);
- its number is never given to another home;
- new homes there get the official number and a home code too.

The mask only ever moves towards official coverage. It never moves back.

**State in October 2026.** No national address register exists and no municipal register is published:
- Praia's municipal website was unreachable on 18 Oct 2026.
- São Vicente's Câmara has a councillor for "Solos, informação geográfica, cadastro e toponímia municipais", but publishes no register.
- INGT's toponymy page returns 404. Its Portal do Cadastro issues cadastral and location plans and CIPs, which identify parcels, not addresses.

Evidence of municipal numbering in the map: 273 OSM buildings with house numbers. They are mostly on the planned streets of western Praia (Rua Barragem de Figueira Gorda, Rua Barragem de Faveta…) and in Santa Maria, Sal (174 with numbers but no street). With the presumed areas, the mask gives 96 lotes `official`, 1,299 `official-pending` and 174,235 `nways` (`registry/<KEY>.csv → coverage`). Each Câmara is asked for its register; its streets become `official` when it is shared.

### 3.7 Plate names: at most 12 characters and 2 words

**Rule.** Map names used raw are too long to say, write or paint (*Lote Achada São Filipe 21 29*; 632 of 1,778 zone names are over 12 characters). The name in a home code is the zone's **plate name**:
- at most `MAX_CHARS` = 12 characters of its NFC form, every character counting one (letters, spaces, hyphens, apostrophes, dots; an accented letter is one);
- at most `MAX_WORDS` = 2 words; a word is a part between spaces or hyphens that is not a linking word (`de da do das dos d' e o a os as em na no di du`); `Lém-Ferreira` is 2 words, `Chã de Areia` is 2;
- no digit.

`cv_engine.plate_ok()` tests this (`reference/plate_names.py → fits`). The register loader MUST refuse a name over the limit unless every zone of it is flagged `needsCouncilChoice` (a provisional name: its codes are issued provisional with that name; when the Câmara chooses, the plate name changes once and every number, block and machine form stays).

Every zone record carries `officialName` (the full map or municipal name; printed small on the card and the plate, `format_plate → official`, `format_home(full=True)`; never required) and `name` (the plate name), plus `plateRule` (`as-is`, `abbreviated`, `known`, `distinctive`, `council`), `needsCouncilChoice`, and when flagged `plateCandidates` (≤ 3, the first is the provisional `name`) and `plateReason`; a documented short form has `plateSource`.

**Derivation** (`plate_names.derive`, configured in `tools/build_names.py` for Portuguese with Cabo Verde lists):
1. `KNOWN`: a documented short form, with its source: Achada Santo António → `ASA`, Achada Grande Frente → `AGF` (SOURCES.md). AGT (Achada Grande Trás) has no published source and stays an alias.
2. Clean: drop text in brackets, after a slash, a second spelling, and generic words (Lote, Lotes, Loteamento, Bairro, Zona, Condomínio/Condóminio, Casa Para Todos, Conjunto Habitacional, Povoação, Urbanização, Localidade, Complexo, village/villagem), each only if what is left still has a real name word; linking words left at an end go too. A reduplicated word stays (Bel Bel).
3. Fits → plate name (`as-is` or `cleaned`).
4. A name "Entre X e Y" → council.
5. Abbreviate a binding prefix followed by its name: Nossa Senhora → N. Sra, Santo → Sto, Santa → Sta, São → S. (`name_key` expands them back) → `abbreviated`.
6. Candidates: every run of whole units (a hyphen compound is one unit, an elided `d'` its own) with ≤ 2 content words and ≤ 12 characters, not starting or ending on a linking word, not cutting a binding word from its name (São | Filipe, Nho | Lobo, João | Vaz), not only weak or head words. Score: Σ 1 / (number of official names containing the word) over non-weak, non-head words, + 0.25 per weak word, × 1.5 if it ends on the name's last content word, × 0.1 if it drops a trailing qualifier (a weak word after the first real word: Grande, de Cima, Branco…).
7. The best candidate is taken (`distinctive`) only if its score is ≥ 1.5 × the next, it drops no qualifier, it has ≥ 4 letters and its key is not in `AVOID`. `AVOID` = the 22 municipality names and seats, the islands (with Santa Luzia), regional capitals (Dakar, Abidjan, … São Tomé, Lisboa, Santa Maria) and countries (Portugal, Espanha, França, Brasil, Angola, Cuba, Madeira, Genebra…), minus the zone's own municipality and seat.
8. Else, and also when the cleaned name is exactly two real words (`Figueira Gorda`), when the official name is itself a town, when only a weak word is left, when a spelt numeral is over the limit (`África 70` → *África Setenta*, 14), and for the names in `COUNCIL` (read by eye): `council`, `needsCouncilChoice = true`, up to 3 candidates. With no candidate the cleaned name stays provisionally, over the limit.

Word lists: `plate_names.LINKING / GENERIC / WEAK / HEADS / BINDING / ABBREV` (shared rule), plus `build_names.GENERIC_EXTRA / WEAK_EXTRA / HEADS_EXTRA / COUNCIL` (Cabo Verde).

**Aliases.** Every official name (and its spelt numeral form) is an alias of its plate name. An alias whose key is another plate name's key, or that two plate names claim, is dropped (`names.json → droppedAliases`; zone `droppedAliases`). The register has none. `parse` reads `África 70 230` as the name `África 70` and the number 230 when the shorter reading owns no such number.

**Counts** (`model/building-stats.json → names.plateNames`): official names over the limit 632 of 1,778 (over 12 characters 632, over 2 words 135); as-is 1,146; distinctive 316; abbreviated 8; known 2; council 306, of which 118 still over the limit provisionally. 130 plate names are shared only because of shortening. Longest code with an unflagged plate name: `Vila Miséria 25 99`.

**Test vectors** (`test-vectors.json`): `plateNames` gives official → plate for Lote Achada São Filipe → `São Filipe 21 30` (council: equals Fogo's town), Achada Santo António → `ASA` (known, with source), Monte Vermelho (council, no fitting candidate), Casa Para Todos-Ribeira de Julião → `Julião`, Entre Chã de Alecrim e Madeiralzinho → `Alecrim` (council), Cidade das Pombas (Eito de Baixo) → `Pombas`, África 70 → `África` (council), Chã de João Vaz → `João Vaz`, each with the official name typed decoding to the same zone; `collideAfterShortening`: Achada Fazenda `Fazenda 12 34` → CR-078 (Santa Cruz), Lugar de Fazenda `Fazenda 31 00` → TA-014 (Tarrafal), Chã de Fazenda `Fazenda 20 50` → PA-005 (Paul); `overLimitRefused`.

## 4. Check digit: Damm

The check digit is not part of what anyone remembers, and people never see it: plates, cards and written forms show the name and number only. It exists only in the machine form, which systems exchange and which a plate carries in its QR code.

```
digits = national name index (4) + number (3, 4 or 5)
T = Damm's totally anti-symmetric quasigroup of order 10 (cv_engine.DAMM)
i = 0;  for d in digits: i = T[i][d]
check = i
valid  ⇔ running the loop over digits + check ends with i == 0
```

**Binding name, number and area.** Inside a name every number has exactly one owning zone, frozen at issue, so name + number determine the area. The zone digits are deliberately **not** in the data string: then a one-digit slip in the number is always a one-digit change of the string, which Damm always detects, including a slip that lands in another zone of the same name. The machine form's municipality key MUST equal the owner's municipality.

The self-test confirms:
- every single-digit substitution and every adjacent transposition of every 3- and 4-digit number under four name indices, and of a sample of 5-digit numbers, is detected; the published vector 572 → 4 holds;
- **92,701 of 92,701** single-digit slips that land in another zone of the same name (25 numbers from every block of every repeated name) are refused by the machine form's check digit; another 140,407 slips land on numbers no zone owns;
- **22,952 of 22,952** corrupted machine forms (one wrong digit in name index or number, an adjacent swap, or the wrong municipality key) are refused.

**Alternative rejected.** ISO/IEC 7064 MOD 11,10 over municipality, zone and number misses about 2 % of adjacent transpositions (12/21, 56/65, 09/90…), and with the zone digits in the string it catches only 90.6 % of cross-zone slips.

A remembered code typed or heard without the check digit is protected two other ways. First, sparseness: at ×3 headroom about two numbers in three are unused, so a slip usually lands on no home. Second, confirmation: the app always shows what a code points to, with its municipality, for example "casa de 2 pisos, Palmarejo, Praia, perto da Praça Center", before it starts navigation.

## 5. Number length: the arithmetic

### 5.1 Units and lengths

```
headroom h = 3   (Cabo Verde's buildings grew 31 % from 2010 to 2021, 114,297 → 150,016;
                  peri-urban Praia faster; ×3 keeps about two free numbers between neighbours)
length  range         unit   units   the unit is
3       100–999       100    1–9     the first digit   (2 14)
4       1000–9999     100    10–99   the first pair    (12 34)
5       10000–99999   1000   10–99   the first pair    (12 345)
zone z of a name needs u(z) = max(1, ceil(h × lotes(z) / unit)) units
a name has the shortest length with Σ u(z) + RESERVE_UNITS (2) ≤ units; none fits → qualifier (§3.4)
```

A zone alone with its name: 3 digits up to 233 lotes, 4 up to 2,933; a name's zones together fit 5 digits up to 29,333 lotes.

| Name | Zones (lotes) | Units | Digits | Blocks | Spacing |
|---|---|---|---|---|---|
| a povoação alone | 40 | 2 | 3 | 100–299 | 5.0 |
| João Vaz (Chã de João Vaz, Paul) | 57 | 2 | 3 | 100–299 | 3.5 |
| Fazenda (seven zones) | CR 309, PA 59, PR 230, SM 17, TA 37, 4, 49 | 10 + 2 + 7 + 1 + 2 + 1 + 2 | 4 | 1000–1999, 2000–2199, 2200–2899, 2900–2999, 3000–3199, 3200–3299, 3300–3499 | 3.2, 3.4, 3.0, 5.9, 5.4, 25, 4.1 |
| Platô (Praia) | 624 | 19 | 4 | 1000–2899 | 3.0 |
| ASA, Achada Santo António (Praia) | 2,855 | 86 | 4 | 1000–9599 | 3.0 |

### 5.2 Effect on the register

1,349 zones have 3 digits and 429 have 4 (keyed on official names it would be 1,501 and 277; numbered zone by zone, without shared ranges, 1,669 and 110). Sharing a range puts 276 zones on 4 digits that would have 3 alone (124 when keyed on official names): shorter names are shared more. No zone needs 5 digits.

### 5.3 Growth

No issued number changes, and a number never moves to another zone.
1. A zone whose blocks are full takes the **lowest free unit of its name** (`take_block`) and continues there at the same relative Hilbert position. Vector `overflow`: Fazenda of Tarrafal (TA-022, `3300–3499` full) gets `3500–3599` and its next home is **`Fazenda 35 05`**.
2. A **new zone with an existing name** gets a block of `u(z)` units from the name's spare units (`new_zone`). Vector `newZoneSameName`: a new 40-lote Fazenda gets `3600–3799`.
3. A name whose range is full **opens the next length**: its whole range there is free for new blocks. Vector `nameOpensNextLength`: a 3-digit name with all 9 units used gets `1000–1099`.
4. A name that has used 5 digits up MUST be split by a qualifier for its new zones.

## 6. Spot layer: Plus Codes

Correios de Cabo Verde adopted Open Location Code for Morada Certa in 2016, so the spot layer **is** OLC. The engine implements encode, decode and shortening from the public specification. The Zurich vector `47.365590, 8.524997 → 8FVC9G8F+6X` is in the self-test.

- **Length.** 11 digits (about 3.5 × 2.8 m) for gates, doors and dense towns; 10 digits (about 14 m) for rural homes and for sharing a spot.
- **Short form.** Drop 6 digits when the reference locality is within 0.015°, else 4 digits when within 0.3°: `9V+X5 Praia`.
- **Clipping.** Spot codes are given on land only (§3.2).

The spot code is what the app shows before a home has a lote code. It is not the home code people are asked to remember.

## 7. Building the registry

The registry is the single source of home codes. Each municipality is built once at first issue; after that, only insertions (§7.4) and status changes happen.

### 7.1 Order of operations

1. **Ingest footprints.** OSM buildings (`osm:way/<id>`, `osm:relation/<id>`) and the Google/Microsoft footprints N-Ways adds where OSM has none (`nw:` + the first 12 hex characters of the SHA-1 of the point-on-surface to 1e-6° and the area to 1 m²). Across map updates a footprint matches its earlier self at intersection-over-union ≥ 0.5.
2. **Keep Cabo Verde's own.** A footprint whose centre, an enclosure whose centre, or a gate more than 300 m outside the full national border (§3.2) is dropped before anything else is done, and a lote whose anchor still lies beyond it is never written (`tools/building_stats.py`, `tools/issue_registry.py`). **Assign the municipality** by point-on-surface against the full outlines.
3. **Group structures into lotes before anything is numbered.**
   - **A, enclosure.** Footprints inside the same N-Ways enclosure (`data/valhalla/compounds.geojsonseq`: schools, hospitals, barracks, government sites, hotels) form one lote, with confidence 0.8.
   - **A2, estate.** An enclosure of 2 ha or more with 20 or more footprints (a resort on Sal or Boa Vista, a condominium) becomes an **estate**: a record with a name and gates. The houses inside it are grouped by the other rules. A route goes to the estate gate, then to the lote.
   - **B, rural annexe.** A footprint under 30 m², within 4 m of one of 40 m² or more, where fewer than 40 footprints lie within 100 m, joins that lote: an outdoor kitchen, latrine, water tank or curral. Confidence 0.5.
   - **C, terraced houses.** In towns, touching footprints are never merged, because each is a household.
   - **D, people.** "These buildings are one home", "this is the gate", "this footprint is two houses". The last is common where imagery merges a terraced row: Praia's map holds 6 % fewer footprints than the 2021 census counted buildings. These changes are applied after agreement and never alter an issued code (§9).
4. **Anchor.** The gate if one is known (`data/valhalla/gates.geojsonseq` within 11 m of the enclosure edge), else the point-on-surface of the main structure (the largest by floor area, then by footprint).
5. **Zones** (§3.3): each lote takes its zone. **Coverage** (§3.6): lotes marked `official` or `official-pending` are recorded with their official address, or flagged pending. **Every lote**, whatever its coverage, goes on to steps 6–8 and takes a number.
6. **Names** (§3.7, §3.4): `tools/build_names.py` derives every zone's plate name from its official name, folds the plate name to its key, plans each name's range and gives every zone its block(s).
7. **Hilbert index** of the anchor over the zone's box (§7.2), then **sort** by (Hilbert index, main structure id).
8. **Number** within the zone's block (§7.3).
9. **Index structures:** 1 is the main structure, then by footprint area descending, then by id. **Index entrances:** 1 is the gate or front door, then in order of confirmation.
10. **Write** `registry/<KEY>.csv`, `registry/zones.csv`, `registry/names.csv` (key, index, plate name, official names, digits, blocks, reserve, aliases, needsCouncilChoice), `registry/lotes.csv.gz` (numbering anchors, entrance sources, enclosures), `registry/structures/<KEY>.csv.gz` (building profiles and footprints) and a manifest (counts, SHA-256 of every file uncompressed, export date, engine version).

### 7.2 Hilbert index

The box maps onto a 2^16 × 2^16 grid: `x = round((lon − west)/(east − west) × 65535)`, and `y` likewise, both clamped. The engine uses the standard iterative `xy2d` (`hilbert_index`). Each zone's box is the box of its lotes plus 300 m, frozen at issue. Neighbours on the ground get near numbers, so in a terraced street the numbers run along the street.

### 7.3 First-issue spreading

For a zone with n lotes and block [lo, hi], the k-th lote (0-based, in Hilbert order) gets

```
number_k = lo + floor((k + 0.5) × (hi − lo + 1) / n)
```

A build MUST fail if 3n exceeds the block; `plan_name` never produces such a block.

### 7.4 Insertion: "Add my home" and new buildings

0. **Border.** A point more than 300 m outside the national border (§3.2) is refused before any other rule, whatever its municipality or zone.
1. **Zone.** Another door of a lote takes that lote's zone (within 80 m of its entrance). A new building takes the zone of the nearest live code within 3 km in the same municipality, else the zone whose anchor is nearest, unless it starts a new settlement (§3.4). A point within 3 m of a live code's entrance or footprint, inside a footprint, or whose outline shares more than half of the smaller of itself and an existing footprint, already has its code and is refused.
2. **Neighbours.** Compute the Hilbert index h in the zone's box and find the issued numbers a and b of that zone's block immediately before and after h in Hilbert order. At the ends use lo − 1 and hi + 1.
3. If `b − a > 1`, the number is `floor((a + b) / 2)`. Otherwise take the nearest free number in the zone's blocks. If they are full, take a new block (§5.3). The number is never in another zone's block.
4. The number is **reserved** at once with status `provisional` and becomes `issued` on confirmation (§8.6). A provisional number that is withdrawn is **retired**, never given to another home.

Test vectors:

- **Toy** (`test-vectors.json → registryToy`). Six lotes over a small box in Palmarejo's block (`1000–3899`) get `12 41, 17 25, 22 08, 26 91, 31 75, 36 58`. A new home at 14.9232, −23.5348 falls between 26 91 and 31 75 in Hilbert order and gets **`Palmarejo 29 33` (PR-0973-2933-7)**.
- **Registry** (`test-vectors-registry.json → insertion`). On the issued state of Belem, Brava (BR-034, 18 codes in `100–199`), a new building at 14.8664528, −24.6885324 falls between `Belem 108` and `Belem 113` in Hilbert order and gets **`Belem 110` (BR-0143-110-1)**. The registry server's tests replay 107 such issues, up to the block filling and taking the extension block `800–899`, against the N-Ways issuer (`server/testdata/parity.json`).

Only the registry server inserts, and only one server per country issues (the designated issuer, `server/README.md`). Phones never mint home codes, so no two homes can share one, even offline.

## 8. Building profile

### 8.1 Records

The **lote** carries:
- the home and machine codes and the zone;
- municipality, island and postcode {value, status, source};
- the street and door number from the municipality, where they exist;
- the NIP, only if the owner shows a CIP;
- use class, plot area, structure count, total floor area;
- gates, estate, status and issue date.

Each **structure** carries:
- its code with the structure index;
- building id, class, class confidence, class source and status;
- footprint area (m²), perimeter (m), height (m), floors and floor area (m²);
- a name, for businesses and public buildings only;
- entrances [{index, kind, plusCode, confirmedSince}];
- a source and a last-confirmed date for each attribute.

The full schema with examples is in [`../model/design.json`](../model/design.json) → `buildingProfile.schema`.

### 8.2 Use classes and inference

Cabo Verde's taxonomy:
- **homes:** moradia; prédio de habitação (multi-storey family buildings, often built floor by floor); habitação precária (barraca, casa de bidão, contentor);
- **mixed:** misto (shop below, home above);
- **commerce and services:** loja, mercado, quiosque, armazém, restauração, escritório/banco;
- **tourism:** hotel/resort, pensão;
- **public:** governo, segurança, defesa, educação, saúde, religioso;
- **industry and infrastructure:** indústria (desalination and power plants), oficina, utilidade, transporte, combustível;
- **other:** agrícola (curral, trapiche, estufa), desporto, cultura, anexo, desconhecido.

The first rule that fires sets the class, its confidence and its source:

| # | Signal | Confidence |
|---|---|---|
| 1 | OSM use tag on the footprint (amenity, shop, tourism, office, government, healthcare, aeroway, man_made) | 0.9 |
| 2 | OSM `building=*` value | 0.3–0.95 |
| 3 | N-Ways place inside the footprint; a shop-type place in a small building of 2+ floors gives misto | 0.55–0.8 |
| 4 | Annexe in a lote (rule B) | 0.55 |
| 5 | Size and context: under 12 m² anexo; 2,500 m² or more and 2 floors or fewer, armazém; Sal and Boa Vista outside towns at 150 m² or more, resort; 3+ floors, prédio | 0.35–0.5 |
| 6 | Prior: moradia (census 2021: 87.0 % of classic buildings are homes only) | 0.5–0.6 |
| 7 | People and partners: door confirmations, the owner, couriers, the municipality | 0.9–0.99; overrides 1–6 |

### 8.3 Size

- **Area and perimeter:** geodesic, on the WGS 84 spheroid.
- **Height:** OSM `height`, else `building:levels` × 3.0 m. The machine-learned height field of the footprint dataset is **not used**: it carries the Overture height where there is one, else floors × 3.2 + 1, else a rendering filler 3.5 + 3.5 × (hash mod 1000)/1000, and in Cabo Verde every value is that filler (spread evenly from 3.5 to 7.0 m), so `ML_HEIGHT_TRUSTED = False`.
- **Floors:** `building:levels`, else round(height / 3), else unknown.
- **Floor area:** footprint × floors. When floors are unknown it is shown as a lower bound (footprint × 1).

### 8.4 Status

em uso; inacabado mas habitado (27.7 % of buildings in the 2021 census were unfinished, usually with an occupied lower floor); em construção; ruína; abandonado; demolido. Status is separate from class.

### 8.5 Public and private

- **Public:** codes, structures, classes, statuses, confirmed entrances and gates, names of businesses and public buildings, municipal street addresses, postcodes.
- **Private** (held, not published): household counts beyond "one" or "several", owner accounts, gate photos (deleted after confirmation), "Add my home" tracks.
- **Never stored:** residents' names, who lives where, interior images, anything about the people inside.

### 8.6 "Add my home"

1. **Gate.** GPS is averaged for 10–20 s at the gate or front door and one gate photo is taken. The spot code shows at once, offline.
2. **Outline,** by one of three methods:
   - (a) tap corners on imagery;
   - (b) walk the inside of the wall with the camera (ARKit/ARCore world tracking, GPS averaged over the walk, snapped to imagery and nearby footprints);
   - (c) import a survey plan with beacon coordinates in **EPSG:4826 WGS 84 / Cape Verde National** (Lambert Conformal Conic; φ1 15°N, φ2 16°40′N, φ0 15°50′N, λ0 24°W; FE 161,587.83 m, FN 128,511.202 m) or in WGS 84, typed or photographed, or an INGT parcel by NIP on cadastral islands (Sal, Boa Vista, Maio, São Vicente).
3. **Describe:** households (a number), structures, floors, use, and whether it is finished or still being built.
4. **Provisional code** by §7.4, issued on the next connection. It can go on the gate the same day.
5. **Confirmed** when deliveries or visits arrive at the gate, no neighbour disputes it within 30 days, or new imagery shows the structure.

Checks run before a code is issued:
- the gate is on the outline (within 3 m);
- the outline is a closed loop;
- the area is between 12 m² and 2 ha;
- the GPS and AR tracks agree within 5 m;
- the outline is not in the sea, a ribeira bed or a road;
- it does not overlap an existing lote, cadastral parcel or public space (an overlap is flagged, not issued).

The flow states, in Portuguese and Kriolu, that **a code is an address, not a land title**. Only the outline and the gate photo are kept: no video, no interior.

### 8.7 Getting the code: steps

| Way | Steps |
|---|---|
| App, home saved | 0: "O teu código de casa: Palmarejo 12 34" on the home screen |
| App, standing at the gate | 1: "É a minha casa?" → Sim |
| Share | 1 tap: WhatsApp or SMS link `nways.ng/a/PR-0973-1234-0`, with the code in words |
| Plate or sticker | 0: printed code and a QR code carrying the machine form |
| New building | Add my home, 5 steps (§8.6) |
| Partner lookup | only from a code the customer gave, or with the customer's consent; never a search by person |

An SMS lookup service is a possible later option, not part of this design.

## 9. Stability

- A home code is never moved or reused. The zone name may change (§3.4) but the number never does.
- A name's blocks are frozen at issue and never renumbered; growth only adds blocks (§5.3).
- A demolished building's code is retired with status demolido.
- **Split lote:** the original code stays with the part that has the primary entrance; the other part gets a new number (§7.4).
- **Merged lotes:** both codes stay valid. The lower becomes primary and the other an alias.
- Regrouping structures never changes an issued code. Structure and entrance indices are never reused.
- A municipal boundary change changes nothing: the key, the zone and its blocks are fixed at issue.

## 10. Offline behaviour and shipped data

| File | Size | Use |
|---|---|---|
| `data/municipalities.geojson` | 142 kB | point to municipality and island |
| `data/border.geojson` | 2 kB | the national border, simplified, with its measured deviation: the 300 m rule (§3.2) |
| `data/zones.json` → `registry/zones.csv` | 760 kB as readable JSON; 230 kB as CSV | official and plate names, aliases, boxes, blocks |
| `data/names.json` → `registry/names.csv` | 410 kB as JSON; 113 kB as CSV | name keys, indices, blocks, reserves: what makes `Name NNNN` decode offline |
| key table (in code) | < 2 kB | keys, indices, islands, postal prefixes |
| `registry/<KEY>.csv` | 31 MB for all of Cabo Verde (175,630 codes), about 6 MB gzipped; 0.5 to 6 MB per municipality | home code → lote, entrance, profile summary |
| `registry/lotes.csv.gz`, `registry/structures/<KEY>.csv.gz` | 2 MB and 11 MB gzipped | numbering anchors; building profiles and footprints |

Offline, the following all work: spot codes, home and machine code parsing, check digits, spoken forms, municipality and island lookup, and code-to-place for downloaded municipalities. Home codes are never minted offline. "Add my home" stores the gate, outline and description and gets its number on the next connection.

## 11. Conformance

An implementation conforms if it:
- reproduces every value in `test-vectors.json`: home, machine and plate forms, check digits, spoken forms, number lengths and blocks, the plate names and their official names, the same-name decodings (including names that collide only after shortening), the toy registry, its insertion, the three growth cases and the coverage mask (official lote, official-pending area, N-Ways area, hand-over alias);
- decodes every `Name NNNN` to exactly one zone using the name register alone, from the plate name or the official name, refuses numbers no zone owns, and never uses context to choose;
- refuses a register name over 12 characters or 2 words unless it is flagged `needsCouncilChoice`;
- detects every corrupted code in `self_test()`;
- refuses spot codes at sea.

`python3 engine/reference/test_cv.py` runs the self-test, checks the vectors reproduce, checks the registry vectors decode and format, checks that the name register reproduces from its rules (`tools/build_names.py`) and matches the published registry. `python3 tools/registry_vectors.py --check` rebuilds the registry vectors from `registry/`.
