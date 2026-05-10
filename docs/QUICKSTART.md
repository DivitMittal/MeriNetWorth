# Quick Start Guide

Get MeriNetWorth running locally with the full parser → JSON → Streamlit dashboard flow.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or with uv:

```bash
uv sync --dev
```

## Step 2: Process All Financial Data

```bash
python process_all.py
```

This processes bank, equity, mutual fund, pension, fixed income, real estate, other assets, and liabilities data into `output/*.json`.

## Step 3: Launch the Dashboard

```bash
./run_dashboard.sh
```

Or manually:

```bash
streamlit run web/app.py
```

The dashboard opens at `http://localhost:8501`.

## Verification Commands

Run these before treating local changes as complete:

```bash
python -m pytest
python process_all.py
python -m py_compile web/app.py process_all.py src/*.py tests/*.py
```

With uv:

```bash
uv run pytest
uv run python process_all.py
uv run python -m py_compile web/app.py process_all.py src/*.py tests/*.py
```

## Generated Files

- `output/bank_data.json`
- `output/equity_data.json`
- `output/mf_data.json`
- `output/fixed_income_data.json`
- `output/real_estate_data.json`
- `output/pension_data.json`
- `output/other_assets_data.json`
- `output/liabilities_data.json`
- `output/networth_data.json`
- `output/planning_data.json`
- `output/history_data.json`

## Troubleshooting

### “No data found” in dashboard

Run `python process_all.py` first and confirm `output/bank_data.json` exists.

### PDF-based parsers skip files

Install the optional PDF dependency used by that parser. For NPS pension PDFs, install `pdfplumber`.

### Dashboard password prompt

Set a local password before launching if needed:

```bash
export DASHBOARD_PASSWORD="change-me"
streamlit run web/app.py
```

## Data Safety

Do not parse or use `*Consolidated.xlsx` files in `data/` for analytics. They are personal-use exports only.
