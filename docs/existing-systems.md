# Existing address and postcode systems in Cabo Verde

Checked 2026-10-18 (sources in [SOURCES.md](../SOURCES.md)). Status: open (CC BY 4.0, see [LICENSING.md](../LICENSING.md)).

## Verdict

**Postal codes exist but are coarse (locality / delivery-zone level), not door-level.** Cabo Verde has no national door-level address system. What it has:

1. **Correios de Cabo Verde postcodes**: four digits written before the locality, such as `7600 PRAIA`. They identify a delivery area (an island, a municipality, a district, a post office), not a building.
2. **Plus Codes through Correios' "Morada Certa" campaign (2016)**: Correios added Open Location Code (Plus Codes) to its website so residents could link the code of their home to their postal identity. It is a coordinate reference with no building or door registry behind it, and we could not confirm that it still runs in 2026.
3. **Street names and door numbers ("toponímia e numeração de polícia")**: a municipal job under Decreto-Lei n.º 5/2012. They exist in the old centres (Platô in Praia, Mindelo) and are patchy elsewhere. Google reported in 2016 that more than 90 % of roads had no name.
4. **The land cadastre (INGT)**: a parcel register with a Número de Identificação Predial (NIP), finished for Sal, Boa Vista, Maio and São Vicente and being extended. It identifies land parcels for title, not addresses for delivery.

So the N-Ways model sits beside these four systems and points to each of them. It never replaces the postcode, never issues a competing coordinate code where Plus Codes already serve, and never claims to be a title or an official door number.

## 1. Correios de Cabo Verde postcodes

**Format.** The UPU addressing sheet for Cabo Verde (dated 04/2014) says "four digits to the left of the locality name", and its diagram reads the four digits of `7600` as **island, municipality (commune), municipal district, post office**. Its example:

```
Luis Felipe Ramos
Rua 5 de Julho 138/Platô      street + zone
C.P. 38                        P.O. box
7600 PRAIA                     postcode + locality
SANTIAGO                       island
CABO VERDE
```

The island goes on its own line. That is the clearest official sign that in Cabo Verde **the island is part of the address**.

**The first digit is the island.** The UPU structure, the codes seen in OpenStreetMap and those returned by Nominatim all agree:

| Digit | Island | Codes seen (source) |
|---|---|---|
| 1 | Santo Antão | 1110–1139 Ribeira Grande (third-party listing) |
| 2 | São Vicente | 2110 Mindelo (OSM) |
| 3 | São Nicolau | none seen; inferred from the island order |
| 4 | Sal | 4110 Espargos, 4111 Santa Maria (OSM, Nominatim) |
| 5 | Boa Vista | 5110 Sal Rei (OSM) |
| 6 | Maio | none seen; inferred |
| 7 | Santiago | 7600–7602 Praia (UPU, OSM); 7110 Tarrafal (third-party, unverified) |
| 8 | Fogo | 8220 São Filipe (Nominatim) |
| 9 | Brava | 9110 Nova Sintra (OSM) |

The numbering runs from north-west (Santo Antão) to south-west (Brava), the order in which people list the islands.

**The first two digits mostly follow the old municipalities.** Statoids reports that the first two digits equal the municipality's number in the national geographic code (CGN): 11 Ribeira Grande, 21 São Vicente, 41 Sal, 51 Boa Vista, 82 São Filipe, 91 Brava. **Praia breaks the rule.** Its CGN number is 74 but its postcodes are 76xx. Municipalities created in 2005 (São Salvador do Mundo, São Lourenço dos Órgãos, Ribeira Grande de Santiago, Santa Catarina do Fogo, Tarrafal de São Nicolau) share their parent's two-digit number, so **the postcode cannot name today's 22 municipalities**. That is one reason the N-Ways code uses the ISO 3166-2 municipality key and keeps the postcode as separate context.

**Use.** Mail is mostly collected from P.O. boxes (`C.P.`, `Caixa Postal`) or community boxes. The Correios site (as archived on 2026-09-20; it was unreachable directly on 2026-10-17 and 2026-10-18) lists services, tracking, branch finder and delivery standards by town and zone (Zona 1/2/3 delivery days from each airport), but **no postcode lookup and no published postcode list**. No licence for postcode data was found. OpenStreetMap holds only 13 `addr:postcode` tags in Cabo Verde (N-Ways extract of 2026-10-17).

**Verdict:** area codes, live but low-profile, with no public directory. **Not door-level.**

## 2. Morada Certa and Plus Codes (Correios + Google, 2016)

Google's Africa blog (1 Dec 2016) reports that Correios de Cabo Verde launched **Morada Certa** ("the right address"), a national initiative to give residents addresses so mail could be delivered, because "more than 90 percent of roads in Cape Verde don't have names". Plus Codes were built into the Correios website: residents found the code for their home or work in four steps and linked it to their postal identification. Wikipedia's Correios article says Open Location Code "has officially been adopted by the Cape Verdean post".

