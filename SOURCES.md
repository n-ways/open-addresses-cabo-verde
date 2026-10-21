# Sources

Accessed 18 October 2026 unless noted; the paper's own reference list, with every entry checked on 21 October 2026, is [`docs/paper/references.bib`](docs/paper/references.bib). Items that could not be verified from public sources are listed at the end of this file.

## Postal codes and addressing

| # | Source | URL | What it supports |
|---|---|---|---|
| 1 | UPU, *Cabo Verde* addressing sheet (04/2014) | https://www.upu.int/UPU/media/upu/PostalEntitiesFiles/addressingUnit/cpvFr.pdf | 4 digits left of the locality; digits = island, commune, district, post office; example `Rua 5 de Julho 138/Platô, C.P. 38, 7600 PRAIA, SANTIAGO`; island on its own line |
| 2 | Correios de Cabo Verde website (archived 2026-09-20) | http://web.archive.org/web/20260920020105/https://correios.cv/ | services list, no postcode lookup |
| 3 | Correios, *Normas de distribuição* (archived 2026-09-20) | http://web.archive.org/web/20260920020105/https://correios.cv/servicos/termos-e-condicoes/normas-distribuicao | delivery zones and days by town from each airport; distribution centres CVRAIA, CVESPA |
| 4 | correios.cv live site | https://correios.cv/ | unreachable (timeout) on 2026-10-17 and 2026-10-18 |
| 5 | Google Africa Blog, "Delivering mail where the streets have no name" (1 Dec 2016) | https://blog.google/intl/en-africa/products/explore-get-answers/delivering-mail-where-streets-have-no/ | Morada Certa; Plus Codes on the Correios website; ">90 % of roads have no name" |
| 6 | Wikipedia, Correios de Cabo Verde | https://en.wikipedia.org/wiki/Correios_de_Cabo_Verde | OLC "officially adopted by the Cape Verdean post"; HQ 7600 Praia |
| 7 | Statoids, Counties of Cape Verde | https://statoids.com/ucv.html | CGN codes per municipality; "first two digits of postcode = county CGN" (third party) |
| 8 | OpenStreetMap, N-Ways extract of 2026-10-17 (`data/detail/countries/cape-verde/`) | https://www.openstreetmap.org/ | 13 `addr:postcode` tags (2110, 4111, 5110, 7600, 7601, 9110…); 273 house numbers; 24 barrier walls/fences |
| 9 | Nominatim queries (2026-10-17) | https://nominatim.openstreetmap.org/ | 4110 Espargos, 7602 Praia, 8220 São Filipe |
| 10 | Overpass API | https://overpass-api.de/ | refused the query on 2026-10-18 (empty response); counts above come from the local extract |

## Toponymy, cadastre, geodesy

| # | Source | URL | What it supports |
|---|---|---|---|
| 11 | Cabo Verde (INGT/CNT), report to UNGEGN, GEGN.2/2023/135/CRP.135 (10 Apr 2023) | https://unstats.un.org/unsd/ungegn/sessions/3rd_session_2023/documents/GEGN.2_2023_135_CRP135.pdf | DL 5/2012 toponymy and the CNT; municipalities' "police numbering"; no duplicate street names; plaque before a name is granted |
| 12 | Cabo Verde, UNGEGN 2023 presentation (theme 135) | https://unstats.un.org/unsd/ungegn/sessions/3rd_session_2023/documents/UNGEGN%20session%20_Cape%20Verde_135.pdf | Creole/Portuguese mistranslations; Brava/Djabraba kept in both languages |
| 13 | Boletim Oficial I Série n.º 17, 10 Mar 2014, Resolução n.º 18/2014 (via FAOLEX) | https://faolex.fao.org/docs/pdf/cvi131954.pdf | creation of INGT; lists DL 5/2012, DL 35/2011 (geodesy), DL 24/2012 (SITCV/IDE-CV), DL 55/2010, DR 14/2010, DL 29/2009 (cadastre) |
| 14 | Secondary summaries of the boe.incv.cv and FAOLEX texts of DL 37/2014 and amendments (DL 52/2015, 44/2016, 39/2017, 16/2019) | https://boe.incv.cv/ ; https://faolex.fao.org/docs/pdf/cvi185111.pdf | special cadastral regime for Sal, Boa Vista, São Vicente, Maio; NIP; CIP; INGT validation; Mindelo from Sept 2019 |
| 15 | Secondary summaries: Decreto-Lei n.º 12/2024 (21 Mar 2024), new cadastral regime | https://boe.incv.cv/ | **primary text not obtained**; replaces DL 29/2009 (amended by DL 45/2014); CIP mandatory in cadastral areas |
| 16 | EPSG:4826, WGS 84 / Cape Verde National | https://epsg.io/4826 ; https://spatialreference.org/ref/epsg/4826/ | Lambert Conformal Conic parameters; supersedes EPSG:4825, ESRI:102214 |

## Municipal and national address registers

| # | Source | URL | What it supports |
|---|---|---|---|
| 16a | Câmara Municipal da Praia | https://www.cmp.cv/ | unreachable (timeout) on 2026-10-18 |
| 16b | Câmara Municipal de São Vicente | https://cmsv.cv/ | councillor portfolio "Solos, informação geográfica, cadastro e toponímia municipais"; no register published |
| 16c | Câmara Municipal do Sal | https://www.cms.cv/ | not reached |
| 16d | INGT | https://ingt.gov.cv/ingt/ | areas: cadastre, toponymy, IDE-CV; toponymy page returns 404; links to UGPE tenders for the cadastre in São Salvador do Mundo and Tarrafal |
| 16e | INGT Portal do Cadastro | https://portaldocadastro.ingt.gov.cv/ | online CIP, cadastral plan, location plan, re-registration: parcels, not addresses |
| 16f | OpenStreetMap, N-Ways extract | (local) | 273 buildings with addr:housenumber: Praia 92 (planned "Rua Barragem de …" streets), Sal 175, São Vicente 4, Paul 2 |

