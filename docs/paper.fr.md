---
title: "Un code de maison pour chaque bâtiment du Cabo Verde"
subtitle: "Un modèle national d'adressage fondé sur les noms de lieux, des séries numériques nationales et les emprises des bâtiments"
kind: "Article de recherche"
author:
  - "The N-Ways Addressing Group"
affiliation: "N-WAYS LIMITED · nways.ng"
date: "Octobre 2026"
abstract-title: "Résumé"
abstract: |
  La plupart des logements du Cabo Verde n'ont pas d'adresse utilisable par un livreur, une équipe d'ambulance ou un visiteur : les codes postaux couvrent des villes entières, la numérotation des portes n'existe que dans quelques centres historiques, et l'on se retrouve par le quartier, un point de repère et un appel téléphonique. Nous présentons un modèle d'adressage conçu pour le Cabo Verde et aujourd'hui en vigueur dans tout le pays. Un *code de maison* est le nom court que les habitants emploient déjà pour leur bairro, leur zona ou leur povoação, de douze caractères au plus, suivi d'un nombre de trois ou quatre chiffres, par exemple `Palmarejo 19 22`. Comme les noms de lieux se répètent, toutes les zones portant le même nom puisent dans une série nationale unique pour ce nom, divisée en blocs figés, de sorte que le code est unique sans mention de commune ni d'île. Les numéros suivent un ordre de Hilbert des bâtiments et laissent de la place entre voisins pour les constructions futures ; un chiffre de contrôle de Damm, présent seulement dans la forme machine, détecte toute erreur sur un chiffre et toute inversion de deux chiffres adjacents. Construit à partir de 192 272 emprises de bâtiments, le registre compte 175 630 codes dans 1 778 zones sous 1 360 noms ; 44 % des codes ont trois chiffres et aucun n'en a plus de quatre. Nous donnons chaque formule avec un exemple résolu, le moteur, le registre et le serveur ouverts, les solutions écartées, ainsi qu'une estimation des bénéfices pour les citoyens, la logistique, les secours et l'administration.

  *Mots-clés :* adressage ; Cabo Verde ; toponymie ; chiffre de contrôle ; courbe de Hilbert ; Open Location Code ; emprises de bâtiments ; données ouvertes.
rights: "© 2026 N-WAYS LIMITED. Texte sous licence CC BY 4.0 ; données sous ODbL 1.0 ; code sous Apache License 2.0."
toc-title: "Table des matières"
lang: fr-FR
---

# Introduction

## Le problème

Le Cabo Verde compte 491 233 habitants [@rtp2022] répartis sur neuf îles habitées (figure 1). En 2016, plus de neuf routes sur dix n'avaient pas de nom [@rinckes2016]. Les résultats provisoires du recensement de 2021 dénombrent 150 016 bâtiments et 200 979 logements [@ine2021], mais ni le recensement ni aucun registre public ne donne à ces bâtiments une adresse que les gens puissent utiliser. On indique le chemin comme on l'a toujours fait : « Achada Santo António, perto da Caixa », « atrás do mercado », « liga quando chegares ».

![Les 22 communes du Cabo Verde, teintées selon le nombre de codes de maison par kilomètre carré, avec le nombre de codes de chaque île. Praia a la plus forte densité, environ 320 codes par km² ; Boa Vista et Maio les plus faibles, environ 8. Données : `registry/` et les contours des communes dans `engine/data/`.](figures/map-fr.svg){width=88%}

L'adresse compte chaque année davantage. Les livraisons ont augmenté avec le paiement mobile et le commerce en ligne. Le tourisme de Sal et de Boa Vista dépend de chauffeurs capables de trouver hôtels et appartements loués ; les établissements hôteliers ont accueilli 1 177 467 clients en 2024, dont 58,5 % à Sal et 24,1 % à Boa Vista [@forbes2025]. Les secours doivent trouver des maisons dans des rues pentues et sans nom. Les familles s'envoient des biens d'une île à l'autre et depuis la diaspora. L'étude de la Banque mondiale sur l'adressage décrit l'adresse comme une infrastructure de base de la gestion municipale, de la fiscalité et des services [@farvacque2005], et l'Union postale universelle fait d'une adresse pour chaque ménage une condition de l'inclusion [@upu2012].

Le Cabo Verde dispose déjà de quatre systèmes partiels : des codes postaux de zone, un code de grille relié à l'identité postale, une numérotation des portes prévue par la loi et un cadastre sur quatre îles (section 2). Aucun ne donne à chaque bâtiment un identifiant qu'une personne puisse retenir et dicter au téléphone.

## Contribution

Cet article décrit un modèle national d'adressage conçu pour le Cabo Verde et émis pour tout le pays les 19 et 20 octobre 2026. Nos contributions sont les suivantes :

1. **Une forme de code choisie pour être retenue.** Un code de maison est un mot de lieu que les habitants emploient déjà, réduit par une règle écrite à douze caractères et deux mots au plus, suivi d'un nombre de trois ou quatre chiffres (sections 4.2 et 4.5).
2. **Une unicité nationale sans contexte.** Toutes les zones qui partagent un nom court puisent leurs numéros dans une série nationale unique pour ce nom, divisée en blocs figés, si bien que « nom et numéro » désignent un seul lieu dans le pays (section 4.6).
3. **Une numérotation qui ménage la croissance.** Dans chaque zone, les numéros suivent un ordre de Hilbert des bâtiments et se répartissent sur un bloc trois fois plus grand que la zone ; les bâtiments construits plus tard reçoivent un numéro compris entre ceux de leurs voisins, et aucun numéro émis ne change (sections 4.7 et 4.8).
4. **Des données de référence au niveau du bâtiment.** Chaque code est rattaché à un *lote* (parcelle ou concession) avec son entrée et le profil de chaque construction, y compris l'état « inachevé mais habité », si caractéristique du pays (section 4.12).
5. **Une mise en œuvre ouverte et reproductible.** Nous publions un moteur de référence, des vecteurs de conformité, le registre complet des 175 630 codes et un serveur du registre que toute institution peut déployer et qui reproduit exactement les décisions de l'émetteur (section 5).
6. **Une évaluation et une estimation d'impact.** Nous mesurons l'unicité, la longueur, la détection d'erreurs et la couverture (section 6), consignons les solutions écartées avec leur coût mesuré (section 7) et estimons les bénéfices pour quatre groupes d'usagers, hypothèses à l'appui (sections 8 à 11).

## Plan de l'article

La section 2 passe en revue les systèmes existants au Cabo Verde et la littérature internationale. La section 3 décrit les données. La section 4 expose le modèle, avec un exemple unique, `Palmarejo 19 22`, suivi à travers toutes les formules. La section 5 décrit la mise en œuvre et la section 6 l'évalue. La section 7 consigne les solutions mesurées puis écartées. Les sections 8 à 11 traitent des bénéfices pour les citoyens, pour la logistique, le commerce et le tourisme, pour les services de secours et pour l'administration. La section 12 porte sur la vie privée, la sécurité et la gouvernance, la section 13 sur les limites, et la section 14 conclut.

# Contexte et travaux connexes

Nous avons vérifié les systèmes existants entre le 17 et le 21 octobre 2026. Le relevé complet, avec toutes les sources et les points que nous n'avons pas pu confirmer, figure dans `docs/existing-systems.md` et `SOURCES.md`.

## Les codes postaux des Correios de Cabo Verde

La fiche d'adressage de l'UPU pour le Cabo Verde, datée d'avril 2014, prévoit quatre chiffres à gauche du nom de la localité, comme dans `7600 PRAIA`, l'île figurant sur une ligne propre au-dessous ; elle lit les quatre chiffres comme île, commune, district communal et bureau de poste [@upu2014cv]. Les codes que nous avons pu observer confirment que le premier chiffre désigne l'île (tableau 1).

| Chiffre | Île | Codes observés |
|:--|:--|:--|
| 1 | Santo Antão | Ribeira Grande (liste de tiers) |
| 2 | São Vicente | 2110 Mindelo |
| 3 | São Nicolau | aucun observé |
| 4 | Sal | 4110 Espargos, 4111 Santa Maria |
| 5 | Boa Vista | 5110 Sal Rei |
| 6 | Maio | aucun observé |
| 7 | Santiago | 7600–7602 Praia |
| 8 | Fogo | 8220 São Filipe |
| 9 | Brava | 9110 Nova Sintra |

: Le premier chiffre du code postal désigne l'île. Sources : UPU [@upu2014cv], OpenStreetMap et Nominatim ; les chiffres de São Nicolau et de Maio se déduisent de l'ordre des îles.

D'après une liste de tiers, les deux premiers chiffres suivent le numéro de la commune dans le code géographique national [@statoids]. Praia fait exception (76 et non 74), et les communes créées en 2005 partagent les chiffres de leur commune d'origine ; le code postal ne peut donc pas nommer les 22 communes actuelles. Les Correios ne publient ni liste ni recherche de codes postaux ; leur site, tel qu'archivé en septembre 2026, propose le suivi des envois, la recherche de guichets et les normes de distribution, mais aucun répertoire de codes [@correios2026]. Le code postal est donc un code de zone, non une adresse à la porte.

