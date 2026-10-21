---
title: "Um código de casa para cada edifício de Cabo Verde"
subtitle: "Um modelo nacional de endereçamento assente nos nomes de lugar, em séries numéricas nacionais e nas pegadas dos edifícios"
kind: "Artigo de investigação"
author:
  - "The N-Ways Addressing Group"
affiliation: "N-WAYS LIMITED · nways.ng"
date: "Outubro de 2026"
abstract-title: "Resumo"
abstract: |
  A maioria das casas de Cabo Verde não tem um endereço que um estafeta, uma equipa de ambulância ou um visitante possam usar: os códigos postais abrangem cidades inteiras, a numeração de polícia existe apenas em alguns centros históricos e as pessoas encontram-se pelo bairro, por um ponto de referência e por telefone. Apresentamos um modelo de endereçamento concebido para Cabo Verde e hoje em vigor em todo o país. Um *código de casa* é o nome curto que os moradores já usam para o seu bairro, zona ou povoação, com doze caracteres no máximo, seguido de um número de três ou quatro algarismos, como `Palmarejo 19 22`. Como os nomes de lugar se repetem, todas as zonas com o mesmo nome partilham uma única série nacional para esse nome, dividida em blocos fixos, e o código é único sem indicação de concelho nem de ilha. Os números seguem uma ordenação de Hilbert dos edifícios e deixam espaço entre vizinhos para construções futuras; um algarismo de controlo de Damm, presente apenas na forma-máquina, deteta todos os erros num algarismo e todas as trocas de algarismos adjacentes. Construído a partir de 192 272 pegadas de edifícios, o registo contém 175 630 códigos em 1 778 zonas com 1 360 nomes; 44 % dos códigos têm três algarismos e nenhum tem mais de quatro. Apresentamos todas as fórmulas com um exemplo resolvido, o motor, o registo e o servidor abertos, as alternativas rejeitadas e estimativas dos benefícios para os cidadãos, a logística, a emergência e a administração pública.

  *Palavras-chave:* endereçamento; Cabo Verde; toponímia; algarismo de controlo; curva de Hilbert; Open Location Code; pegadas de edifícios; dados abertos.
rights: "© 2026 N-WAYS LIMITED. Texto sob licença CC BY 4.0; dados sob ODbL 1.0; código sob a Apache License 2.0."
toc-title: "Índice"
lang: pt-PT
---

# Introdução

## O problema

Cabo Verde tem 491 233 residentes [@rtp2022] em nove ilhas habitadas (figura 1). Em 2016, mais de nove em cada dez estradas não tinham nome [@rinckes2016]. Os resultados preliminares do recenseamento de 2021 contaram 150 016 edifícios e 200 979 alojamentos [@ine2021], mas nem o recenseamento nem qualquer registo público atribui a esses edifícios um endereço que as pessoas possam usar. As indicações dão-se como sempre se deram: «Achada Santo António, perto da Caixa», «atrás do mercado», «liga quando chegares».

![Os 22 concelhos de Cabo Verde, sombreados pelo número de códigos de casa por quilómetro quadrado, com o número de códigos de cada ilha. A Praia tem a maior densidade, cerca de 320 códigos por km²; a Boa Vista e o Maio as menores, cerca de 8. Dados: `registry/` e os limites dos concelhos em `engine/data/`.](figures/map-pt.svg){width=88%}

O endereço pesa cada vez mais. As entregas cresceram com os pagamentos móveis e o comércio eletrónico. O turismo no Sal e na Boa Vista depende de motoristas que encontrem hotéis e apartamentos; os estabelecimentos hoteleiros receberam 1 177 467 hóspedes em 2024, 58,5 % no Sal e 24,1 % na Boa Vista [@forbes2025]. As equipas de emergência têm de encontrar casas em ruas íngremes e sem nome. As famílias enviam bens entre ilhas e da diáspora. O estudo do Banco Mundial sobre endereçamento descreve o endereço como infraestrutura básica da gestão municipal, da cobrança fiscal e da prestação de serviços [@farvacque2005], e a União Postal Universal considera um endereço para cada agregado uma condição de inclusão [@upu2012].

Cabo Verde dispõe já de quatro sistemas parciais: códigos postais de área, um código de grelha associado à identidade postal, numeração de polícia prevista na lei e um cadastro predial em quatro ilhas (secção 2). Nenhum deles dá a cada edifício um identificador que uma pessoa consiga memorizar e dizer ao telefone.

## Contribuição

Este artigo descreve um modelo nacional de endereçamento concebido para Cabo Verde e emitido para todo o país a 19 e 20 de outubro de 2026. As nossas contribuições são:

1. **Uma forma de código escolhida para ser lembrada.** Um código de casa é uma palavra de lugar que os moradores já usam, reduzida por uma regra escrita a doze caracteres e duas palavras no máximo, seguida de um número de três ou quatro algarismos (secções 4.2 e 4.5).
2. **Unicidade nacional sem contexto.** Todas as zonas que partilham um nome curto tiram os seus números de uma única série nacional para esse nome, dividida em blocos fixos, pelo que «nome e número» identificam um só lugar no país (secção 4.6).
3. **Numeração com margem de crescimento.** Dentro de cada zona, os números seguem uma ordenação de Hilbert dos edifícios e repartem-se por um bloco com o triplo do tamanho da zona; os edifícios construídos depois recebem números entre os dos vizinhos e nenhum número emitido muda (secções 4.7 e 4.8).
4. **Dados de referência ao nível do edifício.** Cada código liga-se a um *lote* (terreno ou conjunto) com a sua entrada e o perfil de cada estrutura, incluindo o estado tipicamente cabo-verdiano de «inacabado mas habitado» (secção 4.12).
5. **Uma implementação aberta e reprodutível.** Publicamos um motor de referência, vetores de conformidade, o registo completo dos 175 630 códigos e um servidor do registo que qualquer instituição pode instalar e que reproduz exatamente as decisões do emissor (secção 5).
6. **Uma avaliação e uma estimativa de impacto.** Medimos a unicidade, o comprimento, a deteção de erros e a cobertura (secção 6), registamos as alternativas rejeitadas com o seu custo medido (secção 7) e estimamos os benefícios para quatro grupos de utilizadores com pressupostos explícitos (secções 8 a 11).

## Organização do artigo

A secção 2 revê os sistemas existentes em Cabo Verde e a literatura internacional. A secção 3 descreve os dados. A secção 4 expõe o modelo, com um único exemplo, `Palmarejo 19 22`, seguido ao longo de todas as fórmulas. A secção 5 descreve a implementação e a secção 6 avalia-a. A secção 7 regista as alternativas medidas e rejeitadas. As secções 8 a 11 tratam dos benefícios para os cidadãos, para a logística, o comércio e o turismo, para os serviços de emergência e para a administração pública. A secção 12 trata da privacidade, da segurança e da governação, a secção 13 das limitações, e a secção 14 conclui.

# Enquadramento e trabalhos relacionados

Verificámos os sistemas existentes entre 17 e 21 de outubro de 2026. O registo completo, com todas as fontes e os pontos que não conseguimos confirmar, está em `docs/existing-systems.md` e `SOURCES.md`.

## Os códigos postais dos Correios de Cabo Verde

A ficha de endereçamento da UPU para Cabo Verde, datada de abril de 2014, prevê quatro algarismos à esquerda do nome da localidade, como em `7600 PRAIA`, com a ilha numa linha própria por baixo, e lê os quatro algarismos como ilha, concelho, distrito municipal e estação postal [@upu2014cv]. Os códigos que pudemos observar confirmam que o primeiro algarismo identifica a ilha (tabela 1).

| Algarismo | Ilha | Códigos observados |
|:--|:--|:--|
| 1 | Santo Antão | Ribeira Grande (lista de terceiros) |
| 2 | São Vicente | 2110 Mindelo |
| 3 | São Nicolau | nenhum observado |
| 4 | Sal | 4110 Espargos, 4111 Santa Maria |
| 5 | Boa Vista | 5110 Sal Rei |
| 6 | Maio | nenhum observado |
| 7 | Santiago | 7600–7602 Praia |
| 8 | Fogo | 8220 São Filipe |
| 9 | Brava | 9110 Nova Sintra |

: O primeiro algarismo do código postal identifica a ilha. Fontes: UPU [@upu2014cv], OpenStreetMap e Nominatim; os algarismos de São Nicolau e do Maio deduzem-se da ordem das ilhas.

Segundo uma lista de terceiros, os dois primeiros algarismos seguem o número do concelho no código geográfico nacional [@statoids]. A Praia é uma exceção (76 e não 74), e os concelhos criados em 2005 partilham os algarismos do concelho de origem, pelo que o código postal não consegue designar os 22 concelhos atuais. Os Correios não publicam lista nem pesquisa de códigos postais; o seu sítio, tal como arquivado em setembro de 2026, oferece seguimento de envios, procura de balcões e normas de distribuição, mas nenhum diretório de códigos [@correios2026]. O código postal é, portanto, um código de área, não um endereço à porta.

