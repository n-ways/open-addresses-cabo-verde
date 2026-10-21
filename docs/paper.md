---
title: "A home code for every building in Cabo Verde"
subtitle: "A national addressing model built on place names, national number ranges and building footprints"
kind: "Research paper"
author:
  - "The N-Ways Addressing Group"
affiliation: "N-WAYS LIMITED · nways.ng"
date: "October 2026"
abstract-title: "Abstract"
abstract: |
  Most homes in Cabo Verde have no address that a courier, an ambulance crew or a visitor can use: postcodes cover whole towns, door numbers exist only in a few historic centres, and people find each other by neighbourhood, landmark and telephone call. We present an addressing model designed for Cabo Verde and now in force nationwide. A *home code* is the short name that residents already use for their bairro, zona or povoação, at most twelve characters, followed by a three- or four-digit number, such as `Palmarejo 19 22`. Because place names repeat, every zone sharing a name draws from one national range for that name, divided into frozen blocks, so the code is unique without any municipality or island. Numbers follow a Hilbert ordering of the buildings and leave room between neighbours for later construction; a Damm check digit in the machine form detects every single-digit error and adjacent transposition. Built from 192,272 building footprints, the registry holds 175,630 codes in 1,778 zones under 1,360 names; 44 per cent of codes have three digits and none has more than four. We give every formula with a worked example, the open engine, registry and deployable server, the designs we rejected, and estimates of the benefits for citizens, logistics, emergency services and government.

  *Keywords:* addressing; Cabo Verde; place names; check digits; Hilbert curve; Open Location Code; building footprints; open data.
rights: "© 2026 N-WAYS LIMITED. Text licensed under CC BY 4.0; data under ODbL 1.0; code under the Apache License 2.0."
toc-title: "Contents"
lang: en-GB
---

# Introduction

## The problem

Cabo Verde has 491,233 residents [@rtp2022] on nine inhabited islands (Figure 1). In 2016 more than nine in ten of its roads had no name [@rinckes2016]. The 2021 census counted 150,016 buildings and 200,979 dwellings in its preliminary results [@ine2021], but neither the census nor any public register gives those buildings an address that people can use. Directions are given as they always have been: "Achada Santo António, perto da Caixa", "atrás do mercado", "liga quando chegares".

![The 22 municipalities of Cabo Verde, shaded by the number of home codes per square kilometre, with the number of codes on each island. Praia has the highest density, at about 320 codes per km²; Boa Vista and Maio the lowest, at about 8. Data: `registry/` and the municipality outlines in `engine/data/`.](figures/map.svg){width=88%}

Addresses matter more each year. Deliveries have grown with mobile payments and online shopping. Tourism on Sal and Boa Vista depends on drivers finding hotels and rented flats; hotels received 1,177,467 guests in 2024, 58.5 per cent of them on Sal and 24.1 per cent on Boa Vista [@forbes2025]. Emergency crews must find homes on steep, unnamed streets. Families send goods between islands and from the diaspora. The World Bank's review of street addressing describes the address as basic infrastructure for municipal management, tax collection and service delivery [@farvacque2005], and the Universal Postal Union treats an address for every household as a condition of inclusion [@upu2012].

Cabo Verde already has four partial systems: area postcodes, a grid code linked to postal identities, municipal door numbers in law, and a land cadastre on four islands (Section 2). None of them gives each building an identifier that a person can remember and say over the telephone.

## Contribution

This paper describes a national addressing model designed for Cabo Verde and issued for the whole country on 19 and 20 October 2026. Our contributions are:

1. **A code form chosen for recall.** A home code is a place word that residents already use, reduced by a written rule to at most twelve characters and two words, followed by a number of three or four digits (Sections 4.2 and 4.5).
2. **National uniqueness without context.** Every zone that shares a short name draws from one national number range for that name, divided into frozen blocks, so that "name and number" decodes to exactly one place in the country (Section 4.6).
3. **Numbering with room for growth.** Within a zone, numbers follow a Hilbert ordering of the buildings and are spread over a block three times the size of the zone, so that buildings put up later receive numbers between those of their neighbours and no issued number ever changes (Sections 4.7 and 4.8).
4. **Building-level reference data.** Each code is attached to a *lote* (plot or compound) with its entrance and a profile of every structure, including Cabo Verde's characteristic "unfinished but lived-in" status (Section 4.12).
5. **An open, reproducible implementation.** We publish a reference engine, conformance vectors, the complete registry of 175,630 codes and a registry server that any institution can deploy and that reproduces the issuer's decisions exactly (Section 5).
6. **An evaluation and an impact assessment.** We measure uniqueness, length, error detection and coverage (Section 6), report the designs we rejected with their measured costs (Section 7), and estimate the benefits for four groups of users with explicit assumptions (Sections 8 to 11).

## Structure of the paper

Section 2 reviews the existing systems in Cabo Verde and the international literature. Section 3 describes the data. Section 4 sets out the model, with a single worked example, `Palmarejo 19 22`, carried through every formula. Section 5 describes the implementation and Section 6 evaluates it. Section 7 records the alternatives that were measured and rejected. Sections 8 to 11 discuss the benefits for citizens, for logistics, commerce and tourism, for emergency services and for government. Section 12 covers privacy, safety and governance, Section 13 the limitations, and Section 14 concludes.

# Background and related work

We verified the existing systems between 17 and 21 October 2026. The full record, with every source and the items we could not confirm, is in `docs/existing-systems.md` and `SOURCES.md`.

## Postcodes of Correios de Cabo Verde

The UPU addressing sheet for Cabo Verde, dated April 2014, specifies four digits to the left of the locality name, as in `7600 PRAIA`, with the island on a separate line below. It reads the four digits as island, municipality, municipal district and post office [@upu2014cv]. The codes we were able to observe confirm that the first digit identifies the island (Table 1).

| Digit | Island | Codes observed |
|:--|:--|:--|
| 1 | Santo Antão | Ribeira Grande (third-party listing) |
| 2 | São Vicente | 2110 Mindelo |
| 3 | São Nicolau | none observed |
| 4 | Sal | 4110 Espargos, 4111 Santa Maria |
| 5 | Boa Vista | 5110 Sal Rei |
| 6 | Maio | none observed |
| 7 | Santiago | 7600–7602 Praia |
| 8 | Fogo | 8220 São Filipe |
| 9 | Brava | 9110 Nova Sintra |

: The first digit of the Correios postcode identifies the island. Sources: UPU [@upu2014cv], OpenStreetMap and Nominatim; the digits for São Nicolau and Maio are inferred from the order of the islands.

According to a third-party listing, the first two digits follow the municipality numbers of the national geographic code [@statoids]. Praia is an exception (76, not 74), and the municipalities created in 2005 share the digits of the municipality they were separated from, so the postcode cannot name all 22 present-day municipalities. Correios publishes no postcode list or lookup; its website, as archived in September 2026, offers tracking, branch search and delivery standards but no postcode directory [@correios2026]. The postcode is therefore an area code. It is not a door-level address.

## Morada Certa and Plus Codes

