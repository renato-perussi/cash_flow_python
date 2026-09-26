# AGENTS.md

Greenfield cash-flow analysis repo (Python + pandas/plotly/Streamlit). No app source, tests, or CI yet — only data + deps + design spec.

## Data contract — `data/cash_flow.csv`

- Separator is `;`, not `,`. Always `pd.read_csv("data/cash_flow.csv", sep=";")`.
- Dates are ISO `YYYY-MM-DD`; `valor` uses `.` decimals and is always positive — sign comes from `tipo` (`Entrada`/`Saída`).
- `data_realizada` is empty (`NaT`) on forecast rows. Realized vs. forecast = `status` in (`Pago`,`Recebido`) vs. `Previsto`. Do not treat empty `data_realizada` as missing data.
- Categorical columns use pt-BR strings (`Saída`, `Não`, `Previsto`); preserve accents, do not anglicize.
- Single-month sample (2026-09, 30 rows). Don't hardcode month assumptions into loaders.

## Commands

Use the repo venv (`python` 3.12, tools preinstalled) — `requirements*.txt` are pinned:

```bash
.venv/bin/pip install -r requirements.txt -r requirements_dev.txt
.venv/bin/pytest -q            # no tests exist yet; default rootdir, no config file
.venv/bin/ruff check .         # no ruff config — defaults apply
.venv/bin/black --check .      # formatter of record
.venv/bin/streamlit run app.py # pattern for new Streamlit entrypoint (none exists yet)
```

## UI source of truth — `DESIGN.md`

- Apple-style token system (colors/typography/spacing/components) for any Streamlit/frontend work. Follow its Do's/Don'ts: single `#0066cc` accent (`#2997ff` on dark), 17px body, full-bleed light/dark tile rhythm, pill CTAs, one product-only shadow, no gradients.
- Per its Iteration Guide: one component at a time, reference YAML keys (`{component.*}`), never inline hex (`{token.refs}`), default + Active/Pressed states only.

## Conventions

- `outputs/` is gitignored — write generated reports/exports there, never commit them. `.venv/` is also gitignored; never commit it.
- Keep new code at repo root or a single package dir; don't invent a monorepo layout — this is one small app.