## A Morada Certa e os Plus Codes

Em 2016, os Correios de Cabo Verde e a Google lançaram a *Morada Certa*: os Plus Codes foram integrados no sítio dos Correios para que os moradores associassem o código da sua casa à identificação postal [@rinckes2016]. Um Plus Code é um Open Location Code, uma referência de grelha hierárquica que designa uma célula de cerca de 14 m com dez caracteres, ou de cerca de 3 m com onze [@olc]. Funciona sem rede e dispensa registo, mas não diz de que edifício ou porta se trata. Não encontrámos indícios de que a campanha continuasse ativa em 2026. Como foi esta a grelha escolhida pelos Correios, o modelo usa os Plus Codes como camada de ponto e não introduz grelha concorrente (secção 4.11).

## Toponímia e numeração de polícia

O Decreto-Lei n.º 5/2012, de 28 de fevereiro, regula a toponímia a nível nacional e municipal e criou a Comissão Nacional de Toponímia, coordenada pelo Instituto Nacional de Gestão do Território (INGT) [@ungegn2023; @res18_2014]. No relatório de 2023 ao Grupo de Peritos das Nações Unidas para os Nomes Geográficos, Cabo Verde comprometeu-se a apoiar os municípios na «implementação massiva da toponímia municipal e da numeração de polícia» e fixou a regra de que os nomes de rua não se repetem [@ungegn2023]. Os municípios são, assim, a autoridade legal do endereço à porta. No terreno, esse endereço existe nos centros históricos do Platô e do Mindelo, em alguns bairros planeados da Praia e em Santa Maria, no Sal. Não encontrámos qualquer registo municipal de endereços publicado.

## O cadastro predial e a rede geodésica

O INGT foi criado em 2014 com atribuições de ordenamento do território, geodesia, cartografia, infraestrutura nacional de dados espaciais e cadastro predial [@res18_2014]. Um regime especial regeu a operação sistemática de cadastro no Sal, na Boa Vista, em São Vicente e no Maio [@dl16_2019]. Cada prédio tem um Número de Identificação Predial (NIP). O sistema de coordenadas projetadas nacional é o EPSG:4826, *WGS 84 / Cape Verde National*, uma projeção cónica conforme de Lambert com paralelos padrão a 15° N e 16°40′ N [@epsg4826]. O cadastro estabelece a *titularidade*; o endereço serve para *encontrar*. Um código de casa nunca é um título, embora um lote possa guardar o seu NIP como referência.

## O recenseamento

O recenseamento de 2021 georreferenciou todos os edifícios. Dos 150 016 edifícios dos resultados preliminares, 27,7 % eram clássicos não concluídos, e 87,0 % dos edifícios clássicos destinavam-se exclusivamente à habitação; o número de edifícios crescera 31,3 % desde 2010, quando eram 114 297 [@ine2021]. O apuramento definitivo conta 150 206 edifícios [@rtp2022]. As áreas de enumeração não são publicadas como dados abertos. O modelo usa estes totais como valores *a priori* e como controlo, nunca como informação sobre qualquer agregado.

## Prática internacional

A norma S42 da UPU define os componentes de um endereço postal e os modelos para os apresentar [@upuS42], e a ISO 19160-1 propõe um modelo conceptual do endereçamento que distingue o endereço, os seus componentes e o objeto endereçável [@iso19160]. Ambas acolhem um endereço formado por uma localidade e um identificador dentro dela, que é a estrutura que adotamos. O Banco Mundial estudou o endereçamento em cidades africanas: numa amostra de 21 cidades, apenas 8 % das ruas tinham nome antes dos programas, e o custo médio foi de 5,7 dólares dos EUA por porta endereçada, a preços de 2005 [@farvacque2005]. O mesmo estudo adverte que o endereçamento se degrada quando os moradores não o usam, razão pela qual a memorização é o nosso primeiro critério.

## Outros sistemas de código

Os códigos de grelha, como o Open Location Code [@olc], identificam pontos e não edifícios, e contêm letras e um separador. Existem noutras partes da África Ocidental sistemas nacionais de endereço digital assentes em grelhas, como o sistema nacional de endereços digitais do Gana, lançado em 2017 [@graphic2017]. Todos partilham uma limitação: o código exprime uma posição e não uma palavra de lugar que os moradores reconheçam, pelo que é difícil de lembrar e não protege contra enganos que caiam noutra célula válida. Os códigos nacionais só numéricos não contêm lugar algum, e os alfanuméricos dependem de letras, que nenhum endereço cabo-verdiano contém e que são difíceis de ditar em português (secção 7.1). Mantemos por isso a grelha para os pontos e damos a cada edifício um código formado por uma palavra de lugar e um número curto.

# Dados e fontes

O modelo é calculado a partir de dados cartográficos abertos, verificado com as estatísticas nacionais e publicado como registo aberto. Esta secção descreve cada fonte e o conteúdo do registo.

## Pegadas de edifícios

O registo assenta nas pegadas de edifícios de que a N-Ways dispunha em outubro de 2026: 91 397 do OpenStreetMap [@osm2026] e 100 875 obtidas por aprendizagem automática, do Google Open Buildings [@sirko2021] e da Microsoft [@microsoft2023], recebidas através do tema de edifícios da Overture Maps [@overture2026] onde o OpenStreetMap não tinha nenhuma. As 192 272 pegadas do registo excedem em 28 % o número de edifícios do recenseamento, porque o mapa inclui também anexos, arrecadações, estruturas inacabadas e ruínas. O excesso não é uniforme. Na Praia, o mapa tem 32 591 pegadas para 34 663 edifícios recenseados (menos 6 %) e, em São Vicente, 18 315 para 23 976 (menos 24 %), porque as imagens fundem filas de casas geminadas. No Fogo e no interior de Santiago, as pegadas chegam a 2,7 vezes os edifícios recenseados, porque todas as dependências estão cartografadas. A figura 2 mostra as fontes por ilha.

![Pegadas de edifícios do registo, por ilha e por fonte. As pegadas obtidas por aprendizagem automática preenchem as lacunas do OpenStreetMap, sobretudo no Fogo e na Boa Vista. Dados: `registry/structures/`.](figures/sources-pt.svg){width=80%}

## Localidades e nomes

As zonas constroem-se a partir da camada de localidades da N-Ways: subúrbios, bairros, aldeias e cidades do OpenStreetMap e localidades do GeoNames que não sejam acidentes de relevo [@geonames]. Cerca de 3 800 lugares com nome dão 2 818 zonas candidatas e, depois das regras da secção 4.4, 1 778 zonas. Duas formas curtas usadas na imprensa da Praia, `ASA` para Achada Santo António e `AGF` para Achada Grande Frente, estão documentadas em [@balai2025asa; @anacao2026; @expresso2025agf].

## Valores a priori estatísticos

O perfil do edifício (secção 4.12) usa como valores *a priori* as proporções do recenseamento de 2021: 87,0 % dos edifícios clássicos destinados só à habitação e 27,7 % não concluídos [@ine2021]. As grafias em crioulo são normalizadas segundo o alfabeto unificado ALUPEC [@alupec].

## O registo

O registo (`registry/`) contém todos os códigos emitidos: um ficheiro por concelho, com 20 colunas por código (forma-máquina, código de casa, nome oficial, zona, número, algarismo de controlo, estado, emissão, entrada, Plus Code, uso, tipo de lote, número de estruturas, área de construção, código postal, cobertura, endereço oficial), a tabela das zonas e o registo nacional dos nomes, o ponto de numeração de cada lote, e o perfil e a pegada WKT de cada estrutura. Um manifesto regista as contagens e o resumo SHA-256 de cada ficheiro. Todos os códigos estão publicados; nada é retido.

# O modelo

Esta secção especifica o modelo pela ordem em que um código se constrói: os requisitos a que deve obedecer, as formas do código, a máscara de cobertura dos endereços oficiais, as zonas e os seus nomes de placa, as séries nacionais de cada nome e os seus blocos, a numeração dentro da zona e o seu crescimento, a descodificação, o dígito de controlo, a camada de ponto e o perfil do edifício. Cada regra é dada por uma equação numerada, e o código `Palmarejo 19 22` serve de exemplo resolvido.

## Requisitos

Os requisitos, por ordem de prioridade, são:

1. **Memorização e acesso sem esforço.** Os moradores têm de conseguir lembrar-se do código e obtê-lo sem esforço. Este critério vem antes da brevidade e da elegância matemática, porque um endereço que as pessoas não usam degrada-se [@farvacque2005].
2. **O endereço oficial primeiro.** Onde um município atribuiu rua e número, esse endereço aparece em primeiro lugar, tal como está escrito; o código fica ao lado. O código postal dos Correios, o NIP e o Plus Code aparecem ao lado do código e nenhum é substituído.
3. **Nível do edifício e da porta.** O código leva a um portão ou a uma porta, não a um centroide atrás de um muro.
4. **Funcionamento sem rede.** Um telemóvel sem sinal consegue mostrar, verificar e ler em voz alta os códigos.
5. **Abertura.** O método, o motor e os dados são públicos.
6. **Estabilidade.** Um código nunca se desloca, nunca é reutilizado e nunca fica mais comprido.
7. **Privacidade.** Os códigos descrevem lugares, nunca pessoas.