## Morada Certa et les Plus Codes

En 2016, les Correios de Cabo Verde et Google ont lancé *Morada Certa* (« la bonne adresse ») : les Plus Codes ont été intégrés au site des Correios afin que les habitants relient le code de leur logement à leur identité postale [@rinckes2016]. Un Plus Code est un Open Location Code, une référence de grille hiérarchique qui désigne une cellule d'environ 14 m avec dix caractères, ou d'environ 3 m avec onze [@olc]. Il fonctionne hors ligne et n'exige aucun registre, mais il ne dit pas de quel bâtiment ni de quelle porte il s'agit. Nous n'avons trouvé aucun indice que la campagne soit encore active en 2026. Puisque les Correios ont choisi cette grille, le modèle en fait sa couche de points et n'introduit aucune grille concurrente (section 4.11).

## Noms de rues et numérotation des portes

Le décret-loi n° 5/2012 du 28 février 2012 encadre la toponymie aux niveaux national et municipal et a créé la Comissão Nacional de Toponímia, coordonnée par l'Instituto Nacional de Gestão do Território (INGT) [@ungegn2023; @res18_2014]. Dans son rapport de 2023 au Groupe d'experts des Nations unies pour les noms géographiques, le Cabo Verde s'est engagé à soutenir les communes dans « la mise en œuvre massive de la toponymie municipale et de la numérotation de police », c'est-à-dire des numéros de porte, et a posé la règle qu'un nom de rue ne se répète pas [@ungegn2023]. Les communes sont ainsi l'autorité légale de l'adresse à la porte. Sur le terrain, celle-ci n'existe que dans les centres historiques du Platô et de Mindelo, dans quelques quartiers planifiés de Praia et à Santa Maria, sur Sal. Nous n'avons trouvé aucun registre municipal d'adresses publié.

## Le cadastre et le système de référence national

L'INGT a été créé en 2014 et chargé de l'aménagement du territoire, de la géodésie, de la cartographie, de l'infrastructure nationale de données spatiales et du cadastre [@res18_2014]. Un régime spécial a encadré l'opération systématique de cadastre à Sal, Boa Vista, São Vicente et Maio [@dl16_2019]. Chaque parcelle porte un Número de Identificação Predial (NIP). Le système de coordonnées projetées national est l'EPSG:4826, *WGS 84 / Cape Verde National*, une projection conique conforme de Lambert à parallèles standard de 15° N et 16°40′ N [@epsg4826]. Le cadastre établit la *propriété* ; l'adresse sert à *trouver*. Un code de maison n'est jamais un titre, même si un lote peut conserver son NIP en référence.

## Le recensement

Le recensement de 2021 a géoréférencé chaque bâtiment. Sur les 150 016 bâtiments des résultats provisoires, 27,7 % étaient des bâtiments classiques inachevés, et 87,0 % des bâtiments classiques servaient exclusivement au logement ; le nombre de bâtiments avait augmenté de 31,3 % depuis 2010, où l'on en comptait 114 297 [@ine2021]. Le décompte définitif est de 150 206 bâtiments [@rtp2022]. Les zones de dénombrement ne sont pas publiées en données ouvertes. Le modèle utilise ces totaux comme lois *a priori* et comme contrôles, jamais comme information sur un ménage.

## Pratique internationale

La norme S42 de l'UPU définit les éléments d'une adresse postale et les modèles de leur présentation [@upuS42], et l'ISO 19160-1 propose un modèle conceptuel de l'adressage qui distingue l'adresse, ses composantes et l'objet adressable [@iso19160]. Les deux normes admettent une adresse formée d'une localité et d'un identifiant à l'intérieur de celle-ci, structure que nous adoptons. La Banque mondiale a étudié l'adressage dans des villes africaines : dans un échantillon de 21 villes, seules 8 % des rues avaient un nom avant les programmes, et le coût moyen était de 5,7 dollars des États-Unis par porte adressée, aux prix de 2005 [@farvacque2005]. La même étude avertit que l'adressage se dégrade lorsque les habitants ne s'en servent pas ; c'est pourquoi la mémorisation est notre premier critère.

## Autres systèmes de codes

Les codes de grille comme l'Open Location Code [@olc] désignent des points et non des bâtiments, et comportent des lettres et un séparateur. Ailleurs en Afrique de l'Ouest, des systèmes nationaux d'adresse numérique fondés sur une grille ont été mis en place, par exemple le système national d'adressage numérique des propriétés du Ghana, lancé en 2017 [@graphic2017]. Tous partagent une limite : le code exprime une position et non un mot de lieu que les habitants reconnaissent ; il se retient mal et ne protège pas contre une erreur qui tombe sur une autre cellule valide. Les codes nationaux purement numériques ne contiennent aucun lieu, et les codes alphanumériques reposent sur des lettres, qu'aucune adresse cap-verdienne ne contient et qui se dictent mal en portugais (section 7.1). Nous conservons donc la grille pour les points et donnons à chaque bâtiment un code formé d'un mot de lieu et d'un nombre court.

# Données et sources

Le modèle est calculé à partir de données cartographiques ouvertes, vérifié au moyen des statistiques nationales et publié sous forme de registre ouvert. Cette section décrit chaque source et le contenu du registre.

## Emprises des bâtiments

Le registre repose sur les emprises de bâtiments dont N-Ways disposait en octobre 2026 : 91 397 issues d'OpenStreetMap [@osm2026] et 100 875 issues de l'apprentissage automatique, de Google Open Buildings [@sirko2021] et de Microsoft [@microsoft2023], reçues par le thème bâtiments d'Overture Maps [@overture2026] là où OpenStreetMap n'en avait pas. Les 192 272 emprises du registre dépassent de 28 % le nombre de bâtiments recensés, car la carte compte aussi les annexes, les abris, les constructions inachevées et les ruines. L'écart n'est pas uniforme. À Praia, la carte compte 32 591 emprises pour 34 663 bâtiments recensés (6 % de moins) et, à São Vicente, 18 315 pour 23 976 (24 % de moins), parce que l'imagerie fusionne les rangées de maisons mitoyennes. À Fogo et dans l'intérieur de Santiago, les emprises atteignent jusqu'à 2,7 fois le nombre de bâtiments recensés, car chaque dépendance est cartographiée. La figure 2 montre les sources par île.

![Emprises de bâtiments du registre, par île et par source. Les emprises issues de l'apprentissage automatique comblent les lacunes d'OpenStreetMap, surtout à Fogo et à Boa Vista. Données : `registry/structures/`.](figures/sources-fr.svg){width=80%}

## Localités et noms

Les zones sont construites à partir de la couche des localités de N-Ways : faubourgs, quartiers, villages et villes d'OpenStreetMap, et localités de GeoNames qui ne sont pas des formes de relief [@geonames]. Environ 3 800 lieux nommés donnent 2 818 zones candidates puis, après les règles de la section 4.4, 1 778 zones. Deux formes courtes employées par la presse de Praia, `ASA` pour Achada Santo António et `AGF` pour Achada Grande Frente, sont attestées dans [@balai2025asa; @anacao2026; @expresso2025agf].

## Lois a priori statistiques

Le profil des bâtiments (section 4.12) prend pour lois *a priori* les proportions du recensement de 2021 : 87,0 % des bâtiments classiques consacrés uniquement au logement et 27,7 % inachevés [@ine2021]. Les graphies en créole sont normalisées selon l'alphabet unifié ALUPEC [@alupec].

## Le registre

Le registre (`registry/`) contient tous les codes émis : un fichier par commune, à 20 colonnes par code (forme machine, code de maison, nom officiel, zone, numéro, chiffre de contrôle, statut, émission, entrée, Plus Code, usage, type de lote, nombre de constructions, surface de plancher, code postal, couverture, adresse officielle), la table des zones et le registre national des noms, le point de numérotation de chaque lote, ainsi que le profil et l'emprise WKT de chaque construction. Un manifeste consigne les effectifs et l'empreinte SHA-256 de chaque fichier. Tous les codes sont publiés ; rien n'est retenu.

# Le modèle

Cette section spécifie le modèle dans l'ordre où un code se construit : les exigences auxquelles il doit répondre, les formes du code, le masque de couverture des adresses officielles, les zones et leurs noms de plaque, les séries nationales de chaque nom et leurs blocs, la numérotation dans la zone et sa croissance, le décodage, le chiffre de contrôle, la couche des points et le profil du bâtiment. Chaque règle est donnée par une équation numérotée, et le code `Palmarejo 19 22` sert d'exemple détaillé.

## Exigences

Les exigences, par ordre de priorité, sont :

1. **Mémorisation et accès sans effort.** Les habitants doivent pouvoir retenir leur code et l'obtenir sans effort. Ce critère passe avant la brièveté et l'élégance mathématique, car une adresse que personne n'utilise se dégrade [@farvacque2005].
2. **L'adresse officielle d'abord.** Là où une commune a attribué une rue et un numéro, cette adresse s'affiche en premier, telle qu'elle est écrite ; le code figure à côté. Le code postal des Correios, le NIP et le Plus Code s'affichent à côté du code, et aucun n'est remplacé.
3. **Niveau du bâtiment et de la porte.** Le code mène à un portail ou à une porte, non à un centroïde derrière un mur.
4. **Fonctionnement hors ligne.** Un téléphone sans réseau peut afficher, vérifier et lire à voix haute les codes.
5. **Ouverture.** La méthode, le moteur et les données sont publics.
6. **Stabilité.** Un code ne se déplace jamais, n'est jamais réattribué et ne s'allonge jamais.
7. **Vie privée.** Les codes décrivent des lieux, jamais des personnes.