In 2016 Correios de Cabo Verde and Google launched *Morada Certa* ("the right address"): Plus Codes were built into the Correios website so that residents could link the code of their home to their postal identity [@rinckes2016]. A Plus Code is an Open Location Code: a hierarchical grid reference that names a cell of about 14 m with ten characters, or about 3 m with eleven [@olc]. It works offline and needs no register, but it does not say which building or door is meant. We found no evidence that the campaign was still active in 2026. Because Correios chose this grid, the model uses Plus Codes as its spot layer and introduces no competing grid (Section 4.11).

## Street names and door numbers

Decreto-Lei n.º 5/2012 of 28 February 2012 regulates toponymy at national and municipal level and created the Comissão Nacional de Toponímia, coordinated by the Instituto Nacional de Gestão do Território (INGT) [@ungegn2023; @res18_2014]. In its 2023 report to the United Nations Group of Experts on Geographical Names, Cabo Verde undertook to support the municipalities in "the massive implementation of municipal toponymy and police numbering", that is, door numbers, and set the rule that street names must not be duplicated [@ungegn2023]. The municipalities are therefore the legal authority for door-level addresses. On the ground, such addresses exist in the historic centres of Platô and Mindelo, in some planned districts of Praia and in Santa Maria on Sal. We found no published municipal address register.

## The land cadastre and the national grid

INGT was created in 2014 with responsibility for spatial planning, geodesy, cartography, the national spatial data infrastructure and the land cadastre [@res18_2014]. A special regime governed the systematic cadastral operation on Sal, Boa Vista, São Vicente and Maio [@dl16_2019]. Each parcel carries a Número de Identificação Predial (NIP). The national projected coordinate system is EPSG:4826, *WGS 84 / Cape Verde National*, a Lambert conformal conic projection with standard parallels at 15° N and 16°40′ N [@epsg4826]. The cadastre establishes *title*; an address serves *finding*. A home code is never a title, although a lote may carry its NIP as a reference.

## The census

The 2021 census georeferenced every building. Of the 150,016 buildings in the preliminary results, 27.7 per cent were classic but unfinished, and 87.0 per cent of classic buildings were used only for housing; the number of buildings had grown by 31.3 per cent since 2010, from 114,297 [@ine2021]. The definitive count is 150,206 buildings [@rtp2022]. Census enumeration areas are not published as open data. The model uses these totals as priors and checks, never as data about any household.

## International practice

The UPU's standard S42 defines the components of a postal address and templates for rendering them [@upuS42], and ISO 19160-1 provides a conceptual model of addressing that separates the address, its components and the addressable object [@iso19160]. Both standards accommodate an address made of a locality and an identifier within it, which is the structure we adopt. The World Bank reviewed street addressing in African cities: in a sample of 21 cities, only 8 per cent of streets had names before the programmes began, and the average cost was US\$5.7 per doorway addressed, at 2005 prices [@farvacque2005]. The same review warns that addressing decays when residents do not use it, which is why recall is our first criterion.

## Other code systems

Grid codes such as Open Location Code [@olc] identify points rather than buildings and include letters and a separator. National digital-address systems built on grids exist elsewhere in West Africa, for example Ghana's National Digital Property Addressing System, launched in 2017 [@graphic2017]. These systems share a limitation: the code encodes a position, not a place word that residents recognise, so it is hard to remember and gives no protection against slips that land on another valid cell. Purely numeric national codes carry no place at all, and alphanumeric codes rely on letters, which no address in Cabo Verde contains and which are hard to dictate in Portuguese (Section 7.1). We therefore keep the grid for points and give each building a code made of a place word and a short number.

# Data and sources

The model is computed from open map data, checked against national statistics, and published as an open registry. This section describes each source and what the registry contains.

## Building footprints

The registry is built from the building footprints held by N-Ways in October 2026: 91,397 from OpenStreetMap [@osm2026] and 100,875 machine-learned footprints from Google Open Buildings [@sirko2021] and Microsoft [@microsoft2023], obtained through the Overture Maps buildings theme [@overture2026] wherever OpenStreetMap had none. The 192,272 footprints in the registry exceed the census count of buildings by 28 per cent, because the map also contains annexes, sheds, unfinished shells and ruins. The excess is not uniform. In Praia the map holds 32,591 footprints against 34,663 census buildings (6 per cent fewer), and in São Vicente 18,315 against 23,976 (24 per cent fewer), because imagery merges terraced rows. In rural Fogo and Santiago, footprints exceed census buildings by up to 2.7 times, because every outbuilding is mapped. Figure 2 shows the sources by island.

![Building footprints in the registry, by island and source. Machine-learned footprints fill the gaps in OpenStreetMap, most of all on Fogo and Boa Vista. Data: `registry/structures/`.](figures/sources.svg){width=80%}

## Localities and names

Zones are built from the N-Ways locality layer: OpenStreetMap suburbs, neighbourhoods, villages and towns, and GeoNames localities that are not landforms [@geonames]. About 3,800 named places become 2,818 candidate zones and, after the rules of Section 4.4, 1,778 zones. Two short forms used in the Praia press, `ASA` for Achada Santo António and `AGF` for Achada Grande Frente, are documented in [@balai2025asa; @anacao2026; @expresso2025agf].

## Statistical priors

The building profile (Section 4.12) uses the 2021 census shares as priors: 87.0 per cent of classic buildings used only for housing, 27.7 per cent unfinished [@ine2021]. Kriolu spellings are folded according to the unified alphabet ALUPEC [@alupec].

## The registry

The registry (`registry/`) holds every issued code: one file per municipality with 20 columns per code (machine form, home code, official name, zone, number, check digit, status, issue, entrance, Plus Code, use, kind of lote, number of structures, floor area, postcode, coverage, official address), the zone table and the national name register, the numbering anchor of every lote, and the profile and WKT footprint of every structure. A manifest records the counts and the SHA-256 digest of every file. Every code is listed; nothing is withheld.

# The model

This section specifies the model in the order in which a code is built: the requirements it must meet, the forms of the code, the coverage mask of official addresses, the zones and their plate names, the national name ranges and their blocks, the numbering within a zone and its growth, decoding, the check digit, the spot layer and the building profile. Each rule is stated as a numbered equation, and the code `Palmarejo 19 22` serves as the worked example.

## Requirements

The requirements, in order of priority, are:

1. **Recall and effortless access.** Residents must be able to remember their code and obtain it with no effort. This criterion comes before brevity and before mathematical elegance, because an address that people do not use decays [@farvacque2005].
2. **Official addresses first.** Where a municipality has given a street and a number, that address is shown first, exactly as written; the code stands beside it. The Correios postcode, the NIP and the Plus Code are shown beside the code and none is replaced.
3. **Building and door level.** The code leads to a gate or front door, not to a centroid behind a wall.
4. **Offline operation.** A telephone without a signal can display, check and read out codes.
5. **Openness.** The method, the engine and the data are public.
6. **Stability.** A code never moves, is never reused and never grows longer.
7. **Privacy.** Codes describe places, never people.

## The home code and its forms

A home code is the short name of a zone followed by a number:

