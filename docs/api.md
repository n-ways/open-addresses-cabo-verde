# The registry API

This is the API of the registry server in [`server/`](../server/README.md). Every example below is a real request to a server running on the published registry of Cabo Verde (175,630 codes), with the response it returned. The machine-readable description is [`server/openapi.yaml`](../server/openapi.yaml).

## Conventions

- Base path `/v1`. Responses are JSON (UTF-8) with stable field names; a field with nothing to say is left out rather than sent empty.
- An error is always `{"error": {"code": "...", "message": "..."}}` with its HTTP status: `400` a malformed request, `401` a missing or wrong issuer key, `403` issuing on a read-only deployment, `404` nothing with that name or number, `405` a method the path does not take, `409` a conflict (the building already has a code, or the code is retired), `413` a request body over 64 KB, `422` a request that is well formed but cannot be done (a wrong check digit, a point at sea or more than 300 m outside the national border, a door too far away), `429` an issuer key over its daily limit. The `code` is stable and meant for programs; the `message` is meant for people.
- Coordinates are WGS 84 decimal degrees, `lat` then `lng`. Outlines are lists of `[lng, lat]` points, as in GeoJSON.
- Reading needs no key. Issuing and changing codes (`POST`, `PATCH`) need `Authorization: Bearer <key>`, and only a deployment designated as the issuer has keys ([server/README.md](../server/README.md#one-issuer)).
- GET responses may be cached for 60 seconds (`Cache-Control: public, max-age=60`); `health`, `POST` and `PATCH` are never cached.
- Cross-origin requests are allowed from the origins in `CORS_ORIGINS`.
- **Zones and areas.** The registry is published per municipality (concelho), so the API calls a municipality a *zone* and uses its ISO 3166-2:CV key (`PR` is Praia). The named places that make up the remembered form (bairros, zonas, povoações: *Palmarejo*, *Achada Fazenda*) are *areas*, with ids such as `PR-004`. In [engine/SPEC.md](../engine/SPEC.md) those places are called zones; the API keeps "zone" for the unit of the published files.

## Endpoints

| Method and path | What it does |
|---|---|
| `GET /v1/health` | Liveness and counts |
| `GET /v1/info` | Country, municipalities, counts, licences, credit, engine |
| `GET /v1/codes/{machine}` | The full card of a code |
| `GET /v1/find?q=` | Find what someone typed: remembered form, machine form, official address or spot code |
| `GET /v1/at?lat=&lng=` | The code of the lote at a point |
| `GET /v1/near?lat=&lng=&radius=&limit=` | Codes near a point |
| `GET /v1/verify?code=` | Check a machine code |
| `GET /v1/spot?lat=&lng=` | The spot code (Plus Code) of a point |
| `GET /v1/spot/decode?code=` | A spot code back to its point, and the lote there |
| `GET /v1/zones` | The 22 municipalities |
| `GET /v1/zones/{key}` | One municipality and its areas |
| `GET /v1/zones/{key}/codes?after=&limit=` | Every code of a municipality, page by page |
| `GET /v1/areas/{id}` | One area: names, blocks, counts |
| `GET /v1/areas?name=` | Areas by plate name, official name or alias |
| `POST /v1/codes` | Issue a code (issuer key) |
| `PATCH /v1/codes/{machine}` | Confirm, retire, or move the entrance (issuer key) |

## The card

`GET /v1/codes/{machine}`, `find`, `at` and the issue endpoints return a code as a *card*:

| Field | Meaning |
|---|---|
| `machine` | The machine form, `PR-0973-1234-0`: municipality key, national name index, number, check digit. For systems, forms and plates. |
| `home` | The remembered form, `Palmarejo 12 34`: the plate name and the number. Unique in the country on its own. |
| `check` | The check digit (machine form only; people never have to say it). |
| `name`, `officialName`, `nameProvisional`, `near` | The plate name, the official name when it is longer, whether the Câmara Municipal is still to choose the plate name, and a landmark that helps tell same-named places apart. |
| `area`, `municipality`, `municipalityKey`, `island` | Where the code is. |
| `coverage`, `officialAddress` | `official` where the Câmara numbered the street (the official address is shown first), `official-pending` where a numbered centre's register is not shared yet. |
| `postcode` | The Correios postcode of the area, as context (`kind: area`): postcodes in Cabo Verde cover areas, not doors. |
| `fullLine`, `written`, `spoken`, `spokenKea` | The address line, what a plate prints (`big` alone decodes; `small` gives the municipality and island), and the code said in Portuguese and in Kriolu. |
| `status`, `issued`, `issuedAt` | `provisional` until confirmed, `confirmed`, or `retired`; `bulk` or `on-demand`; when. |
| `entrance`, `location`, `plusCode`, `plusCodeShort` | Where a trip ends (`gate`, `door` or `centre` of the main structure), and its spot code. |
| `lote`, `structures` | The lote's use, kind, structures and floor area, and each structure's building profile (use, confidence and how it was found, footprint, floors). Homes carry no names and nothing about the people in them. |
| `registry` | The code's row of the published registry, every column by its name, exactly as published. |
| `credit`, `creditUrl` | The credit line to show wherever the code appears. |

## GET /v1/health

Liveness, the number of codes served and the date of the registry export they come from.

#### Health

```sh
curl -s 'http://localhost:8080/v1/health'
```

`200 OK`

```json
{
  "status": "ok",
  "country": "CV",
  "codes": 175630,
  "exported": "2026-10-20T02:31:15Z"
}
```

## GET /v1/info

The country, its municipalities with their counts, licences, credit lines and engine.

#### Info

```sh
curl -s 'http://localhost:8080/v1/info'
```

`200 OK` (lists shortened to their first entries)

```json
{
  "country": "CV",
  "name": "Cabo Verde",
  "zones": [
    {
      "key": "BR",
      "iso": "CV-BR",
      "name": "Brava",
      "island": "Brava",
      "postcode": {
        "value": "9110",
        "kind": "area",
        "source": "OpenStreetMap addr:postcode"
      },
      "seat": "Nova Sintra",
      "bbox": [
        -24.749,
        14.8032,
        -24.6284,
        14.9841
      ],
      "codes": 2900,
      "byStatus": {
        "provisional": 2900
      },
      "areas": 36
    },
    {
      "key": "BV",
      "iso": "CV-BV",
      "name": "Boa Vista",
      "island": "Boa Vista",
      "postcode": {
        "value": "5110",
        "kind": "area",
        "source": "OpenStreetMap addr:postcode"
      },
      "seat": "Sal Rei",
      "bbox": [
        -22.966,
        15.9678,
        -22.6673,
        16.2306
      ],
      "codes": 4867,
      "byStatus": {
        "provisional": 4867
      },
      "areas": 61
    }
  ],
  "counts": {
    "codes": 175630,
    "byStatus": {
      "provisional": 175630
    },
    "structures": 192272,
    "areas": 1778,
    "names": 1360
  },
  "registry": {
    "exported": "2026-10-20T02:31:15Z",
    "importedAt": "2026-10-21T13:34:23Z",
    "localChanges": 0
  },
  "licences": {
    "code": "Apache-2.0",
    "data": "ODbL-1.0",
    "documents": "CC-BY-4.0"
  },
  "credit": "Home code by N-Ways Addressing",
  "dataCredit": "N-Ways Addressing for Cabo Verde, © N-WAYS LIMITED (nways.ng)",
  "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde",
  "engine": "internal/addressing/cv (SPEC v0.4)",
  "spec": "engine/SPEC.md",
  "issuing": true,
  "example": {
    "home": "Palmarejo 12 34",
    "machine": "PR-0973-1234-0"
  }
}
```

## GET /v1/codes/{machine}

The full card of an issued code: every registry column (under `registry`), the remembered, written and spoken forms, the spot code, the area and municipality, the lote and its structures.

#### A card

```sh
curl -s 'http://localhost:8080/v1/codes/PR-0973-1234-0'
```

`200 OK`

```json
{
  "country": "CV",
  "machine": "PR-0973-1234-0",
  "home": "Palmarejo 12 34",
  "check": 0,
  "name": "Palmarejo",
  "nameProvisional": false,
  "near": "Monte Vermelho",
  "area": {
    "id": "PR-004",
    "plateName": "Palmarejo",
    "officialName": "Palmarejo"
  },
  "municipality": "Praia",
  "municipalityKey": "PR",
  "island": "Santiago",
  "postcode": {
    "value": "7600",
    "kind": "area",
    "source": "UPU addressing sheet 04/2014; Correios HQ address"
  },
  "fullLine": "Palmarejo 12 34 · Praia, Santiago · 7600",
  "written": {
    "big": "Palmarejo 12 34",
    "small": "Praia · Santiago",
    "machine": "PR-0973-1234-0"
  },
  "spoken": "Palmarejo, doze, trinta e quatro",
  "spokenKea": "Palmarejo, dozi, trinta i kuatu",
  "status": "provisional",
  "issued": "bulk",
  "issuedAt": "2026-10-19T07:40:03Z",
  "entrance": {
    "lat": 14.9067372,
    "lng": -23.5272164,
    "kind": "centre",
    "source": "map"
  },
  "location": {
    "lat": 14.9067372,
    "lng": -23.5272164
  },
  "plusCode": "796RWF4F+M4V",
  "plusCodeShort": "WF4F+M4 Praia",
  "lote": {
    "use": "residencial.moradia",
    "kind": "um_edificio",
    "structures": 1,
    "floorAreaM2": 301.7,
    "enclosed": false
  },
  "structures": [
    {
      "index": 1,
      "id": "osm:way/416144875",
      "use": "residencial.moradia",
      "confidence": 0.6,
      "source": "prior:census2021",
      "status": "em_uso",
      "footprintM2": 301.7,
      "perimeterM": 69.6,
      "floors": 1,
      "floorAreaM2": 301.7,
      "data": "osm"
    }
  ],
  "registry": {
    "machine": "PR-0973-1234-0",
    "home": "Palmarejo 12 34",
    "official_name": "Palmarejo",
    "zone": "PR-004",
    "number": "1234",
    "check": "0",
    "status": "provisional",
    "issued": "bulk",
    "issued_at": "2026-10-19T07:40:03Z",
    "entrance_lat": "14.9067372",
    "entrance_lng": "-23.5272164",
    "entrance_kind": "centre",
    "plus_code": "796RWF4F+M4V",
    "use": "residencial.moradia",
    "lote_kind": "um_edificio",
    "structures": "1",
    "floor_area_m2": "301.7",
    "postcode": "",
    "coverage": "",
    "official_address": ""
  },
  "credit": "Home code by N-Ways Addressing",
  "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
}
```

#### A code that was never issued

```sh
curl -s 'http://localhost:8080/v1/codes/PR-0973-1234-1'
```

`404 Not Found`

```json
{
  "error": {
    "code": "unknown_code",
    "message": "There is no code PR-0973-1234-1."
  }
}
```

## GET /v1/find?q=

One box for whatever people type: a remembered form (any spacing, case or accents), a machine form, an official street address, or a spot code. A machine form with a wrong check digit is refused, never corrected by guessing.

#### A remembered form, typed loosely

Lists inside the card are shortened to keep the page readable; the response holds the full card.

```sh
curl -s 'http://localhost:8080/v1/find?q=palmarejo%201234'
```

`200 OK`

```json
{
  "query": "palmarejo 1234",
  "kind": "home",
  "matches": [
    {
      "country": "CV",
      "machine": "PR-0973-1234-0",
      "home": "Palmarejo 12 34",
      "check": 0,
      "name": "Palmarejo",
      "nameProvisional": false,
      "near": "Monte Vermelho",
      "area": {
        "id": "PR-004",
        "plateName": "Palmarejo",
        "officialName": "Palmarejo"
      },
      "municipality": "Praia",
      "municipalityKey": "PR",
      "island": "Santiago",
      "postcode": {
        "value": "7600",
        "kind": "area",
        "source": "UPU addressing sheet 04/2014; Correios HQ address"
      },
      "fullLine": "Palmarejo 12 34 · Praia, Santiago · 7600",
      "written": {
        "big": "Palmarejo 12 34",
        "small": "Praia · Santiago",
        "machine": "PR-0973-1234-0"
      },
      "spoken": "Palmarejo, doze, trinta e quatro",
      "spokenKea": "Palmarejo, dozi, trinta i kuatu",
      "status": "provisional",
      "issued": "bulk",
      "issuedAt": "2026-10-19T07:40:03Z",
      "entrance": {
        "lat": 14.9067372,
        "lng": -23.5272164,
        "kind": "centre",
        "source": "map"
      },
      "location": {
        "lat": 14.9067372,
        "lng": -23.5272164
      },
      "plusCode": "796RWF4F+M4V",
      "plusCodeShort": "WF4F+M4 Praia",
      "lote": {
        "use": "residencial.moradia",
        "kind": "um_edificio",
        "structures": 1,
        "floorAreaM2": 301.7,
        "enclosed": false
      },
      "structures": [
        {
          "index": 1,
          "id": "osm:way/416144875",
          "use": "residencial.moradia",
          "confidence": 0.6,
          "source": "prior:census2021",
          "status": "em_uso",
          "footprintM2": 301.7,
          "perimeterM": 69.6,
          "floors": 1,
          "floorAreaM2": 301.7,
          "data": "osm"
        }
      ],
      "registry": {
        "machine": "PR-0973-1234-0",
        "home": "Palmarejo 12 34",
        "official_name": "Palmarejo",
        "zone": "PR-004",
        "number": "1234",
        "check": "0",
        "status": "provisional",
        "issued": "bulk",
        "issued_at": "2026-10-19T07:40:03Z",
        "entrance_lat": "14.9067372",
        "entrance_lng": "-23.5272164",
        "entrance_kind": "centre",
        "plus_code": "796RWF4F+M4V",
        "use": "residencial.moradia",
        "lote_kind": "um_edificio",
        "structures": "1",
        "floor_area_m2": "301.7",
        "postcode": "",
        "coverage": "",
        "official_address": ""
      },
      "credit": "Home code by N-Ways Addressing",
      "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
    }
  ]
}
```

#### An official name typed in place of the plate name

```sh
curl -s 'http://localhost:8080/v1/find?q=Lote%20Achada%20S%C3%A3o%20Filipe%2021%2001'
```

`200 OK`

```json
{
  "query": "Lote Achada São Filipe 21 01",
  "kind": "home",
  "matches": [
    {
      "country": "CV",
      "machine": "PR-1221-2101-8",
      "home": "São Filipe 21 01",
      "check": 8,
      "name": "São Filipe",
      "officialName": "Lote Achada São Filipe",
      "nameProvisional": true,
      "near": "Safende",
      "area": {
        "id": "PR-024",
        "plateName": "São Filipe",
        "officialName": "Lote Achada São Filipe"
      },
      "municipality": "Praia",
      "municipalityKey": "PR",
      "island": "Santiago",
      "postcode": {
        "value": "7600",
        "kind": "area",
        "source": "UPU addressing sheet 04/2014; Correios HQ address"
      },
      "fullLine": "São Filipe 21 01 · Lote Achada São Filipe · Praia, Santiago · 7600",
      "written": {
        "big": "São Filipe 21 01",
        "small": "Praia · Santiago",
        "machine": "PR-1221-2101-8",
        "official": "Lote Achada São Filipe"
      },
      "spoken": "São Filipe, vinte e um, zero um",
      "spokenKea": "São Filipe, vinti i un, zeru un",
      "status": "provisional",
      "issued": "bulk",
      "issuedAt": "2026-10-19T07:40:03Z",
      "entrance": {
        "lat": 14.951038,
        "lng": -23.5150778,
        "kind": "centre",
        "source": "map"
      },
      "location": {
        "lat": 14.951038,
        "lng": -23.5150778
      },
      "plusCode": "796RXF2M+CX7",
      "plusCodeShort": "XF2M+CX Praia",
      "lote": {
        "use": "residencial.moradia",
        "kind": "um_edificio",
        "structures": 1,
        "floorAreaM2": 104.1,
        "enclosed": false
      },
      "structures": [
        {
          "index": 1,
          "id": "nw:c496a808a397",
          "use": "residencial.moradia",
          "confidence": 0.6,
          "source": "prior:census2021",
          "status": "em_uso",
          "footprintM2": 104.1,
          "perimeterM": 48.5,
          "floors": 1,
          "floorAreaM2": 104.1,
          "data": "ml"
        }
      ],
      "registry": {
        "machine": "PR-1221-2101-8",
        "home": "São Filipe 21 01",
        "official_name": "Lote Achada São Filipe",
        "zone": "PR-024",
        "number": "2101",
        "check": "8",
        "status": "provisional",
        "issued": "bulk",
        "issued_at": "2026-10-19T07:40:03Z",
        "entrance_lat": "14.9510380",
        "entrance_lng": "-23.5150778",
        "entrance_kind": "centre",
        "plus_code": "796RXF2M+CX7",
        "use": "residencial.moradia",
        "lote_kind": "um_edificio",
        "structures": "1",
        "floor_area_m2": "104.1",
        "postcode": "",
        "coverage": "",
        "official_address": ""
      },
      "credit": "Home code by N-Ways Addressing",
      "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
    }
  ]
}
```

#### A machine form

```sh
curl -s 'http://localhost:8080/v1/find?q=PR-0973-1234-0'
```

`200 OK`

```json
{
  "query": "PR-0973-1234-0",
  "kind": "machine",
  "matches": [
    {
      "country": "CV",
      "machine": "PR-0973-1234-0",
      "home": "Palmarejo 12 34",
      "check": 0,
      "name": "Palmarejo",
      "nameProvisional": false,
      "near": "Monte Vermelho",
      "area": {
        "id": "PR-004",
        "plateName": "Palmarejo",
        "officialName": "Palmarejo"
      },
      "municipality": "Praia",
      "municipalityKey": "PR",
      "island": "Santiago",
      "postcode": {
        "value": "7600",
        "kind": "area",
        "source": "UPU addressing sheet 04/2014; Correios HQ address"
      },
      "fullLine": "Palmarejo 12 34 · Praia, Santiago · 7600",
      "written": {
        "big": "Palmarejo 12 34",
        "small": "Praia · Santiago",
        "machine": "PR-0973-1234-0"
      },
      "spoken": "Palmarejo, doze, trinta e quatro",
      "spokenKea": "Palmarejo, dozi, trinta i kuatu",
      "status": "provisional",
      "issued": "bulk",
      "issuedAt": "2026-10-19T07:40:03Z",
      "entrance": {
        "lat": 14.9067372,
        "lng": -23.5272164,
        "kind": "centre",
        "source": "map"
      },
      "location": {
        "lat": 14.9067372,
        "lng": -23.5272164
      },
      "plusCode": "796RWF4F+M4V",
      "plusCodeShort": "WF4F+M4 Praia",
      "lote": {
        "use": "residencial.moradia",
        "kind": "um_edificio",
        "structures": 1,
        "floorAreaM2": 301.7,
        "enclosed": false
      },
      "structures": [
        {
          "index": 1,
          "id": "osm:way/416144875",
          "use": "residencial.moradia",
          "confidence": 0.6,
          "source": "prior:census2021",
          "status": "em_uso",
          "footprintM2": 301.7,
          "perimeterM": 69.6,
          "floors": 1,
          "floorAreaM2": 301.7,
          "data": "osm"
        }
      ],
      "registry": {
        "machine": "PR-0973-1234-0",
        "home": "Palmarejo 12 34",
        "official_name": "Palmarejo",
        "zone": "PR-004",
        "number": "1234",
        "check": "0",
        "status": "provisional",
        "issued": "bulk",
        "issued_at": "2026-10-19T07:40:03Z",
        "entrance_lat": "14.9067372",
        "entrance_lng": "-23.5272164",
        "entrance_kind": "centre",
        "plus_code": "796RWF4F+M4V",
        "use": "residencial.moradia",
        "lote_kind": "um_edificio",
        "structures": "1",
        "floor_area_m2": "301.7",
        "postcode": "",
        "coverage": "",
        "official_address": ""
      },
      "credit": "Home code by N-Ways Addressing",
      "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
    }
  ]
}
```

#### An official street address

```sh
curl -s 'http://localhost:8080/v1/find?q=Avenida%20Santiago%2032%2C%20Praia'
```

`200 OK`

```json
{
  "query": "Avenida Santiago 32, Praia",
  "kind": "official",
  "matches": [
    {
      "country": "CV",
      "machine": "PR-0973-1666-3",
      "home": "Palmarejo 16 66",
      "check": 3,
      "name": "Palmarejo",
      "nameProvisional": false,
      "near": "Monte Vermelho",
      "area": {
        "id": "PR-004",
        "plateName": "Palmarejo",
        "officialName": "Palmarejo"
      },
      "municipality": "Praia",
      "municipalityKey": "PR",
      "island": "Santiago",
      "coverage": "official",
      "officialAddress": "Avenida Santiago 32, Praia",
      "postcode": {
        "value": "7600",
        "kind": "area",
        "source": "UPU addressing sheet 04/2014; Correios HQ address"
      },
      "fullLine": "Palmarejo 16 66 · Praia, Santiago · 7600",
      "written": {
        "big": "Palmarejo 16 66",
        "small": "Praia · Santiago",
        "machine": "PR-0973-1666-3"
      },
      "spoken": "Palmarejo, dezasseis, sessenta e seis",
      "spokenKea": "Palmarejo, dizaseis, sesenta i seis",
      "status": "provisional",
      "issued": "bulk",
      "issuedAt": "2026-10-20T02:26:38Z",
      "entrance": {
        "lat": 14.9128257,
        "lng": -23.5275868,
        "kind": "centre",
        "source": "map"
      },
      "location": {
        "lat": 14.9128257,
        "lng": -23.5275868
      },
      "plusCode": "796RWF7C+4XM",
      "plusCodeShort": "WF7C+4X Praia",
      "lote": {
        "use": "residencial.predio",
        "kind": "um_edificio",
        "structures": 1,
        "floorAreaM2": 541,
        "enclosed": false
      },
      "structures": [
        {
          "index": 1,
          "id": "osm:way/238359065",
          "use": "residencial.predio",
          "confidence": 0.85,
          "source": "osm:building",
          "status": "em_uso",
          "footprintM2": 541,
          "perimeterM": 100.3,
          "floors": 1,
          "floorAreaM2": 541,
          "data": "osm"
        }
      ],
      "registry": {
        "machine": "PR-0973-1666-3",
        "home": "Palmarejo 16 66",
        "official_name": "Palmarejo",
        "zone": "PR-004",
        "number": "1666",
        "check": "3",
        "status": "provisional",
        "issued": "bulk",
        "issued_at": "2026-10-20T02:26:38Z",
        "entrance_lat": "14.9128257",
        "entrance_lng": "-23.5275868",
        "entrance_kind": "centre",
        "plus_code": "796RWF7C+4XM",
        "use": "residencial.predio",
        "lote_kind": "um_edificio",
        "structures": "1",
        "floor_area_m2": "541.0",
        "postcode": "",
        "coverage": "official",
        "official_address": "Avenida Santiago 32, Praia"
      },
      "credit": "Home code by N-Ways Addressing",
      "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
    }
  ]
}
```

#### A spot code with its town

```sh
curl -s 'http://localhost:8080/v1/find?q=WF4F%2BM4%20Praia'
```

`200 OK`

```json
{
  "query": "WF4F+M4 Praia",
  "kind": "spot",
  "spot": {
    "code": "796RWF4F+M4",
    "lat": 14.9066875,
    "lng": -23.5271875,
    "bounds": {
      "south": 14.906625000000002,
      "west": -23.52725,
      "north": 14.906750000000002,
      "east": -23.527124999999998
    },
    "municipality": "Praia",
    "municipalityKey": "PR",
    "island": "Santiago",
    "at": {
      "status": "found",
      "code": {
        "country": "CV",
        "machine": "PR-0973-1234-0",
        "home": "Palmarejo 12 34",
        "check": 0,
        "name": "Palmarejo",
        "nameProvisional": false,
        "near": "Monte Vermelho",
        "area": {
          "id": "PR-004",
          "plateName": "Palmarejo",
          "officialName": "Palmarejo"
        },
        "municipality": "Praia",
        "municipalityKey": "PR",
        "island": "Santiago",
        "postcode": {
          "value": "7600",
          "kind": "area",
          "source": "UPU addressing sheet 04/2014; Correios HQ address"
        },
        "fullLine": "Palmarejo 12 34 · Praia, Santiago · 7600",
        "written": {
          "big": "Palmarejo 12 34",
          "small": "Praia · Santiago",
          "machine": "PR-0973-1234-0"
        },
        "spoken": "Palmarejo, doze, trinta e quatro",
        "spokenKea": "Palmarejo, dozi, trinta i kuatu",
        "status": "provisional",
        "issued": "bulk",
        "issuedAt": "2026-10-19T07:40:03Z",
        "entrance": {
          "lat": 14.9067372,
          "lng": -23.5272164,
          "kind": "centre",
          "source": "map"
        },
        "location": {
          "lat": 14.9067372,
          "lng": -23.5272164
        },
        "plusCode": "796RWF4F+M4V",
        "plusCodeShort": "WF4F+M4 Praia",
        "lote": {
          "use": "residencial.moradia",
          "kind": "um_edificio",
          "structures": 1,
          "floorAreaM2": 301.7,
          "enclosed": false
        },
        "structures": [
          {
            "index": 1,
            "id": "osm:way/416144875",
            "use": "residencial.moradia",
            "confidence": 0.6,
            "source": "prior:census2021",
            "status": "em_uso",
            "footprintM2": 301.7,
            "perimeterM": 69.6,
            "floors": 1,
            "floorAreaM2": 301.7,
            "data": "osm"
          }
        ],
        "registry": {
          "machine": "PR-0973-1234-0",
          "home": "Palmarejo 12 34",
          "official_name": "Palmarejo",
          "zone": "PR-004",
          "number": "1234",
          "check": "0",
          "status": "provisional",
          "issued": "bulk",
          "issued_at": "2026-10-19T07:40:03Z",
          "entrance_lat": "14.9067372",
          "entrance_lng": "-23.5272164",
          "entrance_kind": "centre",
          "plus_code": "796RWF4F+M4V",
          "use": "residencial.moradia",
          "lote_kind": "um_edificio",
          "structures": "1",
          "floor_area_m2": "301.7",
          "postcode": "",
          "coverage": "",
          "official_address": ""
        },
        "credit": "Home code by N-Ways Addressing",
        "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
      },
      "distanceM": 0.0,
      "area": {
        "key": "PR",
        "name": "Praia",
        "island": "Santiago",
        "bbox": [
          -23.5885,
          14.8999,
          -23.4541,
          14.9963
        ]
      }
    }
  }
}
```

#### A wrong check digit

```sh
curl -s 'http://localhost:8080/v1/find?q=PR-0973-1234-1'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "check_digit",
    "message": "The check digit does not match: a digit is wrong or two are swapped. Read the machine code again, or scan the QR code."
  }
}
```

#### A name that is not a place

```sh
curl -s 'http://localhost:8080/v1/find?q=Atlantida%2012%2034'
```

`404 Not Found`

```json
{
  "error": {
    "code": "unknown_name",
    "message": "No place in Cabo Verde has that name: 'Atlantida'."
  }
}
```

#### A number no home has yet

```sh
curl -s 'http://localhost:8080/v1/find?q=Palmarejo%2012%2035'
```

`404 Not Found`

```json
{
  "error": {
    "code": "not_issued",
    "message": "No home has Palmarejo 12 35 yet (the number is in the range of Palmarejo, Praia)."
  }
}
```

#### Not a code

```sh
curl -s 'http://localhost:8080/v1/find?q=hello'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_format",
    "message": "A home code is a place name and a number, e.g. \"Palmarejo 12 34\"."
  }
}
```

#### Nothing to find

```sh
curl -s 'http://localhost:8080/v1/find'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_request",
    "message": "Give something to find: /v1/find?q=Palmarejo 12 34"
  }
}
```

## GET /v1/at?lat=&lng=

The code of the lote at a point: the lote whose footprint holds the point, else the one whose entrance or footprint is nearest within 12 m. Otherwise `status` is `none` with the municipality the point is in, or `outside` at sea.

#### A point on a building

```sh
curl -s 'http://localhost:8080/v1/at?lat=14.9067372&lng=-23.5272164'
```

`200 OK`

```json
{
  "status": "found",
  "code": {
    "country": "CV",
    "machine": "PR-0973-1234-0",
    "home": "Palmarejo 12 34",
    "check": 0,
    "name": "Palmarejo",
    "nameProvisional": false,
    "near": "Monte Vermelho",
    "area": {
      "id": "PR-004",
      "plateName": "Palmarejo",
      "officialName": "Palmarejo"
    },
    "municipality": "Praia",
    "municipalityKey": "PR",
    "island": "Santiago",
    "postcode": {
      "value": "7600",
      "kind": "area",
      "source": "UPU addressing sheet 04/2014; Correios HQ address"
    },
    "fullLine": "Palmarejo 12 34 · Praia, Santiago · 7600",
    "written": {
      "big": "Palmarejo 12 34",
      "small": "Praia · Santiago",
      "machine": "PR-0973-1234-0"
    },
    "spoken": "Palmarejo, doze, trinta e quatro",
    "spokenKea": "Palmarejo, dozi, trinta i kuatu",
    "status": "provisional",
    "issued": "bulk",
    "issuedAt": "2026-10-19T07:40:03Z",
    "entrance": {
      "lat": 14.9067372,
      "lng": -23.5272164,
      "kind": "centre",
      "source": "map"
    },
    "location": {
      "lat": 14.9067372,
      "lng": -23.5272164
    },
    "plusCode": "796RWF4F+M4V",
    "plusCodeShort": "WF4F+M4 Praia",
    "lote": {
      "use": "residencial.moradia",
      "kind": "um_edificio",
      "structures": 1,
      "floorAreaM2": 301.7,
      "enclosed": false
    },
    "structures": [
      {
        "index": 1,
        "id": "osm:way/416144875",
        "use": "residencial.moradia",
        "confidence": 0.6,
        "source": "prior:census2021",
        "status": "em_uso",
        "footprintM2": 301.7,
        "perimeterM": 69.6,
        "floors": 1,
        "floorAreaM2": 301.7,
        "data": "osm"
      }
    ],
    "registry": {
      "machine": "PR-0973-1234-0",
      "home": "Palmarejo 12 34",
      "official_name": "Palmarejo",
      "zone": "PR-004",
      "number": "1234",
      "check": "0",
      "status": "provisional",
      "issued": "bulk",
      "issued_at": "2026-10-19T07:40:03Z",
      "entrance_lat": "14.9067372",
      "entrance_lng": "-23.5272164",
      "entrance_kind": "centre",
      "plus_code": "796RWF4F+M4V",
      "use": "residencial.moradia",
      "lote_kind": "um_edificio",
      "structures": "1",
      "floor_area_m2": "301.7",
      "postcode": "",
      "coverage": "",
      "official_address": ""
    },
    "credit": "Home code by N-Ways Addressing",
    "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
  },
  "distanceM": 0.0,
  "area": {
    "key": "PR",
    "name": "Praia",
    "island": "Santiago",
    "bbox": [
      -23.5885,
      14.8999,
      -23.4541,
      14.9963
    ]
  }
}
```

#### A point with no lote

```sh
curl -s 'http://localhost:8080/v1/at?lat=14.9037&lng=-23.5357'
```

`200 OK`

```json
{
  "status": "none",
  "canIssue": true,
  "building": false,
  "area": {
    "key": "PR",
    "name": "Praia",
    "island": "Santiago",
    "bbox": [
      -23.5885,
      14.8999,
      -23.4541,
      14.9963
    ]
  },
  "spot": "796RWF37+FPM"
}
```

#### At sea

```sh
curl -s 'http://localhost:8080/v1/at?lat=14.87&lng=-23.47'
```

`200 OK`

```json
{
  "status": "outside",
  "note": "At sea or outside Cabo Verde: no code is issued here."
}
```

#### A point that is not one

```sh
curl -s 'http://localhost:8080/v1/at?lat=north&lng=-23.5'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_request",
    "message": "lat and lng are required, in decimal degrees (lat=14.9177&lng=-23.5372)."
  }
}
```

## GET /v1/near?lat=&lng=&radius=&limit=

Codes whose entrance is within `radius` metres (default 100, at most 500), nearest first, at most `limit` (default 20, at most 100).

#### Codes near a point

```sh
curl -s 'http://localhost:8080/v1/near?lat=14.9067372&lng=-23.5272164&radius=40&limit=3'
```

`200 OK`

```json
{
  "lat": 14.9067372,
  "lng": -23.5272164,
  "radiusM": 40.0,
  "count": 2,
  "codes": [
    {
      "machine": "PR-0973-1234-0",
      "home": "Palmarejo 12 34",
      "distanceM": 0.0,
      "status": "provisional",
      "use": "residencial.moradia",
      "entrance": {
        "lat": 14.9067372,
        "lng": -23.5272164,
        "kind": "centre"
      },
      "plusCode": "796RWF4F+M4V"
    },
    {
      "machine": "PR-0973-1237-9",
      "home": "Palmarejo 12 37",
      "distanceM": 32.9,
      "status": "provisional",
      "use": "residencial.moradia",
      "entrance": {
        "lat": 14.906888,
        "lng": -23.5269535,
        "kind": "centre"
      },
      "plusCode": "796RWF4F+Q63"
    }
  ]
}
```

#### Too far

```sh
curl -s 'http://localhost:8080/v1/near?lat=14.9067372&lng=-23.5272164&radius=900'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_request",
    "message": "radius is between 1 and 500 metres."
  }
}
```

## GET /v1/verify?code=

Checks a machine code: its syntax, its check digit and whether it is issued.

#### An issued code

```sh
curl -s 'http://localhost:8080/v1/verify?code=PR-0973-1234-0'
```

`200 OK`

```json
{
  "code": "PR-0973-1234-0",
  "syntax": true,
  "checkDigit": true,
  "issued": true,
  "machine": "PR-0973-1234-0",
  "status": "provisional",
  "home": "Palmarejo 12 34",
  "issuedAt": "2026-10-19T07:40:03Z"
}
```

#### A wrong check digit

```sh
curl -s 'http://localhost:8080/v1/verify?code=PR-0973-1234-7'
```

`200 OK`

```json
{
  "code": "PR-0973-1234-7",
  "syntax": true,
  "checkDigit": false,
  "issued": false,
  "reason": "The check digit does not match: a digit is wrong or two are swapped."
}
```

#### Well formed, not issued

```sh
curl -s 'http://localhost:8080/v1/verify?code=PR-0973-1235-4'
```

`200 OK`

```json
{
  "code": "PR-0973-1235-4",
  "syntax": true,
  "checkDigit": true,
  "issued": false,
  "machine": "PR-0973-1235-4",
  "reason": "Well formed, but no code with this number has been issued."
}
```

#### Not a machine code

```sh
curl -s 'http://localhost:8080/v1/verify?code=Palmarejo%2012%2034'
```

`200 OK`

```json
{
  "code": "Palmarejo 12 34",
  "syntax": false,
  "checkDigit": null,
  "issued": false,
  "reason": "Not a machine code: KEY-NNNN-NUMBER-C, like PR-0973-1234-0."
}
```

#### Nothing to verify

```sh
curl -s 'http://localhost:8080/v1/verify'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_request",
    "message": "Give a machine code: /v1/verify?code=PR-0973-1234-0"
  }
}
```

## GET /v1/spot?lat=&lng= and GET /v1/spot/decode?code=

The spot code of a point (an 11-character Plus Code, about 3 m, and its short form with the municipal seat), and back.

#### The spot code of a point

```sh
curl -s 'http://localhost:8080/v1/spot?lat=14.9067372&lng=-23.5272164'
```

`200 OK`

```json
{
  "lat": 14.9067372,
  "lng": -23.5272164,
  "code": "796RWF4F+M4V",
  "code10": "796RWF4F+M4",
  "short": "WF4F+M4 Praia",
  "municipality": "Praia",
  "municipalityKey": "PR",
  "island": "Santiago",
  "postcode": {
    "value": "7600",
    "kind": "area",
    "source": "UPU addressing sheet 04/2014; Correios HQ address"
  },
  "bounds": {
    "south": 14.906725000000002,
    "west": -23.52721875,
    "north": 14.906750000000002,
    "east": -23.5271875
  }
}
```

#### At sea

```sh
curl -s 'http://localhost:8080/v1/spot?lat=14.87&lng=-23.47'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "outside",
    "message": "At sea or outside Cabo Verde: no spot code is issued here."
  }
}
```

#### Decoding a short spot code

```sh
curl -s 'http://localhost:8080/v1/spot/decode?code=WF4F%2BM4%20Praia'
```

`200 OK`

```json
{
  "code": "796RWF4F+M4",
  "lat": 14.9066875,
  "lng": -23.5271875,
  "bounds": {
    "south": 14.906625000000002,
    "west": -23.52725,
    "north": 14.906750000000002,
    "east": -23.527124999999998
  },
  "municipality": "Praia",
  "municipalityKey": "PR",
  "island": "Santiago",
  "at": {
    "status": "found",
    "code": {
      "country": "CV",
      "machine": "PR-0973-1234-0",
      "home": "Palmarejo 12 34",
      "check": 0,
      "name": "Palmarejo",
      "nameProvisional": false,
      "near": "Monte Vermelho",
      "area": {
        "id": "PR-004",
        "plateName": "Palmarejo",
        "officialName": "Palmarejo"
      },
      "municipality": "Praia",
      "municipalityKey": "PR",
      "island": "Santiago",
      "postcode": {
        "value": "7600",
        "kind": "area",
        "source": "UPU addressing sheet 04/2014; Correios HQ address"
      },
      "fullLine": "Palmarejo 12 34 · Praia, Santiago · 7600",
      "written": {
        "big": "Palmarejo 12 34",
        "small": "Praia · Santiago",
        "machine": "PR-0973-1234-0"
      },
      "spoken": "Palmarejo, doze, trinta e quatro",
      "spokenKea": "Palmarejo, dozi, trinta i kuatu",
      "status": "provisional",
      "issued": "bulk",
      "issuedAt": "2026-10-19T07:40:03Z",
      "entrance": {
        "lat": 14.9067372,
        "lng": -23.5272164,
        "kind": "centre",
        "source": "map"
      },
      "location": {
        "lat": 14.9067372,
        "lng": -23.5272164
      },
      "plusCode": "796RWF4F+M4V",
      "plusCodeShort": "WF4F+M4 Praia",
      "lote": {
        "use": "residencial.moradia",
        "kind": "um_edificio",
        "structures": 1,
        "floorAreaM2": 301.7,
        "enclosed": false
      },
      "structures": [
        {
          "index": 1,
          "id": "osm:way/416144875",
          "use": "residencial.moradia",
          "confidence": 0.6,
          "source": "prior:census2021",
          "status": "em_uso",
          "footprintM2": 301.7,
          "perimeterM": 69.6,
          "floors": 1,
          "floorAreaM2": 301.7,
          "data": "osm"
        }
      ],
      "registry": {
        "machine": "PR-0973-1234-0",
        "home": "Palmarejo 12 34",
        "official_name": "Palmarejo",
        "zone": "PR-004",
        "number": "1234",
        "check": "0",
        "status": "provisional",
        "issued": "bulk",
        "issued_at": "2026-10-19T07:40:03Z",
        "entrance_lat": "14.9067372",
        "entrance_lng": "-23.5272164",
        "entrance_kind": "centre",
        "plus_code": "796RWF4F+M4V",
        "use": "residencial.moradia",
        "lote_kind": "um_edificio",
        "structures": "1",
        "floor_area_m2": "301.7",
        "postcode": "",
        "coverage": "",
        "official_address": ""
      },
      "credit": "Home code by N-Ways Addressing",
      "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
    },
    "distanceM": 0.0,
    "area": {
      "key": "PR",
      "name": "Praia",
      "island": "Santiago",
      "bbox": [
        -23.5885,
        14.8999,
        -23.4541,
        14.9963
      ]
    }
  }
}
```

#### Not a spot code

```sh
curl -s 'http://localhost:8080/v1/spot/decode?code=hello'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_format",
    "message": "A spot code is a full Plus Code (796RWF8Q+2V8) or a short one with its town (WF8Q+2V Praia)."
  }
}
```

#### A town that is not a municipal seat

```sh
curl -s 'http://localhost:8080/v1/spot/decode?code=WF4F%2BM4%20Lisboa'
```

`404 Not Found`

```json
{
  "error": {
    "code": "unknown_place",
    "message": "Lisboa is not a municipality or its seat."
  }
}
```

## GET /v1/zones and GET /v1/zones/{key}

The registry is published per municipality (concelho), so the API calls a municipality a *zone*; its key is the ISO 3166-2:CV suffix (`PR` for Praia). The named places inside it, which the engine specification calls zones (bairros, zonas, povoações), are the API's *areas*.

#### Every municipality

```sh
curl -s 'http://localhost:8080/v1/zones'
```

`200 OK` (lists shortened to their first entries)

```json
{
  "zones": [
    {
      "key": "BR",
      "iso": "CV-BR",
      "name": "Brava",
      "island": "Brava",
      "postcode": {
        "value": "9110",
        "kind": "area",
        "source": "OpenStreetMap addr:postcode"
      },
      "seat": "Nova Sintra",
      "bbox": [
        -24.749,
        14.8032,
        -24.6284,
        14.9841
      ],
      "codes": 2900,
      "byStatus": {
        "provisional": 2900
      },
      "areas": 36
    },
    {
      "key": "BV",
      "iso": "CV-BV",
      "name": "Boa Vista",
      "island": "Boa Vista",
      "postcode": {
        "value": "5110",
        "kind": "area",
        "source": "OpenStreetMap addr:postcode"
      },
      "seat": "Sal Rei",
      "bbox": [
        -22.966,
        15.9678,
        -22.6673,
        16.2306
      ],
      "codes": 4867,
      "byStatus": {
        "provisional": 4867
      },
      "areas": 61
    }
  ]
}
```

#### One municipality with its areas

```sh
curl -s 'http://localhost:8080/v1/zones/BR'
```

`200 OK` (lists shortened to their first entries)

```json
{
  "key": "BR",
  "iso": "CV-BR",
  "name": "Brava",
  "island": "Brava",
  "postcode": {
    "value": "9110",
    "kind": "area",
    "source": "OpenStreetMap addr:postcode"
  },
  "seat": "Nova Sintra",
  "bbox": [
    -24.749,
    14.8032,
    -24.6284,
    14.9841
  ],
  "codes": 2900,
  "byStatus": {
    "provisional": 2900
  },
  "areas": 36,
  "areaList": [
    {
      "id": "BR-001",
      "municipality": "BR",
      "plateName": "Vereda",
      "officialName": "Vereda",
      "nameIndex": 1338,
      "needsCouncilChoice": false,
      "codes": 39
    },
    {
      "id": "BR-002",
      "municipality": "BR",
      "plateName": "Poio Preto",
      "officialName": "Achada do Poio Preto",
      "nameIndex": 1058,
      "needsCouncilChoice": false,
      "codes": 23
    },
    {
      "id": "BR-003",
      "municipality": "BR",
      "plateName": "Pathal",
      "officialName": "Pathal",
      "nameIndex": 985,
      "needsCouncilChoice": false,
      "codes": 37
    }
  ]
}
```

#### An unknown key

```sh
curl -s 'http://localhost:8080/v1/zones/XX'
```

`404 Not Found`

```json
{
  "error": {
    "code": "unknown_zone",
    "message": "There is no municipality 'XX'. The keys are BR, BV, CA, CF, CR, MA, MO, PA, PN, PR, RB, RG, RS, SD, SF, SL, SM, SO, SS, SV, TA, TS."
  }
}
```

## GET /v1/zones/{key}/codes?after=&limit=

Every code of a municipality, in machine-code order, a page at a time (`limit` up to 1000). Pass the `next` of one page as `after` to get the following one; `next` is null on the last page.

#### First page

```sh
curl -s 'http://localhost:8080/v1/zones/BR/codes?limit=2'
```

`200 OK`

```json
{
  "zone": "BR",
  "count": 2,
  "next": "BR-0117-1006-2",
  "codes": [
    {
      "machine": "BR-0117-1002-4",
      "home": "Baleia 10 02",
      "area": "BR-036",
      "number": 1002,
      "status": "provisional",
      "lat": 14.847437,
      "lng": -24.6824147,
      "plusCode": "796QR8W9+X2G",
      "use": "residencial.moradia"
    },
    {
      "machine": "BR-0117-1006-2",
      "home": "Baleia 10 06",
      "area": "BR-036",
      "number": 1006,
      "status": "provisional",
      "lat": 14.8490668,
      "lng": -24.682251,
      "plusCode": "796QR8X9+J3H",
      "use": "agricola"
    }
  ]
}
```

#### Next page

```sh
curl -s 'http://localhost:8080/v1/zones/BR/codes?limit=2&after=BR-0117-1006-2'
```

`200 OK`

```json
{
  "zone": "BR",
  "count": 2,
  "next": "BR-0117-1014-5",
  "codes": [
    {
      "machine": "BR-0117-1010-0",
      "home": "Baleia 10 10",
      "area": "BR-036",
      "number": 1010,
      "status": "provisional",
      "lat": 14.8545906,
      "lng": -24.691364,
      "plusCode": "796QV835+RFJ",
      "use": "residencial.moradia"
    },
    {
      "machine": "BR-0117-1014-5",
      "home": "Baleia 10 14",
      "area": "BR-036",
      "number": 1014,
      "status": "provisional",
      "lat": 14.8571459,
      "lng": -24.6882426,
      "plusCode": "796QV846+VP2",
      "use": "residencial.moradia"
    }
  ]
}
```

#### A bad limit

```sh
curl -s 'http://localhost:8080/v1/zones/BR/codes?limit=5000'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_request",
    "message": "limit is between 1 and 1000."
  }
}
```

## GET /v1/areas/{id} and GET /v1/areas?name=

A named place: its plate and official names, its blocks in the national range of its name, and its counts. A search by name matches the plate name, the official name and every alias, with or without accents.

#### An area

```sh
curl -s 'http://localhost:8080/v1/areas/PR-004'
```

`200 OK`

```json
{
  "id": "PR-004",
  "municipality": {
    "key": "PR",
    "name": "Praia",
    "island": "Santiago"
  },
  "plateName": "Palmarejo",
  "officialName": "Palmarejo",
  "plateRule": "as-is",
  "needsCouncilChoice": false,
  "aliases": [],
  "near": "Monte Vermelho",
  "nameKey": "palmarejo",
  "nameIndex": 973,
  "box": [
    -23.53404,
    14.90097,
    -23.51928,
    14.91902
  ],
  "anchor": [
    14.912684,
    -23.526747
  ],
  "blocks": [
    {
      "lo": 1000,
      "hi": 3899
    }
  ],
  "name": {
    "plateName": "Palmarejo",
    "digits": 4,
    "reserve": [
      5600,
      9999
    ],
    "blocks": [
      {
        "zone": "PR-004",
        "lo": 1000,
        "hi": 3899
      },
      {
        "zone": "PR-006",
        "lo": 3900,
        "hi": 5599
      }
    ],
    "officialNames": [
      "Palmarejo",
      "Palmarejo Grande"
    ]
  },
  "codes": 938,
  "byStatus": {
    "provisional": 938
  }
}
```

#### Areas by name (one name, five places)

```sh
curl -s 'http://localhost:8080/v1/areas?name=fazenda'
```

`200 OK` (lists shortened to their first entries)

```json
{
  "name": "fazenda",
  "areas": [
    {
      "id": "CR-078",
      "municipality": "CR",
      "plateName": "Fazenda",
      "officialName": "Achada Fazenda",
      "nameIndex": 534,
      "needsCouncilChoice": false,
      "codes": 309
    },
    {
      "id": "PA-005",
      "municipality": "PA",
      "plateName": "Fazenda",
      "officialName": "Chã de Fazenda",
      "nameIndex": 534,
      "needsCouncilChoice": false,
      "codes": 59
    },
    {
      "id": "PR-049",
      "municipality": "PR",
      "plateName": "Fazenda",
      "officialName": "Fazenda",
      "nameIndex": 534,
      "needsCouncilChoice": false,
      "codes": 229
    }
  ],
  "count": 7
}
```

#### An official name finds its plate name

```sh
curl -s 'http://localhost:8080/v1/areas?name=Lote%20Achada%20S%C3%A3o%20Filipe'
```

`200 OK`

```json
{
  "name": "Lote Achada São Filipe",
  "areas": [
    {
      "id": "PR-024",
      "municipality": "PR",
      "plateName": "São Filipe",
      "officialName": "Lote Achada São Filipe",
      "nameIndex": 1221,
      "needsCouncilChoice": true,
      "codes": 585
    }
  ],
  "count": 1
}
```

#### An unknown area

```sh
curl -s 'http://localhost:8080/v1/areas/PR-999'
```

`404 Not Found`

```json
{
  "error": {
    "code": "unknown_area",
    "message": "There is no area 'PR-999'. Area ids look like PR-024."
  }
}
```

#### No name given

```sh
curl -s 'http://localhost:8080/v1/areas'
```

`400 Bad Request`

```json
{
  "error": {
    "code": "bad_request",
    "message": "Give a place name: /v1/areas?name=Palmarejo"
  }
}
```

## POST /v1/codes

Issues a code for a building that has none (a new building) or for another door of a lote (`of`). Needs an issuer key, and only a designated issuer has keys (see server/README.md).

#### A new building, with its outline

```sh
curl -s -X POST 'http://localhost:8080/v1/codes' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"lat": 14.9037, "lng": -23.5357, "outline": [[-23.53574, 14.90366], [-23.53566, 14.90366], [-23.53566, 14.90374], [-23.53574, 14.90374]]}'
```

`201 Created`

```json
{
  "country": "CV",
  "machine": "PR-0364-3982-3",
  "home": "Cidadela 39 82",
  "check": 3,
  "name": "Cidadela",
  "nameProvisional": false,
  "area": {
    "id": "PR-002",
    "plateName": "Cidadela",
    "officialName": "Cidadela"
  },
  "municipality": "Praia",
  "municipalityKey": "PR",
  "island": "Santiago",
  "postcode": {
    "value": "7600",
    "kind": "area",
    "source": "UPU addressing sheet 04/2014; Correios HQ address"
  },
  "fullLine": "Cidadela 39 82 · Praia, Santiago · 7600",
  "written": {
    "big": "Cidadela 39 82",
    "small": "Praia · Santiago",
    "machine": "PR-0364-3982-3"
  },
  "spoken": "Cidadela, trinta e nove, oitenta e dois",
  "spokenKea": "Cidadela, trinta i novi, oitenta i dos",
  "status": "provisional",
  "issued": "on-demand",
  "issuedAt": "2026-10-21T13:53:06Z",
  "entrance": {
    "lat": 14.9037,
    "lng": -23.5357,
    "kind": "centre",
    "source": "map"
  },
  "location": {
    "lat": 14.9037,
    "lng": -23.5357
  },
  "plusCode": "796RWF37+FPM",
  "plusCodeShort": "WF37+FP Praia",
  "lote": {
    "use": "residencial.moradia",
    "kind": "um_edificio",
    "structures": 1,
    "floorAreaM2": 76.6,
    "enclosed": false
  },
  "structures": [
    {
      "index": 1,
      "id": "people:PR-0364-3982-3",
      "use": "residencial.moradia",
      "confidence": 0.6,
      "source": "prior:census2021",
      "status": "em_uso",
      "footprintM2": 76.6,
      "perimeterM": 35,
      "floors": 1,
      "floorAreaM2": 76.6,
      "data": "people"
    }
  ],
  "registry": {
    "machine": "PR-0364-3982-3",
    "home": "Cidadela 39 82",
    "official_name": "Cidadela",
    "zone": "PR-002",
    "number": "3982",
    "check": "3",
    "status": "provisional",
    "issued": "on-demand",
    "issued_at": "2026-10-21T13:53:06Z",
    "entrance_lat": "14.9037000",
    "entrance_lng": "-23.5357000",
    "entrance_kind": "centre",
    "plus_code": "796RWF37+FPM",
    "use": "residencial.moradia",
    "lote_kind": "um_edificio",
    "structures": "1",
    "floor_area_m2": "76.6",
    "postcode": "",
    "coverage": "",
    "official_address": ""
  },
  "credit": "Home code by N-Ways Addressing",
  "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
}
```

#### The same building again

The refusal carries the card of the code the building already has (shortened here).

```sh
curl -s -X POST 'http://localhost:8080/v1/codes' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"lat": 14.90371, "lng": -23.53571}'
```

`409 Conflict`

```json
{
  "error": {
    "code": "exists",
    "message": "This building already has its code: Cidadela 39 82."
  },
  "card": {
    "country": "CV",
    "machine": "PR-0364-3982-3",
    "home": "Cidadela 39 82",
    "check": 3,
    "name": "Cidadela",
    "nameProvisional": false,
    "area": {
      "id": "PR-002",
      "plateName": "Cidadela",
      "officialName": "Cidadela"
    },
    "municipality": "Praia",
    "municipalityKey": "PR",
    "island": "Santiago",
    "postcode": {
      "value": "7600",
      "kind": "area",
      "source": "UPU addressing sheet 04/2014; Correios HQ address"
    },
    "fullLine": "Cidadela 39 82 · Praia, Santiago · 7600",
    "written": {
      "big": "Cidadela 39 82",
      "small": "Praia · Santiago",
      "machine": "PR-0364-3982-3"
    },
    "spoken": "Cidadela, trinta e nove, oitenta e dois",
    "spokenKea": "Cidadela, trinta i novi, oitenta i dos",
    "status": "provisional",
    "issued": "on-demand",
    "issuedAt": "2026-10-21T13:53:06Z",
    "entrance": {
      "lat": 14.9037,
      "lng": -23.5357,
      "kind": "centre",
      "source": "map"
    },
    "location": {
      "lat": 14.9037,
      "lng": -23.5357
    },
    "plusCode": "796RWF37+FPM",
    "plusCodeShort": "WF37+FP Praia",
    "lote": {
      "use": "residencial.moradia",
      "kind": "um_edificio",
      "structures": 1,
      "floorAreaM2": 76.6,
      "enclosed": false
    },
    "structures": [
      {
        "index": 1,
        "id": "people:PR-0364-3982-3",
        "use": "residencial.moradia",
        "confidence": 0.6,
        "source": "prior:census2021",
        "status": "em_uso",
        "footprintM2": 76.6,
        "perimeterM": 35,
        "floors": 1,
        "floorAreaM2": 76.6,
        "data": "people"
      }
    ],
    "registry": {
      "machine": "PR-0364-3982-3",
      "home": "Cidadela 39 82",
      "official_name": "Cidadela",
      "zone": "PR-002",
      "number": "3982",
      "check": "3",
      "status": "provisional",
      "issued": "on-demand",
      "issued_at": "2026-10-21T13:53:06Z",
      "entrance_lat": "14.9037000",
      "entrance_lng": "-23.5357000",
      "entrance_kind": "centre",
      "plus_code": "796RWF37+FPM",
      "use": "residencial.moradia",
      "lote_kind": "um_edificio",
      "structures": "1",
      "floor_area_m2": "76.6",
      "postcode": "",
      "coverage": "",
      "official_address": ""
    },
    "credit": "Home code by N-Ways Addressing",
    "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
  }
}
```

#### Another door of a lote

```sh
curl -s -X POST 'http://localhost:8080/v1/codes' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"lat": 14.9068, "lng": -23.52715, "of": "PR-0973-1234-0"}'
```

`201 Created`

```json
{
  "country": "CV",
  "machine": "PR-0973-1232-2",
  "home": "Palmarejo 12 32",
  "check": 2,
  "name": "Palmarejo",
  "nameProvisional": false,
  "near": "Monte Vermelho",
  "area": {
    "id": "PR-004",
    "plateName": "Palmarejo",
    "officialName": "Palmarejo"
  },
  "municipality": "Praia",
  "municipalityKey": "PR",
  "island": "Santiago",
  "postcode": {
    "value": "7600",
    "kind": "area",
    "source": "UPU addressing sheet 04/2014; Correios HQ address"
  },
  "fullLine": "Palmarejo 12 32 · Praia, Santiago · 7600",
  "written": {
    "big": "Palmarejo 12 32",
    "small": "Praia · Santiago",
    "machine": "PR-0973-1232-2"
  },
  "spoken": "Palmarejo, doze, trinta e dois",
  "spokenKea": "Palmarejo, dozi, trinta i dos",
  "status": "provisional",
  "issued": "on-demand",
  "issuedAt": "2026-10-21T13:53:06Z",
  "entrance": {
    "lat": 14.9068,
    "lng": -23.52715,
    "kind": "door",
    "source": "map"
  },
  "location": {
    "lat": 14.9068,
    "lng": -23.52715
  },
  "plusCode": "796RWF4F+P4H",
  "plusCodeShort": "WF4F+P4 Praia",
  "lote": {
    "use": "",
    "kind": "porta",
    "structures": 0,
    "floorAreaM2": 0,
    "enclosed": false
  },
  "structures": [],
  "registry": {
    "machine": "PR-0973-1232-2",
    "home": "Palmarejo 12 32",
    "official_name": "Palmarejo",
    "zone": "PR-004",
    "number": "1232",
    "check": "2",
    "status": "provisional",
    "issued": "on-demand",
    "issued_at": "2026-10-21T13:53:06Z",
    "entrance_lat": "14.9068000",
    "entrance_lng": "-23.5271500",
    "entrance_kind": "door",
    "plus_code": "796RWF4F+P4H",
    "use": "",
    "lote_kind": "porta",
    "structures": "0",
    "floor_area_m2": "0.0",
    "postcode": "",
    "coverage": "",
    "official_address": ""
  },
  "credit": "Home code by N-Ways Addressing",
  "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
}
```

#### A door too far from its lote

```sh
curl -s -X POST 'http://localhost:8080/v1/codes' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"lat": 14.92, "lng": -23.5266, "of": "PR-0973-1234-0"}'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "too_far",
    "message": "That door is more than 80 m from Palmarejo 12 34."
  }
}
```

#### An outline too small for a building

```sh
curl -s -X POST 'http://localhost:8080/v1/codes' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"lat": 14.904, "lng": -23.536, "outline": [[-23.536, 14.904], [-23.53599, 14.904], [-23.53599, 14.90401]]}'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "bad_outline",
    "message": "That outline is 1 m², but a building is between 12 m² and 2 ha."
  }
}
```

#### At sea

```sh
curl -s -X POST 'http://localhost:8080/v1/codes' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"lat": 14.87, "lng": -23.47}'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "outside",
    "message": "That spot is at sea or outside Cabo Verde, so it cannot have a code."
  }
}
```

#### More than 300 m outside the national border

The border decides: a point more than 300 m outside Cabo Verde's national border (the OpenStreetMap admin_level 2 boundary) never gets a code, whatever the other rules allow.

```sh
curl -s -X POST 'http://localhost:8080/v1/codes' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"lat": 15.5, "lng": -27.0}'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "outside",
    "message": "That spot is more than 300 m outside the national border of Cabo Verde, so it cannot have a Cabo Verde code."
  }
}
```

#### No key

```sh
curl -s -X POST 'http://localhost:8080/v1/codes' \
  -H 'Content-Type: application/json' \
  -d '{"lat": 14.9037, "lng": -23.5357}'
```

`401 Unauthorized`

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Issuing needs an issuer key: Authorization: Bearer <key>."
  }
}
```

## PATCH /v1/codes/{machine}

Confirms or retires a code, or moves its entrance (at most 80 m). A retired code stays retired and its number is never given again. Needs an issuer key.

#### Confirm

```sh
curl -s -X PATCH 'http://localhost:8080/v1/codes/PR-0364-3982-3' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"status": "confirmed"}'
```

`200 OK`

```json
{
  "country": "CV",
  "machine": "PR-0364-3982-3",
  "home": "Cidadela 39 82",
  "check": 3,
  "name": "Cidadela",
  "nameProvisional": false,
  "area": {
    "id": "PR-002",
    "plateName": "Cidadela",
    "officialName": "Cidadela"
  },
  "municipality": "Praia",
  "municipalityKey": "PR",
  "island": "Santiago",
  "postcode": {
    "value": "7600",
    "kind": "area",
    "source": "UPU addressing sheet 04/2014; Correios HQ address"
  },
  "fullLine": "Cidadela 39 82 · Praia, Santiago · 7600",
  "written": {
    "big": "Cidadela 39 82",
    "small": "Praia · Santiago",
    "machine": "PR-0364-3982-3"
  },
  "spoken": "Cidadela, trinta e nove, oitenta e dois",
  "spokenKea": "Cidadela, trinta i novi, oitenta i dos",
  "status": "confirmed",
  "issued": "on-demand",
  "issuedAt": "2026-10-21T13:53:06Z",
  "entrance": {
    "lat": 14.9037,
    "lng": -23.5357,
    "kind": "centre",
    "source": "map"
  },
  "location": {
    "lat": 14.9037,
    "lng": -23.5357
  },
  "plusCode": "796RWF37+FPM",
  "plusCodeShort": "WF37+FP Praia",
  "lote": {
    "use": "residencial.moradia",
    "kind": "um_edificio",
    "structures": 1,
    "floorAreaM2": 76.6,
    "enclosed": false
  },
  "structures": [
    {
      "index": 1,
      "id": "people:PR-0364-3982-3",
      "use": "residencial.moradia",
      "confidence": 0.6,
      "source": "prior:census2021",
      "status": "em_uso",
      "footprintM2": 76.6,
      "perimeterM": 35,
      "floors": 1,
      "floorAreaM2": 76.6,
      "data": "people"
    }
  ],
  "registry": {
    "machine": "PR-0364-3982-3",
    "home": "Cidadela 39 82",
    "official_name": "Cidadela",
    "zone": "PR-002",
    "number": "3982",
    "check": "3",
    "status": "confirmed",
    "issued": "on-demand",
    "issued_at": "2026-10-21T13:53:06Z",
    "entrance_lat": "14.9037000",
    "entrance_lng": "-23.5357000",
    "entrance_kind": "centre",
    "plus_code": "796RWF37+FPM",
    "use": "residencial.moradia",
    "lote_kind": "um_edificio",
    "structures": "1",
    "floor_area_m2": "76.6",
    "postcode": "",
    "coverage": "",
    "official_address": ""
  },
  "credit": "Home code by N-Ways Addressing",
  "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
}
```

#### Move the entrance to the gate

```sh
curl -s -X PATCH 'http://localhost:8080/v1/codes/PR-0364-3982-3' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"entrance": {"lat": 14.90364, "lng": -23.5357, "kind": "gate"}}'
```

`200 OK`

```json
{
  "country": "CV",
  "machine": "PR-0364-3982-3",
  "home": "Cidadela 39 82",
  "check": 3,
  "name": "Cidadela",
  "nameProvisional": false,
  "area": {
    "id": "PR-002",
    "plateName": "Cidadela",
    "officialName": "Cidadela"
  },
  "municipality": "Praia",
  "municipalityKey": "PR",
  "island": "Santiago",
  "postcode": {
    "value": "7600",
    "kind": "area",
    "source": "UPU addressing sheet 04/2014; Correios HQ address"
  },
  "fullLine": "Cidadela 39 82 · Praia, Santiago · 7600",
  "written": {
    "big": "Cidadela 39 82",
    "small": "Praia · Santiago",
    "machine": "PR-0364-3982-3"
  },
  "spoken": "Cidadela, trinta e nove, oitenta e dois",
  "spokenKea": "Cidadela, trinta i novi, oitenta i dos",
  "status": "confirmed",
  "issued": "on-demand",
  "issuedAt": "2026-10-21T13:53:06Z",
  "entrance": {
    "lat": 14.90364,
    "lng": -23.5357,
    "kind": "gate",
    "source": "people"
  },
  "location": {
    "lat": 14.90364,
    "lng": -23.5357
  },
  "plusCode": "796RWF37+FP3",
  "plusCodeShort": "WF37+FP Praia",
  "lote": {
    "use": "residencial.moradia",
    "kind": "um_edificio",
    "structures": 1,
    "floorAreaM2": 76.6,
    "enclosed": false
  },
  "structures": [
    {
      "index": 1,
      "id": "people:PR-0364-3982-3",
      "use": "residencial.moradia",
      "confidence": 0.6,
      "source": "prior:census2021",
      "status": "em_uso",
      "footprintM2": 76.6,
      "perimeterM": 35,
      "floors": 1,
      "floorAreaM2": 76.6,
      "data": "people"
    }
  ],
  "registry": {
    "machine": "PR-0364-3982-3",
    "home": "Cidadela 39 82",
    "official_name": "Cidadela",
    "zone": "PR-002",
    "number": "3982",
    "check": "3",
    "status": "confirmed",
    "issued": "on-demand",
    "issued_at": "2026-10-21T13:53:06Z",
    "entrance_lat": "14.9036400",
    "entrance_lng": "-23.5357000",
    "entrance_kind": "gate",
    "plus_code": "796RWF37+FP3",
    "use": "residencial.moradia",
    "lote_kind": "um_edificio",
    "structures": "1",
    "floor_area_m2": "76.6",
    "postcode": "",
    "coverage": "",
    "official_address": ""
  },
  "credit": "Home code by N-Ways Addressing",
  "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
}
```

#### Too far

```sh
curl -s -X PATCH 'http://localhost:8080/v1/codes/PR-0364-3982-3' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"entrance": {"lat": 14.905, "lng": -23.5357}}'
```

`422 Unprocessable Content`

```json
{
  "error": {
    "code": "too_far",
    "message": "The new entrance is 151 m away; an entrance moves at most 80 m."
  }
}
```

#### Retire

```sh
curl -s -X PATCH 'http://localhost:8080/v1/codes/PR-0364-3982-3' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"status": "retired"}'
```

`200 OK`

```json
{
  "country": "CV",
  "machine": "PR-0364-3982-3",
  "home": "Cidadela 39 82",
  "check": 3,
  "name": "Cidadela",
  "nameProvisional": false,
  "area": {
    "id": "PR-002",
    "plateName": "Cidadela",
    "officialName": "Cidadela"
  },
  "municipality": "Praia",
  "municipalityKey": "PR",
  "island": "Santiago",
  "postcode": {
    "value": "7600",
    "kind": "area",
    "source": "UPU addressing sheet 04/2014; Correios HQ address"
  },
  "fullLine": "Cidadela 39 82 · Praia, Santiago · 7600",
  "written": {
    "big": "Cidadela 39 82",
    "small": "Praia · Santiago",
    "machine": "PR-0364-3982-3"
  },
  "spoken": "Cidadela, trinta e nove, oitenta e dois",
  "spokenKea": "Cidadela, trinta i novi, oitenta i dos",
  "status": "retired",
  "issued": "on-demand",
  "issuedAt": "2026-10-21T13:53:06Z",
  "entrance": {
    "lat": 14.90364,
    "lng": -23.5357,
    "kind": "gate",
    "source": "people"
  },
  "location": {
    "lat": 14.90364,
    "lng": -23.5357
  },
  "plusCode": "796RWF37+FP3",
  "plusCodeShort": "WF37+FP Praia",
  "lote": {
    "use": "residencial.moradia",
    "kind": "um_edificio",
    "structures": 1,
    "floorAreaM2": 76.6,
    "enclosed": false
  },
  "structures": [
    {
      "index": 1,
      "id": "people:PR-0364-3982-3",
      "use": "residencial.moradia",
      "confidence": 0.6,
      "source": "prior:census2021",
      "status": "em_uso",
      "footprintM2": 76.6,
      "perimeterM": 35,
      "floors": 1,
      "floorAreaM2": 76.6,
      "data": "people"
    }
  ],
  "registry": {
    "machine": "PR-0364-3982-3",
    "home": "Cidadela 39 82",
    "official_name": "Cidadela",
    "zone": "PR-002",
    "number": "3982",
    "check": "3",
    "status": "retired",
    "issued": "on-demand",
    "issued_at": "2026-10-21T13:53:06Z",
    "entrance_lat": "14.9036400",
    "entrance_lng": "-23.5357000",
    "entrance_kind": "gate",
    "plus_code": "796RWF37+FP3",
    "use": "residencial.moradia",
    "lote_kind": "um_edificio",
    "structures": "1",
    "floor_area_m2": "76.6",
    "postcode": "",
    "coverage": "",
    "official_address": ""
  },
  "credit": "Home code by N-Ways Addressing",
  "creditUrl": "https://github.com/n-ways/open-addresses-cabo-verde"
}
```

#### A retired code

```sh
curl -s -X PATCH 'http://localhost:8080/v1/codes/PR-0364-3982-3' \
  -H 'Authorization: Bearer example-issuer-key' \
  -H 'Content-Type: application/json' \
  -d '{"status": "confirmed"}'
```

`409 Conflict`

```json
{
  "error": {
    "code": "retired",
    "message": "Cidadela 39 82 is retired. A retired code stays retired and its number is never given again."
  }
}
```

## Errors common to every endpoint


#### An unknown path

```sh
curl -s 'http://localhost:8080/v1/addresses'
```

`404 Not Found`

```json
{
  "error": {
    "code": "not_found",
    "message": "There is no endpoint /v1/addresses. See /v1/info and docs/api.md."
  }
}
```

#### A method the path does not take

```sh
curl -s -X DELETE 'http://localhost:8080/v1/codes/PR-0973-1234-0'
```

`405 Method Not Allowed`

```json
{
  "error": {
    "code": "method_not_allowed",
    "message": "DELETE is not allowed here. Allowed: GET, PATCH."
  }
}
```