**What it is and is not.** A Plus Code names a grid square of about 14 × 14 m (10 digits), or about 3 × 3 m (11 digits), anywhere on Earth. It works offline, it is open (Apache-2.0), and no register is needed. It does not say which building or door is meant, it does not change when a house is built, and nobody records that a building exists.

**Status in 2026: unverified.** The archived Correios site of 2026-09-20 has no Morada Certa or Plus Code page in its service menus, and we found no 2024–2026 news of the campaign. It may survive at the counter only.

**Consequence for the design.** This is the official precedent, so **the N-Ways spot layer in Cabo Verde is the Plus Code itself**, not a new grid (model.md §4). The N-Ways model adds what Morada Certa lacked: a stable building and lote register, doors and gates confirmed by people, a building profile, and the island, municipality and postcode context.

## 3. Street names and door numbers (municipal toponymy)

**Law.** Decreto-Lei n.º 5/2012 (28 Feb 2012) governs toponymy at national and municipal level and creates the **Comissão Nacional de Toponímia (CNT)**, coordinated by the **Instituto Nacional de Gestão do Território (INGT)**. Cabo Verde's 2023 report to the UN Group of Experts on Geographical Names (UNGEGN) says the CNT standardises, compiles and validates names. It also commits to "obliging, stimulating and supporting the municipalities to give a new impetus to the massive implementation of municipal toponymy and **police numbering**" (numeração de polícia, i.e. door numbers). Names must not duplicate street names, and a plaque must go up before a name is granted.

**Practice.** Names and numbers exist in historic centres (Platô, Mindelo's centre) and in newer planned districts. Most streets elsewhere have no plate, and people navigate by zone (bairro), landmark and phone call. The UNGEGN report also describes toponyms mistranslated between Portuguese and Kriolu (Mampatraz → "Mão para traz"; Lin d'corvo → "Lindo Corvo"), and the CNT policy keeps names in both languages where both exist (Brava / Djabraba).

**Short forms people already use.** The Praia press writes `ASA` for Achada Santo António (Inforpress via Balai: "A Tabanka do bairro de Achada Santo António (ASA)"; A Nação, 4 Feb 2026, "na ASA") and `AGF` for Achada Grande Frente (Expresso das Ilhas, 9 Aug 2025: "na subida de Achada Grande Frente (AGF)"). These are the only documented short forms the model uses as plate names (model.md §3.5; SOURCES.md 21a–21d). "AGT" for Achada Grande Trás is in the map's alias list, but we found no published use, so it stays an alias only.

**Consequence for the design.** Where a municipality has given a street name and a door number, the N-Ways record **shows them first** and links them to the lote. The municipality stays the authority for door numbers. The N-Ways code is never painted as a "número de polícia".

**Verdict:** an official door-level system **in law, municipality by municipality, but not implemented nationally**. The model points to it wherever it exists.

### 3.1 Municipal and national registers (checked 2026-10-18)

Official data comes first wherever it exists, so every body that could hold an address register was checked.

| Body | What we found | Register usable as official address data? |
|---|---|---|
| Câmara Municipal da Praia (cmp.cv) | site unreachable (timeout) | not found |
| Câmara Municipal de São Vicente (cmsv.cv) | a councillor's portfolio "Solos, informação geográfica, cadastro e toponímia municipais"; no street or number register published | not found; to request |
| Câmara Municipal do Sal (cms.cv) | no site reached | not found |
| INGT toponymy page | 404 | not found |
| INGT Portal do Cadastro (portaldocadastro.ingt.gov.cv) | online CIP, cadastral plan, location plan ("planta de localização"), re-registration; cadastre being extended to São Salvador do Mundo and Tarrafal (UGPE tenders linked from ingt.gov.cv) | parcels (title), not addresses |
| National address register | none found | none |
| OpenStreetMap evidence | 273 buildings with house numbers: Praia 92 (mostly the planned "Rua Barragem de …" streets of the west), Sal 175 (174 without street), São Vicente 4, Paul 2 | evidence of municipal numbering, to confirm with each Câmara |

**Verdict.** No government address dataset can be used yet. Where municipal numbering exists on the ground (Platô, central Mindelo, planned streets of Praia and Sal), the model **shows those addresses first**, and every lote there has its home code too (model.md §1.1, SPEC §3.6). Each Câmara is asked for its register; its streets become `official` once it is shared. Municipal numbering campaigns after 2016 could not be verified from public sources.

## 4. Land cadastre (INGT) and the national geodetic frame