> **Palmarejo 19 22** · Praia, Santiago  
> **São Filipe 21 29** · *Lote Achada São Filipe* · Praia, Santiago  
> **Fazenda 34 48** · Tarrafal, Santiago  
> **João Vaz 214** · *Chã de João Vaz* · Paul, Santo Antão

The number has three digits (100–999) or four (1000–9999); the length is a property of the name (Section 4.6). It never begins with zero. Four digits are written and spoken as two pairs, the way telephone numbers are said in Cabo Verde: "Palmarejo, dezanove, vinte e dois", or in Kriolu "dizanovi, vinti i dos". Three digits are said like a door number: "João Vaz, duzentos e catorze".

The code is **unique in the whole country on its own**. The official name, the municipality and the island shown above are printed for information; nobody has to type or say them, and the decoder never uses them to choose between places. A **machine form** corresponds one-to-one to each home code: `PR-0973-1922-6` gives the municipality key, the national index of the name, the number and a check digit. People never see the check digit: plates and written forms show the name and number, and the machine form appears only in systems and in the QR code of a plate.

## Official addresses first: the coverage mask

Where a municipality has given a street name and a door number, the record shows that address first, exactly as the municipality writes it, for example `Rua Barragem de Figueira Gorda 142, Praia`, with the home code `Cidadela 10 88` beside it. Every building has a home code, whether or not its street is numbered, so a courier, a family or a software system needs only one kind of code for the whole country. Each lote is marked **official** (street and number known), **official-pending** (in an area presumed to be numbered whose register has not been shared: Platô and central Mindelo), or neither. Table 2 gives the counts.

| Coverage | Lotes | Share |
|:--|--:|--:|
| Official: municipal street and number known | 96 | 0.05 % |
| Official-pending: Platô and central Mindelo | 1,299 | 0.74 % |
| No official address | 174,235 | 99.21 % |
| **All lotes, each with a home code** | **175,630** | **100 %** |

: Coverage of official addresses in the registry.

When a municipality numbers further streets, those addresses are shown first. The home code remains valid and leads to the same door, and its number is never given to anyone else.

## Zones

Each lote $\ell$ is assigned to the nearest zone candidate in its own municipality $m(\ell)$:

$$
z(\ell) = \operatorname*{arg\,min}_{z \in Z(m(\ell))} d(\ell, z),
\tag{1}
$$

where $Z(m)$ is the set of candidates in municipality $m$ and $d$ is the great-circle distance between the lote's anchor and the candidate's point. A candidate with fewer than 15 lotes merges into its neighbours unless it is an isolated povoação more than 1.5 km from any other:

$$
\text{prune}(z) \iff L(z) < 15 \;\wedge\; \min_{z' \neq z} d(z, z') \le 1500\ \text{m},
\tag{2}
$$

where $L(z)$ is the number of lotes assigned to $z$. Equations (1) and (2) are applied repeatedly until no candidate is pruned. In towns, the bairros are the place words: residents of Praia say Achada Santo António, Palmarejo or Safende, not "Praia", and Praia has 64 zones. A zone is a list of lotes fixed at issue, not a boundary on the ground, so a renamed or disputed bairro never changes a code.

## Plate names

Map names are often too long to say: 632 of the 1,778 official zone names exceed twelve characters, for example *Entre Chã de Alecrim e Madeiralzinho* or *Casa Para Todos-Ribeira de Julião*. Every zone therefore has an **official name**, printed in small type and still accepted when typed, and a **plate name**, the name in the code. A plate name $s$ is admissible when

$$
\operatorname{fit}(s) \iff |\mathrm{NFC}(s)| \le 12 \;\wedge\; \bigl|\operatorname{words}(s) \setminus \{\text{de}, \text{da}, \text{do}, \dots\}\bigr| \le 2,
\tag{3}
$$

where $|\mathrm{NFC}(s)|$ counts characters after Unicode canonical composition (an accented letter counts once) and the connecting words *de, da, do, das, dos, d', di, du, e* are not counted. The plate name is derived by one written rule, applied in order: a short form already in documented use wins (`ASA`, `AGF`); generic words, bracketed text and second spellings are removed (*Lote*, *Bairro*, *Zona*, *Casa Para Todos*); *Santo*, *Santa* and *São* may be abbreviated before a name; otherwise the most distinctive run of whole words that fits is kept, preferring the specific end of the name (*Lote Achada São Filipe* becomes `São Filipe`, *Casa Para Todos-Ribeira de Julião* becomes `Julião`). A word is never cut. When the choice is not clear, the zone is flagged for its Câmara Municipal with up to three candidates and the first is used provisionally. This happens when two words are both the name (*Figueira Gorda*), when shortening would drop a qualifier (*Calheta de Baixo*, *Calheta de Cima*), when the result would equal a town or island elsewhere, or when no run of words fits. Of the 1,778 zones, 1,146 names fit as they are, 326 are shortened automatically and 306 are flagged; 118 of the flagged names have no form that fits yet, such as *Monte Vermelho*. The Câmara's choice changes the name once and never the number.

Two names are the same name when their keys agree:

$$
\operatorname{key}(s) = \bigl(\operatorname{drop\_articles} \circ \operatorname{expand\_abbrev} \circ \operatorname{alupec} \circ \operatorname{split} \circ \operatorname{unaccent} \circ \operatorname{lower}\bigr)(s).
\tag{4}
$$

The folding steps are listed in Table 3.

| Step | Rule | Example |
|:-----|:--------------|:--------|
| letters | NFKD, accents removed, lower case | Platô → plato |
| split | apostrophes, dots, hyphens, slashes and commas become spaces | Lém-Ferreira → lem ferreira |
| ALUPEC | tch, tx → ch; dj → j; k → c before a, o, u; k → qu before e, i | Tchada → chada |
| abbreviations | sto → santo, sta → santa, s → são, n, na → nossa | Sto Antão → santo antao |
| articles | de, da, do, das, dos, d, o, a, os, as dropped | Chã de Baixo → cha baixo |

: Folding of names to keys, Eq. (4).

Every official name is an alias of its plate name, and aliases also cover Platô/Plateau and the Portuguese and Kriolu forms that the toponymy commission keeps side by side [@ungegn2023].

## National name ranges and blocks

Short names repeat: 254 plate names are used by two or more zones, 672 zones in all, holding 64,873 codes. *Figueira* names ten zones, *Achadinha* and *Cutelo* eight each. A code that needed its municipality to be distinguished would fail whenever the municipality is omitted, which is most of the time. Instead, each name has **one national number range**, divided among its zones in blocks that are frozen at issue.

Numbers are allocated in whole units of size $s_d$: $s_3 = s_4 = 100$ and $s_5 = 1000$. A zone with $L(z)$ lotes at first issue needs

$$
u(z) = \max\!\left(1, \left\lceil \frac{3\,L(z)}{s_d} \right\rceil\right)
\tag{5}
$$

units, so that its block holds three numbers for each of its lotes. A name with zones $z_1, \dots, z_k$ takes the shortest length whose range holds all its zones and two spare units:

