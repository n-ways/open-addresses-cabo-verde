# The Cabo Verde model

Status: in force. Every lote of the country has its code, issued on 19 and 20 October 2026; the registry is published in [`../registry/`](../registry/README.md) and the model is open (see [LICENSING.md](../LICENSING.md)). Machine-readable version: [`../model/design.json`](../model/design.json). Engine: [`../engine/SPEC.md`](../engine/SPEC.md). Existing systems: [`existing-systems.md`](existing-systems.md).

This model is for Cabo Verde only, and every choice below is argued from Cabo Verde's own facts.

## 1. The format in one line

> **A home code is the short name of your bairro, zona or povoação and a 3- or 4-digit number: `Palmarejo 12 34`, `João Vaz 214`, `São Filipe 21 29`, `Fazenda 34 48`. It is unique in the whole country on its own.**

The name in the code is the **plate name**: at most 12 characters and 2 words (§3.5). Map names used raw are too long for a plate, a form field or one breath (*Lote Achada São Filipe 21 29*). The full name, here *Lote Achada São Filipe*, stays as the zone's **official name**: printed small on the card and the plate, never required, and it still decodes when typed.

Nothing is typed or said after it. People give their code without context, on the phone, on a form or to a courier from another island, so a code that needed the municipality or island to be told apart from another would fail exactly when it is needed. Cabo Verde repeats names, and shortening repeats more of them: seven zones have the plate name Fazenda (Achada Fazenda, Chã de Fazenda, Lugar de Fazenda, Porto Fazenda and three plain Fazendas) and eight are Achadinha. So every zone with the same plate name draws its numbers from **one national range for that name**, cut into blocks: `Fazenda 12 34` is Achada Fazenda in Santa Cruz, `Fazenda 24 33` is in Praia, `Fazenda 29 50` in São Miguel and `Fazenda 34 48` in Tarrafal (§3.4). The municipality and island are still printed on the card and the plate, for information only. Behind each home code there is:

- a **machine form** `PR-0973-1234-0` (municipality key, national name index, number, check digit), used by systems and carried in the QR code of a plate; people never see its check digit;
- a **lote** (plot or compound) with its structures, each carrying a building profile;
- a **primary entrance** (the gate or front door) where navigation ends;
- a **spot code**, the Plus Code that Correios de Cabo Verde adopted in 2016, for any point on land;
- the **Correios postcode**, the municipal street address and the cadastral NIP where they exist, shown beside it and never replaced.

### 1.1 Official addresses first: the coverage mask

The rule: **where the government already has an address, N-Ways uses it as written and shows it first; every building still has its home code**, so that one kind of code works for every home in the country and an official address and a home code never compete. In Cabo Verde the government address means the street names and door numbers ("números de polícia") given by the Câmaras Municipais under Decreto-Lei 5/2012, and any future national address register. There, the app shows the address exactly as the municipality writes it, for example `Rua Barragem de Figueira Gorda 142, Praia · 7600`, with the home code beside it: `Cidadela 10 88`. The Correios postcode is area-level, so it does not count as a door-level address: the model applies under it and maps to it.

Each lote is marked **official**, **official-pending** or **N-Ways** (SPEC §3.6):
- **official**: on a numbered street with a known number;
- **official-pending**: an area presumed numbered whose register is not yet shared (Platô, the historic centre of Mindelo);
- **N-Ways**: nothing official exists.

The boundary follows street frontages and is drawn from:
1. the municipal register when shared;
2. door plates people confirm;
3. OpenStreetMap house numbers as evidence.

When a municipality later numbers an area, its address is shown first. The home code stays and leads to the same door, and its number is never reused.

We found **no national address register and no published municipal register** (October 2026). Praia's municipal site was unreachable; São Vicente has a councillor for toponymy and cadastre but publishes no register; INGT's cadastre portal identifies parcels, not addresses. So in the registry 96 lotes have an official address, 1,299 are official-pending and 174,235 (99.2 %) have nothing official. **All 175,630 have a home code.** Official coverage starts with Platô, central Mindelo, the numbered planned streets of western Praia and Santa Maria on Sal, and grows as each Câmara shares its register.

## 2. First criterion: people remember it and get it without effort

An address works only if people can remember it and get it without effort, so memorability comes before elegance, before the shortest code and before the neatest mathematics.

### 2.1 What people in Cabo Verde already remember

- **Their zone.** People give their address by bairro and landmark: "Achada Santo António, perto da Caixa", "Monte Sossego", "Palmarejo Grande". In 2016 Google reported that more than 90 % of roads had no name, so the bairro is the address.
- **Numbers in pairs.** Phone numbers have seven digits, written and said in groups. Door numbers in Platô and Mindelo are two or three digits.
- **Not letters.** Nobody's address in Cabo Verde contains letter strings. Portuguese letter names also rhyme in two big families (bê cê dê gê pê quê tê vê zê; efe ele eme ene erre esse), so letters are hard to pass over the phone.

