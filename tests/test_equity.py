"""Tests for equity processing."""

from pathlib import Path

from src.process_equity import process_all_equity_statements, save_equity_json

PROJECT_ROOT = Path(__file__).parent.parent


def test_equity_processing_returns_standard_summary(tmp_path):
    equity_path = PROJECT_ROOT / "data" / "10.25" / "equity"

    assert equity_path.exists(), f"Equity path not found: {equity_path}"

    equity_data = process_all_equity_statements(equity_path=equity_path, sync_prices=False)

    assert equity_data["total_accounts"] > 0
    assert equity_data["total_holdings"] > 0
    assert equity_data["total_value"] > 0
    assert equity_data["accounts"]
    assert equity_data["consolidated_holdings"]

    json_file = save_equity_json(equity_data, tmp_path)
    assert json_file.exists()