## Census and statistics

| # | Source | URL | What it supports |
|---|---|---|---|
| 17 | INE, RGPH-2021 preliminary results (slides) | https://cmsf.cv/wp-content/uploads/2020/07/resultados_preliminares_rgph-2021.pdf | 150,016 buildings; 200,979 dwellings; 70.0 % finished, 27.7 % unfinished, 2.0 % non-classic; buildings per municipality (Praia 34,663, 41.6 % unfinished); use: 87.0 % homes only, 6.5 % mostly homes, 1.0 % mostly other, 5.4 % only other |
| 18 | RTP / Lusa, definitive census figures | https://www.rtp.pt/noticias/economia/ine-cabo-verde-tinha-491233-residentes-em-2021_n1396288 | 491,233 residents; 150,206 buildings, 201,348 dwellings (definitive) |
| 19 | Press summaries of the 2010 census | (several press pages) | 114,297 buildings, 141,761 dwellings in 2010 |

## Language

| # | Source | URL | What it supports |
|---|---|---|---|
| 20 | Wikipedia (pt), ALUPEC | https://pt.wikipedia.org/wiki/ALUPEC | alphabet without c/q (k for /k/); DL 67/98; Resolução 48/2005 |
| 21 | Language situation | Cabo Verde's UNGEGN 2023 report and presentation (11, 12); ALUPEC (20) | Portuguese official; Kriolu (kea) everyday; Sotavento and Barlavento variants |

## Short forms of place names (plate names, `tools/build_names.py → KNOWN`)

| # | Source | URL | What it supports |
|---|---|---|---|
| 21a | Inforpress via Balai, "Praia: Tabanka de ASA com festividades de rua em homenagem ao santo padroeiro" | https://www.balai.cv/balai-kultural/praia-tabanka-de-asa-com-festividades-de-rua-em-homenagem-ao-santo-padroeiro/ | "A Tabanka do bairro de Achada Santo António (ASA)": `ASA` is the short form of Achada Santo António |
| 21b | A Nação, 4 Feb 2026, "Praia: Prisão preventiva para o principal suspeito do homicídio de jovem de 17 anos, na ASA, em 2024" | https://www.anacao.cv/noticia/2026/02/04/praia-prisao-preventiva-para-o-principal-suspeito-do-homicidio-de-jovem-de-17-anos-na-asa-em-2024/ | headline "na ASA"; the body names Achada Santo António |
| 21c | Expresso das Ilhas, 9 Aug 2025, "CMP repudia roubo de plantas e promete levar à justiça os infractores" (topic page) | https://expressodasilhas.cv/topico/achada-grande-frente | "na subida de Achada Grande Frente (AGF)": `AGF` is the short form of Achada Grande Frente |
| 21d | Searches for "AGT" (Achada Grande Trás), 2026-10-18 | (Wikipedia, press, web search) | no published use found: AGT stays an alias, the plate name goes to the Câmara |

## Data protection

| # | Source | URL | What it supports |
|---|---|---|---|
| 22 | Lei n.º 121/IX/2021 (republishing Lei 133/V/2001), CNPD | https://www.cnpd.cv/wp-content/uploads/2025/03/Lei-121.IX_.2021-alteracao-Lei-41.VIII_.2013.pdf | scope art. 2(2)(c), information art. 13, breach art. 27, transfers arts. 35-36, notification art. 39 (read 2026-10-17) |
| 23 | CNPD | https://www.cnpd.cv/ | authority, Praia |

## Data used to build the model

| # | Source | Licence | Use |
|---|---|---|---|
| 24 | OpenStreetMap buildings, places, admin boundaries (N-Ways extract 2026-10-17) | ODbL 1.0 | 91,399 footprints, municipality outlines, the national border (admin_level 2, `engine/data/border.geojson`), suburbs and villages |
| 25 | Google Open Buildings via Overture Maps | CC BY 4.0 | footprints OSM lacks |
| 26 | Microsoft building footprints via Overture Maps | ODbL 1.0 | footprints OSM lacks (100,875 ML footprints in total with 25) |
| 27 | GeoNames | CC BY 4.0 | localities (zones) |
| 28 | N-Ways places (OSM, Overture, Foursquare OS Places, All The Places) | per source (LICENSING.md) | categories of POIs inside footprints |
| 29 | N-Ways routing build: enclosures and gates | derived from OSM (ODbL) | 862 enclosures, 127 gates in Cabo Verde |
| 30 | N-Ways footprint processing | internal | the machine-learned height field is the Overture height, else floors×3.2+1, else a rendering filler 3.5+3.5×hash: not used |

## Methods

| # | Source | URL |
|---|---|---|
| 31 | Open Location Code specification and reference code | https://github.com/google/open-location-code |
| 32 | ISO/IEC 7064:2003 Check character systems (MOD 11,10: the alternative considered, SPEC §4) | https://www.iso.org/standard/31531.html |
| 33 | H. M. Damm, *Total anti-symmetrische Quasigruppen*, dissertation, Philipps-Universität Marburg, 2004 (the Damm check digit) | https://archiv.ub.uni-marburg.de/diss/z2004/0516/ |

## Unverified

- Island digits 3 (São Nicolau) and 6 (Maio) of the postcode: inferred.
- 7110 Tarrafal and 1110–1139 Ribeira Grande: third-party listings.
- Whether Morada Certa still runs in 2026.
- The text of DL 12/2024 and the current rules for licensed cadastral surveyors.
- Municipal door-numbering campaigns since 2016.
- The Kriolu number words in `cv_engine.py`.
