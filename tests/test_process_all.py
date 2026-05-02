from process_all import build_legacy_networth_data


def test_build_legacy_networth_data_includes_all_asset_classes() -> None:
    result = build_legacy_networth_data(
        bank_data={"total_balance": 100.0},
        equity_data={"total_value": 200.0},
        mf_data={"total_value": 300.0},
        pension_data={"total_value": 400.0},
        fixed_income_data={"total_principal": 500.0},
        real_estate_data={"total_value": 600.0},
        other_assets_data={"total_value": 700.0},
        liabilities_data={"total_liability": 50.0},
    )

    assert result["summary"]["total_networth"] == 2750.0
    assert result["summary"]["mf_value"] == 300.0
    assert result["mf"] == {"total_value": 300.0}
