# Using uv with MeriNetWorth

This project supports [uv](https://docs.astral.sh/uv/) for reproducible local development.

## Setup

```bash
uv sync --dev
```

## Common Commands

```bash
uv run python process_all.py
uv run streamlit run web/app.py
uv run pytest
uv run python -m py_compile web/app.py process_all.py src/*.py tests/*.py
```

## Dependency Management

```bash
uv add <package>
uv add --dev <package>
uv remove <package>
uv lock
uv sync --frozen
```

## Local Verification Sequence

Use this sequence before shipping changes:

```bash
uv sync --dev
uv run pytest
uv run python process_all.py
uv run python -m py_compile web/app.py process_all.py src/*.py tests/*.py
```

Optional quality checks, when the tools are available:

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
```

## Quick Reference

| Task | Command |
| --- | --- |
| Install dependencies | `uv sync --dev` |
| Process all data | `uv run python process_all.py` |
| Run dashboard | `uv run streamlit run web/app.py` |
| Run tests | `uv run pytest` |
| Compile smoke check | `uv run python -m py_compile web/app.py process_all.py src/*.py tests/*.py` |
| Lock dependencies | `uv lock` |

## Notes

- `requirements.txt` remains available for pip-based installs.
- `uv.lock` should be kept in sync when dependencies change.
- Raw `data/` files contain sensitive financial information and should not be committed.