## O código de casa e as suas formas

Um código de casa é o nome curto de uma zona seguido de um número:

> **Palmarejo 19 22** · Praia, Santiago  
> **São Filipe 21 29** · *Lote Achada São Filipe* · Praia, Santiago  
> **Fazenda 34 48** · Tarrafal, Santiago  
> **João Vaz 214** · *Chã de João Vaz* · Paul, Santo Antão

O número tem três algarismos (100–999) ou quatro (1000–9999); o comprimento é uma propriedade do nome (secção 4.6) e nunca começa por zero. Quatro algarismos escrevem-se e dizem-se em dois pares, como os números de telefone em Cabo Verde: «Palmarejo, dezanove, vinte e dois» ou, em crioulo, «dizanovi, vinti i dos». Três algarismos dizem-se como um número de porta: «João Vaz, duzentos e catorze».

O código é **único no país inteiro por si só**. O nome oficial, o concelho e a ilha que figuram acima imprimem-se a título informativo; ninguém tem de os escrever ou dizer, e o descodificador nunca os usa para escolher entre lugares. A cada código de casa corresponde, de forma biunívoca, uma **forma-máquina**: `PR-0973-1922-6` indica a chave do concelho, o índice nacional do nome, o número e um algarismo de controlo. As pessoas nunca veem o algarismo de controlo: as placas e os formulários mostram o nome e o número, e a forma-máquina aparece apenas nos sistemas e no código QR de uma placa.

## O endereço oficial primeiro: a máscara de cobertura

Onde um município atribuiu nome de rua e número de polícia, o registo mostra esse endereço em primeiro lugar, tal como o município o escreve, por exemplo `Rua Barragem de Figueira Gorda 142, Praia`, com o código de casa `Cidadela 10 88` ao lado. Todos os edifícios têm código de casa, haja ou não numeração na rua, para que um estafeta, uma família ou um sistema informático precisem de um único tipo de código em todo o país. Cada lote é marcado como **oficial** (rua e número conhecidos), **oficial pendente** (numa área presumivelmente numerada cujo registo não foi partilhado: o Platô e o centro do Mindelo) ou nenhum dos dois. A tabela 2 dá as contagens.

| Cobertura | Lotes | Proporção |
|:----------------------------|------:|------:|
| Oficial: rua e número municipais conhecidos | 96 | 0,05 % |
| Oficial pendente: Platô e centro do Mindelo | 1 299 | 0,74 % |
| Sem endereço oficial | 174 235 | 99,21 % |
| **Todos os lotes, cada um com código de casa** | **175 630** | **100 %** |

: Cobertura dos endereços oficiais no registo.

Quando um município numerar novas ruas, esses endereços passarão a aparecer primeiro. O código de casa continua válido e leva à mesma porta, e o seu número nunca é dado a outrem.

## Zonas

Cada lote $\ell$ é atribuído à zona candidata mais próxima no seu próprio concelho $m(\ell)$:

$$
z(\ell) = \operatorname*{arg\,min}_{z \in Z(m(\ell))} d(\ell, z),
\tag{1}
$$

em que $Z(m)$ é o conjunto das candidatas do concelho $m$ e $d$ é a distância ortodrómica entre o ponto de numeração do lote e o ponto da candidata. Uma candidata com menos de 15 lotes funde-se com as vizinhas, a menos que seja uma povoação isolada a mais de 1,5 km de qualquer outra:

$$
\text{fundir}(z) \iff L(z) < 15 \;\wedge\; \min_{z' \neq z} d(z, z') \le 1500\ \text{m},
\tag{2}
$$

em que $L(z)$ é o número de lotes atribuídos a $z$. As equações (1) e (2) aplicam-se repetidamente até nenhuma candidata se fundir. Nas cidades, as palavras de lugar são os bairros: na Praia diz-se Achada Santo António, Palmarejo ou Safende, e não «Praia»; a Praia tem 64 zonas. Uma zona é uma lista de lotes fixada no momento da emissão, não um limite no terreno; por isso, um bairro rebatizado ou contestado nunca altera um código.

## Nomes de placa

Os nomes do mapa são muitas vezes compridos demais para se dizerem: 632 dos 1 778 nomes oficiais de zona têm mais de doze caracteres, como *Entre Chã de Alecrim e Madeiralzinho* ou *Casa Para Todos-Ribeira de Julião*. Cada zona tem por isso um **nome oficial**, impresso em letra pequena e aceite quando escrito, e um **nome de placa**, que é o nome no código. Um nome de placa $s$ é admissível quando

$$
\operatorname{cabe}(s) \iff |\mathrm{NFC}(s)| \le 12 \;\wedge\; \bigl|\operatorname{palavras}(s) \setminus \{\text{de}, \text{da}, \text{do}, \dots\}\bigr| \le 2,
\tag{3}
$$

em que $|\mathrm{NFC}(s)|$ conta os caracteres após a composição canónica Unicode (uma letra acentuada conta uma vez) e as palavras de ligação *de, da, do, das, dos, d', di, du, e* não contam. O nome de placa deriva de uma única regra escrita, aplicada por ordem: vence uma forma curta de uso documentado (`ASA`, `AGF`); retiram-se as palavras genéricas, o texto entre parênteses e as segundas grafias (*Lote*, *Bairro*, *Zona*, *Casa Para Todos*); *Santo*, *Santa* e *São* podem abreviar-se antes de um nome; caso contrário, guarda-se a sequência de palavras inteiras mais distintiva que caiba, de preferência a parte específica do nome (*Lote Achada São Filipe* dá `São Filipe`, *Casa Para Todos-Ribeira de Julião* dá `Julião`). Uma palavra nunca se corta. Quando a escolha não é clara, a zona é assinalada à sua Câmara Municipal com até três candidatos e usa-se provisoriamente o primeiro. Isto acontece quando duas palavras são ambas o nome (*Figueira Gorda*), quando encurtar eliminaria um qualificativo (*Calheta de Baixo*, *Calheta de Cima*), quando o resultado igualaria uma cidade ou ilha de outro lugar, ou quando nenhuma sequência de palavras cabe. Das 1 778 zonas, 1 146 nomes cabem tal como são, 326 são encurtados automaticamente e 306 estão assinalados; 118 destes ainda não têm forma que caiba, como *Monte Vermelho*. A escolha da Câmara muda o nome uma única vez e nunca o número.

Dois nomes são o mesmo nome quando as suas chaves coincidem:

$$
\begin{aligned}
\operatorname{chave}(s) = \bigl(&\operatorname{sem\_artigos} \circ \operatorname{expandir\_abrev} \circ \operatorname{alupec} \\
&\circ \operatorname{separar} \circ \operatorname{sem\_acentos} \circ \operatorname{minúsculas}\bigr)(s).
\end{aligned}
\tag{4}
$$

A tabela 3 enumera os passos.

| Passo | Regra | Exemplo |
|:-----|:--------------|:--------|
| letras | NFKD, sem acentos, minúsculas | Platô → plato |
| separar | apóstrofos, pontos, hífenes, barras e vírgulas passam a espaços | Lém-Ferreira → lem ferreira |
| ALUPEC | tch, tx → ch; dj → j; k → c antes de a, o, u; k → qu antes de e, i | Tchada → chada |
| abreviaturas | sto → santo, sta → santa, s → são, n, na → nossa | Sto Antão → santo antao |
| artigos | de, da, do, das, dos, d, o, a, os, as eliminados | Chã de Baixo → cha baixo |

: Normalização dos nomes em chaves, equação (4).

Cada nome oficial é um alias do seu nome de placa, e os aliases abrangem também Platô/Plateau e as formas portuguesas e crioulas que a comissão de toponímia mantém lado a lado [@ungegn2023].

## Séries nacionais por nome e blocos

Os nomes curtos repetem-se: 254 nomes de placa são usados por duas ou mais zonas, 672 zonas ao todo, com 64 873 códigos. *Figueira* dá nome a dez zonas, *Achadinha* e *Cutelo* a oito cada. Um código que precisasse do concelho para se distinguir falharia sempre que o concelho fosse omitido, ou seja, quase sempre. Em vez disso, cada nome tem **uma série numérica nacional**, repartida pelas suas zonas em blocos fixados no momento da emissão.

Os números atribuem-se em unidades inteiras de tamanho $s_d$: $s_3 = s_4 = 100$ e $s_5 = 1000$. Uma zona com $L(z)$ lotes na primeira emissão precisa de

