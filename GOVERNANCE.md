# Governance

Status: in force since the first issue (the whole country, 19 October 2026). Licences and credit: [LICENSING.md](LICENSING.md).

## Maintainers

**N-Ways** maintains this repository, the Cabo Verde engine and the Cabo Verde registry until a Cabo Verdean public body takes them over. Maintainers are named in the repository settings at https://github.com/n-ways/open-addresses-cabo-verde.

N-Ways addresses are **not official addresses or postcodes** until a Cabo Verdean public body adopts them, and nothing in this repository may describe them as official.

## Authorities this model works beside

| Body | What it decides | How the model follows |
|---|---|---|
| Correios de Cabo Verde | postcodes; Morada Certa | the postcode is shown, never changed or derived |
| The 22 Câmaras Municipais | street names, door numbers (Decreto-Lei 5/2012); zone names; local disputes | each Câmara checks its zones and chooses its flagged plate names; municipal numbers are shown first |
| INGT and the Comissão Nacional de Toponímia | toponymy, cadastre, geodesy, IDE-CV | names follow CNT spelling where it exists; NIPs are references only |
| INE | census geography | mapping tables only |
| CNPD | data protection | notified of the app's processing; complaints answered under Lei 133/V/2001 |

## What may change, and how

1. **Issued codes never change.** No pull request may move, reuse or lengthen an issued code (engine/SPEC.md §9).
2. **Zone names** change only with the Câmara Municipal's agreement, or the Comissão Nacional de Toponímia's for national names. The old name stays as an alias.
   **Plate names** (the short name in the code, at most 12 characters and 2 words) flagged `needsCouncilChoice` are provisional until the Câmara Municipal chooses. Their codes were issued provisional; the Câmara's choice changes the name once and every number stays. A documented short form (ASA, AGF) needs a cited source.
3. **Name ranges.** A home code is unique nationally on its own. Every name has one national number range; its blocks are frozen at first issue and never renumbered. A new zone with an existing name gets a new block from that name's spare units. A qualifier is added to a name only when its zones cannot fit 5 digits, for its new zones, and is listed in the register.
4. **New zones, new lotes, splits, merges and retirements** follow SPEC §7.4 and §9. They are made by the registry build from the app's agreed confirmations, not by hand.
5. **Building profiles and doors** are settled by agreement between independent people: arrivals, couriers, owners. Nothing is queued for a maintainer to review. A maintainer may undo vandalism.
6. **Engine and spec changes** raise the specification version (recorded in every registry manifest), update the test vectors, and explain in the pull request why the change is right for Cabo Verde. No change may alter how an issued code decodes.
7. **Registry releases** come with `registry/MANIFEST.json`, giving the counts and the SHA-256 of every file. The registry server refuses a registry that does not match its manifest.

## One issuer

Codes are issued by **one issuer for the country**: the deployment the State of Cabo Verde or N-WAYS LIMITED designates, today the N-Ways registry server. Anyone may run the registry server in [`server/`](server/README.md) to serve and look up codes, but every other deployment is read-only. Two issuers starting from the same registry would see the same free numbers and give the same number to two buildings, which could never be repaired without renumbering one of them. A body that needs to issue (a municipal front desk, a utility) does so through the issuer's API with a key of its own. The issuer publishes its registry after each round of issuing, and other deployments update from it.

## Disputes

A neighbour who disputes a lote or a door uses the app. The provisional code stays reserved and is not shown while the dispute is open. If people do not agree within 30 days, the Câmara Municipal's view is followed. An N-Ways code never decides ownership.

## Hand-over

The repository is built to move to a national body without forking the engine: Correios de Cabo Verde first, or INGT, or a body they name. Hand-over moves:

- the repository, its signing keys and the registry;
- the zone list and the rules in this file;
- the right to name maintainers.

From then on N-Ways is a user like any other. Codes issued before hand-over stay valid.
