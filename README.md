# Evidence Collider

[![ci](https://github.com/mahmood726-cyber/evidence-collider/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mahmood726-cyber/evidence-collider/actions/workflows/ci.yml) [![codeql](https://github.com/mahmood726-cyber/evidence-collider/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/mahmood726-cyber/evidence-collider/actions/workflows/codeql.yml) [![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

Maps clinical trial density (from the AACT ClinicalTrials.gov mirror) against global disease burden (IHME SDI) to surface "research deserts" — geographies where burden is high but trial activity is low.

## Run

Open `index.html` in any modern browser. The page fetches `data/collider_results.json` (pre-computed) and renders the desert/non-desert grid.

To regenerate the JSON from source data:

```bash
python core/collider.py
```

For local development:

```bash
python -m http.server 8000
# then open http://localhost:8000/
```

## Test

```bash
python -m pytest -q
```

Tests live under `tests/`. The collider pipeline core lives in `core/`.

## Data

`data/collider_results.json` is a pre-computed snapshot. Regenerating it requires:

- An AACT (ClinicalTrials.gov AACT mirror) snapshot.
- The IHME GBD SDI tables for the year being analysed.

The pipeline auto-discovers common `C:`, `D:`, and `F:` workspace locations for both inputs. If your layout differs, set:

- `EVIDENCE_COLLIDER_AACT_PATH`
- `EVIDENCE_COLLIDER_SDI_PATH`

## Repo layout

| Path | Purpose |
|---|---|
| `index.html` | the dashboard |
| `core/` | pipeline (AACT query + SDI join + desert classifier) |
| `data/` | pre-computed collider output JSON |
| `tests/` | pytest unit tests |

## License

See `LICENSE` (MIT).