## Le code de maison et ses formes

Un code de maison est le nom court d'une zone suivi d'un numéro :

> **Palmarejo 19 22** · Praia, Santiago  
> **São Filipe 21 29** · *Lote Achada São Filipe* · Praia, Santiago  
> **Fazenda 34 48** · Tarrafal, Santiago  
> **João Vaz 214** · *Chã de João Vaz* · Paul, Santo Antão

Le numéro a trois chiffres (100–999) ou quatre (1000–9999) ; la longueur est une propriété du nom (section 4.6) et le numéro ne commence jamais par zéro. Quatre chiffres s'écrivent et se disent en deux paires, comme les numéros de téléphone au Cabo Verde : « Palmarejo, dezanove, vinte e dois », ou en créole « dizanovi, vinti i dos ». Trois chiffres se disent comme un numéro de porte : « João Vaz, duzentos e catorze ».

Le code est **unique dans tout le pays à lui seul**. Le nom officiel, la commune et l'île indiqués ci-dessus sont imprimés pour information ; personne n'a à les écrire ni à les dire, et le décodeur ne s'en sert jamais pour choisir entre des lieux. À chaque code de maison correspond, de façon biunivoque, une **forme machine** : `PR-0973-1922-6` donne la clé de la commune, l'indice national du nom, le numéro et un chiffre de contrôle. Personne ne voit jamais le chiffre de contrôle : les plaques et les formulaires portent le nom et le numéro, et la forme machine n'apparaît que dans les systèmes et dans le code QR d'une plaque.

## L'adresse officielle d'abord : le masque de couverture

Là où une commune a attribué un nom de rue et un numéro de porte, le registre affiche d'abord cette adresse, telle que la commune l'écrit, par exemple `Rua Barragem de Figueira Gorda 142, Praia`, avec le code de maison `Cidadela 10 88` à côté. Chaque bâtiment a un code de maison, que sa rue soit numérotée ou non, si bien qu'un livreur, une famille ou un logiciel n'a besoin que d'un seul type de code dans tout le pays. Chaque lote est marqué **officiel** (rue et numéro connus), **officiel en attente** (dans un secteur présumé numéroté dont le registre n'a pas été communiqué : le Platô et le centre de Mindelo) ou ni l'un ni l'autre. Le tableau 2 donne les effectifs.

| Couverture | Lotes | Part |
|:----------------------------|------:|------:|
| Officiel : rue et numéro municipaux connus | 96 | 0,05 % |
| Officiel en attente : Platô et centre de Mindelo | 1 299 | 0,74 % |
| Sans adresse officielle | 174 235 | 99,21 % |
| **Tous les lotes, chacun avec un code de maison** | **175 630** | **100 %** |

: Couverture des adresses officielles dans le registre.

Lorsqu'une commune numérotera de nouvelles rues, ces adresses s'afficheront en premier. Le code de maison reste valable et mène à la même porte, et son numéro n'est jamais donné à quelqu'un d'autre.

## Les zones

Chaque lote $\ell$ est rattaché à la zone candidate la plus proche dans sa propre commune $m(\ell)$ :

$$
z(\ell) = \operatorname*{arg\,min}_{z \in Z(m(\ell))} d(\ell, z),
\tag{1}
$$

où $Z(m)$ est l'ensemble des candidates de la commune $m$ et $d$ la distance orthodromique entre le point de numérotation du lote et le point de la candidate. Une candidate de moins de 15 lotes est fusionnée avec ses voisines, sauf s'il s'agit d'une povoação isolée à plus de 1,5 km de toute autre :

$$
\text{fusion}(z) \iff L(z) < 15 \;\wedge\; \min_{z' \neq z} d(z, z') \le 1500\ \text{m},
\tag{2}
$$

où $L(z)$ est le nombre de lotes rattachés à $z$. Les équations (1) et (2) s'appliquent de façon répétée jusqu'à ce qu'aucune candidate ne fusionne. En ville, les mots de lieu sont les quartiers : à Praia, on dit Achada Santo António, Palmarejo ou Safende, et non « Praia » ; Praia compte 64 zones. Une zone est une liste de lotes figée à l'émission, non une limite tracée au sol ; un quartier renommé ou contesté ne modifie donc jamais un code.

## Les noms de plaque

Les noms de la carte sont souvent trop longs pour être dits : 632 des 1 778 noms officiels de zones dépassent douze caractères, comme *Entre Chã de Alecrim e Madeiralzinho* ou *Casa Para Todos-Ribeira de Julião*. Chaque zone a donc un **nom officiel**, imprimé en petits caractères et accepté lorsqu'on le saisit, et un **nom de plaque**, qui est le nom figurant dans le code. Un nom de plaque $s$ est admissible lorsque

$$
\operatorname{tient}(s) \iff |\mathrm{NFC}(s)| \le 12 \;\wedge\; \bigl|\operatorname{mots}(s) \setminus \{\text{de}, \text{da}, \text{do}, \dots\}\bigr| \le 2,
\tag{3}
$$

où $|\mathrm{NFC}(s)|$ compte les caractères après composition canonique Unicode (une lettre accentuée compte une fois) et où les mots de liaison *de, da, do, das, dos, d', di, du, e* ne comptent pas. Le nom de plaque découle d'une seule règle écrite, appliquée dans l'ordre : une forme courte d'usage attesté l'emporte (`ASA`, `AGF`) ; on retire les mots génériques, le texte entre parenthèses et les secondes graphies (*Lote*, *Bairro*, *Zona*, *Casa Para Todos*) ; *Santo*, *Santa* et *São* peuvent s'abréger devant un nom ; sinon, on garde la suite de mots entiers la plus distinctive qui tienne, de préférence la partie spécifique du nom (*Lote Achada São Filipe* donne `São Filipe`, *Casa Para Todos-Ribeira de Julião* donne `Julião`). Un mot n'est jamais coupé. Lorsque le choix n'est pas évident, la zone est signalée à sa Câmara Municipal avec jusqu'à trois candidats, et le premier est utilisé à titre provisoire. C'est le cas lorsque deux mots forment ensemble le nom (*Figueira Gorda*), lorsque le raccourcissement supprimerait un qualificatif (*Calheta de Baixo*, *Calheta de Cima*), lorsque le résultat coïnciderait avec une ville ou une île ailleurs, ou lorsqu'aucune suite de mots ne tient. Sur les 1 778 zones, 1 146 noms tiennent tels quels, 326 sont raccourcis automatiquement et 306 sont signalés ; 118 de ces derniers n'ont encore aucune forme qui tienne, comme *Monte Vermelho*. Le choix de la Câmara change le nom une seule fois, jamais le numéro.

Deux noms sont un même nom lorsque leurs clés coïncident :

$$
\begin{aligned}
\operatorname{clé}(s) = \bigl(&\operatorname{sans\_articles} \circ \operatorname{dév\_abrév} \circ \operatorname{alupec} \\
&\circ \operatorname{séparer} \circ \operatorname{sans\_accents} \circ \operatorname{minuscules}\bigr)(s).
\end{aligned}
\tag{4}
$$

Le tableau 3 énumère les étapes.

| Étape | Règle | Exemple |
|:-----|:--------------|:--------|
| lettres | NFKD, accents retirés, minuscules | Platô → plato |
| séparer | apostrophes, points, traits d'union, barres et virgules deviennent des espaces | Lém-Ferreira → lem ferreira |
| ALUPEC | tch, tx → ch ; dj → j ; k → c devant a, o, u ; k → qu devant e, i | Tchada → chada |
| abréviations | sto → santo, sta → santa, s → são, n, na → nossa | Sto Antão → santo antao |
| articles | de, da, do, das, dos, d, o, a, os, as supprimés | Chã de Baixo → cha baixo |

: Normalisation des noms en clés, équation (4).

Chaque nom officiel est un alias de son nom de plaque, et les alias couvrent aussi Platô/Plateau ainsi que les formes portugaises et créoles que la commission de toponymie conserve côte à côte [@ungegn2023].

## Séries nationales par nom et blocs

Les noms courts se répètent : 254 noms de plaque sont portés par deux zones ou plus, soit 672 zones et 64 873 codes. *Figueira* désigne dix zones, *Achadinha* et *Cutelo* huit chacune. Un code qui aurait besoin de la commune pour se distinguer échouerait chaque fois que la commune est omise, c'est-à-dire presque toujours. Chaque nom reçoit donc **une série numérique nationale**, répartie entre ses zones en blocs figés à l'émission.

Les numéros sont attribués par unités entières de taille $s_d$ : $s_3 = s_4 = 100$ et $s_5 = 1000$. Une zone de $L(z)$ lotes à la première émission a besoin de

$$
u(z) = \max\!\left(1, \left\lceil \frac{3\,L(z)}{s_d} \right\rceil\right)
\tag{5}
$$