### 2.2 The options weighed

| Option | Example | For | Against | Verdict |
|---|---|---|---|---|
| **Zone name + 3–4 digits** | Palmarejo 12 34 | the name people already use; a door-number-sized number; the same words in Portuguese and Kriolu; any keypad | names are often too long to say (632 of 1,778 over 12 characters): a short plate name (§3.5); names repeat (254 plate names in 672 zones): one national number range per name (§3.4) | **chosen** |
| Municipality + digits | Praia 48 213 | one word | Praia needs 5 digits: 31,052 lotes × 3 = 93,156 > 9,000; the municipality is not how people describe home in Praia | rejected |
| Key + alphanumeric | PR R5H8-R | short, dense | letters people never use for places; rhyming letter names | rejected |
| Digits only, national | 7 digits | phone-like | means nothing; a slip lands on a real home on another island | rejected |
| Plus Code | 9V+X5 Praia | open, offline, Correios precedent | letters and a plus sign; changes every 14 m; says nothing about the house | kept as the spot layer |

### 2.3 The arithmetic

The number range belongs to the **name**, not the zone (§3.4). Each zone of a name gets a **block** of whole units holding its lotes (plots/compounds, §3.3) times 3, and every name keeps **2 units free** for zones of that name created later. The name's length is the shortest that holds all its blocks and the reserve:

```
length   numbers       unit         units      a name fits if  Σ ceil(3 × lotes / unit) + 2 ≤ units
3        100–999       100 numbers  1–9        (the unit is the first digit: 2 14)
4        1000–9999     100 numbers  10–99      (the unit is the first pair: 12 34)
5        10000–99999   1000 numbers 10–99      (the unit is the first pair: 12 345)
(no leading zero: people drop it; never more than 5 digits)
```

A zone alone with its name therefore has 3 digits up to 233 lotes and 4 digits up to 2,933. A name whose zones together pass 29,333 lotes would need a qualifier (§3.4); none does.

Why ×3: Cabo Verde's buildings grew 31 % in eleven years (census: 114,297 in 2010, 150,016 in 2021), faster on Praia's edges. ×3 leaves about two free numbers between every pair of neighbours. New homes then get numbers that sit among their neighbours', and two in three possible numbers are unused, so a slip of the tongue usually lands on nothing.

The register as issued (`tools/build_zones.py`, `tools/build_names.py`), with the codes counted in `registry/`:

| | Zones | Lotes |
|---|---|---|
| 3-digit numbers | 1,349 | 77,467 (44 %) |
| 4-digit numbers | 429 | 98,163 (56 %) |
| 5-digit numbers | 0 | 0 |
| Total | 1,778 | 175,630 |

- Median zone: 50 lotes. 90th percentile: 213.
- Largest zone: Achada Santo António (plate name ASA), Praia: 2,855 lotes × 3 = 8,565, so 86 units: `1000–9599`, with `9600–9999` in reserve. 4 digits.
- Praia: 64 zones, 47 of them with 4 digits, for example Pensamento (2,435), Safende (1,671), Palmarejo (938), Platô (624), Fazenda (230; 4 digits because it shares its plate name with six other zones).
- Sharing a range puts 276 zones on 4 digits that would have 3 alone (124 before plate names: shorter names collide more). That is the price of codes that are short and need no context.

So more than four homes in ten in Cabo Verde have a **three-digit** number, and none needs more than four. When a zone's block fills up, it takes a new block from its name's spare units; when the name's range is full, the name continues in the next length. No issued number changes.

### 2.4 Saying it

- Three digits are said like a door number: "João Vaz, duzentos e catorze"; in Kriolu, "duzentu i katorzi".
- Four digits are said as two pairs, like a phone number: "Palmarejo, doze, trinta e quatro"; in Kriolu, "dozi, trinta i kuatu".

The engine's voice does both (SPEC §2.3). The Kriolu number words are to be checked with Santiago and São Vicente speakers before the voice is used.

### 2.5 What nobody has to remember

- **The check digit.** People never see it: plates and written forms show the name and number only. It exists only in the machine form, which systems use and the plate's QR code carries.
- **The machine form.** It is for systems.
- **The official name.** `São Filipe 21 29` is enough; *Lote Achada São Filipe* is printed small on the card and the plate for context, and typing it works too.
- **The municipality and island.** The code never needs them: `Fazenda 34 48` is Tarrafal wherever it is said or typed. The app shows them as information. If someone adds one ("Fazenda 24 33, Tarrafal") and it does not match, the app says where the code really is; it never uses it to choose.