- **Institutions.** INGT was created by Resolução n.º 18/2014 (B.O. I Série n.º 17, 10 Mar 2014) for spatial planning, urban development, housing, geodesy, cartography, the national spatial data infrastructure (IDE-CV / SITCV, Decreto-Lei n.º 24/2012) and the land cadastre. Its legal base includes Decreto-Lei n.º 35/2011 (geodesy), Decreto-Lei n.º 55/2010 (cartographic production) and Decreto-Regulamentar n.º 14/2010 (national cartographic plan).
- **Cadastre law.** Decreto-Lei n.º 29/2009 (cadastre regime), amended by Decreto-Lei n.º 45/2014. A special regime for the cadastral operation on Sal, Boa Vista, São Vicente and Maio came in Decreto-Lei n.º 37/2014, amended four times (the last, Decreto-Lei n.º 16/2019). Third-party summaries report that **Decreto-Lei n.º 12/2024 (21 Mar 2024)** approved a new cadastral regime that replaces Decreto-Lei 29/2009, makes the Certidão de Identificação Predial mandatory in cadastral areas, and amends the notary, land-registry and State-assets codes. *The 2024 text itself could not be obtained; the summary rests on secondary sources (SOURCES.md).*
- **Identifiers.** Each parcel has a **NIP (Número de Identificação Predial)** and, once its boundaries are final, a **Certidão de Identificação Predial (CIP)**. INGT declared the whole of São Vicente a cadastral area after the work there (extended to Mindelo from Sept 2019). Praia had not been through a cadastral operation in the academic work we found.
- **Surveyors.** Under the 2009 regime, private people and firms with recognised technical competence could do cadastral work only with authorisation and an *alvará* from the central cadastre service, and could be inspected at any time. Whether the 2024 regime keeps this model is unverified.
- **Datum and projection.** The national projected system is **EPSG:4826 "WGS 84 / Cape Verde National"**: Lambert Conformal Conic (2SP), standard parallels 15°N and 16°40′N, latitude of origin 15°50′N, central meridian 24°W, false easting 161,587.83 m, false northing 128,511.202 m. The definition comes from Cabo Verde's Ministry of Infrastructure and Transport and replaces EPSG:4825 and ESRI:102214. Older island datums (the "Cape Verde" datum on EPSG ellipsoid codes, the 1969 1:25,000 military chart) still appear on old survey plans.

**Consequence for the design.** The cadastre is the land title. An N-Ways lote can carry a parcel's NIP as a **reference** when the owner shows a CIP, and the "Add my home" flow can import a survey plan in EPSG:4826. An N-Ways code is **never a title** and never settles a boundary (model.md §9).

## 5. The census geography (INE)

INE's 2021 census (RGPH-2021) set out to georeference and describe every building, dwelling and household. The preliminary results count **150,016 buildings** (definitive: 150,206), **200,979 dwellings** and 145,952 households. Of these buildings, 70.0 % are classic and finished, **27.7 % are classic but unfinished**, 0.3 % are other classic buildings (collective housing, factories) and 2.0 % are non-classic (shacks, *casas de bidão*, containers). Of the classic buildings, 87.0 % are used only as homes, 6.5 % mostly as homes, 1.0 % mostly for other uses and 5.4 % only for other uses. Census zones (*zonas* and *lugares* in the national geographic code, CGN) are not published as open data. The N-Ways building profile uses these figures as **priors and checks**, never as data about any one household.

## 6. What N-Ways already holds

- 22 municipality outlines (OpenStreetMap, ODbL).
- **192,272 building footprints** in the registry: 91,397 from OpenStreetMap and 100,875 from Google Open Buildings / Microsoft (through Overture) that OSM lacks. That is 28 % more footprints than the census has buildings, because the map also counts annexes, sheds, unfinished shells and ruins.
- 273 OSM buildings with house numbers, 13 with postcodes.
- 862 mapped enclosures (schools, hotels, barracks, government sites) and 127 gates from the N-Ways routing build.
- About 6,800 places (POIs) inside the Cabo Verde box.

## 7. Data protection

**Lei n.º 133/V/2001** (personal data of natural persons), amended by **Lei n.º 41/VIII/2013** and **Lei n.º 121/IX/2021** (republished). It applies to controllers abroad that offer services to people in Cabo Verde (art. 2(2)(c)), requires prior notification to the **Comissão Nacional de Proteção de Dados (CNPD)** before automated processing (art. 39), sets 72-hour breach notice (art. 27) and limits transfers abroad to adequate countries or authorised safeguards (arts. 35–36). The CNPD is at Avenida China, Praia (cnpd.cv). See model.md §10 for how the model keeps codes about places and not people.

## Unverified items

- Island digits 3 (São Nicolau) and 6 (Maio): inferred from the island order; no code was seen.
- The full list of Correios postcodes: none is published. Correios was unreachable on 2026-10-17 and 2026-10-18.
- Whether Morada Certa still runs in 2026.
- The text of Decreto-Lei n.º 12/2024 (cadastre), and whether its surveyor licensing (alvará) matches the 2009 regime.
- Whether Praia or other municipalities have run door-numbering campaigns since 2016.
