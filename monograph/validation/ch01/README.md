# Chapter 1 checks

The checks behind the [C] labels of `chapters/ch01-what-disease-is.tex`.
They reuse the data snapshot of the cycle-tolerance paper
(`cause-for-concern/docs/disease-circuit-tolerance/validation/realdata/raw/`,
retrieved 2026-10-21, SHA-256 in its `SOURCES.json`).

| Script | Needs | Writes |
|---|---|---|
| `build_network.py` | eQuilibrator cache 0.8.1 (full tier) | `species.csv`, `network.csv` |
| `emergent_holonomy.py` | equilibrator-api 0.8.1 | `holonomy.json` |
| `medium_closure.py` | numpy | `results.json` |
| `make_figure.py` | matplotlib | `../../figures/ch01_erythrocyte_cycles.{png,pdf}` |

The first two are stage A and need the environment in
`realdata/requirements.txt`; the last two run from the written tables alone.

```
python build_network.py        # stage A
python emergent_holonomy.py    # stage A
python medium_closure.py
python make_figure.py
```

`species_key.py` identifies a species by its InChI up to anomers (the parity
of a carbon bonded to two oxygens is dropped) and keeps every other
stereocentre, so glucose and mannose stay apart. The tolerance paper used the
InChIKey connectivity block, which merges them; its cycle space (7) and the
19 reactions on a cycle are unchanged by the correction, its reaction and
species counts (70, 101) become 75 and 108.

`medium_closure.py` adds one reaction the annotation omits: RHEA:27626,
the second reaction of human transketolase (UniProtKB P29401 lists only
RHEA:10508). It is listed in `SUPPLIED` and reported separately.