A typed or spoken code without its check digit is still protected. Most wrong numbers are unused, and the app always shows what a code points to ("casa de 2 pisos, Fazenda, Tarrafal, perto da escola") before it navigates. That description names the municipality, so a slip into another Fazenda is visible before anyone sets off.

### 2.6 Getting it: zero effort

| Way | Steps |
|---|---|
| N-Ways app with a saved home | **0**: "O teu código de casa: Palmarejo 12 34" is on the home screen |
| Standing at the gate | **1**: "É a minha casa?" → Sim |
| Sharing | **1** tap: WhatsApp or SMS link `nways.ng/a/PR-0973-1234-0` with the code in words |
| Plate or sticker | **0**: the code and a QR code; scanning opens navigation to the gate |
| A new building | **Add my home**, 5 steps (§9) |
| A courier or partner | looks up a code the customer gave, or the customer's address with consent; never a search by person |

An SMS lookup service is a possible later option; it is not part of this design.

## 3. Hierarchy: why the code hangs off the zone, inside the municipality

### 3.1 Levels

| Level | Count | Role in the model | Why |
|---|---|---|---|
| Barlavento / Sotavento | 2 | none | ISO categories with no administration |
| Island | 9 | always displayed | how people place themselves; the island has its own line in the UPU address and is the first digit of the Correios postcode. Not a key, because Santiago alone has 9 municipalities |
| **Municipality (concelho)** | 22 | context on the card; key in the machine form | the elected Câmara Municipal names streets and numbers doors (DL 5/2012) and curates its zone names. It is **not** needed to tell same-named zones apart: the name's national range does that |
| **Zone** (bairro, zona, povoação) | 1,778 | **the place word**: its plate name in the code, its official name on the card; its block in the name's national range | what people already say |
| Lote | 175,630 codes (175,629 lotes of the map, 1 issued since for a new building) | the number | the addressable unit (§6) |
| Structure, entrance, unit | | suffixes and record fields | the shop in the wall, the second gate, the 2nd-floor flat |

### 3.2 Islands and island-hopping

Cabo Verde is nine inhabited islands, linked by ferries and short flights. The same names recur from one island to the next: Ribeira Grande, Tarrafal, Santa Catarina, São Filipe, Ponta do Sol. A courier on Sal handles parcels for Boa Vista, and a family in Praia sends things to Fogo. So the island is shown on every card and plate, but only to inform: the remembered part alone is unique in the whole country. Of the 254 repeated plate names, 132 repeat across islands (São Pedro is on Brava, Santiago and São Vicente; Bela Vista on Santiago, Sal and São Vicente). Their zones sit in different blocks of one range, so `São Pedro 11 99` (Brava), `São Pedro 25 01` (Praia) and `São Pedro 44 99` (São Vicente) never need "Brava" or "São Vicente" after them. The machine form's municipality key is checked against the block's owner.

### 3.3 Zones: how the place word is chosen

1. **Source.** The N-Ways locality layer:
   - OpenStreetMap suburbs and neighbourhoods (the bairros of Praia and Mindelo);
   - OpenStreetMap villages and towns;
   - GeoNames localities that are not landforms (Ponta, Ilhéu, Baía, Pico, Morro and the like are excluded).

   Squares, streets and school points (Largo, Praça, Rua, Escola) are never zones.
2. **One candidate per name.** Within a municipality, the same name within 2 km counts once.
3. **Town names.** In towns the bairro list wins over GeoNames points. A city point with three or more bairros around it is not itself a zone: in Praia people say "Achada Santo António", not "Praia".
4. **Assignment.** Each lote goes to the nearest candidate in its own municipality.
5. **Small zones.** A zone with fewer than 15 lotes merges into its neighbour, unless it is an isolated povoação more than 1.5 km from any other, which keeps its own name.
6. **Index.** Zones are numbered in space-filling order across the municipality, for the machine form.

These rules turn about 3,800 named places into 1,778 zones. Their official names fold to 1,547 keys; their plate names (§3.5) to 1,360. Each Câmara Municipal can rename a zone at any time (the codes stay, §3.4) and chooses the 306 plate names flagged for it.

### 3.4 Same names: one national range per name

A home code must be unique in the **whole country on its own**. Context does not count: neither the phone's position nor a municipality or island typed after a comma. A code that needed a qualifier after it (`Achadinha 214, Paul`) or a bracket in its name (`Achadinha (Mancanha)`) would be longer to say and would fail whenever the qualifier is left out, which is most of the time.