$$
d^{*} = \min \left\{ d \in \{3, 4, 5\} \;:\; \sum_{i=1}^{k} u(z_i) + 2 \le U_d \right\},
\qquad U_3 = 9,\; U_4 = U_5 = 90,
\tag{6}
$$

where $U_d$ is the number of units in a $d$-digit range (100–999 has nine units of 100; 1000–9999 and 10000–99999 have 90 units each). A zone alone with its name therefore has three digits up to 233 lotes ($\lceil 3 \cdot 233/100 \rceil + 2 = 9$) and four digits up to 2,933. Blocks are assigned from the bottom of the range in the order of municipality index and zone index.

*Worked example.* The name *Palmarejo* (national index 973) has two zones in Praia: Palmarejo, with 935 lotes at first issue, and Palmarejo Grande, with 537. By Eq. (5), $u = \lceil 28.05 \rceil = 29$ and $u = \lceil 16.11 \rceil = 17$. Since $29 + 17 + 2 = 48 > 9$, three digits are not enough; since $48 \le 90$, the name takes four digits. Palmarejo receives the block 1000–3899 and Palmarejo Grande 3900–5599; 5600–9999 remains free.

Figure 3 shows the distribution of zone sizes and Figure 4 the blocks of three repeated names. *Fazenda* is shared by seven zones in five municipalities and occupies 1000–3499; Achada Fazenda in Santa Cruz holds 1000–1999 and Fazenda in Tarrafal holds 3300–3499, so `Fazenda 34 48` can only be in Tarrafal. The largest shared range is *Bela Vista* (Praia, Sal and São Vicente; 1,562 codes), which uses 4,900 of its 9,000 numbers. No name needs five digits.

![Zones by number of home codes, on logarithmic bins. Light: zones whose name range has three digits; dark: four digits. The dashed lines mark the largest zone that fits three digits alone (233 lotes) and four digits (2,933). The median zone has 50 codes; the largest, Achada Santo António (`ASA`), has 2,855. Data: `registry/`.](figures/zone-sizes.svg){width=95%}

![Three national name ranges divided into the blocks of their zones (official name, municipality and codes issued). The grey reserve is free for new zones of the same name and for growth. Data: `registry/names.csv`.](figures/ranges.svg){width=100%}

When a zone's block is full, it takes the lowest free unit of its name; when a name's range is full, the name continues in the next length. A new zone with an existing name, such as a new Achadinha, receives a new block from the spare units. No issued number changes.

## Numbering within a zone

The lotes of a zone are ordered along a Hilbert curve [@hilbert1891], which preserves spatial locality well among space-filling curves [@moon2001]: lotes that are close on the ground usually receive close numbers (Figure 5). Each zone's bounding box, enlarged by 300 m, is mapped onto a $2^{16} \times 2^{16}$ grid. A lote whose anchor (its gate if known, otherwise its main structure) has longitude $\lambda$ and latitude $\varphi$ is placed in the cell

$$
x = \operatorname{round}\!\left( \frac{\lambda - \lambda_W}{\lambda_E - \lambda_W} \,(2^{16} - 1) \right),
\qquad
y = \operatorname{round}\!\left( \frac{\varphi - \varphi_S}{\varphi_N - \varphi_S} \,(2^{16} - 1) \right),
\tag{7}
$$

where $\lambda_W, \lambda_E, \varphi_S, \varphi_N$ are the edges of the box, and receives the Hilbert index $h = H_{16}(x, y)$, computed bit by bit from the most significant level.

