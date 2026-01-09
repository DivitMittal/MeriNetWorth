# Using uv with MeriNetWorth This project now uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management. ## Quick Start ### Install uv (if not already installed)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh # Or with Homebrew
brew install uv # Or with pip
pip install uv
``` ### Setup Project
```bash
# Create virtual environment and install all dependencies
uv sync # Install with dev dependencies (testing, linting)
uv sync --dev
``` ### Common Commands #### Managing Dependencies
```bash
# Add a new package
uv add pandas # Add a dev dependency
uv add --dev pytest # Remove a package
uv remove pandas # Update all dependencies
uv sync --upgrade # Update specific package
uv add pandas --upgrade
``` #### Running Commands
```bash
# Run Python script with project dependencies
uv run python script.py # Launch Jupyter notebook
uv run jupyter notebook notebooks/bank_data_processor.ipynb # Start Streamlit dashboard
uv run streamlit run web/app.py # Or use the convenience script
./run_dashboard.sh
``` #### Lock File Management
```bash
# Generate/update lock file
uv lock # Sync from lock file (reproducible install)
uv sync --frozen
``` ## Migration from pip ### Old workflow (pip):
```bash
pip install -r requirements.txt
jupyter notebook notebooks/bank_data_processor.ipynb
streamlit run web/app.py
``` ### New workflow (uv):
```bash
uv sync
uv run jupyter notebook notebooks/bank_data_processor.ipynb
uv run streamlit run web/app.py
``` ## Why uv? ### Performance
- **10-100x faster**than pip for dependency resolution
- Parallel downloads and installations
- Efficient caching ### Reliability
- Lock file (`uv.lock`) ensures reproducible builds
- Better conflict resolution
- Consistent across environments ### Developer Experience
- Single command setup: `uv sync`
- Clear dependency groups (main vs dev)
- No need to activate virtual environment with `uv run` ## Project Structure ### Dependencies are organized in `pyproject.toml`: **Main dependencies**(always installed):
- pandas, numpy - Data processing
- openpyxl, xlrd - Excel file handling
- streamlit, plotly - Web dashboard
- jupyter, matplotlib - Notebooks and visualization **Dev dependencies**(optional, `--dev` flag):
- pytest, pytest-cov - Testing
- black, ruff - Code formatting and linting
- mypy - Type checking ## Troubleshooting ### "Command not found: uv"
Install uv using one of the methods in Quick Start above. ### "No such file: uv.lock"
Run `uv lock` to generate the lock file, then `uv sync`. ### Old virtual environment conflicts
Remove old venv and let uv create a new one:
```bash
rm -rf venv .venv
uv sync
``` ### Want to use specific Python version
```bash
uv python install 3.11
uv sync
``` ## Advanced Usage ### Multiple Python Versions
```bash
# Install Python 3.11
uv python install 3.11 # Use specific Python version
uv venv --python 3.11
``` ### Dependency Groups
```bash
# Install only specific groups
uv sync --group jupyter
uv sync --group web
``` ### CI/CD Integration
```bash
# In CI pipeline
uv sync --frozen # Use exact versions from lock file
uv run pytest # Run tests
``` ## Quick Reference | Task | Command |
|------|---------|
| Initial setup | `uv sync` |
| Add package | `uv add <package>` |
| Remove package | `uv remove <package>` |
| Update all | `uv sync --upgrade` |
| Run script | `uv run python script.py` |
| Run Jupyter | `uv run jupyter notebook` |
| Run dashboard | `uv run streamlit run web/app.py` |
| Install dev deps | `uv sync --dev` |
| Lock dependencies | `uv lock` | ## Migration Checklist - [x] Created `pyproject.toml` with all dependencies
- [x] Updated `.gitignore` for uv files
- [ ] Run `uv sync` to test installation
- [ ] Run `uv lock` to generate lock file
- [ ] Test Jupyter notebook: `uv run jupyter notebook`
- [ ] Test dashboard: `uv run streamlit run web/app.py`
- [ ] Update CI/CD pipelines (if any)
- [ ] Consider removing `requirements.txt` (optional, can keep for compatibility) --- **For more information**: https://docs.astral.sh/uv/