**How it works.**
1. **One key per name.** Plate names (§3.5) are folded to a national key (below). All zones with the same key form one name, so two zones whose official names differ share a range when their plate names agree (Achada Fazenda and Lugar de Fazenda are both `Fazenda`).
2. **One range per name.** The name has one number range for the whole country, cut into **blocks** of whole units: 100 numbers in 3- and 4-digit ranges, 1,000 in 5-digit ranges. Each zone gets the blocks that hold 3 × its lotes. Zones are ordered by municipality index, then zone index, and blocks are given from the bottom of the range. At least 2 units stay free (§2.3).
3. **Decoding.** "Name NNNN" finds the name, then the one block that contains the number, then the zone. A number outside every block is not a home code. There is exactly one answer, anywhere in the country.
4. **Frozen at issue.** A zone's blocks never move and are never renumbered. A zone whose block fills takes the next free unit of its name. A **new zone with an existing name** (a new Achadinha) takes a new block from the name's spare units. When a name's range is full, the name continues in the next length. A municipal boundary change, a renamed zone or a merged pair of zones changes no block.
5. **Qualifier only when 5 digits cannot hold a name.** Such a name is split once, before first issue, by a qualifier people already say, the way "Achada Santo António" is said and not just "Achada". The qualified names are listed in `cv_engine.QUALIFIERS` and `engine/data/names.json`. **None is needed**: the most a name uses is 49 units (Bela Vista).

**Fazenda, seven zones, one range** (four of them share it only through their plate names):

| Block | Zone (official name) | Lotes | Example |
|---|---|---|---|
| 1000–1999 | Achada Fazenda, Santa Cruz (CR-078) | 309 | `Fazenda 12 34` |
| 2000–2199 | Chã de Fazenda, Paul (PA-005) | 59 | `Fazenda 20 49` |
| 2200–2899 | Fazenda, Praia (PR-049) | 229 | `Fazenda 24 33` |
| 2900–2999 | Fazenda, São Miguel (SM-062) | 17 | `Fazenda 29 50` |
| 3000–3199 | Lugar de Fazenda, Tarrafal (TA-014) | 37 | `Fazenda 31 00` |
| 3200–3299 | Porto Fazenda, Tarrafal (TA-021) | 4 | `Fazenda 32 62` |
| 3300–3499 | Fazenda, Tarrafal (TA-022) | 49 | `Fazenda 34 48` |
| 3500–9999 | free for later Fazendas and for growth | | `Fazenda 52 29` is not a code |

**Counts** (`tools/build_names.py` → `model/building-stats.json → names`), keyed on the official names and on the plate names in use:

| | Official names | Plate names |
|---|---|---|
| Distinct names | 1,547 | 1,360 |
| Names used by two or more zones | 163, in 394 zones | **254**, in **672** zones (64,872 lotes) |
| … shared only because of shortening | | 130 names |
| … across municipalities | 148 names; 83 across islands | 207 names; 132 across islands |
| … only inside one municipality | 15 names | 47 names; 208 zones share a plate name with another zone of the same municipality |
| Zones per repeated name | 2: 120; 3: 29; 4: 9; 5: 3; 8: 2 | 2: 162; 3: 56; 4: 23; 5: 3; 6: 2; 7: 5; 8: 2; 10: 1 (Figueira) |
| Repeated names by length | 109 with 3 digits, 54 with 4 | 152 with 3 digits, 102 with 4, none with 5 |
| Zones by length | 1,501 with 3 digits, 277 with 4 | 1,349 with 3 digits, 429 with 4, none with 5 |
| Largest shared range | Bela Vista, 49 units | **Bela Vista**: Praia 1,473 lotes `1000–5499`, Sal 17 `5500–5599`, São Vicente 72 `5600–5899`; 4,900 of 9,000 numbers in blocks, **4 digits** |
| Most zones in one range | Achadinha and Cutelo, 8 | Figueira: 10 zones, 728 lotes, `1000–3699`, 4 digits |
| Qualifiers needed | 0 | 0 |

The three Achadinhas of Santa Catarina are plain `Achadinha 11 00`, `Achadinha 12 52` and `Achadinha 13 50`. The neighbouring zone, by its plate name (Covão Baixo, Isabel, Mancanha), is shown on the card only to help people recognise the place.

**National normalisation (Portuguese and Kriolu).** Two names are the same name when their keys are equal:
- case and accents fold (Platô = PLATO);
- apostrophes, hyphens, dots and slashes become spaces (Lém-Ferreira = Lem Ferreira);
- articles and the prepositions de, da, do, das, dos, d' drop (Chã de Baixo = Chã Baixo, Pé do Monte = Pé de Monte, As Hortas = Hortas, Ponta d'Água = Ponta Água; typed "Ponta dagua" is read both ways);
- abbreviations expand (Sto, Sta, S. → Santo, Santa, São);
- ALUPEC spellings fold to the Portuguese ones: tx and tch = ch, dj = j, k = c or qu (Txada = Chada);
- a numeral in a name is spelt out, because a code never holds two numbers; `África 70` (Espargos) would be *África Setenta*, 14 characters, so it is flagged for the council with `África` as its provisional plate name, and "África 70" typed in full stays an alias;
- the key is taken of the plate name, so a bracketed part of an official name does not reach it (Cidade das Pombas (Eito de Baixo) is `Pombas`, in one range with Cidade das Pombas and Eito de Cima).