$$
u(z) = \max\!\left(1, \left\lceil \frac{3\,L(z)}{s_d} \right\rceil\right)
\tag{5}
$$

unidades, para que o seu bloco tenha três números por lote. Um nome com as zonas $z_1, \dots, z_k$ toma o menor comprimento cuja série acomode todas as zonas e duas unidades de reserva:

$$
d^{*} = \min \left\{ d \in \{3, 4, 5\} \;:\; \sum_{i=1}^{k} u(z_i) + 2 \le U_d \right\},
\qquad U_3 = 9,\; U_4 = U_5 = 90,
\tag{6}
$$

em que $U_d$ é o número de unidades de uma série de $d$ algarismos (100–999 tem nove unidades de 100; 1000–9999 e 10000–99999 têm 90 unidades cada). Uma zona sozinha com o seu nome tem, portanto, três algarismos até 233 lotes ($\lceil 3 \cdot 233/100 \rceil + 2 = 9$) e quatro até 2 933. Os blocos atribuem-se a partir do início da série, pela ordem do índice do concelho e do índice da zona.

*Exemplo.* O nome *Palmarejo* (índice nacional 973) tem duas zonas na Praia: Palmarejo, com 935 lotes na primeira emissão, e Palmarejo Grande, com 537. Pela equação (5), $u = \lceil 28{,}05 \rceil = 29$ e $u = \lceil 16{,}11 \rceil = 17$. Como $29 + 17 + 2 = 48 > 9$, três algarismos não chegam; como $48 \le 90$, o nome fica com quatro. Palmarejo recebe o bloco 1000–3899 e Palmarejo Grande o bloco 3900–5599; 5600–9999 fica livre.

A figura 3 mostra a distribuição da dimensão das zonas e a figura 4 os blocos de três nomes repetidos. *Fazenda* é partilhado por sete zonas em cinco concelhos e ocupa 1000–3499; a Achada Fazenda, em Santa Cruz, tem 1000–1999 e a Fazenda do Tarrafal tem 3300–3499, pelo que `Fazenda 34 48` só pode estar no Tarrafal. A maior série partilhada é a de *Bela Vista* (Praia, Sal e São Vicente; 1 562 códigos), que usa 4 900 dos seus 9 000 números. Nenhum nome precisa de cinco algarismos.

![Zonas pelo número de códigos de casa, em classes logarítmicas. Claro: zonas cuja série tem três algarismos; escuro: quatro. As linhas tracejadas marcam a maior zona que cabe sozinha em três algarismos (233 lotes) e em quatro (2 933). A zona mediana tem 50 códigos; a maior, a Achada Santo António (`ASA`), tem 2 855. Dados: `registry/`.](figures/zone-sizes-pt.svg){width=95%}

![Três séries nacionais de nomes repartidas pelos blocos das suas zonas (nome oficial, concelho e códigos emitidos). A reserva a cinzento fica livre para novas zonas com o mesmo nome e para o crescimento. Dados: `registry/names.csv`.](figures/ranges.svg){width=100%}

Quando o bloco de uma zona se esgota, a zona toma a unidade livre mais baixa do seu nome; quando a série de um nome se esgota, o nome passa ao comprimento seguinte. Uma nova zona com um nome já existente, como uma nova Achadinha, recebe um bloco novo das unidades de reserva. Nenhum número emitido muda.

## Numeração dentro de uma zona

Os lotes de uma zona ordenam-se ao longo de uma curva de Hilbert [@hilbert1891], que, entre as curvas de preenchimento do espaço, preserva bem a proximidade espacial [@moon2001]: lotes próximos no terreno recebem em geral números próximos (figura 5). A caixa envolvente de cada zona, alargada em 300 m, é projetada numa grelha de $2^{16} \times 2^{16}$. Um lote cujo ponto de numeração (o portão, se conhecido, senão a estrutura principal) tem longitude $\lambda$ e latitude $\varphi$ cai na célula

$$
x = \operatorname{round}\!\left( \frac{\lambda - \lambda_W}{\lambda_E - \lambda_W} \,(2^{16} - 1) \right),
\qquad
y = \operatorname{round}\!\left( \frac{\varphi - \varphi_S}{\varphi_N - \varphi_S} \,(2^{16} - 1) \right),
\tag{7}
$$

em que $\lambda_W, \lambda_E, \varphi_S, \varphi_N$ são os limites da caixa, e recebe o índice de Hilbert $h = H_{16}(x, y)$, calculado bit a bit a partir do nível mais significativo.

![A curva de Hilbert de ordem 3 numa grelha de 8 × 8, pela ordem dada pela função `hilbert_index` do motor de referência. O modelo usa a mesma curva na ordem 16; no Palmarejo, uma célula mede cerca de 2,4 cm por 3 cm.](figures/hilbert.svg){width=45%}

Na primeira emissão, os $n$ lotes de uma zona com o bloco $[\,a, b\,]$ ordenam-se pelo índice de Hilbert $h$, desempatando pelo identificador da estrutura principal, e recebem números repartidos de forma regular:

$$
N_k = a + \left\lfloor \left(k + \tfrac{1}{2}\right) \frac{b - a + 1}{n} \right\rfloor,
\qquad k = 0, 1, \dots, n - 1.
\tag{8}
$$

*Exemplo.* A caixa do Palmarejo vai de $\lambda = -23{,}53404$ a $-23{,}51928$ e de $\varphi = 14{,}90097$ a $14{,}91902$. O ponto de numeração de um prédio de habitação em $\varphi = 14{,}9113759$, $\lambda = -23{,}5282136$ cai, pela equação (7), na célula $(x, y) = (25\,869,\ 37\,781)$, cujo índice de Hilbert é $h = 2\,099\,014\,114$. Nesta ordem, 297 dos 935 lotes da primeira emissão do Palmarejo vêm antes dele, logo $k = 297$, e a equação (8) dá

$$
N_{297} = 1000 + \left\lfloor 297{,}5 \cdot \frac{2900}{935} \right\rfloor = 1000 + \lfloor 922{,}73 \rfloor = 1922 .
$$

O código de casa do prédio é `Palmarejo 19 22`. A figura 6 mostra a zona inteira. Os três lotes em ruas com numeração oficial foram acrescentados depois, numerados entre os vizinhos pela equação (9), sem alterar nenhum outro código.

![Os 938 códigos de casa da zona Palmarejo (Praia) nos seus pontos de numeração, coloridos pelo número e ligados pela ordem numérica. Edifícios vizinhos recebem números vizinhos; entre eles ficam intervalos de cerca de dois números para edifícios futuros. Círculo: `Palmarejo 19 22`. Triângulos: os três lotes em ruas com numeração oficial. Dados: `registry/`.](figures/palmarejo-pt.svg){width=78%}

## Códigos para edifícios novos

Um edifício que ainda não está no mapa, ou uma segunda porta, recebe um número entre os seus vizinhos de Hilbert. Sejam $p$ e $q$ os números dos lotes emitidos imediatamente antes e depois do novo ponto, pela ordem de Hilbert, dentro do bloco da zona ($a - 1$ e $b + 1$ nas extremidades). Então

$$
N_{\text{novo}} =
\begin{cases}
\left\lfloor \dfrac{p + q}{2} \right\rfloor & \text{se } q - p > 1 \text{ e estiver livre},\\[1ex]
\text{o número livre mais próximo nos blocos} & \text{caso contrário},\\[0.5ex]
\text{um número num bloco novo do nome} & \text{se os blocos estiverem cheios.}
\end{cases}
\tag{9}
$$

*Exemplo do registo.* A 19 de outubro de 2026, um edifício em Cruz de Joana, São Vicente, foi acrescentado a pedido. Os seus vizinhos de Hilbert no bloco 100–699 da zona eram os números 219 e 222, pelo que a equação (9) deu $\lfloor 441/2 \rfloor = 220$ e o código `Joana 220` (`SV-0654-220-9`). O motor de referência reproduz este número a partir do registo publicado. Um número novo nunca pode cair no bloco de outra zona.

## Descodificação sem contexto

Um código dito ou escrito descodifica-se normalizando o nome na sua chave, encontrando os blocos do nome e tomando o único bloco que contém o número:

$$
\operatorname{descodificar}(P, N) = \bigl\{\, z \;:\; \operatorname{chave}(P) \in \operatorname{chaves}(z),\; a(z) \le N \le b(z) \,\bigr\},
\tag{10}
$$

em que $\operatorname{chaves}(z)$ contém a chave do nome de placa da zona e dos seus aliases, e $[a(z), b(z)]$ percorre os blocos da zona. Como os blocos de um nome são disjuntos, o conjunto tem no máximo um elemento. `palmarejo 1922` está em 1000–3899 e é o Palmarejo; `palmarejo 4500` seria o Palmarejo Grande; `fazenda 5229` é recusado, porque nenhuma zona desse nome tem o 5229.

## O algarismo de controlo