unités, afin que son bloc offre trois numéros par lote. Un nom de zones $z_1, \dots, z_k$ prend la plus petite longueur dont la série accueille toutes ses zones et deux unités de réserve :

$$
d^{*} = \min \left\{ d \in \{3, 4, 5\} \;:\; \sum_{i=1}^{k} u(z_i) + 2 \le U_d \right\},
\qquad U_3 = 9,\; U_4 = U_5 = 90,
\tag{6}
$$

où $U_d$ est le nombre d'unités d'une série à $d$ chiffres (100–999 compte neuf unités de 100 ; 1000–9999 et 10000–99999 en comptent 90 chacune). Une zone seule à porter son nom a donc trois chiffres jusqu'à 233 lotes ($\lceil 3 \cdot 233/100 \rceil + 2 = 9$) et quatre jusqu'à 2 933. Les blocs sont attribués depuis le bas de la série, dans l'ordre de l'indice de la commune puis de celui de la zone.

*Exemple.* Le nom *Palmarejo* (indice national 973) a deux zones à Praia : Palmarejo, avec 935 lotes à la première émission, et Palmarejo Grande, avec 537. D'après l'équation (5), $u = \lceil 28{,}05 \rceil = 29$ et $u = \lceil 16{,}11 \rceil = 17$. Comme $29 + 17 + 2 = 48 > 9$, trois chiffres ne suffisent pas ; comme $48 \le 90$, le nom prend quatre chiffres. Palmarejo reçoit le bloc 1000–3899 et Palmarejo Grande le bloc 3900–5599 ; 5600–9999 reste libre.

La figure 3 montre la distribution de la taille des zones et la figure 4 les blocs de trois noms répétés. *Fazenda* est partagé par sept zones dans cinq communes et occupe 1000–3499 ; Achada Fazenda, à Santa Cruz, détient 1000–1999 et Fazenda, à Tarrafal, 3300–3499 : `Fazenda 34 48` ne peut donc se trouver qu'à Tarrafal. La plus grande série partagée est celle de *Bela Vista* (Praia, Sal et São Vicente ; 1 562 codes), qui utilise 4 900 de ses 9 000 numéros. Aucun nom n'a besoin de cinq chiffres.

![Zones selon le nombre de codes de maison, en classes logarithmiques. Clair : zones dont la série a trois chiffres ; foncé : quatre. Les tirets marquent la plus grande zone tenant seule en trois chiffres (233 lotes) et en quatre (2 933). La zone médiane compte 50 codes ; la plus grande, Achada Santo António (`ASA`), 2 855. Données : `registry/`.](figures/zone-sizes-fr.svg){width=95%}

![Trois séries nationales de noms réparties entre les blocs de leurs zones (nom officiel, commune et codes émis). La réserve en gris reste libre pour de nouvelles zones du même nom et pour la croissance. Données : `registry/names.csv`.](figures/ranges.svg){width=100%}

Lorsque le bloc d'une zone est plein, elle prend l'unité libre la plus basse de son nom ; lorsque la série d'un nom est pleine, le nom passe à la longueur suivante. Une nouvelle zone portant un nom existant, comme une nouvelle Achadinha, reçoit un nouveau bloc pris sur les unités de réserve. Aucun numéro émis ne change.

## La numérotation dans une zone