These rules join 10 pairs of names that differ only by an article or a preposition (Chã de Baixo/Chã Baixo, Chão de Riba/Chão Riba, Ribeirão de Areia/Ribeirão Areia…). Aliases hold the other forms: every official name, Plateau for Platô, AGT for Achada Grande Trás, the Portuguese and Kriolu spellings the Comissão Nacional de Toponímia keeps side by side (Brava/Djabraba). An alias that is another plate name's key, or that two plate names would claim, is dropped and listed in `engine/data/names.json → droppedAliases` (none in the register).

**Renaming, disputes, new settlements.**
- **Renaming.** The code never changes. The new name becomes the official name and the old one an alias, and the zone keeps its plate name and its blocks. If the Câmara also wants a new plate name and it already belongs to other zones, the two ranges would collide, so the old plate name stays in the code and the new one is shown on the card only (an alias that equals another plate name is dropped).
- **Disputed bairro limits.** A zone is a list of lotes fixed at issue, not a boundary. If neighbours disagree about where Palmarejo ends, nothing changes.
- **New settlements.** 15 or more new lotes far from any zone form a new zone, named with the residents and the municipality. If the name exists, the zone takes a block from that name's spare units.

### 3.5 Plate names: short enough to say

A code is said aloud, written on forms and painted on plates, so its name must be short. Map names used raw are not: 632 of the 1,778 zone names are over 12 characters (135 over 2 words), for example *Entre Chã de Alecrim e Madeiralzinho*, *Casa Para Todos-Ribeira de Julião*, *Cidade das Pombas (Eito de Baixo)*, and a code such as *Lote Achada São Filipe 21 29* is too long to say in one breath. So every zone has two names:

