# AGENTS.md

Streamlit cash-flow app: `app.py` entrypoint + `cashflow/` package (`data.py`, `metrics.py`, `charts.py`). Tests in `tests/` mirror modules. Run everything from repo root — `data/cash_flow.csv` is loaded via relative `DATA_PATH`. No pytest/ruff config, no CI, no `opencode.json`.

## Data contract — `data/cash_flow.csv`

- Separator `;`, encoding `utf-8-sig`: `pd.read_csv(path, sep=";", encoding="utf-8-sig")`. Canonical loader is `cashflow.data.load_cashflow` (dates parsed with `errors="coerce"`).
- `valor` always positive finite (`>0`) with `.` decimals — sign comes from `tipo` (`Entrada` + / `Saída` −) via `with_signed_value` → `signed_value` column.
- Realized vs. forecast = `status` in (`Pago`,`Recebido`) vs. `Previsto`. `data_realizada` NaT on forecast rows (~24) is expected, not missing data.
- pt-BR strings with accents (`Saída`, `Não`, `Previsto`) — preserve, never anglicize.
- 360 rows, 2025-10-06→2026-09-30. Don't hardcode month/window assumptions.

## Commands (repo venv, python 3.12, pinned `requirements*.txt`)

```bash
.venv/bin/pip install -r requirements.txt -r requirements_dev.txt
.venv/bin/python -m pytest -q      # bare `.venv/bin/pytest` fails with 83 ModuleNotFoundError; `python -m` fixes sys.path
.venv/bin/python -m pytest tests/test_data.py -q   # single file; add `-k name` for one test
.venv/bin/ruff check .             # no ruff config — defaults; currently clean
.venv/bin/black --check .          # formatter of record, but repo is NOT black-clean (8 files) — don't mass-reformat
.venv/bin/streamlit run app.py     # run from repo root (relative data path)
```

## Pipeline order + error contract

- `get_frame()` (`app.py`) already returns the frame with `signed_value`. New code paths starting from `load_cashflow` must call `with_signed_value` first — `group_daily_net`, `daily_net_flow`, `cumulative_balance`, `metrics.daily_flow` raise `KeyError` without it.
- `filter_cashflow` date window filters `data_prevista` only, never `data_realizada`. Period anchor is `max(data_prevista) - days + 1`. `None` disables a filter, `[]` returns empty, `start > end` returns empty by design (no exception).
- `ValueError` = user-facing (`app.py` shows `st.error`); `KeyError` only for missing `tipo`/`signed_value`. New validations on filterable columns must raise `ValueError` via `require_columns`, or `app.py` won't catch them.
- `group_daily_net` and `build_summary` drop `data_prevista` NaT (with warning) to keep `summary.net == sum(daily)` — don't "fix" the dropna. `build_summary` does NOT need `signed_value` (net = inflows − outflows on `valor`); `forecast_coverage` is `inf` when forecast_in > 0 with no forecast_out, `0.0` when both are 0.
- Charts are empty-safe (empty frame → empty figure, no exception).
- `get_frame` is `@st.cache_data` with no TTL — after changing the CSV call `get_frame.clear()`.
- CSV export must keep `sep=";"` for round-trip (`render_action_row`).

## UI — `DESIGN.md` is source of truth

- Single accent `#0066cc` (`#2997ff` on dark), 17px body, pill CTAs, one product-only shadow, no gradients.
- One component at a time, reference YAML keys (`{component.*}`), never inline hex; default + Active/Pressed states only.

## Conventions

- `README.md` is the user/management-facing doc (pt-BR, formal tone, no decorative icons) — keep it in sync when changing features, data contract, metrics, or commands. Agent-oriented detail lives here; user-oriented detail lives there.
- `outputs/` is gitignored — generated reports/exports go there, never commit. Never commit `.venv/`.
- Keep code flat: repo root or `cashflow/` only; no monorepo layout.
