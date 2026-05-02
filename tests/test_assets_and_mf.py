from pathlib import Path

from src.asset_parsers import parse_asset_file
from src.fixed_income_parser import parse_date, parse_fixed_income_file
from src.liability_parser import parse_liability_file
from src.mf_parsers import consolidate_mf_data
from src.pension_parser import parse_pension_csv


def test_parse_asset_file(tmp_path: Path) -> None:
    asset_file = tmp_path / "assets.csv"
    asset_file.write_text('Name,Current Value\nHouse,"₹ 1,000.50"\nGold,2500\n', encoding="utf-8")

    result = parse_asset_file(asset_file, "test")

    assert result is not None
    assert result["asset_count"] == 2
    assert result["total_value"] == 3500.5
    assert result["assets"][0] == {"name": "House", "value": 1000.5}


def test_parse_fixed_income_file(tmp_path: Path) -> None:
    fd_file = tmp_path / "term_deposits.csv"
    fd_file.write_text(
        "S.No,Bank,FD Number,Amount,Inception Date,Maturity Date,Maturity Instruction,Holders,Nomination,Interest rate,Quarterly,Interest Payout\n"
        "1,IDFC,FD123,₹ 100000.00,01-01-2025,31-12-2025,Renew,Holder,Nominee,7.5%,1875,Quarterly\n",
        encoding="utf-8",
    )

    result = parse_fixed_income_file(fd_file)

    assert result is not None
    assert result["deposit_count"] == 1
    assert result["total_principal"] == 100000.0
    assert result["deposits"][0]["maturity_date"] == "2025-12-31"
    assert parse_date("31/12/2025") == "2025-12-31"


def test_parse_liability_file(tmp_path: Path) -> None:
    liability_file = tmp_path / "liabilities.csv"
    liability_file.write_text(
        "Date,Beneficiary,Amount (INR),Amount (Euro),Exchange Rate\n"
        "2025-01-01,Loan,-5000,,\n"
        "2025-01-02,Receivable,2000,,\n",
        encoding="utf-8",
    )

    result = parse_liability_file(liability_file)

    assert result is not None
    assert result["transaction_count"] == 2
    assert result["total_amount"] == -3000.0
    assert result["net_liability"] == 3000.0


def test_parse_pension_csv(tmp_path: Path) -> None:
    pension_file = tmp_path / "pension.csv"
    pension_file.write_text(
        "Name,Type,Current Value\nNPS Account,NPS,₹ 250000.00\n", encoding="utf-8"
    )

    accounts = parse_pension_csv(pension_file)

    assert accounts == [
        {
            "name": "NPS Account",
            "type": "NPS",
            "value": 250000.0,
            "source_file": "pension.csv",
        }
    ]


def test_consolidate_mf_data() -> None:
    account = {
        "pan": "ABCDE1234F",
        "holder_name": "Holder",
        "soa_holdings": [
            {
                "folio": "12345678",
                "scheme": "Equity Fund",
                "invested_value": 900.0,
                "units": 10.0,
                "nav": 100.0,
                "market_value": 1000.0,
                "holding_type": "SOA",
            }
        ],
        "demat_holdings": [],
        "soa_value": 1000.0,
        "demat_value": 0.0,
        "total_value": 1000.0,
        "total_holdings": 1,
    }

    result = consolidate_mf_data([account])

    assert result["total_accounts"] == 1
    assert result["total_holdings"] == 1
    assert result["total_value"] == 1000.0
    assert result["consolidated_holdings"][0]["pan"] == "ABCDE1234F"