O algarismo de controlo calcula-se com o algoritmo de Damm [@damm2004; @damm2007] sobre os quatro algarismos do índice nacional do nome seguidos do número. Sendo $T$ um quase-grupo totalmente antissimétrico de ordem 10 e $\delta_1, \dots, \delta_r$ os algarismos,

$$
c_0 = 0, \qquad c_j = T[c_{j-1}][\delta_j] \quad (j = 1, \dots, r), \qquad \text{controlo} = c_r ,
\tag{11}
$$

e uma cadeia seguida do seu algarismo de controlo é válida quando a recorrência termina em 0. A tabela usada é

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

*Exemplo.* Para `Palmarejo 19 22`, os algarismos são `0973 1922`. O valor $c_j$ depois de cada algarismo é 0, 2, 3, 0, 3, 6, 6, 6; o algarismo de controlo é 6 e a forma-máquina é `PR-0973-1922-6`.

Cada linha e cada coluna de $T$ é uma permutação, pelo que qualquer algarismo errado altera o resultado; a antissimetria total garante o mesmo para qualquer troca de dois algarismos adjacentes diferentes [@damm2004]. Ao contrário do esquema diedral de Verhoeff [@verhoeff1969], o de Damm precisa de uma só tabela e de nenhuma permutação. A zona não entra nos algarismos: dentro de um nome, cada número tem uma única zona dona, pelo que um engano num algarismo que caia noutra zona do mesmo nome muda exatamente um algarismo e é sempre detetado. Na forma-máquina, a chave do concelho tem ainda de coincidir com o concelho da zona dona.

## A camada de ponto

Todo o ponto em terra tem um Plus Code [@olc], a grelha escolhida pelos Correios para a *Morada Certa*. Com $\varphi' = \varphi + 90$ e $\lambda' = \lambda + 180$, os cinco pares de caracteres usam as resoluções $r_k \in \{20;\ 1;\ 0{,}05;\ 0{,}0025;\ 0{,}000125\}$ graus:

