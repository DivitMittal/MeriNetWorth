from datetime import date

from src.planning_analytics import (
    calculate_asset_allocation,
    calculate_fd_alerts,
    calculate_goal_progress,
    calculate_rebalance_suggestions,
    calculate_tax_harvesting_candidates,
)


def test_calculate_asset_allocation_and_rebalance() -> None:
    allocation = calculate_asset_allocation(
        {"summary": {"bank_balance": 100.0, "equity_value": 300.0, "total_networth": 400.0}}
    )
    rebalancing = calculate_rebalance_suggestions(
        allocation,
        {"bank_balance": 50.0, "equity_value": 50.0},
    )

    assert allocation["total_assets"] == 400.0
    assert rebalancing["configured"] is True
    assert rebalancing["suggestions"][0]["delta"] == 100.0


def test_calculate_fd_alerts_buckets() -> None:
    result = calculate_fd_alerts(
        {
            "deposits": [
                {"bank": "A", "fd_number": "1", "maturity_date": "2025-01-01"},
                {"bank": "B", "fd_number": "2", "maturity_date": "2025-01-20"},
                {"bank": "C", "fd_number": "3", "maturity_date": "2025-03-01"},
            ]
        },
        today=date(2025, 1, 10),
    )

    assert result["buckets"]["matured"] == 1
    assert result["buckets"]["next_30_days"] == 1
    assert result["buckets"]["next_90_days"] == 1


def test_calculate_tax_harvesting_candidates() -> None:
    result = calculate_tax_harvesting_candidates(
        {
            "consolidated_holdings": [
                {
                    "scheme": "Fund",
                    "account": "Holder",
                    "pan": "ABCDE1234F",
                    "invested_value": 100.0,
                    "market_value": 80.0,
                }
            ]
        },
        {"total_holdings": 1},
    )

    assert result["candidates"][0]["gain"] == -20.0
    assert result["candidates"][0]["direction"] == "loss"
    assert result["missing_reasons"]


def test_calculate_goal_progress_missing_file(tmp_path) -> None:
    result = calculate_goal_progress(tmp_path / "goals.csv", 1000.0)

    assert result == {"configured": False, "goals": []}
