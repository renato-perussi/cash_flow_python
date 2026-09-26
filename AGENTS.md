# AGENTS.md

Streamlit cash-flow app: `app.py` entrypoint + `cashflow/` package (`data.py`, `metrics.py`, `charts.py`). Tests in `tests/` mirror modules. Run everything from repo root — `data/cash_flow.csv` is loaded via relative path.

## Data contract — `data/cash_flow.csv`

- Separator is `;`: `pd.read_csv(path, sep=";")`. Canonical loader is `cashflow.data.load_cashflow`.
- `valor` always positive with `.` decimals — sign comes from `tipo` (`Entrada` + / `Saída` −) via `with_signed_value` → `signed_value` column.
- Realized vs. forecast = `status` in (`Pago`,`Recebido`) vs. `Previsto`. Empty `data_realizada` (`NaT`) on forecast rows is expected, not missing data.
- pt-BR strings with accents (`Saída`, `Não`, `Previsto`) — preserve, never anglicize.
- 360 rows, 2025-10-06→2026-09-30. Don't hardcode month/window assumptions.

## Commands (repo venv, python 3.12, pinned `requirements*.txt`)

```bash
.venv/bin/pip install -r requirements.txt -r requirements_dev.txt
.venv/bin/python -m pytest -q      # NOT `.venv/bin/pytest`: bare pytest misses `cashflow` (ModuleNotFoundError); `python -m` fixes sys.path. No config file.
.venv/bin/ruff check .             # no ruff config — defaults; currently clean
.venv/bin/black --check .          # formatter of record, but repo is NOT black-clean — don't mass-reformat
.venv/bin/streamlit run app.py     # run from repo root (relative data path)
```

## Ordering gotchas

- Charts (`daily_net_flow`, `cumulative_balance`) and `metrics.daily_flow` group by `signed_value` — always call `data.with_signed_value(...)` first; `app.py:396` shows the order.
- `filter_cashflow` date window filters `data_prevista` only, never `data_realizada`. Period anchor is `max(data_prevista) - days + 1` (`app.py:401-413`).
- CSV export must keep `sep=";"` for round-trip (`app.py:346`).

## UI — `DESIGN.md` is source of truth

- Single accent `#0066cc` (`#2997ff` on dark), 17px body, pill CTAs, one product-only shadow, no gradients.
- One component at a time, reference YAML keys (`{component.*}`), never inline hex; default + Active/Pressed states only.

## Conventions

- `outputs/` is gitignored — generated reports/exports go there, never commit. Never commit `.venv/`.
- Keep code flat: repo root or `cashflow/` only; no monorepo layout.
