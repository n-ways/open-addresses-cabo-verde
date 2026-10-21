# doors/

Confirmed entrances and gates, exported from the N-Ways app once people have agreed on them (engine/SPEC.md §8.6, §9). No door has been confirmed yet, so the folder is empty: until one is, each code leads to its lote's mapped gate or, where none is mapped, to the centre of its main structure (`entrance_kind` in `registry/<KEY>.csv`).

Each row will hold:

- home code
- entrance index and kind (portão, porta, garagem, loja)
- Plus Code (11 characters)
- confirmed-since date

A door carries no names of residents and nothing about the people who live there. A household that asked for its door to be private is left out; its code then routes to the gate or the street.