![The order-3 Hilbert curve over an 8 × 8 grid, in the order given by the reference engine's `hilbert_index`. The model uses the same curve at order 16; in Palmarejo a cell measures about 2.4 cm by 3 cm.](figures/hilbert.svg){width=45%}

At first issue, the $n$ lotes of a zone with block $[\,a, b\,]$ are sorted by their Hilbert index $h$, ties being broken by the identifier of the main structure, and receive evenly spread numbers:

$$
N_k = a + \left\lfloor \left(k + \tfrac{1}{2}\right) \frac{b - a + 1}{n} \right\rfloor,
\qquad k = 0, 1, \dots, n - 1.
\tag{8}
$$

*Worked example.* Palmarejo's box spans $\lambda \in [-23.53404, -23.51928]$ and $\varphi \in [14.90097, 14.91902]$. The anchor of an apartment building at $\varphi = 14.9113759$, $\lambda = -23.5282136$ maps by Eq. (7) to the cell $(x, y) = (25\,869,\ 37\,781)$, whose Hilbert index is $h = 2\,099\,014\,114$. In this order, 297 of Palmarejo's 935 first-issue lotes precede it, so $k = 297$, and Eq. (8) gives

$$
N_{297} = 1000 + \left\lfloor 297.5 \cdot \frac{2900}{935} \right\rfloor = 1000 + \lfloor 922.73 \rfloor = 1922 .
$$

The building's home code is `Palmarejo 19 22`. Figure 6 shows the whole zone. The three lotes on officially numbered streets were added afterwards, numbered between their neighbours by Eq. (9), without changing any other code.

![The 938 home codes of the zone Palmarejo (Praia) at their numbering anchors, coloured by number and joined in number order. Neighbouring buildings receive neighbouring numbers; gaps of about two numbers remain between them for later buildings. Circle: `Palmarejo 19 22`. Triangles: the three lotes on officially numbered streets. Data: `registry/`.](figures/palmarejo.svg){width=78%}

## Codes for new buildings

A building that is not yet on the map, or a second door, receives a number between its Hilbert neighbours. Let $p$ and $q$ be the numbers of the issued lotes immediately before and after the new anchor in Hilbert order within the zone's block ($a - 1$ and $b + 1$ at the ends). Then

$$
N_{\text{new}} =
\begin{cases}
\left\lfloor \dfrac{p + q}{2} \right\rfloor & \text{if } q - p > 1 \text{ and it is free},\\[1ex]
\text{nearest free number in the zone's blocks} & \text{otherwise},\\[0.5ex]
\text{a number in a new block of the name} & \text{if the blocks are full.}
\end{cases}
\tag{9}
$$

*Example from the registry.* On 19 October 2026 a building in Cruz de Joana, São Vicente, was added on demand. Its Hilbert neighbours in the zone's block 100–699 were numbers 219 and 222, so Eq. (9) gave $\lfloor 441/2 \rfloor = 220$ and the code `Joana 220` (`SV-0654-220-9`). The reference engine reproduces this number from the published registry. A new number can never fall in another zone's block.

## Decoding without context

A spoken or typed code is decoded by folding the name to its key, finding the name's blocks, and taking the one block that contains the number:

$$
\operatorname{decode}(P, N) = \bigl\{\, z \;:\; \operatorname{key}(P) \in \operatorname{keys}(z),\; a(z) \le N \le b(z) \,\bigr\},
\tag{10}
$$

where $\operatorname{keys}(z)$ contains the key of the zone's plate name and of its aliases, and $[a(z), b(z)]$ ranges over the zone's blocks. Because blocks of a name are disjoint, the set has at most one element. `palmarejo 1922` lies in 1000–3899 and is Palmarejo; `palmarejo 4500` would be Palmarejo Grande; `fazenda 5229` is refused, because no zone of that name owns 5229.

## The check digit

The check digit is computed with the Damm algorithm [@damm2004; @damm2007] over the four digits of the name's national index followed by the number. With $T$ a totally anti-symmetric quasigroup of order 10 and digits $\delta_1, \dots, \delta_r$,

$$
c_0 = 0, \qquad c_j = T[c_{j-1}][\delta_j] \quad (j = 1, \dots, r), \qquad \text{check} = c_r ,
\tag{11}
$$

and a string followed by its check digit is valid when the recurrence ends at 0. The table used is

$$
T =
\begin{pmatrix}
0&3&1&7&5&9&8&6&4&2\\
7&0&9&2&1&5&4&8&6&3\\
4&2&0&6&8&7&1&3&5&9\\
1&7&5&0&9&8&3&4&2&6\\
6&1&2&3&0&4&5&9&7&8\\
3&6&7&4&2&0&9&5&8&1\\
5&8&6&9&7&2&0&1&3&4\\
8&9&4&5&3&6&2&0&1&7\\
9&4&3&8&6&1&7&2&0&5\\
2&5&8&1&4&3&6&7&9&0
\end{pmatrix}.
\tag{12}
$$

*Worked example.* For `Palmarejo 19 22` the digits are `0973 1922`. The running value $c_j$ after each digit is 0, 2, 3, 0, 3, 6, 6, 6, so the check digit is 6 and the machine form is `PR-0973-1922-6`.

Each row and column of $T$ is a permutation, so every single wrong digit changes the result; total anti-symmetry ensures that every transposition of two different adjacent digits does as well [@damm2004]. Unlike Verhoeff's dihedral scheme [@verhoeff1969], Damm's needs only one table and no permutation step. The zone is not among the digits: inside a name, every number has exactly one owning zone, so a one-digit slip that lands in another zone of the same name changes exactly one digit and is always detected. In the machine form, the municipality key must also equal the owning zone's municipality.

## The spot layer

Every point on land has a Plus Code [@olc], the grid that Correios chose for *Morada Certa*. With $\varphi' = \varphi + 90$ and $\lambda' = \lambda + 180$, the five pairs of characters use resolutions $r_k \in \{20, 1, 0.05, 0.0025, 0.000125\}$ degrees:

$$
\text{lat}_k = \left\lfloor \frac{\varphi'}{r_k} \right\rfloor \bmod 20, \qquad
\text{lng}_k = \left\lfloor \frac{\lambda'}{r_k} \right\rfloor \bmod 20, \qquad k = 1, \dots, 5,
\tag{13}
$$

and an eleventh character divides the last cell into five rows and four columns:

$$
g = 4 \left( \left\lfloor \frac{5\varphi'}{r_5} \right\rfloor \bmod 5 \right) + \left( \left\lfloor \frac{4\lambda'}{r_5} \right\rfloor \bmod 4 \right),
\tag{14}
$$

each value being written with the alphabet `23456789CFGHJMPQRVWX`. For the anchor of `Palmarejo 19 22`, the pairs are (5, 7), (4, 16), (18, 9), (4, 8), (11, 14) and $g = 1$, giving `796RWF6C+HP3`, or `WF6C+HP3 Praia` in short form. The model offers eleven characters (about 3 m) in towns and at gates and ten (about 14 m) in the countryside, on land only. Figure 7 shows the grid in Platô.

![The spot layer around the Correios building in Platô (`Platô 11 32`, red). Building footprints from the registry beneath the 10-character Plus Code grid (13.45 m × 13.82 m at this latitude); the building's own cell is divided into the 4 × 5 cells of the eleventh character. A spot code names a point; the home code names the building. Data: `registry/structures/`.](figures/spot.svg){width=80%}

## The lote and the building profile

The addressable unit is the **lote**: a plot or compound with its structures and its entrance. Settlement in Cabo Verde follows its own pattern, and the grouping rules follow it. Town houses stand wall to wall along streets and up slopes, so touching buildings in town are never merged. Rural houses often have an outdoor kitchen, a latrine, a water tank or a *curral*, which join the house's lote as structures. Enclosed sites such as schools, hospitals and barracks form one lote each, and hotel complexes on Sal and Boa Vista are estates whose units are reached through the estate gate. In the registry, 12,604 lotes have two or more structures and hold 15.2 per cent of all footprints; 453 lotes are enclosed sites, of which only 16 (3.5 per cent) have a mapped gate. The code leads to the primary entrance: the gate where there is one, otherwise the confirmed front door.

Each structure carries a profile: a use class from a taxonomy built for Cabo Verde (moradia, prédio de habitação, habitação precária, misto, loja, mercado, armazém, restauração, escritório, hotel, pensão, governo, educação, saúde, religioso, indústria, agrícola, anexo and others); its footprint area and perimeter; height and floors where known; a status (in use, *unfinished but lived in*, under construction, ruin, abandoned, demolished); and the source and confidence of every attribute. Status is kept separate from use, because an unfinished house is still a home. The class is set by the first rule that applies, with its confidence: an OpenStreetMap use tag (0.9); the OpenStreetMap building type (0.3–0.95); a mapped place inside the footprint (0.55–0.8); the structure's role in the lote (0.55); size and island context (0.35–0.5); the census prior that most buildings are homes (0.5–0.6); and corrections by residents, couriers and municipalities, which override all others (0.9–0.99).

## Stability

A code is never moved or reused. If a lote is split, the code stays with the part that holds the first entrance; if two lotes merge, both codes remain valid; a demolished building's code is retired and never reissued; a name's blocks are never renumbered. A code is **provisional** until independent residents confirm it, and **confirmed** thereafter.

# Implementation

Four published components implement the model: a reference engine with its normative specification, the registry, a registry server with its API, and two sets of conformance vectors that bind any other implementation to the same results.

## Reference engine and specification

The specification (`engine/SPEC.md`) is normative. The reference engine (`engine/reference/cv_engine.py`) uses only the Python standard library and implements every rule of Section 4: parsing a home code in any spacing, case or accent, decoding by Eq. (10), the machine form and Eqs. (11)–(12), the Plus Code by Eqs. (13)–(14), the plate and spoken forms in Portuguese and Kriolu, the Hilbert order and Eqs. (7)–(9), the block plan of Eqs. (5)–(6), and the building-profile rules. Its self-test checks every zone, every official name and every slip described in Section 6.4.

## The registry

The registry is published per municipality in plain CSV, with the zone table, the name register, the numbering anchors and the building layer (Section 3.4). The manifest's SHA-256 digests allow any copy to be verified. The registry is the authoritative record: decoding needs only the name register, while issuing a new code needs the anchors and footprints.

## The registry server and its API

The repository includes a registry server (`server/`) that a ministry, a post office or a developer can deploy with a single command (`docker compose up`). It imports the registry into SQLite after verifying every digest and every total, serves a JSON API under `/v1` (lookup by code, search by any written form, the code at a point, codes nearby, verification, spot codes, zones and areas, paged lists), and exports the registry back in the published format, byte for byte. A deployment can issue codes only if it holds keys and has been designated as the issuer (Section 12.3); it then applies the rules of Section 4 exactly, including the duplicate checks (no new code within 3 m of an existing entrance or inside an existing footprint), the outline limits (12 m² to 2 ha) and Eq. (9). The API is documented with real requests and responses in `docs/api.md` and as OpenAPI 3.1 in `server/openapi.yaml`.

## Conformance and parity

Two sets of vectors define conformance. `engine/test-vectors.json` covers the forms, check digits, spoken forms, blocks, plate names, same-name decodings and growth cases. `engine/test-vectors-registry.json` contains real issued codes with every derived form, the codes of every zone of four repeated names, codes with official addresses and an insertion computed on a real zone. An implementation in another language conforms if it reproduces both sets. The server's issuing logic was compared with the issuer's own implementation on 107 sequential issues in one zone, including the filling of a block and the opening of an extension block, and agreed on every number and form.

# Evaluation

We measure the issued registry against the requirements of Section 4.1. Every figure in this section is computed from the published files in `registry/` and from the reference engine, and can be reproduced with the tools in the repository.

## Uniqueness and decoding

All 1,778 zones and all official names decode to the expected zone, and every one of the 175,630 codes decodes to exactly one lote. Within each of the 1,360 names, blocks are disjoint by construction, so by Eq. (10) no two codes in the country share a remembered form.

## Code length

Table 4 summarises the lengths. Of the 175,630 codes, 77,467 (44.1 per cent) have three digits and 98,163 (55.9 per cent) have four; none has five. The median zone has 50 codes, the 90th percentile 213 and the largest, Achada Santo António, 2,855: three times that is 8,565, so its block is 1000–9599.

| | Zones | Codes | Share of codes |
|:--|--:|--:|--:|
| Three-digit numbers | 1,349 | 77,467 | 44.1 % |
| Four-digit numbers | 429 | 98,163 | 55.9 % |
| Five-digit numbers | 0 | 0 | 0 % |
| **Total** | **1,778** | **175,630** | **100 %** |

: Number lengths in the registry.

## Plate names

Plate names have at most twelve characters and two words except for the 118 flagged names that await a municipal choice. Among names that are not flagged, the longest remembered codes have 18 characters, for example `Vila Miséria 25 98`.

## Error detection

The self-test generates single-digit slips from 25 numbers in every block of every repeated name. Of the 92,701 slips that land in another zone of the same name, all 92,701 are refused by the check digit; a further 140,407 slips land on numbers that no zone owns. All 22,952 corrupted machine forms (wrong digit, swapped digits or wrong municipality key) are refused. Without the check digit, as when a code is spoken, a code is still protected by sparseness. At first issue a block holds about three numbers per lote, so the probability that a random slip within a block reaches an issued code is approximately

$$
P(\text{hit}) \approx \frac{L(z)}{s_d\, u(z)} \approx \frac{1}{3},
\tag{15}
$$

and the decoder always shows what a code points to, with its municipality, before navigation starts.

## Coverage

Every lote on the map has a code: 175,629 issued in bulk and one issued on demand by Eq. (9). The 1,395 lotes with official or official-pending addresses carry both their municipal address and a home code (Table 2).

## Building profiles

Table 5 summarises the inferred profiles. Height is known for only 0.3 per cent of footprints, from OpenStreetMap tags; the height field of the machine-learned data is a rendering placeholder rather than a measurement and is not used. The census finds 5.4 per cent of classic buildings used wholly for non-residential purposes [@ine2021]; the map detects about 3 per cent, the difference being shops and offices that nobody has tagged.

| | Cabo Verde | Praia | Sal |
|:-----------|-------:|-------:|-------:|
| Footprints | 192,272 | 32,591 | 7,661 |
| Residential | 84.1 % | 89.2 % | 61.0 % |
| Annexes | 11.1 % | 6.1 % | 7.3 % |
| Tourism | 1.7 % | 0.1 % | 27.2 % |
| Commerce, food and offices | 0.8 % | 1.9 % | 3.1 % |
| Agricultural | 1.7 % | 2.0 % | 0.3 % |
| Confidence high / medium / low | 3.6 / 73.0 / 23.5 % | 4.4 / 75.2 / 20.4 % | 8.0 / 51.8 / 40.2 % |
| Median footprint | 44.9 m² | 60.8 m² | 108.5 m² |

: Inferred building profiles. High confidence is 0.8 or above, medium 0.55 to 0.8. Data: `registry/structures/`.

## Server fidelity and performance

After importing the full registry (about six seconds on a laptop), the server returned the same card as the issuer's live service for 58 codes compared field by field, including official, official-pending, on-demand and multi-structure codes, and the same answer for 400 random points. The only difference is a rounding of one entrance coordinate to seven decimals (about 1 cm) in the published format. On the same machine the server answered about 1,200 code lookups and 120 point lookups per second.

# Designs considered

Each of the main choices of Section 4 was compared with its alternatives on the same data before the codes were issued. This section records those alternatives and the measurements on which they were rejected.

## Alternative code forms

We evaluated the adopted form against six alternatives, judged by what residents already remember (Table 6).

| Form | Example | Assessment |
|:---------|:-------|:------------------|
| Short place name and a number from one national range per name | `Palmarejo 19 22` | **adopted** |
| Municipality and digits | `Praia 48 213` | Praia would need five digits (31,052 lotes × 3 > 9,000); residents describe home by bairro, not municipality |
| Municipality key and an alphanumeric code | `PR R5H8-R` | no address in Cabo Verde contains letters; Portuguese letter names rhyme in two large families (bê, cê, dê, gê, pê, tê, vê; efe, ele, eme, ene, erre, esse) and are hard to dictate |
| A national digits-only code | `07 0973 1922` | carries no place; a slip can land on a real house on another island |
| Plus Code alone | `796RWF6C+HP3` | precise for a point, but contains letters and a plus sign and changes every few metres; retained as the spot layer |
| Zone, number and municipality to separate repeated names | `Achadinha 214, Paul` | not unique on its own: fails whenever the municipality is omitted |
| Full official name and a number | `Lote Achada São Filipe 21 29` | too long to say in one breath or to fit on a plate |

: Code forms considered.

## The cost of national ranges

Sharing a range among same-named zones lengthens some codes. Table 7 compares three designs on the registry's counts. With one range per zone, unique only together with the municipality, 1,625 zones would have three digits. One range per official name gives 1,501. Our design, one range per plate name, gives 1,349: sharing puts 276 zones on four digits that would have three on their own. That is the price of a code that is short and needs no context. No design needs five digits.

| Design | 3 digits | 4 digits |
|:--------------------|-----:|-----:|
| One range per zone (unique only together with the municipality) | 1,625 | 153 |
| One range per official name | 1,501 | 277 |
| **One range per plate name (adopted)** | **1,349** | **429** |

: Number lengths under three designs, computed on the registry's counts.

## The check-digit scheme

We compared Damm's algorithm with ISO/IEC 7064 MOD 11,10 [@iso7064] computed over the municipality, zone and number. MOD 11,10 misses about 2 per cent of adjacent transpositions (for example 12/21, 56/65 or 09/90), and with the zone among the digits it detected only 90.6 per cent of slips into another zone of the same name. Damm's algorithm over the name index and the number detects all of them (Section 6.4).

## Official streets

One option was to give no home code to lotes on streets that a municipality has numbered, so that those homes would show only their official address. We rejected it: a single kind of code for every home is simpler for residents, couriers and software, and the official address is in any case shown first (Section 4.3). The 1,395 lotes concerned were numbered between their neighbours by Eq. (9), without changing any other code.

# Benefits for citizens

For a family in Achada Santo António, in a povoação of Santo Antão or on a terraced street of Mindelo, a home code changes four ordinary things.

**Being found.** Today a visitor, a taxi or a delivery rider is guided by telephone. With a code, the resident says one short phrase, "Palmarejo, dezanove, vinte e dois", and the visitor is led to the door or the gate.

**Proving where one lives.** Banks, schools, employers and public services ask for an address. Only 96 lotes have a known municipal street and number, and 1,299 more lie in historic centres presumed to be numbered; all 175,630 have a home code (Table 2).

**Receiving goods and services.** Families in the diaspora, online shops and utilities can send to a code instead of a description, and a household can request a connection, a meter reading or a repair at the right door.

**Between islands.** A code works in the same way in Praia, Mindelo, Espargos and Nova Sintra. A parcel sent from São Vicente to a village on Fogo carries one code that identifies the village and the building, without a sketch.

**Obtaining the code takes no effort.** Every building on the map has had its code since 20 October 2026, and nothing is asked of the household (Table 8). Obtaining a code is free, requires no document and records no personal data. A code is not a property title.

| Situation | Steps |
|:--|:--|
| A saved home in the N-Ways app | none: the code is shown on the home screen |
| Standing at the gate | one: confirm "É a minha casa?" |
| Sharing the code | one tap: a link with the code in words |
| A plate or sticker on the gate | none: the code, and a QR code that opens navigation |
| A new building | "Add my home": gate, outline, description; a code by Eq. (9) |

: How residents obtain their code.

**Who benefits most.** Those with the least today: families on the steep, unnamed streets of Praia's newer bairros, households living in homes that are still unfinished (27.7 per cent of buildings in 2021 [@ine2021]), and povoações far from any landmark.

**Estimated reach.** If every household in the 2021 census used its code, 145,952 households would gain an address they can say; 99.2 per cent of lotes have no other door-level address (Table 2). Recall is the critical assumption. We will measure it (Section 13); if recall after one month were 50 per cent rather than our 80 per cent target, the reach would be about 73,000 households rather than 117,000.

# Logistics, commerce and tourism

Delivery in Cabo Verde runs on the telephone and crosses the sea. For logistics businesses, the machine form is a stable key for a customer's lote that can be stored, deduplicated and joined to past deliveries; the code resolves to the gate or front door, so routes can be planned before the rider leaves; a typed code is verified at once; every lote carries its Correios postcode, so mail is still sorted to the right post office; and the registry and engine are open, so any courier, shop, bank or payment provider can resolve codes in its own systems, offline, without fees.

**Tourism.** On Sal and Boa Vista, which received 82.6 per cent of the 1,177,467 hotel guests of 2024 [@forbes2025], hotels and rented flats depend on drivers finding them. A hotel complex is an estate: a route leads to its gate and then to each unit. A guest can give a driver one code instead of a description.

**Small businesses.** A shop or workshop built into the front wall of a house is its own structure with its own entrance, addressed by the lote's code and a structure suffix (for example `.2`), so customers can find it without directions.

**Estimated savings.** Let $f_0$ be the share of first delivery attempts that fail, $\phi$ the share of those failures that a precise code removes, and $c$ the cost of an attempt. The saving per 1,000 deliveries is

$$
S = 1000 \, f_0 \, \phi \, c .
\tag{16}
$$

Published industry estimates for Africa put the first-attempt success rate as low as 60 per cent ($f_0$ up to 0.40) and the cost of an attempt at about US\$2.70 [@odeloye2023]. No Cabo Verdean measurement exists, so we report a range (Table 9). With central values $f_0 = 0.20$ and $\phi = 0.5$, $S \approx$ US\$270 per 1,000 deliveries. Between islands a failed delivery costs more, because the parcel waits for the next boat or flight.

| $f_0$ | $\phi = 0.25$ | $\phi = 0.50$ | $\phi = 0.75$ |
|--:|--:|--:|--:|
| 0.10 | US\$68 | US\$135 | US\$203 |
| 0.20 | US\$135 | US\$270 | US\$405 |
| 0.40 | US\$270 | US\$540 | US\$810 |

: Savings per 1,000 deliveries by Eq. (16), with $c$ = US\$2.70.

# Emergency services

An ambulance, the fire service or the police face the courier's problem with more at stake, on streets that are steep, narrow and often unnamed. A qualitative study of emergency medical services in Kigali found that crews and dispatchers lost time locating patients because they depended on local knowledge and needed several calls to establish the location [@hunt2024]. We know of no published measurement for Cabo Verde, which is itself a reason to begin one.

**How a code helps a dispatcher.** The caller says one phrase, "Fazenda, trinta e quatro, quarenta e oito". The dispatcher types it and the registry returns one lote: Fazenda in Tarrafal, not one of the six other Fazendas, because only Tarrafal's block holds 34 48 (Figure 4). The dispatcher reads back what the code points to, with its municipality, before the crew leaves. The code resolves to the lote's entrance and its Plus Code, which any dispatch system that reads Plus Codes understands. The engine and registry work without a network.

**Estimated effect.** Larsen and colleagues modelled survival after out-of-hospital cardiac arrest as 67 per cent, less 2.3 points for each minute until cardiopulmonary resuscitation, 1.1 points for each minute until defibrillation and 2.1 points for each minute until advanced care [@larsen1993]. Where a single crew delivers all three, a delay of $\Delta t$ minutes in finding the door reduces survival by

$$
\Delta S = (2.3 + 1.1 + 2.1)\,\Delta t = 5.5\,\Delta t \ \text{percentage points}.
\tag{17}
$$

A saving of one to three minutes corresponds to 5.5 to 16.5 points. The model was fitted in King County, Washington, so these values indicate an order of magnitude for Cabo Verde rather than a prediction; the direction of the effect is not in doubt.

**Planning the network.** On the N-Ways map of October 2026, 72 per cent of a sample of 20,000 lotes lie within 5 km, in a straight line, of a mapped health facility, and 41 per cent within 5 km of a mapped police station (Section 11).

# Government coordination and planning

A home code is a shared key. When ministries, Câmaras Municipais, utilities and the statistics institute refer to a lote by the same code, their records can be joined without matching names and descriptions. The World Bank identifies this as a primary benefit for local government: an address directory lists premises more completely than the tax roll and shows who is missing from it [@farvacque2005]. Each code carries the Correios postcode, the municipal address where one exists and, on the cadastral islands, the NIP where it is known, so each institution keeps its own records and still agrees on the lote.

**Planning with real counts.** The registry counts lotes by island, municipality, zone, building class and status, including *unfinished but lived in*, and every count can be recomputed from the open files. Praia alone holds 31,052 lotes in 64 zones.

**Access to services.** Table 10 gives straight-line distances from a sample of 20,000 lotes to the nearest mapped facility of each kind. The values describe the map rather than the ground: facilities that are not mapped make distances appear longer. A ministry can replace the facility list with its own and recompute the table in minutes.

| Facility | Within 2 km | Within 5 km | Median distance |
|:----------------|-----:|-----:|-----:|
| Health facility (hospital, health centre, health post) | 45.1 % | 71.6 % | 2.53 km |
| School | 58.8 % | 83.8 % | 1.33 km |
| Police station | 28.7 % | 41.0 % | 7.83 km |
| Pharmacy | 35.6 % | 56.5 % | 4.02 km |

: Straight-line distance to the nearest mapped facility; N-Ways map, October 2026, sample of 20,000 lotes.

**Housing policy.** The building profiles keep the census distinction between status and use for every lote and are updated as residents confirm them, so housing policy can follow how homes are completed floor by floor.

**Estimated cost avoided.** A conventional door-numbering programme for the same lotes, at the World Bank average of US\$5.7 per doorway [@farvacque2005], would cost

$$
C = N\,c = 175\,630 \times \text{US}\$5.7 \approx \text{US}\$1.0 \text{ million}
\tag{18}
$$

at 2005 prices, before inflation and before the cost of working across nine islands. With the per-doorway cost observed in a single city of the same review, US\$7.6, the figure is US\$1.33 million. Street signs and municipal numbering remain valuable; home codes do not replace them, but they give every building a usable reference immediately, and official numbers, as they are assigned, are shown first.

# Privacy, safety and governance

An address register describes places, but people use it, and some uses carry risk. This section sets out what the registry records about the people at an address, how the model limits the harm a code could do, and how the issuing of codes is governed.

## Data protection

Codes describe places, never people. Cabo Verde's data protection law, Lei n.º 133/V/2001 as amended and republished by Lei n.º 121/IX/2021, applies to services offered to people in Cabo Verde from abroad, requires notification of the Comissão Nacional de Proteção de Dados before automated processing, and sets a 72-hour deadline for notifying breaches [@lei121_2021]. The registry of codes, lotes and building profiles contains no personal data. Residents' names and household composition are never stored. A household may keep its door private, in which case the code leads to the gate or the street, and business names appear only when their owners publish them.

## Safety

The registry publishes what is visible from the street: footprints, use classes and entrances. It records no occupants, no interior details and no photographs of people; gate photographs used for confirmation are deleted once a gate is confirmed. Corrections are accepted only when independent residents agree, one of them present at the lote, so that a single account cannot move another family's code.

## Governance and the single issuer

N-WAYS LIMITED maintains the model, the engine and the registry in a public repository [@nways2026]. Zone names change only with the agreement of the Câmara Municipal concerned; issued codes never change. Codes must be issued by **one issuer for the country**: the N-Ways issuer today, or any body that the State of Cabo Verde designates. Two independent issuers would assign the same free number to two buildings. Every other deployment of the registry server is read-only. The model is designed to be handed over: the repository, the registry and its rules can move to Correios de Cabo Verde, to INGT and the Comissão Nacional de Toponímia, or to a body they name, without modifying the engine. Until a national body adopts them, these are N-Ways addresses, not official addresses or postcodes. Table 11 lists the institutions concerned.

| Institution | Role |
|:--|:--|
| Correios de Cabo Verde | postcodes and Morada Certa; first partner for hand-over |
| The 22 Câmaras Municipais | zone names, street names, door numbers, local disputes |
| INGT and the Comissão Nacional de Toponímia | toponymy, cadastre, geodesy, national spatial data infrastructure |
| Instituto Nacional de Estatística | census geography |
| Comissão Nacional de Proteção de Dados | data protection |

: Institutions and their roles.

# Limitations and future work

**Zone names.** The names come from OpenStreetMap and GeoNames and include spellings that municipalities may wish to change; 306 plate names are flagged for the Câmaras, 118 of them with no form that fits yet. **Uneven map.** Imagery merges terraced rows in Mindelo and Praia and over-counts annexes on Fogo and in rural Santiago. **Heights and floors** are mostly unknown. **Building classes** are inferences, about a quarter of them of low confidence, and non-residential buildings are under-detected. **Gates** are almost unmapped: only 16 lotes have a mapped gate. **Postcodes** are incomplete: no Correios list is published and the island digits for São Nicolau and Maio are inferred. **Unconfirmed items** include whether Morada Certa still operates and the text of the 2024 cadastre decree, which we know only from secondary summaries. **Language:** the Kriolu number words used by the voice need checking by speakers from Santiago and São Vicente.

**Planned measurements.** We will measure the quantities on which the impact estimates depend (Table 12), and publish the results in the repository.

| Measure | Method | Target |
|:--|:--|:--|
| Recall of one's own code after one week and one month | residents asked without the app | at least 80 % exact |
| Entry errors when spoken, typed and written | courier calls, app search, paper forms; compared with Plus Codes for the same homes | fewer errors than Plus Codes |
| First-attempt delivery success | partner couriers, with and without a code | at least 20 points higher |
| Time from street to door | courier app timestamps | halved |
| Doors and gates confirmed | residents and couriers | 5,000 |
| Locating time for emergency calls | with a willing ambulance or fire service | measured, then halved |
| Acceptance of folded names | residents of each island (Chã de Baixo = Chã Baixo) | accepted |

: Measurements planned.

# Conclusion

We have described a national addressing model for Cabo Verde in which every building has a code made of a place word that residents already use and a short number. National ranges per name make the code unique without any context; Hilbert-ordered, spread numbering keeps neighbours close and leaves room for growth; a Damm check digit in the machine form detects every single-digit error and adjacent transposition. The model is in force for all 175,630 lotes of the country; 44 per cent of codes have three digits and none has more than four. It sits beside the postcode, the municipal address, the cadastre and the Plus Code without replacing any of them. The engine, the registry and a ready-to-deploy server are open, so the State and any institution can verify every code and, once designated, issue new ones by the same rules.

# Data and code availability {-}

The specification, reference engine, conformance vectors, registry, registry server, tools and this paper are available at <https://github.com/n-ways/open-addresses-cabo-verde> [@nways2026]. Code is licensed under the Apache License 2.0, data under the Open Database License 1.0 and documents under Creative Commons Attribution 4.0. Credit line: "N-Ways Addressing for Cabo Verde, © N-WAYS LIMITED (nways.ng)". The figures are compiled from `docs/figures/*.tex` with the tables in `docs/figures/data/`, which `tools/paper_figures.py` recomputes from the registry; the PDFs are built with `sh docs/paper/build.sh`.

# Acknowledgements {-}

We thank the OpenStreetMap contributors, whose buildings, places and boundaries are the foundation of the registry; Google Research and Microsoft for their open building-footprint datasets, and the Overture Maps Foundation for distributing them; GeoNames; and the Instituto Nacional de Estatística, Correios de Cabo Verde, INGT and the Comissão Nacional de Toponímia for the public documents on which Section 2 relies.

# References {-}

::: {#refs}
:::