- the **official name**: the full name from the map or the Câmara's list, printed small on the card and the plate, never required; typed, it decodes to the same zone;
- the **plate name**: the name in the code, **at most 12 characters** (a letter, space, hyphen, apostrophe or dot each counts one; an accented letter is one) and **at most 2 words** (de, da, do, das, dos, d', di, du, e do not count; a hyphen separates words: Lém-Ferreira is 2). The code stays short: `São Filipe 21 29`, `ASA 87 63`, `Julião 24 29`.

**How the plate name is derived** (`engine/reference/plate_names.py`, configured in `tools/build_names.py`), in this order:
1. **A documented short form wins**, with its source in the table: `ASA` for Achada Santo António and `AGF` for Achada Grande Frente (Praia press, see `SOURCES.md`). "AGT" for Achada Grande Trás is in the map's alias list, but we found no published use, so it stays an alias and the zone goes to the council.
2. **Clean**: drop generic words (Lote, Bairro, Zona, Condomínio, Casa Para Todos, Povoação, Complexo, villagem), text in brackets or after a slash, and a second spelling ("Vila Baixa (Bila Baxo)"). A word repeated as a name ("Achada Bel Bel", "Moia Moia") stays.
3. If it fits, it is the plate name. Else **Santo, Santa, São, Nossa Senhora** before a name may be written Sto, Sta, S., N. Sra (`Sto António`, `Sta Bárbara`, `S. Sebastião`): the name key expands them back, so the full form typed decodes too.
4. Else **the most distinctive run of whole words** that fits, preferring the specific end of the name: `Lote Achada São Filipe` → `São Filipe`, `Casa Para Todos-Ribeira de Julião` → `Julião`, `Chã de João Vaz` → `João Vaz`. A word is never cut. Landform and settlement heads (Achada, Ribeira, Chã, Cutelo, Lombo, Covão, Curral, Fajã, Casa, Ilhéu…) are the first to go and are never a plate name alone; adjectives (Grande, de Cima, Novo, Branco, Queimado, Formosa…) are never a plate name alone either.
5. **Flag for the Câmara** (`needsCouncilChoice`, with up to 3 candidates; the first is used provisionally, so the zone could be numbered) when the choice is not clear: two words that are both the name (`Figueira Gorda`, `Bernardo Gomes`), every short form drops a qualifier (`Calheta de Baixo` and `Calheta de Cima` would both be `Calheta`), the result would equal a municipality, municipal seat, island, regional capital or country elsewhere (`Achada São Filipe` → `São Filipe` is also Fogo's town; `Alto de Santa Luzia` → `Santa Luzia` is an island), a name "between X and Y", or no run of words fits at all (`Monte Vermelho`, `Ribeira Grande`, `Nossa Senhora da Luz`). Names read by eye and refused are listed in `tools/build_names.py → COUNCIL`. Codes with a flagged plate name are issued provisional with the provisional name; the Câmara's choice changes the name once and keeps every number. The engine refuses an unflagged plate name over the limit.

**A numeral** is spelt out (a code never holds two numbers). `África 70` would be *África Setenta*, 14 characters, so it is flagged with `África` provisionally; "África 70" typed in full still decodes.

**Same plate name, one range.** The national key is taken of the plate name, so zones whose official names differ share a range when their plate names agree (§3.4). Every official name is an alias of its plate name; an alias that two plate names would claim is dropped and listed (none in the register).

**The register** (`model/building-stats.json → names.plateNames`):

| | Zones |
|---|---|
| Official name fits as is | 1,146 |
| Shortened automatically: distinctive words | 316 |
| … abbreviated saint prefix | 8 |
| … documented short form (ASA, AGF) | 2 |
| Flagged for the Câmara (`needsCouncilChoice`) | 306 |
| … of which still over the limit provisionally (no run of whole words fits) | 118 |

- Names shared by two or more zones: 163 in 394 zones keyed on official names, **254 in 672** keyed on plate names; 130 of them are shared only because of shortening (Fazenda, São Filipe, Pombas…). Code lengths: 1,501 zones with 3 digits and 277 with 4 on official names; **1,349 and 429** on plate names; none with 5. The largest shared range is still Bela Vista (4,900 numbers, 4 digits).
- Longest remembered codes: 18 characters among plate names that are not flagged (for example `Vila Miséria 25 98`); overall `Lombo de Nossa Senhora de Luz 198`, a flagged name with no fitting candidate.

## 4. Settlement patterns and the spot layer

Cabo Verde has no computed cell code of its own. The spot layer is the Plus Code, because Correios adopted it for Morada Certa in 2016. The model only chooses which length to offer in each kind of settlement:

| Settlement | Example | Plus Code length | Why |
|---|---|---|---|
| Dense town grid | Platô, Mindelo centre, Achada Santo António | 11 (≈3 m) | terraced houses 5–8 m wide; 14 m would cover two or three doors |
| Hillside bairros and town edges | Praia periphery, Monte Sossego | 11 | close, often unfinished, houses |
| Rural achadas, ribeiras, hill villages | Santo Antão, Fogo, interior Santiago | 10 (≈14 m) | houses tens of metres apart |
| Resorts and condominiums | Santa Maria (Sal), Sal Rei (Boa Vista) | 11 | many units behind one estate gate |

Spot codes are offered on land only. The sea between islands has no addresses, apart from listed ports and marinas.

## 5. Relation to existing systems

| System | Level | How the model relates |
|---|---|---|
| Correios postcode (`7600 PRAIA`) | area: island, municipality, district, office | shown beside the home code when verified; never derived from it. The first digit is the island; Praia is 7600–7602 |
| Morada Certa / Plus Codes | point | the spot layer itself; the home code adds the building, the gate and the profile |
| Street names and door numbers (municipal, DL 5/2012) | door | shown first wherever they exist; the N-Ways code is never painted as a "número de polícia" |
| Cadastre (INGT): NIP, CIP | parcel / title | a lote may carry the NIP as a reference; a code is never a title |
| INE geographic code and census zones | zone | a mapping table if INE publishes zones; census totals used as priors |

## 6. The lote: plot or compound as the addressable unit

The addressable unit is the **lote**: a plot or compound with its structures and its entrance. The home code belongs to the lote. Its structures are sub-units (`Palmarejo 12 34.2`), each with its own building profile, and the **primary entrance is the gate or front door**. A driver is taken there, not to a centroid behind a wall.

Cabo Verde's pattern differs from mainland West Africa:

- **Towns are terraced.** Houses are built wall to wall along streets and up slopes, and most town lotes are one building. The model therefore **never merges touching footprints in towns** (rule C).
- **The reverse case is common.** Imagery often merges a terraced row into one footprint. Praia's map holds 32,591 footprints against the census's 34,663 buildings (−6 %), São Vicente's 18,315 against 23,976 (−24 %). Door confirmations ("this footprint is two houses") split them, and the original code stays with the part that has the first entrance.
- **Rural houses come with annexes.** An outdoor kitchen, a latrine, a water tank, a curral: these join the house's lote (rule B).
- **Enclosed sites** (schools, hospitals, barracks, ministries in Platô) are one lote each (rule A).
- **Resorts and condominiums on Sal and Boa Vista are estates:** an estate gate, then each unit's own lote (rule A2).
- **Prédios with flats** are one lote with units ("2.º Esq."), counted in the record but not named.
- **Shops built into a front wall** are their own structure with their own entrance.

Figures from the registry (`registry/structures/`, `registry/lotes.csv.gz`):

| | Cabo Verde | Praia |
|---|---|---|
| Footprints | 192,272 | 32,591 |
| Lotes (codes) | 175,630 | 31,052 |
| Footprints in multi-structure lotes | 15.2 % | 7.8 % |
| Enclosed lotes (sites) | 453 | 106 |
| Enclosed lotes with a mapped gate | 3.5 % | 7.5 % |
| All lotes with a known gate | 0.009 % | 0.026 % |

Gates are almost unmapped. Capturing them through "Add my home", door confirmations and couriers is therefore the first job after issue.

## 7. Building profile

Every structure carries a profile:
- **use class** with confidence and source;
- **size:** footprint, perimeter, height, floors, floor area;
- a **source and last-confirmed date** for each attribute;
- **entrances**;
- a **name** (businesses and public buildings only);
- a **status**.

Lotes carry use class, plot area, number of structures, total floor area and gates.

**Taxonomy (Cabo Verde's own):**
- homes: moradia; prédio de habitação (built floor by floor); habitação precária (barraca, casa de bidão, contentor, the census "non-classic building");
- mixed: misto (shop below, home above; the census counts 6.5 % "mostly residential");
- commerce and services: loja, mercado (Sucupira), quiosque, armazém, restauração, escritório/banco;
- tourism: hotel/resort (Sal, Boa Vista), pensão;
- public: governo (Platô ministries, câmaras, correios), segurança, defesa, educação, saúde (hospital, centro de saúde, unidade sanitária de base), religioso;
- industry and infrastructure: indústria (desalination plants and power stations, essential on dry islands), oficina, utilidade, transporte, combustível;
- other: agrícola (curral, trapiche for grogue, estufa), desporto, cultura, anexo, desconhecido.

**Status:** em uso; **inacabado mas habitado**; em construção; ruína; abandonado; demolido. The second is a Cabo Verde norm: 27.7 % of buildings nationally and 41.6 % in Praia were unfinished in the 2021 census, usually lived in, with the rebar of the next floor waiting.

**Inference, in order:**
1. OSM use tags (confidence 0.9);
2. OSM building type (0.3–0.95);
3. N-Ways places inside the footprint (0.55–0.8);
4. lote role (annexe, 0.55);
5. size and island context (0.35–0.5);
6. the census prior, homes (0.5–0.6);
7. people and partners (0.9–0.99, overriding all others).

**What the data says.** These are inferences, mostly low or medium confidence:

| | Cabo Verde | Praia | Sal |
|---|---|---|---|
| Residential | 84.1 % | 89.2 % | 61.0 % |
| Annexe | 11.1 % | 6.1 % | 7.3 % |
| Tourism | 1.7 % | 0.1 % | 27.2 % (low confidence) |
| Commerce, food, offices | 0.8 % | 1.9 % | 3.1 % |
| Agricultural | 1.7 % | 2.0 % | 0.3 % |
| High / medium / low confidence | 3.6 / 73.0 / 23.5 % | 4.4 / 75.2 / 20.4 % | 8.0 / 51.8 / 40.2 % |

- Footprint area: median 44.9 m² nationally, 60.8 m² in Praia (quartiles 26.8 and 156.3 m²; 2,405 Praia footprints over 500 m²).
- Height is known for only 0.3 % of footprints (from OSM tags).
- The machine-learned height field of the footprint dataset is a rendering filler and is never used.
- Floors are therefore mostly unknown. Floor area is a lower bound until people confirm.

The census says 5.4 % of classic buildings are wholly non-residential; the map detects about 3 %. The gap is shops and offices nobody has tagged yet. Corrections come from door confirmations ("this is a shop"), owners, couriers and municipalities. They are settled by agreement, never queued for review.

**Public and private:**
- **Public:** codes, structures, classes, statuses, confirmed entrances, names of businesses and public buildings.
- **Private:** household counts beyond one or several, owners' accounts, gate photos (deleted after confirmation).
- **Never stored:** residents' names or anything about the people inside.

## 8. Check digit, stability, doors

- **Check digit:** the Damm algorithm over the national name index (4 digits) and the number. It catches every single wrong digit and every swap of neighbours. The area is bound through the register: inside a name every number has one owning zone, frozen at issue. So a slip that lands in **another zone of the same name** is always caught when the machine form is used (92,701 of 92,701 in the self-test: `Fazenda 24 33` mistyped as `Fazenda 34 33`, which is Tarrafal's block, is refused). The machine form adds the municipality key, which must match the block's owner; every one of 22,952 corrupted machine forms in the self-test is refused. ISO/IEC 7064 MOD 11,10, the other common choice, misses about 2 % of adjacent swaps, and binding the zone digits into the check would catch only 90.6 % of cross-zone slips. The check digit lives only in the machine form; plates and written forms show the name and number.
- **Stability:**
  - a code never moves or is reused;
  - a renamed zone keeps its codes and its blocks;
  - a name's blocks are frozen at issue and never renumbered; a new zone with an existing name gets a new block from the spare units;
  - a split lote keeps its code on the part with the first entrance;
  - merged lotes keep both codes;
  - demolished means retired.
- **Doors and gates:** confirmed by agreement (arrivals, couriers, the household twice), with no manual review queue. A household may keep its door private; the code then routes to the gate or the street.

## 9. "Add my home"

New homes appear every month, many of them built floor by floor. The household gets its code in five steps:

1. **Gate:** stand at the gate (GPS averaged for 10–20 s) and take one photo. The spot code appears at once, offline.
2. **Outline:** tap the corners on imagery, walk inside the wall with the camera (AR tracking anchored by averaged GPS), or import a survey plan. Plans give beacon coordinates in **EPSG:4826 WGS 84 / Cape Verde National**, the national Lambert grid. On cadastral islands (Sal, Boa Vista, Maio, São Vicente) the INGT parcel can be imported by its NIP.
3. **Describe:** households, structures, floors, use, finished or still building.
4. **Provisional code:** the zone of the nearest code and the middle free number between the gate's neighbours in that zone's block; for example a new building in Belem, Brava, between `Belem 108` and `Belem 113` on the ground, would get `Belem 110` (`engine/test-vectors-registry.json → insertion`); the building in Cruz de Joana, São Vicente, added on 19 October 2026 between `Joana 219` and `Joana 222`, got `Joana 220`. It can never fall in another same-named zone's block. It can go on the gate the same day.
5. **Confirmed:** deliveries arrive, no neighbour disputes it within 30 days, or new imagery shows the house.

**Safeguards:**
- The flow states, in Portuguese and Kriolu, "Um código N-Ways é uma morada, não é título de propriedade" (an N-Ways code is an address, not a property title).
- Overlaps with another lote, a cadastral parcel or public land are flagged, not issued.
- Checks: gate on the outline, closed loop, plausible size, GPS and AR agreeing, not in the sea or a ribeira bed.
- Only the outline and the gate photo are kept.
- Offline, the spot code is immediate and the home code arrives on the next connection from the Cabo Verde registry, the single source of codes.

**Legal angle.** INGT holds the cadastre (Resolução 18/2014). Cadastral operations ran under DL 37/2014 (Sal, Boa Vista, São Vicente, Maio) and the 2009 regime (DL 29/2009, amended by DL 45/2014). Under the 2009 regime cadastral work needed an alvará from the cadastre service. Third-party summaries report a new regime, DL 12/2024, which we have not read. Building permits come from the Câmara Municipal. Land is held mainly as private freehold and State land under the civil code and land registry; there is no customary tenure like the mainland's. None of this is decided by an N-Ways code.

## 10. Privacy and data protection

Codes describe places, never people. The law is Lei n.º 133/V/2001, as amended by Lei 41/VIII/2013 and Lei 121/IX/2021, and the authority is the **CNPD** in Praia. N-Ways, as controller of the app's personal data:
- notifies the CNPD (art. 39);
- keeps a 72-hour breach procedure (art. 27);
- covers transfers to servers outside Cabo Verde (arts. 35–36);
- publishes the art. 13 information in Portuguese.

The registry holds no personal data. The app's accounts and "Add my home" submissions do, and they are minimised: outline and gate photo only, photos deleted after confirmation.

## 11. Governance

N-Ways maintains the repository and the registry until a Cabo Verdean public body takes them over. The bodies that matter:
- **Correios de Cabo Verde:** postcodes and Morada Certa; the natural hand-over partner.
- **The 22 Câmaras Municipais:** zone names, streets, door numbers.
- **INGT and the Comissão Nacional de Toponímia:** names, cadastre, geodesy, IDE-CV.
- **INE:** census geography.
- **CNPD:** data protection.

See [`../GOVERNANCE.md`](../GOVERNANCE.md).

## 12. Unverified or open

- Island digits 3 and 6 of the postcode.
- The full Correios postcode list.
- Morada Certa's status in 2026.
- The text of DL 12/2024.
- Kriolu number words.
- The zone names themselves: each Câmara Municipal is to check its zones and choose the 306 plate names flagged for it; the numbers and blocks do not change when it does.
- Whether people in each island accept the folded name pairs (Chã de Baixo = Chã Baixo) as one name.
- Footprint counts where imagery merges terraced rows (São Vicente).