$$
\text{lat}_k = \left\lfloor \frac{\varphi'}{r_k} \right\rfloor \bmod 20, \qquad
\text{lng}_k = \left\lfloor \frac{\lambda'}{r_k} \right\rfloor \bmod 20, \qquad k = 1, \dots, 5,
\tag{13}
$$

e um décimo primeiro carácter divide a última célula em cinco linhas e quatro colunas:

$$
g = 4 \left( \left\lfloor \frac{5\varphi'}{r_5} \right\rfloor \bmod 5 \right) + \left( \left\lfloor \frac{4\lambda'}{r_5} \right\rfloor \bmod 4 \right),
\tag{14}
$$

escrevendo-se cada valor com o alfabeto `23456789CFGHJMPQRVWX`. Para o ponto de `Palmarejo 19 22`, os pares são (5, 7), (4, 16), (18, 9), (4, 8), (11, 14) e $g = 1$, o que dá `796RWF6C+HP3`, ou `WF6C+HP3 Praia` na forma curta. O modelo oferece onze caracteres (cerca de 3 m) nas cidades e nos portões e dez (cerca de 14 m) no campo, apenas em terra. A figura 7 mostra a grelha no Platô.

![A camada de ponto à volta do edifício dos Correios, no Platô (`Platô 11 32`, a vermelho). Pegadas do registo sob a grelha dos Plus Codes de dez caracteres (13,45 m × 13,82 m a esta latitude); a célula do edifício está dividida nas 4 × 5 células do décimo primeiro carácter. Um código de ponto designa um ponto; o código de casa designa o edifício. Dados: `registry/structures/`.](figures/spot-pt.svg){width=80%}

## O lote e o perfil do edifício

A unidade endereçável é o **lote**: um terreno ou conjunto, com as suas estruturas e a sua entrada. A ocupação do território em Cabo Verde tem um padrão próprio, e as regras de agrupamento seguem-no. Nas cidades, as casas erguem-se parede com parede ao longo das ruas e encosta acima, pelo que edifícios contíguos nunca se fundem. No campo, a casa tem muitas vezes cozinha exterior, latrina, cisterna ou curral, que entram no lote da casa como estruturas. Os recintos fechados, como escolas, hospitais e quartéis, formam um lote cada, e os complexos hoteleiros do Sal e da Boa Vista são conjuntos cujas unidades se alcançam pelo portão do conjunto. No registo, 12 604 lotes têm duas ou mais estruturas e reúnem 15,2 % das pegadas; 453 lotes são recintos fechados, dos quais apenas 16 (3,5 %) têm portão cartografado. O código leva à entrada principal: o portão, se existir, senão a porta confirmada.

Cada estrutura tem um perfil: uma classe de uso de uma taxonomia feita para Cabo Verde (moradia, prédio de habitação, habitação precária, misto, loja, mercado, armazém, restauração, escritório, hotel, pensão, governo, educação, saúde, religioso, indústria, agrícola, anexo e outras); a área e o perímetro da pegada; a altura e os pisos, quando se conhecem; um estado (em uso, *inacabado mas habitado*, em construção, ruína, abandonado, demolido); e a fonte e a confiança de cada atributo. O estado guarda-se à parte do uso, porque uma casa inacabada continua a ser uma casa. A classe é dada pela primeira regra aplicável, com a sua confiança: uma etiqueta de uso do OpenStreetMap (0,9); o tipo de edifício do OpenStreetMap (0,3–0,95); um lugar cartografado dentro da pegada (0,55–0,8); o papel da estrutura no lote (0,55); a dimensão e o contexto da ilha (0,35–0,5); o valor *a priori* do recenseamento de que a maioria dos edifícios são casas (0,5–0,6); e as correções de moradores, estafetas e municípios, que prevalecem sobre todas as outras (0,9–0,99).

## Estabilidade

Um código nunca se desloca nem se reutiliza. Se um lote se dividir, o código fica com a parte que tem a primeira entrada; se dois lotes se juntarem, ambos os códigos continuam válidos; o código de um edifício demolido é retirado e nunca reemitido; os blocos de um nome nunca se renumeram. Um código é **provisório** até moradores independentes o confirmarem, e **confirmado** a partir daí.

# Implementação

O modelo é implementado por quatro componentes publicados: um motor de referência com a sua especificação normativa, o registo, um servidor do registo com a sua API e dois conjuntos de vetores de conformidade que obrigam qualquer outra implementação a chegar aos mesmos resultados.

## Motor de referência e especificação

A especificação (`engine/SPEC.md`) é normativa. O motor de referência (`engine/reference/cv_engine.py`) usa apenas a biblioteca padrão de Python e implementa todas as regras da secção 4: a leitura de um código de casa com qualquer espaçamento, maiúsculas ou acentos, a descodificação pela equação (10), a forma-máquina e as equações (11)–(12), o Plus Code pelas equações (13)–(14), as formas de placa e faladas em português e em crioulo, a ordem de Hilbert e as equações (7)–(9), o plano de blocos das equações (5)–(6) e as regras do perfil do edifício. O seu autoteste verifica todas as zonas, todos os nomes oficiais e todos os enganos descritos na secção 6.4.

## O registo

O registo publica-se por concelho em CSV simples, com a tabela das zonas, o registo dos nomes, os pontos de numeração e a camada de edifícios (secção 3.4). Os resumos SHA-256 do manifesto permitem verificar qualquer cópia. O registo é a referência autêntica: para descodificar basta o registo dos nomes, ao passo que emitir um código novo exige os pontos de numeração e as pegadas.

## O servidor do registo e a sua API

O repositório inclui um servidor do registo (`server/`) que um ministério, um operador postal ou um programador pode instalar com um único comando (`docker compose up`). O servidor importa o registo para SQLite depois de verificar todos os resumos e todos os totais, serve uma API JSON em `/v1` (consulta por código, pesquisa por qualquer forma escrita, código num ponto, códigos próximos, verificação, códigos de ponto, zonas e áreas, listas paginadas) e exporta o registo no formato publicado, byte a byte. Uma instalação só pode emitir códigos se tiver chaves e tiver sido designada como emissora (secção 12.3); aplica então exatamente as regras da secção 4, incluindo as verificações de duplicado (nenhum código novo a menos de 3 m de uma entrada existente nem dentro de uma pegada existente), os limites do contorno (de 12 m² a 2 ha) e a equação (9). A API está documentada com pedidos e respostas reais em `docs/api.md` e em OpenAPI 3.1 em `server/openapi.yaml`.

## Conformidade e paridade

Dois conjuntos de vetores definem a conformidade. `engine/test-vectors.json` cobre as formas, os algarismos de controlo, as formas faladas, os blocos, os nomes de placa, as descodificações de nomes repetidos e os casos de crescimento. `engine/test-vectors-registry.json` contém códigos reais emitidos com todas as formas derivadas, os códigos de todas as zonas de quatro nomes repetidos, códigos com endereço oficial e uma inserção calculada sobre uma zona real. Uma implementação noutra linguagem é conforme se reproduzir os dois conjuntos. A lógica de emissão do servidor foi comparada com a implementação do próprio emissor em 107 emissões sucessivas numa zona, incluindo o preenchimento de um bloco e a abertura de um bloco de extensão, e coincidiu em todos os números e formas.

# Avaliação

Medimos o registo emitido face aos requisitos da secção 4.1. Todos os valores desta secção são calculados a partir dos ficheiros publicados em `registry/` e do motor de referência, e podem ser reproduzidos com as ferramentas do repositório.

## Unicidade e descodificação

As 1 778 zonas e todos os nomes oficiais descodificam para a zona esperada, e cada um dos 175 630 códigos descodifica para exatamente um lote. Dentro de cada um dos 1 360 nomes, os blocos são disjuntos por construção, pelo que, pela equação (10), não há no país dois códigos com a mesma forma lembrada.

## Comprimento do código

A tabela 4 resume os comprimentos. Dos 175 630 códigos, 77 467 (44,1 %) têm três algarismos e 98 163 (55,9 %) têm quatro; nenhum tem cinco. A zona mediana tem 50 códigos, o percentil 90 tem 213 e a maior, a Achada Santo António, 2 855: o triplo é 8 565, pelo que o seu bloco é 1000–9599.

| | Zonas | Códigos | Proporção dos códigos |
|:--|--:|--:|--:|
| Números de três algarismos | 1 349 | 77 467 | 44,1 % |
| Números de quatro algarismos | 429 | 98 163 | 55,9 % |
| Números de cinco algarismos | 0 | 0 | 0 % |
| **Total** | **1 778** | **175 630** | **100 %** |

: Comprimento dos números no registo.

## Nomes de placa

Os nomes de placa têm no máximo doze caracteres e duas palavras, exceto os 118 nomes assinalados que aguardam a escolha municipal. Entre os nomes não assinalados, os códigos lembrados mais longos têm 18 caracteres, por exemplo `Vila Miséria 25 98`.

## Deteção de erros

O autoteste gera enganos num algarismo a partir de 25 números de cada bloco de cada nome repetido. Dos 92 701 enganos que caem noutra zona do mesmo nome, todos os 92 701 são recusados pelo algarismo de controlo; outros 140 407 caem em números que nenhuma zona detém. Todas as 22 952 formas-máquina corrompidas (algarismo errado, algarismos trocados ou chave de concelho errada) são recusadas. Sem algarismo de controlo, como quando o código é dito em voz alta, o código continua protegido pela esparsidade. Na primeira emissão, um bloco tem cerca de três números por lote, pelo que a probabilidade de um engano aleatório dentro de um bloco atingir um código emitido é aproximadamente

$$
P(\text{acerto}) \approx \frac{L(z)}{s_d\, u(z)} \approx \frac{1}{3},
\tag{15}
$$

e o descodificador mostra sempre o que o código designa, com o concelho, antes de iniciar a navegação.

## Cobertura

Todos os lotes do mapa têm código: 175 629 emitidos em bloco e um emitido a pedido pela equação (9). Os 1 395 lotes com endereço oficial ou oficial pendente têm o endereço municipal e um código de casa (tabela 2).

## Perfis dos edifícios

A tabela 5 resume os perfis inferidos. A altura só é conhecida em 0,3 % das pegadas, pelas etiquetas do OpenStreetMap; o campo de altura dos dados de aprendizagem automática é um valor de preenchimento para a visualização e não uma medição, e não é usado. O recenseamento encontra 5,4 % de edifícios clássicos com uso exclusivamente não residencial [@ine2021]; o mapa deteta cerca de 3 %, sendo a diferença lojas e escritórios que ninguém etiquetou.

| | Cabo Verde | Praia | Sal |
|:-----------|-------:|-------:|-------:|
| Pegadas | 192 272 | 32 591 | 7 661 |
| Residencial | 84,1 % | 89,2 % | 61,0 % |
| Anexos | 11,1 % | 6,1 % | 7,3 % |
| Turismo | 1,7 % | 0,1 % | 27,2 % |
| Comércio, restauração e escritórios | 0,8 % | 1,9 % | 3,1 % |
| Agrícola | 1,7 % | 2,0 % | 0,3 % |
| Confiança alta / média / baixa | 3,6 / 73,0 / 23,5 % | 4,4 / 75,2 / 20,4 % | 8,0 / 51,8 / 40,2 % |
| Pegada mediana | 44,9 m² | 60,8 m² | 108,5 m² |

: Perfis inferidos dos edifícios. Confiança alta: 0,8 ou mais; média: de 0,55 a 0,8. Dados: `registry/structures/`.

## Fidelidade e desempenho do servidor

Depois de importar o registo completo (cerca de seis segundos num portátil), o servidor devolveu a mesma ficha que o serviço em linha do emissor para 58 códigos comparados campo a campo, incluindo códigos oficiais, oficiais pendentes, emitidos a pedido e com várias estruturas, e a mesma resposta para 400 pontos aleatórios. A única diferença é o arredondamento de uma coordenada de entrada a sete casas decimais (cerca de 1 cm) no formato publicado. Na mesma máquina, o servidor respondeu a cerca de 1 200 consultas por código e 120 consultas por ponto por segundo.

# Alternativas consideradas

Cada uma das escolhas principais da secção 4 foi comparada com as suas alternativas, sobre os mesmos dados, antes da emissão dos códigos. Esta secção regista essas alternativas e as medições que levaram a pô-las de parte.

## Outras formas de código

Avaliámos a forma adotada e seis alternativas segundo aquilo que os moradores já sabem de cor (tabela 6).

| Forma | Exemplo | Apreciação |
|:---------|:-------|:------------------|
| Nome curto de lugar e número de uma série nacional por nome | `Palmarejo 19 22` | **adotada** |
| Concelho e algarismos | `Praia 48 213` | a Praia precisaria de cinco algarismos (31 052 lotes × 3 > 9 000); os moradores descrevem a casa pelo bairro, não pelo concelho |
| Chave do concelho e código alfanumérico | `PR R5H8-R` | nenhum endereço cabo-verdiano tem letras; os nomes das letras em português rimam em duas grandes famílias (bê, cê, dê, gê, pê, tê, vê; efe, ele, eme, ene, erre, esse) e são difíceis de ditar |
| Código nacional só numérico | `07 0973 1922` | não contém lugar; um engano pode cair numa casa real de outra ilha |
| Plus Code sozinho | `796RWF6C+HP3` | preciso para um ponto, mas tem letras e um sinal de mais e muda de poucos em poucos metros; mantido como camada de ponto |
| Zona, número e concelho para separar nomes repetidos | `Achadinha 214, Paul` | não é único por si só: falha sempre que se omite o concelho |
| Nome oficial completo e número | `Lote Achada São Filipe 21 29` | comprido demais para dizer de um fôlego ou para caber numa placa |

: Formas de código consideradas.

## O custo das séries nacionais

Partilhar uma série entre zonas com o mesmo nome alonga alguns códigos. A tabela 7 compara três desenhos sobre as contagens do registo. Com uma série por zona, única apenas juntamente com o concelho, 1 625 zonas teriam três algarismos. Uma série por nome oficial dá 1 501. O nosso desenho, uma série por nome de placa, dá 1 349: a partilha põe em quatro algarismos 276 zonas que, sozinhas, teriam três. É o preço de um código curto que dispensa contexto. Nenhum desenho precisa de cinco algarismos.

| Desenho | 3 algarismos | 4 algarismos |
|:--------------------|-----:|-----:|
| Uma série por zona (única apenas com o concelho) | 1 625 | 153 |
| Uma série por nome oficial | 1 501 | 277 |
| **Uma série por nome de placa (adotado)** | **1 349** | **429** |

: Comprimento dos números em três desenhos, calculado sobre as contagens do registo.

## O esquema do algarismo de controlo

Comparámos o algoritmo de Damm com o ISO/IEC 7064 MOD 11,10 [@iso7064] calculado sobre o concelho, a zona e o número. O MOD 11,10 falha cerca de 2 % das trocas de algarismos adjacentes (por exemplo 12/21, 56/65 ou 09/90) e, com a zona entre os algarismos, só detetava 90,6 % dos enganos que caem noutra zona do mesmo nome. O algoritmo de Damm sobre o índice do nome e o número deteta-os todos (secção 6.4).

## Ruas com numeração oficial

Uma opção era não dar código de casa aos lotes em ruas que um município numerou, para que essas casas mostrassem apenas o endereço oficial. Rejeitámo-la: um único tipo de código para todas as casas é mais simples para os moradores, os estafetas e os sistemas, e o endereço oficial aparece, de qualquer modo, em primeiro lugar (secção 4.3). Os 1 395 lotes em causa foram numerados entre os vizinhos pela equação (9), sem alterar nenhum outro código.

# Benefícios para os cidadãos

Para uma família da Achada Santo António, de uma povoação de Santo Antão ou de uma rua de casas geminadas do Mindelo, um código de casa muda quatro coisas do dia a dia.

**Ser encontrado.** Hoje, um visitante, um táxi ou um estafeta é guiado por telefone. Com um código, o morador diz uma frase curta, «Palmarejo, dezanove, vinte e dois», e o visitante é levado à porta ou ao portão.

**Provar onde se mora.** Bancos, escolas, empregadores e serviços públicos pedem um endereço. Só 96 lotes têm rua e número municipais conhecidos, e outros 1 299 ficam em centros históricos presumivelmente numerados; todos os 175 630 têm código de casa (tabela 2).

**Receber bens e serviços.** As famílias na diáspora, as lojas em linha e as empresas de água e eletricidade podem enviar para um código em vez de uma descrição, e um agregado pode pedir uma ligação, uma leitura de contador ou uma reparação na porta certa.

**Entre ilhas.** Um código funciona da mesma forma na Praia, no Mindelo, em Espargos e em Nova Sintra. Uma encomenda enviada de São Vicente para uma aldeia do Fogo leva um código que identifica a aldeia e o edifício, sem croqui.

**Obter o código não custa esforço.** Todos os edifícios do mapa têm código desde 20 de outubro de 2026, e nada é pedido ao agregado (tabela 8). Obter o código é gratuito, não exige documento e não regista dados pessoais. Um código não é um título de propriedade.

| Situação | Passos |
|:--|:--|
| Casa guardada na aplicação N-Ways | nenhum: o código aparece no ecrã inicial |
| À porta de casa | um: confirmar «É a minha casa?» |
| Partilhar o código | um toque: uma ligação com o código por extenso |
| Placa ou autocolante no portão | nenhum: o código e um código QR que abre a navegação |
| Edifício novo | «Adicionar a minha casa»: portão, contorno, descrição; código pela equação (9) |

: Como os moradores obtêm o seu código.

**Quem mais beneficia.** Quem hoje tem menos: as famílias das ruas íngremes e sem nome dos bairros mais recentes da Praia, os agregados que vivem em casas ainda inacabadas (27,7 % dos edifícios em 2021 [@ine2021]) e as povoações longe de qualquer ponto de referência.

**Alcance estimado.** Se todos os agregados do recenseamento de 2021 usassem o seu código, 145 952 agregados ganhariam um endereço que conseguem dizer; 99,2 % dos lotes não têm outro endereço à porta (tabela 2). A memorização é o pressuposto crítico. Vamos medi-la (secção 13); se, ao fim de um mês, fosse de 50 % e não dos 80 % que temos como meta, o alcance seria de cerca de 73 000 agregados em vez de 117 000.

# Logística, comércio e turismo

As entregas em Cabo Verde fazem-se por telefone e atravessam o mar. Para as empresas de logística, a forma-máquina é uma chave estável do lote do cliente, que se pode guardar, desduplicar e cruzar com entregas anteriores; o código leva ao portão ou à porta, pelo que as rotas se planeiam antes da saída do estafeta; um código escrito verifica-se de imediato; cada lote tem o seu código postal dos Correios, pelo que o correio continua a ser triado para a estação certa; e o registo e o motor são abertos, de modo que qualquer transportadora, loja, banco ou prestador de pagamentos pode resolver códigos nos seus próprios sistemas, sem rede e sem custos.

**Turismo.** No Sal e na Boa Vista, que receberam 82,6 % dos 1 177 467 hóspedes hoteleiros de 2024 [@forbes2025], hotéis e apartamentos dependem de motoristas que os encontrem. Um complexo hoteleiro é um conjunto: a rota leva ao portão e depois a cada unidade. Um hóspede pode dar ao motorista um código em vez de uma descrição.

**Pequenos negócios.** Uma loja ou uma oficina aberta na fachada de uma casa é uma estrutura própria com entrada própria, designada pelo código do lote e por um sufixo de estrutura (por exemplo `.2`), e os clientes encontram-na sem indicações.

**Poupança estimada.** Seja $f_0$ a proporção de primeiras tentativas de entrega que falham, $\phi$ a parte dessas falhas que um código preciso elimina e $c$ o custo de uma tentativa. A poupança por 1 000 entregas é

$$
S = 1000 \, f_0 \, \phi \, c .
\tag{16}
$$

As estimativas publicadas do setor para África situam a taxa de sucesso à primeira tentativa em apenas 60 % ($f_0$ até 0,40) e o custo de uma tentativa em cerca de 2,70 dólares [@odeloye2023]. Não existe medição cabo-verdiana, pelo que apresentamos um intervalo (tabela 9). Com os valores centrais $f_0 = 0{,}20$ e $\phi = 0{,}5$, $S \approx 270$ dólares por 1 000 entregas. Entre ilhas, uma entrega falhada custa mais, porque a encomenda espera pelo barco ou pelo voo seguinte.

| $f_0$ | $\phi = 0{,}25$ | $\phi = 0{,}50$ | $\phi = 0{,}75$ |
|--:|--:|--:|--:|
| 0,10 | 68 USD | 135 USD | 203 USD |
| 0,20 | 135 USD | 270 USD | 405 USD |
| 0,40 | 270 USD | 540 USD | 810 USD |

: Poupança por 1 000 entregas pela equação (16), com $c$ = 2,70 USD.

# Serviços de emergência

Uma ambulância, os bombeiros ou a polícia enfrentam o problema do estafeta com mais em jogo, em ruas íngremes, estreitas e muitas vezes sem nome. Um estudo qualitativo dos serviços de emergência médica de Kigali concluiu que as equipas e os operadores perdiam tempo a localizar os doentes, porque dependiam do conhecimento local e precisavam de várias chamadas para estabelecer o local [@hunt2024]. Não conhecemos nenhuma medição publicada para Cabo Verde, o que é, em si, razão para começar uma.

**Como o código ajuda o operador.** Quem liga diz uma frase, «Fazenda, trinta e quatro, quarenta e oito». O operador escreve-a e o registo devolve um lote: a Fazenda do Tarrafal, e não uma das outras seis Fazendas, porque só o bloco do Tarrafal contém o 34 48 (figura 4). O operador lê em voz alta o que o código designa, com o concelho, antes de a equipa partir. O código leva à entrada do lote e ao seu Plus Code, que qualquer sistema de despacho que leia Plus Codes entende. O motor e o registo funcionam sem rede.

**Efeito estimado.** Larsen e colegas modelaram a sobrevivência após paragem cardíaca extra-hospitalar como 67 %, menos 2,3 pontos por minuto até à reanimação cardiopulmonar, 1,1 pontos por minuto até à desfibrilhação e 2,1 pontos por minuto até ao suporte avançado [@larsen1993]. Quando uma só equipa presta os três, um atraso de $\Delta t$ minutos a encontrar a porta reduz a sobrevivência em

$$
\Delta S = (2{,}3 + 1{,}1 + 2{,}1)\,\Delta t = 5{,}5\,\Delta t \ \text{pontos percentuais}.
\tag{17}
$$

Ganhar um a três minutos corresponde a 5,5 a 16,5 pontos. O modelo foi ajustado no condado de King, Washington, pelo que estes valores indicam uma ordem de grandeza para Cabo Verde, não uma previsão; o sentido do efeito não oferece dúvida.

**Planear a rede.** No mapa da N-Ways de outubro de 2026, 72 % de uma amostra de 20 000 lotes ficam a menos de 5 km, em linha reta, de uma unidade de saúde cartografada, e 41 % a menos de 5 km de uma esquadra de polícia cartografada (secção 11).

# Coordenação e planeamento da administração pública

Um código de casa é uma chave comum. Quando ministérios, Câmaras Municipais, empresas de serviços públicos e o instituto de estatística designam um lote pelo mesmo código, os seus registos podem cruzar-se sem comparar nomes e descrições. O Banco Mundial identifica este aspeto como um dos principais benefícios para a administração local: um diretório de endereços enumera os prédios de forma mais completa do que o cadastro fiscal e mostra quem falta nele [@farvacque2005]. Cada código traz o código postal dos Correios, o endereço municipal quando existe e, nas ilhas com cadastro, o NIP quando se conhece, de modo que cada instituição mantém os seus registos e continua de acordo quanto ao lote.

**Planear com contagens reais.** O registo conta lotes por ilha, concelho, zona, classe e estado do edifício, incluindo o *inacabado mas habitado*, e todas as contagens podem recalcular-se a partir dos ficheiros abertos. Só a Praia tem 31 052 lotes em 64 zonas.

**Acesso aos serviços.** A tabela 10 dá as distâncias em linha reta de uma amostra de 20 000 lotes à instalação cartografada mais próxima de cada tipo. Os valores descrevem o mapa e não o terreno: as instalações não cartografadas fazem as distâncias parecer maiores. Um ministério pode substituir a lista de instalações pela sua e recalcular o quadro em minutos.

| Instalação | Até 2 km | Até 5 km | Distância mediana |
|:----------------|-----:|-----:|-----:|
| Unidade de saúde (hospital, centro de saúde, posto sanitário) | 45,1 % | 71,6 % | 2,53 km |
| Escola | 58,8 % | 83,8 % | 1,33 km |
| Esquadra de polícia | 28,7 % | 41,0 % | 7,83 km |
| Farmácia | 35,6 % | 56,5 % | 4,02 km |

: Distância em linha reta à instalação cartografada mais próxima; mapa da N-Ways, outubro de 2026, amostra de 20 000 lotes.

**Política de habitação.** Os perfis dos edifícios mantêm, para cada lote, a distinção do recenseamento entre estado e uso e atualizam-se à medida que os moradores os confirmam, pelo que a política de habitação pode acompanhar a forma como as casas se acabam piso a piso.

**Custo evitado estimado.** Um programa convencional de numeração de portas para os mesmos lotes, ao custo médio do Banco Mundial de 5,7 dólares por porta [@farvacque2005], custaria

$$
C = N\,c = 175\,630 \times 5{,}7\ \text{USD} \approx 1{,}0 \text{ milhões de USD}
\tag{18}
$$

a preços de 2005, antes da inflação e do custo de trabalhar em nove ilhas. Com o custo por porta observado numa única cidade do mesmo estudo, 7,6 dólares, o valor sobe para 1,33 milhões. A sinalização das ruas e a numeração municipal continuam a ter valor; os códigos de casa não as substituem, mas dão de imediato a cada edifício uma referência utilizável, e os números oficiais, à medida que forem atribuídos, aparecem primeiro.

# Privacidade, segurança e governação

Um registo de endereços descreve lugares, mas são pessoas que o usam, e alguns usos comportam riscos. Esta secção expõe o que o registo contém sobre quem vive num endereço, como o modelo limita o dano que um código poderia causar e como se governa a emissão de códigos.

## Proteção de dados

Os códigos descrevem lugares, nunca pessoas. A lei cabo-verdiana de proteção de dados, a Lei n.º 133/V/2001, alterada e republicada pela Lei n.º 121/IX/2021, aplica-se aos serviços prestados do estrangeiro a pessoas em Cabo Verde, exige a notificação da Comissão Nacional de Proteção de Dados antes de qualquer tratamento automatizado e fixa um prazo de 72 horas para a notificação de violações [@lei121_2021]. O registo de códigos, lotes e perfis de edifícios não contém dados pessoais. Os nomes dos moradores e a composição dos agregados nunca se guardam. Um agregado pode manter a porta privada, caso em que o código leva ao portão ou à rua, e os nomes dos negócios só aparecem quando os donos os publicam.

## Segurança

O registo publica o que se vê da rua: pegadas, classes de uso e entradas. Não regista ocupantes, interiores nem fotografias de pessoas; as fotografias de portão usadas na confirmação são apagadas logo que o portão é confirmado. As correções só se aceitam quando moradores independentes concordam, estando um deles presente no lote, para que uma única conta não possa mudar o código de outra família.

## Governação e emissor único

A N-WAYS LIMITED mantém o modelo, o motor e o registo num repositório público [@nways2026]. Os nomes das zonas só mudam com o acordo da Câmara Municipal respetiva; os códigos emitidos nunca mudam. Os códigos têm de ser emitidos por **um único emissor para o país**: hoje o emissor da N-Ways, ou qualquer entidade que o Estado de Cabo Verde designe. Dois emissores independentes atribuiriam o mesmo número livre a dois edifícios. Todas as outras instalações do servidor do registo funcionam só em leitura. O modelo foi concebido para ser transferido: o repositório, o registo e as suas regras podem passar para os Correios de Cabo Verde, para o INGT e a Comissão Nacional de Toponímia, ou para uma entidade por eles designada, sem alterar o motor. Até uma entidade nacional os adotar, estes são endereços N-Ways, não endereços oficiais nem códigos postais. A tabela 11 enumera as instituições envolvidas.

| Instituição | Papel |
|:--|:--|
| Correios de Cabo Verde | códigos postais e Morada Certa; primeiro parceiro para a transferência |
| As 22 Câmaras Municipais | nomes das zonas, toponímia, numeração de polícia, litígios locais |
| INGT e Comissão Nacional de Toponímia | toponímia, cadastro, geodesia, infraestrutura nacional de dados espaciais |
| Instituto Nacional de Estatística | geografia censitária |
| Comissão Nacional de Proteção de Dados | proteção de dados |

: Instituições e respetivos papéis.

# Limitações e trabalho futuro

**Nomes das zonas.** Os nomes vêm do OpenStreetMap e do GeoNames e incluem grafias que os municípios poderão querer mudar; 306 nomes de placa estão assinalados às Câmaras, 118 deles ainda sem forma que caiba. **Mapa desigual.** As imagens fundem filas de casas geminadas no Mindelo e na Praia e contam anexos a mais no Fogo e no interior de Santiago. **Alturas e pisos** são quase sempre desconhecidos. **As classes dos edifícios** são inferências, cerca de um quarto de baixa confiança, e os edifícios não residenciais estão subdetetados. **Os portões** quase não estão cartografados: apenas 16 lotes têm portão cartografado. **Os códigos postais** estão incompletos: não há lista publicada pelos Correios e os algarismos de São Nicolau e do Maio são deduzidos. **Pontos por confirmar:** se a Morada Certa continua em funcionamento e o texto do decreto de 2024 sobre o cadastro, que só conhecemos por resumos secundários. **Língua:** as palavras dos números em crioulo usadas pela voz precisam de ser verificadas por falantes de Santiago e de São Vicente.

**Medições previstas.** Vamos medir as grandezas de que dependem as estimativas de impacto (tabela 12) e publicar os resultados no repositório.

| Medida | Método | Meta |
|:--|:--|:--|
| Memorização do próprio código ao fim de uma semana e de um mês | perguntar aos moradores sem a aplicação | pelo menos 80 % exatos |
| Erros ao dizer, escrever e preencher | chamadas a estafetas, pesquisa na aplicação, formulários em papel; comparação com os Plus Codes das mesmas casas | menos erros do que com Plus Codes |
| Sucesso da entrega à primeira tentativa | transportadoras parceiras, com e sem código | pelo menos 20 pontos acima |
| Tempo da rua à porta | registos horários da aplicação do estafeta | reduzido a metade |
| Portas e portões confirmados | moradores e estafetas | 5 000 |
| Tempo de localização nas chamadas de emergência | com um serviço de ambulâncias ou de bombeiros disponível | medido e depois reduzido a metade |
| Aceitação dos nomes normalizados | moradores de cada ilha (Chã de Baixo = Chã Baixo) | aceites |

: Medições previstas.

# Conclusão

Descrevemos um modelo nacional de endereçamento para Cabo Verde em que cada edifício tem um código formado por uma palavra de lugar que os moradores já usam e por um número curto. As séries nacionais por nome tornam o código único sem contexto; a numeração ordenada por Hilbert e repartida mantém os vizinhos próximos e deixa margem de crescimento; um algarismo de controlo de Damm na forma-máquina deteta todos os erros num algarismo e todas as trocas adjacentes. O modelo está em vigor para os 175 630 lotes do país; 44 % dos códigos têm três algarismos e nenhum tem mais de quatro. Funciona ao lado do código postal, do endereço municipal, do cadastro e do Plus Code, sem substituir nenhum deles. O motor, o registo e um servidor pronto a instalar são abertos, para que o Estado e qualquer instituição possam verificar todos os códigos e, uma vez designados, emitir novos segundo as mesmas regras.

# Disponibilidade dos dados e do código {-}

A especificação, o motor de referência, os vetores de conformidade, o registo, o servidor do registo, as ferramentas e este artigo estão disponíveis em <https://github.com/n-ways/open-addresses-cabo-verde> [@nways2026]. O código está sob a Apache License 2.0, os dados sob a Open Database License 1.0 e os documentos sob a Creative Commons Atribuição 4.0. Menção de crédito: «N-Ways Addressing for Cabo Verde, © N-WAYS LIMITED (nways.ng)». As figuras compilam-se a partir de `docs/figures/*.tex`, com as tabelas de `docs/figures/data/`, que `tools/paper_figures.py` recalcula a partir do registo; os PDF geram-se com `sh docs/paper/build.sh`.

# Agradecimentos {-}

Agradecemos aos contribuidores do OpenStreetMap, cujos edifícios, lugares e limites são o alicerce do registo; à Google Research e à Microsoft pelos seus conjuntos abertos de pegadas de edifícios, e à Overture Maps Foundation por os distribuir; ao GeoNames; e ao Instituto Nacional de Estatística, aos Correios de Cabo Verde, ao INGT e à Comissão Nacional de Toponímia pelos documentos públicos em que assenta a secção 2.

# Referências {-}

::: {#refs}
:::