Les lotes d'une zone sont ordonnés le long d'une courbe de Hilbert [@hilbert1891], qui, parmi les courbes de remplissage, préserve bien la proximité spatiale [@moon2001] : des lotes voisins sur le terrain reçoivent en général des numéros voisins (figure 5). La boîte englobante de chaque zone, élargie de 300 m, est projetée sur une grille de $2^{16} \times 2^{16}$. Un lote dont le point de numérotation (le portail s'il est connu, sinon la construction principale) a pour longitude $\lambda$ et pour latitude $\varphi$ tombe dans la cellule

$$
x = \operatorname{round}\!\left( \frac{\lambda - \lambda_W}{\lambda_E - \lambda_W} \,(2^{16} - 1) \right),
\qquad
y = \operatorname{round}\!\left( \frac{\varphi - \varphi_S}{\varphi_N - \varphi_S} \,(2^{16} - 1) \right),
\tag{7}
$$

où $\lambda_W, \lambda_E, \varphi_S, \varphi_N$ sont les bords de la boîte, et reçoit l'indice de Hilbert $h = H_{16}(x, y)$, calculé bit par bit depuis le niveau le plus significatif.

![La courbe de Hilbert d'ordre 3 sur une grille de 8 × 8, dans l'ordre donné par la fonction `hilbert_index` du moteur de référence. Le modèle utilise la même courbe à l'ordre 16 ; à Palmarejo, une cellule mesure environ 2,4 cm sur 3 cm.](figures/hilbert.svg){width=45%}

À la première émission, les $n$ lotes d'une zone de bloc $[\,a, b\,]$ sont triés par indice de Hilbert $h$, les ex aequo étant départagés par l'identifiant de la construction principale, et reçoivent des numéros régulièrement répartis :

$$
N_k = a + \left\lfloor \left(k + \tfrac{1}{2}\right) \frac{b - a + 1}{n} \right\rfloor,
\qquad k = 0, 1, \dots, n - 1.
\tag{8}
$$

*Exemple.* La boîte de Palmarejo s'étend de $\lambda = -23{,}53404$ à $-23{,}51928$ et de $\varphi = 14{,}90097$ à $14{,}91902$. Le point de numérotation d'un immeuble d'habitation situé en $\varphi = 14{,}9113759$, $\lambda = -23{,}5282136$ tombe, d'après l'équation (7), dans la cellule $(x, y) = (25\,869,\ 37\,781)$, d'indice de Hilbert $h = 2\,099\,014\,114$. Dans cet ordre, 297 des 935 lotes de Palmarejo de la première émission le précèdent ; donc $k = 297$, et l'équation (8) donne

$$
N_{297} = 1000 + \left\lfloor 297{,}5 \cdot \frac{2900}{935} \right\rfloor = 1000 + \lfloor 922{,}73 \rfloor = 1922 .
$$

Le code de maison de l'immeuble est `Palmarejo 19 22`. La figure 6 montre la zone entière. Les trois lotes situés dans des rues à numérotation officielle ont été ajoutés ensuite, numérotés entre leurs voisins par l'équation (9), sans modifier aucun autre code.

![Les 938 codes de maison de la zone Palmarejo (Praia) à leurs points de numérotation, colorés selon le numéro et reliés dans l'ordre des numéros. Des bâtiments voisins reçoivent des numéros voisins ; entre eux subsistent des écarts d'environ deux numéros pour les bâtiments à venir. Cercle : `Palmarejo 19 22`. Triangles : les trois lotes des rues à numérotation officielle. Données : `registry/`.](figures/palmarejo-fr.svg){width=78%}

## Les codes des nouveaux bâtiments

Un bâtiment qui ne figure pas encore sur la carte, ou une seconde porte, reçoit un numéro compris entre ses voisins de Hilbert. Soient $p$ et $q$ les numéros des lotes émis qui précèdent et suivent immédiatement le nouveau point dans l'ordre de Hilbert, au sein du bloc de la zone ($a - 1$ et $b + 1$ aux extrémités). Alors

$$
N_{\text{nouveau}} =
\begin{cases}
\left\lfloor \dfrac{p + q}{2} \right\rfloor & \text{si } q - p > 1 \text{ et s'il est libre},\\[1ex]
\text{le numéro libre le plus proche} & \text{sinon},\\[0.5ex]
\text{un numéro dans un nouveau bloc du nom} & \text{si les blocs sont pleins.}
\end{cases}
\tag{9}
$$

*Exemple tiré du registre.* Le 19 octobre 2026, un bâtiment de Cruz de Joana, à São Vicente, a été ajouté à la demande. Ses voisins de Hilbert dans le bloc 100–699 de la zone portaient les numéros 219 et 222 ; l'équation (9) a donc donné $\lfloor 441/2 \rfloor = 220$ et le code `Joana 220` (`SV-0654-220-9`). Le moteur de référence retrouve ce numéro à partir du registre publié. Un nouveau numéro ne peut jamais tomber dans le bloc d'une autre zone.

## Le décodage sans contexte

Un code dit ou saisi se décode en ramenant le nom à sa clé, en trouvant les blocs du nom et en retenant l'unique bloc qui contient le numéro :

$$
\operatorname{décoder}(P, N) = \bigl\{\, z \;:\; \operatorname{clé}(P) \in \operatorname{clés}(z),\; a(z) \le N \le b(z) \,\bigr\},
\tag{10}
$$

où $\operatorname{clés}(z)$ contient la clé du nom de plaque de la zone et celles de ses alias, et où $[a(z), b(z)]$ parcourt les blocs de la zone. Les blocs d'un même nom étant disjoints, l'ensemble a au plus un élément. `palmarejo 1922` se trouve dans 1000–3899 et désigne Palmarejo ; `palmarejo 4500` désignerait Palmarejo Grande ; `fazenda 5229` est refusé, car aucune zone de ce nom ne détient 5229.

## Le chiffre de contrôle

Le chiffre de contrôle est calculé par l'algorithme de Damm [@damm2004; @damm2007] sur les quatre chiffres de l'indice national du nom suivis du numéro. Soit $T$ un quasi-groupe totalement antisymétrique d'ordre 10 et $\delta_1, \dots, \delta_r$ les chiffres :

$$
c_0 = 0, \qquad c_j = T[c_{j-1}][\delta_j] \quad (j = 1, \dots, r), \qquad \text{contrôle} = c_r ,
\tag{11}
$$

et une chaîne suivie de son chiffre de contrôle est valide lorsque la récurrence se termine sur 0. La table employée est

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

*Exemple.* Pour `Palmarejo 19 22`, les chiffres sont `0973 1922`. La valeur $c_j$ après chaque chiffre vaut 0, 2, 3, 0, 3, 6, 6, 6 ; le chiffre de contrôle est 6 et la forme machine est `PR-0973-1922-6`.

Chaque ligne et chaque colonne de $T$ est une permutation, si bien que toute erreur sur un chiffre modifie le résultat ; l'antisymétrie totale garantit qu'il en va de même pour toute inversion de deux chiffres adjacents différents [@damm2004]. Contrairement au schéma diédral de Verhoeff [@verhoeff1969], celui de Damm n'exige qu'une table et aucune permutation. La zone ne figure pas parmi les chiffres : au sein d'un nom, chaque numéro a une seule zone propriétaire, de sorte qu'une erreur sur un chiffre qui tombe dans une autre zone du même nom modifie exactement un chiffre et est toujours détectée. Dans la forme machine, la clé de la commune doit en outre coïncider avec la commune de la zone propriétaire.

## La couche de points

Tout point à terre a un Plus Code [@olc], la grille retenue par les Correios pour *Morada Certa*. Avec $\varphi' = \varphi + 90$ et $\lambda' = \lambda + 180$, les cinq paires de caractères utilisent les résolutions $r_k \in \{20 ;\ 1 ;\ 0{,}05 ;\ 0{,}0025 ;\ 0{,}000125\}$ degré :

$$
\text{lat}_k = \left\lfloor \frac{\varphi'}{r_k} \right\rfloor \bmod 20, \qquad
\text{lng}_k = \left\lfloor \frac{\lambda'}{r_k} \right\rfloor \bmod 20, \qquad k = 1, \dots, 5,
\tag{13}
$$

et un onzième caractère divise la dernière cellule en cinq lignes et quatre colonnes :

$$
g = 4 \left( \left\lfloor \frac{5\varphi'}{r_5} \right\rfloor \bmod 5 \right) + \left( \left\lfloor \frac{4\lambda'}{r_5} \right\rfloor \bmod 4 \right),
\tag{14}
$$

chaque valeur s'écrivant avec l'alphabet `23456789CFGHJMPQRVWX`. Pour le point de `Palmarejo 19 22`, les paires sont (5, 7), (4, 16), (18, 9), (4, 8), (11, 14) et $g = 1$, ce qui donne `796RWF6C+HP3`, soit `WF6C+HP3 Praia` en forme courte. Le modèle propose onze caractères (environ 3 m) en ville et aux portails et dix (environ 14 m) à la campagne, uniquement à terre. La figure 7 montre la grille au Platô.

![La couche de points autour du bâtiment des Correios, au Platô (`Platô 11 32`, en rouge). Emprises du registre sous la grille des Plus Codes à dix caractères (13,45 m × 13,82 m à cette latitude) ; la cellule du bâtiment est divisée en 4 × 5 cellules du onzième caractère. Un code de point désigne un point ; le code de maison désigne le bâtiment. Données : `registry/structures/`.](figures/spot-fr.svg){width=80%}

## Le lote et le profil du bâtiment

L'unité adressable est le **lote** : une parcelle ou une concession, avec ses constructions et son entrée. L'habitat cap-verdien a ses propres formes, et les règles de regroupement les suivent. En ville, les maisons s'alignent mur contre mur le long des rues et à flanc de colline ; des bâtiments contigus n'y sont donc jamais fusionnés. À la campagne, la maison s'accompagne souvent d'une cuisine extérieure, de latrines, d'une citerne ou d'un *curral*, qui rejoignent le lote de la maison en tant que constructions. Les sites clos, comme les écoles, les hôpitaux et les casernes, forment chacun un lote, et les complexes hôteliers de Sal et de Boa Vista sont des ensembles dont on atteint les unités par le portail de l'ensemble. Dans le registre, 12 604 lotes comptent deux constructions ou plus et réunissent 15,2 % des emprises ; 453 lotes sont des sites clos, dont 16 seulement (3,5 %) ont un portail cartographié. Le code mène à l'entrée principale : le portail s'il existe, sinon la porte confirmée.

Chaque construction porte un profil : une classe d'usage tirée d'une taxonomie établie pour le Cabo Verde (moradia, prédio de habitação, habitação precária, misto, loja, mercado, armazém, restauração, escritório, hotel, pensão, governo, educação, saúde, religioso, indústria, agrícola, anexo, etc.) ; la surface et le périmètre de l'emprise ; la hauteur et le nombre d'étages lorsqu'on les connaît ; un état (en usage, *inachevé mais habité*, en construction, ruine, abandonné, démoli) ; et la source et le degré de confiance de chaque attribut. L'état est tenu à part de l'usage, car une maison inachevée reste un logement. La classe est fixée par la première règle applicable, avec sa confiance : une étiquette d'usage OpenStreetMap (0,9) ; le type de bâtiment OpenStreetMap (0,3–0,95) ; un lieu cartographié dans l'emprise (0,55–0,8) ; le rôle de la construction dans le lote (0,55) ; la taille et le contexte insulaire (0,35–0,5) ; la loi *a priori* du recensement selon laquelle la plupart des bâtiments sont des logements (0,5–0,6) ; et les corrections des habitants, des livreurs et des communes, qui priment sur toutes les autres (0,9–0,99).

## La stabilité

Un code n'est jamais déplacé ni réattribué. Si un lote est divisé, le code reste à la partie qui porte la première entrée ; si deux lotes fusionnent, les deux codes restent valables ; le code d'un bâtiment démoli est retiré et jamais réémis ; les blocs d'un nom ne sont jamais renumérotés. Un code est **provisoire** tant que des habitants indépendants ne l'ont pas confirmé, et **confirmé** ensuite.

# Mise en œuvre

Quatre composants publiés mettent le modèle en œuvre : un moteur de référence et sa spécification normative, le registre, un serveur du registre et son API, et deux jeux de vecteurs de conformité qui obligent toute autre implémentation à produire les mêmes résultats.

## Moteur de référence et spécification

La spécification (`engine/SPEC.md`) est normative. Le moteur de référence (`engine/reference/cv_engine.py`) n'utilise que la bibliothèque standard de Python et met en œuvre toutes les règles de la section 4 : la lecture d'un code de maison quels que soient les espaces, la casse ou les accents, le décodage par l'équation (10), la forme machine et les équations (11)–(12), le Plus Code par les équations (13)–(14), les formes de plaque et les formes parlées en portugais et en créole, l'ordre de Hilbert et les équations (7)–(9), le plan de blocs des équations (5)–(6) et les règles du profil des bâtiments. Son autotest vérifie toutes les zones, tous les noms officiels et toutes les erreurs décrites à la section 6.4.

## Le registre

Le registre est publié par commune en CSV simple, avec la table des zones, le registre des noms, les points de numérotation et la couche des bâtiments (section 3.4). Les empreintes SHA-256 du manifeste permettent de vérifier toute copie. Le registre fait foi : le décodage n'exige que le registre des noms, tandis que l'émission d'un nouveau code exige les points de numérotation et les emprises.

## Le serveur du registre et son API

Le dépôt comprend un serveur du registre (`server/`) qu'un ministère, un opérateur postal ou un développeur peut déployer d'une seule commande (`docker compose up`). Il importe le registre dans SQLite après avoir vérifié chaque empreinte et chaque total, sert une API JSON sous `/v1` (consultation par code, recherche par toute forme écrite, code en un point, codes voisins, vérification, codes de point, zones et secteurs, listes paginées) et réexporte le registre au format publié, à l'octet près. Un déploiement ne peut émettre de codes que s'il détient des clés et a été désigné comme émetteur (section 12.3) ; il applique alors exactement les règles de la section 4, y compris les contrôles de doublon (aucun nouveau code à moins de 3 m d'une entrée existante ni à l'intérieur d'une emprise existante), les limites du contour (de 12 m² à 2 ha) et l'équation (9). L'API est documentée par des requêtes et des réponses réelles dans `docs/api.md` et au format OpenAPI 3.1 dans `server/openapi.yaml`.

## Conformité et parité

Deux jeux de vecteurs définissent la conformité. `engine/test-vectors.json` couvre les formes, les chiffres de contrôle, les formes parlées, les blocs, les noms de plaque, les décodages de noms répétés et les cas de croissance. `engine/test-vectors-registry.json` contient des codes réellement émis avec toutes leurs formes dérivées, les codes de toutes les zones de quatre noms répétés, des codes à adresse officielle et une insertion calculée sur une zone réelle. Une mise en œuvre dans un autre langage est conforme si elle reproduit les deux jeux. La logique d'émission du serveur a été comparée à la mise en œuvre de l'émetteur lui-même sur 107 émissions successives dans une zone, y compris le remplissage d'un bloc et l'ouverture d'un bloc d'extension, et a concordé pour chaque numéro et chaque forme.

# Évaluation

Nous mesurons le registre émis au regard des exigences de la section 4.1. Toutes les valeurs de cette section sont calculées à partir des fichiers publiés dans `registry/` et du moteur de référence, et peuvent être reproduites avec les outils du dépôt.

## Unicité et décodage

Les 1 778 zones et tous les noms officiels se décodent vers la zone attendue, et chacun des 175 630 codes se décode vers exactement un lote. Au sein de chacun des 1 360 noms, les blocs sont disjoints par construction ; d'après l'équation (10), aucun couple de codes du pays ne partage donc la même forme mémorisée.

## Longueur du code

Le tableau 4 résume les longueurs. Sur les 175 630 codes, 77 467 (44,1 %) ont trois chiffres et 98 163 (55,9 %) en ont quatre ; aucun n'en a cinq. La zone médiane compte 50 codes, le 90e centile 213 et la plus grande, Achada Santo António, 2 855 : le triple vaut 8 565, si bien que son bloc est 1000–9599.

| | Zones | Codes | Part des codes |
|:--|--:|--:|--:|
| Numéros à trois chiffres | 1 349 | 77 467 | 44,1 % |
| Numéros à quatre chiffres | 429 | 98 163 | 55,9 % |
| Numéros à cinq chiffres | 0 | 0 | 0 % |
| **Total** | **1 778** | **175 630** | **100 %** |

: Longueur des numéros dans le registre.

## Noms de plaque

Les noms de plaque ont au plus douze caractères et deux mots, sauf les 118 noms signalés en attente d'un choix municipal. Parmi les noms non signalés, les codes mémorisés les plus longs comptent 18 caractères, par exemple `Vila Miséria 25 98`.

## Détection des erreurs

L'autotest engendre des erreurs sur un chiffre à partir de 25 numéros de chaque bloc de chaque nom répété. Sur les 92 701 erreurs qui tombent dans une autre zone du même nom, les 92 701 sont refusées par le chiffre de contrôle ; 140 407 autres tombent sur des numéros qu'aucune zone ne détient. Les 22 952 formes machine altérées (chiffre erroné, chiffres inversés ou mauvaise clé de commune) sont toutes refusées. Sans chiffre de contrôle, lorsqu'un code est dit à voix haute, il reste protégé par la parcimonie. À la première émission, un bloc offre environ trois numéros par lote ; la probabilité qu'une erreur aléatoire au sein d'un bloc atteigne un code émis vaut donc environ

$$
P(\text{atteinte}) \approx \frac{L(z)}{s_d\, u(z)} \approx \frac{1}{3},
\tag{15}
$$

et le décodeur affiche toujours ce que désigne un code, avec sa commune, avant de lancer la navigation.

## Couverture

Chaque lote de la carte a un code : 175 629 émis en bloc et un émis à la demande par l'équation (9). Les 1 395 lotes dotés d'une adresse officielle ou officielle en attente portent à la fois leur adresse municipale et un code de maison (tableau 2).

## Profils des bâtiments

Le tableau 5 résume les profils inférés. La hauteur n'est connue que pour 0,3 % des emprises, par les étiquettes d'OpenStreetMap ; le champ de hauteur des données d'apprentissage automatique est une valeur de remplissage destinée au rendu, non une mesure, et n'est pas utilisé. Le recensement trouve 5,4 % de bâtiments classiques à usage entièrement non résidentiel [@ine2021] ; la carte en détecte environ 3 %, l'écart correspondant aux commerces et aux bureaux que personne n'a étiquetés.

| | Cabo Verde | Praia | Sal |
|:-----------|-------:|-------:|-------:|
| Emprises | 192 272 | 32 591 | 7 661 |
| Résidentiel | 84,1 % | 89,2 % | 61,0 % |
| Annexes | 11,1 % | 6,1 % | 7,3 % |
| Tourisme | 1,7 % | 0,1 % | 27,2 % |
| Commerce, restauration et bureaux | 0,8 % | 1,9 % | 3,1 % |
| Agricole | 1,7 % | 2,0 % | 0,3 % |
| Confiance haute / moyenne / basse | 3,6 / 73,0 / 23,5 % | 4,4 / 75,2 / 20,4 % | 8,0 / 51,8 / 40,2 % |
| Emprise médiane | 44,9 m² | 60,8 m² | 108,5 m² |

: Profils inférés des bâtiments. Confiance haute : 0,8 ou plus ; moyenne : de 0,55 à 0,8. Données : `registry/structures/`.

## Fidélité et performance du serveur

Après import du registre complet (environ six secondes sur un ordinateur portable), le serveur a renvoyé la même fiche que le service en ligne de l'émetteur pour 58 codes comparés champ par champ, dont des codes officiels, officiels en attente, émis à la demande et à plusieurs constructions, et la même réponse pour 400 points tirés au hasard. La seule différence est l'arrondi d'une coordonnée d'entrée à sept décimales (environ 1 cm) dans le format publié. Sur la même machine, le serveur a traité environ 1 200 consultations par code et 120 consultations par point par seconde.

# Solutions envisagées

Chacun des choix principaux de la section 4 a été comparé à ses alternatives, sur les mêmes données, avant l'émission des codes. Cette section consigne ces alternatives et les mesures qui ont conduit à les écarter.

## Autres formes de code

Nous avons évalué la forme retenue et six variantes à l'aune de ce que les habitants retiennent déjà (tableau 6).

| Forme | Exemple | Appréciation |
|:---------|:-------|:------------------|
| Nom de lieu court et numéro d'une série nationale par nom | `Palmarejo 19 22` | **retenue** |
| Commune et chiffres | `Praia 48 213` | Praia exigerait cinq chiffres (31 052 lotes × 3 > 9 000) ; les habitants situent leur maison par le quartier, non par la commune |
| Clé de commune et code alphanumérique | `PR R5H8-R` | aucune adresse cap-verdienne ne comporte de lettres ; en portugais, les noms des lettres riment en deux grandes familles (bê, cê, dê, gê, pê, tê, vê ; efe, ele, eme, ene, erre, esse) et se dictent mal |
| Code national purement numérique | `07 0973 1922` | ne contient aucun lieu ; une erreur peut tomber sur une vraie maison d'une autre île |
| Plus Code seul | `796RWF6C+HP3` | précis pour un point, mais comporte des lettres et un signe plus, et change tous les quelques mètres ; conservé comme couche de points |
| Zone, numéro et commune pour distinguer les noms répétés | `Achadinha 214, Paul` | pas unique à lui seul : échoue dès que la commune est omise |
| Nom officiel complet et numéro | `Lote Achada São Filipe 21 29` | trop long pour être dit d'une traite ou tenir sur une plaque |

: Formes de code envisagées.

## Le coût des séries nationales

Partager une série entre zones homonymes allonge certains codes. Le tableau 7 compare trois conceptions sur les effectifs du registre. Avec une série par zone, unique seulement accompagnée de la commune, 1 625 zones auraient trois chiffres. Une série par nom officiel en donne 1 501. Notre conception, une série par nom de plaque, en donne 1 349 : le partage fait passer à quatre chiffres 276 zones qui, seules, en auraient eu trois. C'est le prix d'un code court qui se passe de contexte. Aucune conception n'exige cinq chiffres.

| Conception | 3 chiffres | 4 chiffres |
|:--------------------|-----:|-----:|
| Une série par zone (unique seulement avec la commune) | 1 625 | 153 |
| Une série par nom officiel | 1 501 | 277 |
| **Une série par nom de plaque (retenue)** | **1 349** | **429** |

: Longueur des numéros selon trois conceptions, calculée sur les effectifs du registre.

## Le choix du chiffre de contrôle

Nous avons comparé l'algorithme de Damm à l'ISO/IEC 7064 MOD 11,10 [@iso7064] calculé sur la commune, la zone et le numéro. MOD 11,10 laisse passer environ 2 % des inversions de chiffres adjacents (par exemple 12/21, 56/65 ou 09/90) et, avec la zone parmi les chiffres, ne détectait que 90,6 % des erreurs tombant dans une autre zone du même nom. L'algorithme de Damm sur l'indice du nom et le numéro les détecte toutes (section 6.4).

## Les rues à numérotation officielle

Une option consistait à ne pas donner de code de maison aux lotes situés dans des rues qu'une commune a numérotées, afin que ces logements n'affichent que leur adresse officielle. Nous l'avons écartée : un seul type de code pour chaque logement est plus simple pour les habitants, les livreurs et les logiciels, et l'adresse officielle s'affiche de toute façon en premier (section 4.3). Les 1 395 lotes concernés ont été numérotés entre leurs voisins par l'équation (9), sans modifier aucun autre code.

# Bénéfices pour les citoyens

Pour une famille d'Achada Santo António, d'une povoação de Santo Antão ou d'une rue de maisons mitoyennes de Mindelo, un code de maison change quatre choses du quotidien.

**Être trouvé.** Aujourd'hui, un visiteur, un taxi ou un livreur est guidé par téléphone. Avec un code, l'habitant dit une courte phrase, « Palmarejo, dezanove, vinte e dois », et le visiteur est conduit à la porte ou au portail.

**Justifier de son domicile.** Banques, écoles, employeurs et services publics demandent une adresse. Seuls 96 lotes ont une rue et un numéro municipaux connus, et 1 299 autres se trouvent dans des centres historiques présumés numérotés ; les 175 630 ont tous un code de maison (tableau 2).

**Recevoir biens et services.** Les familles de la diaspora, les boutiques en ligne et les sociétés d'eau et d'électricité peuvent envoyer à un code plutôt qu'à une description, et un ménage peut demander un raccordement, un relevé de compteur ou une réparation à la bonne porte.

**D'une île à l'autre.** Un code fonctionne de la même manière à Praia, à Mindelo, à Espargos et à Nova Sintra. Un colis envoyé de São Vicente vers un village de Fogo porte un seul code qui désigne le village et le bâtiment, sans croquis.

**Obtenir son code ne demande aucun effort.** Chaque bâtiment de la carte a son code depuis le 20 octobre 2026, et rien n'est demandé au ménage (tableau 8). L'obtention est gratuite, n'exige aucun document et n'enregistre aucune donnée personnelle. Un code n'est pas un titre de propriété.

| Situation | Étapes |
|:--|:--|
| Logement enregistré dans l'application N-Ways | aucune : le code s'affiche sur l'écran d'accueil |
| Devant son portail | une : confirmer « É a minha casa? » |
| Partager son code | une touche : un lien avec le code en toutes lettres |
| Plaque ou autocollant sur le portail | aucune : le code et un code QR qui ouvre la navigation |
| Nouveau bâtiment | « Ajouter mon logement » : portail, contour, description ; code par l'équation (9) |

: Comment les habitants obtiennent leur code.

**Qui en bénéficie le plus.** Ceux qui ont le moins aujourd'hui : les familles des rues pentues et sans nom des quartiers récents de Praia, les ménages qui vivent dans des maisons encore inachevées (27,7 % des bâtiments en 2021 [@ine2021]) et les povoações éloignées de tout point de repère.

**Portée estimée.** Si tous les ménages du recensement de 2021 utilisaient leur code, 145 952 ménages disposeraient d'une adresse qu'ils peuvent dire ; 99,2 % des lotes n'ont aucune autre adresse à la porte (tableau 2). La mémorisation est l'hypothèse décisive. Nous la mesurerons (section 13) ; si elle n'était que de 50 % après un mois, au lieu des 80 % visés, la portée serait d'environ 73 000 ménages au lieu de 117 000.

# Logistique, commerce et tourisme

Au Cabo Verde, la livraison passe par le téléphone et traverse la mer. Pour une entreprise de logistique, la forme machine est une clé stable du lote du client, que l'on peut conserver, dédoublonner et rapprocher des livraisons passées ; le code mène au portail ou à la porte, si bien que les tournées se planifient avant le départ du livreur ; un code saisi est vérifié immédiatement ; chaque lote porte son code postal des Correios, de sorte que le courrier continue d'être trié vers le bon bureau ; enfin, le registre et le moteur sont ouverts, et tout transporteur, commerçant, banque ou prestataire de paiement peut résoudre les codes dans ses propres systèmes, hors ligne et sans frais.

**Tourisme.** À Sal et à Boa Vista, qui ont reçu 82,6 % des 1 177 467 clients hôteliers de 2024 [@forbes2025], hôtels et appartements loués dépendent de chauffeurs capables de les trouver. Un complexe hôtelier est un ensemble : l'itinéraire mène à son portail, puis à chaque unité. Un client peut donner au chauffeur un code au lieu d'une description.

**Petits commerces.** Une boutique ou un atelier ouvert dans la façade d'une maison est une construction à part entière, avec son entrée, désignée par le code du lote et un suffixe de construction (par exemple `.2`) ; les clients la trouvent sans explications.

**Économies estimées.** Soit $f_0$ la part des premières tentatives de livraison qui échouent, $\phi$ la part de ces échecs qu'un code précis supprime et $c$ le coût d'une tentative. L'économie pour 1 000 livraisons vaut

$$
S = 1000 \, f_0 \, \phi \, c .
\tag{16}
$$

Les estimations publiées par le secteur pour l'Afrique situent le taux de réussite à la première tentative à 60 % seulement ($f_0$ jusqu'à 0,40) et le coût d'une tentative à environ 2,70 dollars [@odeloye2023]. Faute de mesure cap-verdienne, nous donnons un intervalle (tableau 9). Avec les valeurs centrales $f_0 = 0{,}20$ et $\phi = 0{,}5$, $S \approx 270$ dollars pour 1 000 livraisons. Entre les îles, une livraison manquée coûte davantage, car le colis attend le bateau ou le vol suivant.

| $f_0$ | $\phi = 0{,}25$ | $\phi = 0{,}50$ | $\phi = 0{,}75$ |
|--:|--:|--:|--:|
| 0,10 | 68 USD | 135 USD | 203 USD |
| 0,20 | 135 USD | 270 USD | 405 USD |
| 0,40 | 270 USD | 540 USD | 810 USD |

: Économies pour 1 000 livraisons selon l'équation (16), avec $c$ = 2,70 USD.

# Services de secours

Une ambulance, les pompiers ou la police affrontent le problème du livreur avec un enjeu plus grave, dans des rues pentues, étroites et souvent sans nom. Une étude qualitative des services médicaux d'urgence de Kigali a montré que les équipes et les régulateurs perdaient du temps à localiser les patients, parce qu'ils dépendaient de la connaissance locale et devaient multiplier les appels pour établir le lieu [@hunt2024]. Nous ne connaissons aucune mesure publiée pour le Cabo Verde, ce qui est en soi une raison d'en entreprendre une.

**Comment le code aide le régulateur.** L'appelant dit une phrase : « Fazenda, trinta e quatro, quarenta e oito ». Le régulateur la saisit et le registre renvoie un seul lote : Fazenda à Tarrafal, et non l'une des six autres Fazenda, car seul le bloc de Tarrafal contient 34 48 (figure 4). Le régulateur relit ce que désigne le code, avec sa commune, avant le départ de l'équipe. Le code mène à l'entrée du lote et à son Plus Code, que comprend tout système de régulation lisant les Plus Codes. Le moteur et le registre fonctionnent sans réseau.

**Effet estimé.** Larsen et ses collègues ont modélisé la survie après un arrêt cardiaque extrahospitalier comme 67 %, moins 2,3 points par minute avant la réanimation cardio-pulmonaire, 1,1 point par minute avant la défibrillation et 2,1 points par minute avant la réanimation avancée [@larsen1993]. Lorsqu'une même équipe assure les trois, un retard de $\Delta t$ minutes pour trouver la porte réduit la survie de

$$
\Delta S = (2{,}3 + 1{,}1 + 2{,}1)\,\Delta t = 5{,}5\,\Delta t \ \text{points de pourcentage}.
\tag{17}
$$

Gagner une à trois minutes correspond à 5,5 à 16,5 points. Le modèle a été ajusté dans le comté de King, dans l'État de Washington ; ces valeurs indiquent donc un ordre de grandeur pour le Cabo Verde, non une prévision, mais le sens de l'effet ne fait pas de doute.

**Planifier le réseau.** Sur la carte de N-Ways d'octobre 2026, 72 % d'un échantillon de 20 000 lotes se trouvent à moins de 5 km à vol d'oiseau d'un établissement de santé cartographié, et 41 % à moins de 5 km d'un poste de police cartographié (section 11).

# Coordination et planification publiques

Un code de maison est une clé commune. Lorsque ministères, Câmaras Municipais, sociétés de services publics et institut de statistique désignent un lote par le même code, leurs fichiers peuvent être rapprochés sans comparer des noms et des descriptions. La Banque mondiale y voit l'un des principaux bénéfices pour l'administration locale : un répertoire d'adresses recense les locaux de façon plus complète que le rôle fiscal et montre qui en est absent [@farvacque2005]. Chaque code porte le code postal des Correios, l'adresse municipale lorsqu'elle existe et, dans les îles cadastrées, le NIP lorsqu'il est connu ; chaque institution conserve ainsi ses propres fichiers tout en s'accordant sur le lote.

**Planifier sur des effectifs réels.** Le registre dénombre les lotes par île, commune, zone, classe et état des bâtiments, y compris l'état *inachevé mais habité*, et chaque effectif peut être recalculé à partir des fichiers ouverts. Praia compte à elle seule 31 052 lotes répartis en 64 zones.

**Accès aux services.** Le tableau 10 donne les distances à vol d'oiseau d'un échantillon de 20 000 lotes à l'établissement cartographié le plus proche de chaque type. Ces valeurs décrivent la carte et non le terrain : les établissements absents de la carte allongent les distances apparentes. Un ministère peut remplacer la liste des établissements par la sienne et recalculer le tableau en quelques minutes.

| Établissement | À moins de 2 km | À moins de 5 km | Distance médiane |
|:----------------|-----:|-----:|-----:|
| Établissement de santé (hôpital, centre de santé, poste de santé) | 45,1 % | 71,6 % | 2,53 km |
| École | 58,8 % | 83,8 % | 1,33 km |
| Poste de police | 28,7 % | 41,0 % | 7,83 km |
| Pharmacie | 35,6 % | 56,5 % | 4,02 km |

: Distance à vol d'oiseau jusqu'à l'établissement cartographié le plus proche ; carte de N-Ways, octobre 2026, échantillon de 20 000 lotes.

**Politique du logement.** Les profils des bâtiments conservent pour chaque lote la distinction du recensement entre état et usage et se mettent à jour à mesure que les habitants les confirment ; la politique du logement peut ainsi suivre l'achèvement des maisons étage par étage.

**Coût évité estimé.** Un programme classique de numérotation des portes pour les mêmes lotes, au coût moyen de 5,7 dollars par porte relevé par la Banque mondiale [@farvacque2005], coûterait

$$
C = N\,c = 175\,630 \times 5{,}7\ \text{USD} \approx 1{,}0 \text{ million de USD}
\tag{18}
$$

aux prix de 2005, hors inflation et hors coût d'un travail réparti sur neuf îles. Avec le coût par porte observé dans une seule ville de la même étude, 7,6 dollars, le montant atteint 1,33 million. La signalisation des rues et la numérotation municipale gardent toute leur valeur ; les codes de maison ne les remplacent pas, mais ils donnent immédiatement à chaque bâtiment une référence utilisable, et les numéros officiels, à mesure qu'ils sont attribués, s'affichent en premier.

# Vie privée, sécurité et gouvernance

Un registre d'adresses décrit des lieux, mais ce sont des personnes qui l'utilisent, et certains usages comportent des risques. Cette section expose ce que le registre contient sur les personnes qui vivent à une adresse, comment le modèle limite le tort qu'un code pourrait causer et comment l'émission des codes est gouvernée.

## Protection des données

Les codes décrivent des lieux, jamais des personnes. La loi cap-verdienne sur la protection des données, la loi n° 133/V/2001 modifiée et republiée par la loi n° 121/IX/2021, s'applique aux services fournis depuis l'étranger à des personnes se trouvant au Cabo Verde, impose la notification à la Comissão Nacional de Proteção de Dados avant tout traitement automatisé et fixe à 72 heures le délai de notification des violations [@lei121_2021]. Le registre des codes, des lotes et des profils de bâtiments ne contient aucune donnée personnelle. Ni le nom des habitants ni la composition des ménages ne sont jamais conservés. Un ménage peut garder sa porte privée ; le code mène alors au portail ou à la rue, et les noms des commerces n'apparaissent que si leurs propriétaires les publient.

## Sécurité

Le registre publie ce que l'on voit depuis la rue : emprises, classes d'usage et entrées. Il n'enregistre ni occupants, ni intérieurs, ni photographies de personnes ; les photographies de portail servant à la confirmation sont effacées dès que le portail est confirmé. Une correction n'est acceptée que si des habitants indépendants s'accordent, l'un d'eux étant présent sur le lote, afin qu'un compte isolé ne puisse pas déplacer le code d'une autre famille.

## Gouvernance et émetteur unique

N-WAYS LIMITED tient le modèle, le moteur et le registre dans un dépôt public [@nways2026]. Les noms de zones ne changent qu'avec l'accord de la Câmara Municipal concernée ; les codes émis ne changent jamais. Les codes doivent être émis par **un seul émetteur pour le pays** : aujourd'hui l'émetteur de N-Ways, ou tout organisme que l'État du Cabo Verde désignera. Deux émetteurs indépendants attribueraient le même numéro libre à deux bâtiments. Tout autre déploiement du serveur du registre fonctionne en lecture seule. Le modèle est conçu pour être transmis : le dépôt, le registre et leurs règles peuvent passer aux Correios de Cabo Verde, à l'INGT et à la Comissão Nacional de Toponímia, ou à un organisme qu'ils désigneront, sans modifier le moteur. Tant qu'un organisme national ne les a pas adoptées, ce sont des adresses N-Ways, et non des adresses officielles ni des codes postaux. Le tableau 11 énumère les institutions concernées.

| Institution | Rôle |
|:--|:--|
| Correios de Cabo Verde | codes postaux et Morada Certa ; premier partenaire pour la transmission |
| Les 22 Câmaras Municipais | noms des zones, noms de rues, numéros de porte, litiges locaux |
| INGT et Comissão Nacional de Toponímia | toponymie, cadastre, géodésie, infrastructure nationale de données spatiales |
| Instituto Nacional de Estatística | géographie du recensement |
| Comissão Nacional de Proteção de Dados | protection des données |

: Institutions et rôles.

# Limites et travaux futurs

**Noms des zones.** Les noms proviennent d'OpenStreetMap et de GeoNames et comprennent des graphies que les communes voudront peut-être changer ; 306 noms de plaque sont signalés aux Câmaras, dont 118 sans forme qui tienne pour l'instant. **Carte inégale.** L'imagerie fusionne les rangées de maisons mitoyennes à Mindelo et à Praia et surcompte les annexes à Fogo et dans l'intérieur de Santiago. **Hauteurs et étages** restent le plus souvent inconnus. **Les classes de bâtiments** sont des inférences, dont un quart environ de faible confiance, et les bâtiments non résidentiels sont sous-détectés. **Les portails** ne sont presque pas cartographiés : seuls 16 lotes en ont un. **Les codes postaux** sont incomplets : les Correios ne publient aucune liste et les chiffres de São Nicolau et de Maio sont déduits. **Points à confirmer :** la poursuite de Morada Certa et le texte du décret de 2024 sur le cadastre, que nous ne connaissons que par des résumés secondaires. **Langue :** les mots des nombres en créole employés par la voix doivent être vérifiés par des locuteurs de Santiago et de São Vicente.

**Mesures prévues.** Nous mesurerons les grandeurs dont dépendent les estimations d'impact (tableau 12) et publierons les résultats dans le dépôt.

| Mesure | Méthode | Objectif |
|:--|:--|:--|
| Mémorisation de son propre code après une semaine et un mois | habitants interrogés sans l'application | au moins 80 % exacts |
| Erreurs à l'oral, à la saisie et à l'écrit | appels aux livreurs, recherche dans l'application, formulaires papier ; comparaison avec les Plus Codes des mêmes logements | moins d'erreurs qu'avec les Plus Codes |
| Réussite de la livraison à la première tentative | transporteurs partenaires, avec et sans code | au moins 20 points de plus |
| Temps de la rue à la porte | horodatages de l'application des livreurs | divisé par deux |
| Portes et portails confirmés | habitants et livreurs | 5 000 |
| Temps de localisation lors des appels d'urgence | avec un service d'ambulances ou de pompiers volontaire | mesuré, puis divisé par deux |
| Acceptation des noms normalisés | habitants de chaque île (Chã de Baixo = Chã Baixo) | acceptés |

: Mesures prévues.

# Conclusion

Nous avons décrit un modèle national d'adressage pour le Cabo Verde dans lequel chaque bâtiment porte un code formé d'un mot de lieu que les habitants emploient déjà et d'un nombre court. Les séries nationales par nom rendent le code unique sans contexte ; la numérotation ordonnée selon Hilbert et répartie garde les voisins proches et ménage la croissance ; un chiffre de contrôle de Damm dans la forme machine détecte toute erreur sur un chiffre et toute inversion adjacente. Le modèle est en vigueur pour les 175 630 lotes du pays ; 44 % des codes ont trois chiffres et aucun n'en a plus de quatre. Il coexiste avec le code postal, l'adresse municipale, le cadastre et le Plus Code sans en remplacer aucun. Le moteur, le registre et un serveur prêt à déployer sont ouverts, afin que l'État et toute institution puissent vérifier chaque code et, une fois désignés, en émettre de nouveaux selon les mêmes règles.

# Disponibilité des données et du code {-}

La spécification, le moteur de référence, les vecteurs de conformité, le registre, le serveur du registre, les outils et le présent article sont disponibles à l'adresse <https://github.com/n-ways/open-addresses-cabo-verde> [@nways2026]. Le code est sous Apache License 2.0, les données sous Open Database License 1.0 et les documents sous Creative Commons Attribution 4.0. Mention à faire figurer : « N-Ways Addressing for Cabo Verde, © N-WAYS LIMITED (nways.ng) ». Les figures sont compilées à partir de `docs/figures/*.tex` et des tables de `docs/figures/data/`, que `tools/paper_figures.py` recalcule à partir du registre ; les PDF sont produits par `sh docs/paper/build.sh`.

# Remerciements {-}

Nous remercions les contributeurs d'OpenStreetMap, dont les bâtiments, les lieux et les limites forment le socle du registre ; Google Research et Microsoft pour leurs jeux ouverts d'emprises de bâtiments, et l'Overture Maps Foundation pour leur diffusion ; GeoNames ; ainsi que l'Instituto Nacional de Estatística, les Correios de Cabo Verde, l'INGT et la Comissão Nacional de Toponímia pour les documents publics sur lesquels repose la section 2.

# Références {-}

::: {#refs}
:::
