"""Asset aggregation by PAN for tax computation."""

from dataclasses import dataclass, field
from typing import Optional

from .pan_config import find_pan_for_holder, get_holder_info, get_all_pans, get_holder_name


@dataclass
class AggregatedAssets:
    """Aggregated assets for a single PAN holder."""
    pan: str
    holder_name: str

    # Bank accounts
    bank_accounts: list = field(default_factory=list)
    total_bank_balance: float = 0.0

    # Equity holdings
    demat_accounts: list = field(default_factory=list)
    total_equity_value: float = 0.0
    total_equity_holdings: int = 0

    # Mutual Fund holdings
    mf_accounts: list = field(default_factory=list)
    total_mf_value: float = 0.0
    total_mf_invested: float = 0.0
    total_mf_holdings: int = 0

    # NPS/Pension
    pension_accounts: list = field(default_factory=list)
    total_pension_value: float = 0.0

    # Fixed Income
    fixed_income_accounts: list = field(default_factory=list)
    total_fixed_income_value: float = 0.0

    # Real Estate
    real_estate_assets: list = field(default_factory=list)
    total_real_estate_value: float = 0.0

    # Other Assets
    other_assets: list = field(default_factory=list)
    total_other_assets_value: float = 0.0

    # Liabilities
    liabilities: list = field(default_factory=list)
    total_liabilities: float = 0.0

    @property
    def total_assets(self) -> float:
        """Total asset value (excluding liabilities)."""
        return (
            self.total_bank_balance
            + self.total_equity_value
            + self.total_mf_value
            + self.total_pension_value
            + self.total_fixed_income_value
            + self.total_real_estate_value
            + self.total_other_assets_value
        )

    @property
    def net_worth(self) -> float:
        """Net worth (assets - liabilities)."""
        return self.total_assets - self.total_liabilities

    @property
    def mf_unrealized_gain(self) -> float:
        """Unrealized gain on mutual funds."""
        return max(0, self.total_mf_value - self.total_mf_invested)


def aggregate_by_pan(
    bank_data: Optional[dict] = None,
    equity_data: Optional[dict] = None,
    mf_data: Optional[dict] = None,
    pension_data: Optional[dict] = None,
    fixed_income_data: Optional[dict] = None,
    real_estate_data: Optional[dict] = None,
    other_assets_data: Optional[dict] = None,
    liabilities_data: Optional[dict] = None,
) -> dict[str, AggregatedAssets]:
    """Aggregate all assets by PAN.

    Args:
        bank_data: Bank data JSON dict
        equity_data: Equity data JSON dict
        mf_data: Mutual fund data JSON dict
        pension_data: Pension data JSON dict
        fixed_income_data: Fixed income data JSON dict
        real_estate_data: Real estate data JSON dict
        other_assets_data: Other assets data JSON dict
        liabilities_data: Liabilities data JSON dict

    Returns:
        Dict mapping PAN to AggregatedAssets
    """
    aggregated: dict[str, AggregatedAssets] = {}

    # Initialize for all known PANs
    for pan in get_all_pans():
        holder_name = get_holder_name(pan)
        aggregated[pan] = AggregatedAssets(pan=pan, holder_name=holder_name)

    # Unknown bucket for accounts we can't map
    aggregated["UNKNOWN"] = AggregatedAssets(pan="UNKNOWN", holder_name="Unmapped Accounts")

    # Aggregate bank accounts
    if bank_data and "accounts" in bank_data:
        for account in bank_data["accounts"]:
            holder = account.get("holder_name", "")
            pan = find_pan_for_holder(holder)
            target = aggregated.get(pan) if pan else aggregated["UNKNOWN"]

            target.bank_accounts.append({
                "bank": account.get("bank", "Unknown"),
                "account_number": account.get("account_number", ""),
                "holder_name": holder,
                "balance": account.get("balance", 0),
            })
            target.total_bank_balance += account.get("balance", 0)

    # Aggregate equity holdings
    if equity_data and "accounts" in equity_data:
        for account in equity_data["accounts"]:
            holder = account.get("holder_name", "")
            pan = find_pan_for_holder(holder)
            target = aggregated.get(pan) if pan else aggregated["UNKNOWN"]

            demat_summary = {
                "depository": account.get("depository", "Unknown"),
                "dp_id": account.get("dp_id", ""),
                "client_id": account.get("client_id", ""),
                "holder_name": holder,
                "total_value": account.get("total_value", 0),
                "holdings_count": account.get("total_holdings", 0),
            }
            target.demat_accounts.append(demat_summary)
            target.total_equity_value += account.get("total_value", 0)
            target.total_equity_holdings += account.get("total_holdings", 0)

    # Aggregate MF holdings
    if mf_data and "accounts" in mf_data:
        for account in mf_data["accounts"]:
            # MF data has PAN directly
            pan = account.get("pan", "")
            target = aggregated.get(pan) if pan in aggregated else aggregated["UNKNOWN"]

            soa_holdings = account.get("soa_holdings", [])
            total_market = sum(h.get("market_value", 0) for h in soa_holdings)
            total_invested = sum(h.get("invested_value", 0) for h in soa_holdings)

            mf_summary = {
                "pan": pan,
                "holder_name": account.get("holder_name", ""),
                "total_value": total_market,
                "invested_value": total_invested,
                "holdings_count": len(soa_holdings),
            }
            target.mf_accounts.append(mf_summary)
            target.total_mf_value += total_market
            target.total_mf_invested += total_invested
            target.total_mf_holdings += len(soa_holdings)

    # Aggregate Pension/NPS
    if pension_data and "accounts" in pension_data:
        for account in pension_data["accounts"]:
            holder = account.get("name", "")
            pan = find_pan_for_holder(holder)
            target = aggregated.get(pan) if pan else aggregated["UNKNOWN"]

            summary = {
                "name": account.get("name", ""),
                "type": account.get("type", "NPS"),
                "value": account.get("value", 0),
            }
            target.pension_accounts.append(summary)
            target.total_pension_value += account.get("value", 0)

    # Aggregate Fixed Income
    if fixed_income_data and "deposits" in fixed_income_data:
        for deposit in fixed_income_data["deposits"]:
            # Handle both "holders" (JSON) and "Holders" (CSV raw if passed)
            holder = deposit.get("holders") or deposit.get("Holders") or ""

            # Assume primary holder is first
            primary_holder = holder.split(',')[0].strip() if holder else ""

            pan = find_pan_for_holder(primary_holder)
            target = aggregated.get(pan) if pan else aggregated["UNKNOWN"]

            target.fixed_income_accounts.append(deposit)
            # Ensure value is float, check both "amount" and "Amount"
            amount = deposit.get("amount") if "amount" in deposit else deposit.get("Amount", 0)

            if isinstance(amount, str):
                try:
                    amount = float(amount.replace(",", "").replace("₹", "").strip())
                except:
                    amount = 0.0
            target.total_fixed_income_value += amount

    # Aggregate Real Estate
    if real_estate_data and "assets" in real_estate_data:
        for asset in real_estate_data["assets"]:
            holder = asset.get("name", "")
            pan = find_pan_for_holder(holder)
            target = aggregated.get(pan) if pan else aggregated["UNKNOWN"]

            target.real_estate_assets.append(asset)
            target.total_real_estate_value += asset.get("value", 0)

    # Aggregate Other Assets
    if other_assets_data and "assets" in other_assets_data:
        for asset in other_assets_data["assets"]:
            holder = asset.get("name", "")
            pan = find_pan_for_holder(holder)
            target = aggregated.get(pan) if pan else aggregated["UNKNOWN"]

            target.other_assets.append(asset)
            target.total_other_assets_value += asset.get("value", 0)

    # Aggregate liabilities (shared across all PANs for now)
    # Liabilities are distributed to a special SHARED entry or first PAN
    if liabilities_data and "liabilities" in liabilities_data:
        total_liability = liabilities_data.get("total_liability", 0)
        liability_entries = liabilities_data.get("liabilities", [])

        # Add liabilities to UNKNOWN bucket (shared family liabilities)
        if "SHARED" not in aggregated:
            aggregated["SHARED"] = AggregatedAssets(pan="SHARED", holder_name="Shared/Family")

        for entry in liability_entries:
            for txn in entry.get("transactions", []):
                aggregated["SHARED"].liabilities.append({
                    "source": entry.get("source_file", "Unknown"),
                    "beneficiary": txn.get("beneficiary", ""),
                    "amount": txn.get("amount_inr", 0),
                    "date": txn.get("date"),
                })

        aggregated["SHARED"].total_liabilities = total_liability

    # Remove empty unknown bucket
    if (
        aggregated["UNKNOWN"].total_bank_balance == 0
        and aggregated["UNKNOWN"].total_equity_value == 0
        and aggregated["UNKNOWN"].total_mf_value == 0
        and aggregated["UNKNOWN"].total_pension_value == 0
        and aggregated["UNKNOWN"].total_fixed_income_value == 0
        and aggregated["UNKNOWN"].total_real_estate_value == 0
        and aggregated["UNKNOWN"].total_other_assets_value == 0
    ):
        del aggregated["UNKNOWN"]

    return aggregated


def get_asset_summary_for_pan(
    pan: str,
    aggregated: dict[str, AggregatedAssets]
) -> Optional[dict]:
    """Get asset summary for a specific PAN.

    Args:
        pan: PAN card number
        aggregated: Dict from aggregate_by_pan()

    Returns:
        Summary dict or None if PAN not found
    """
    if pan not in aggregated:
        return None

    assets = aggregated[pan]
    return {
        "pan": pan,
        "holder_name": assets.holder_name,
        "bank_balance": assets.total_bank_balance,
        "equity_value": assets.total_equity_value,
        "mf_value": assets.total_mf_value,
        "pension_value": assets.total_pension_value,
        "fixed_income_value": assets.total_fixed_income_value,
        "real_estate_value": assets.total_real_estate_value,
        "other_assets_value": assets.total_other_assets_value,
        "total_assets": assets.total_assets,
        "liabilities": assets.total_liabilities,
        "net_worth": assets.net_worth,
        "bank_accounts_count": len(assets.bank_accounts),
        "demat_accounts_count": len(assets.demat_accounts),
        "mf_holdings_count": assets.total_mf_holdings,
        "equity_holdings_count": assets.total_equity_holdings,
        "fixed_income_count": len(assets.fixed_income_accounts),
        "pension_count": len(assets.pension_accounts),
        "real_estate_count": len(assets.real_estate_assets),
    }


def format_pan_summary(aggregated: dict[str, AggregatedAssets]) -> str:
    """Format all PAN summaries as readable text.

    Args:
        aggregated: Dict from aggregate_by_pan()

    Returns:
        Formatted summary string
    """
    lines = ["=" * 60, "ASSET SUMMARY BY PAN", "=" * 60, ""]

    for pan, assets in sorted(aggregated.items()):
        if pan in ("UNKNOWN", "SHARED"):
            continue

        lines.extend([
            f"📋 {assets.holder_name} ({pan})",
            "-" * 40,
            f"  🏦 Bank Balance: ₹{assets.total_bank_balance:,.2f}",
            f"     ({len(assets.bank_accounts)} accounts)",
            f"  📈 Equity Value: ₹{assets.total_equity_value:,.2f}",
            f"     ({assets.total_equity_holdings} holdings in {len(assets.demat_accounts)} demat accounts)",
            f"  💰 MF Value: ₹{assets.total_mf_value:,.2f}",
            f"     (Invested: ₹{assets.total_mf_invested:,.2f}, {assets.total_mf_holdings} holdings)",
            f"  👴 Pension Value: ₹{assets.total_pension_value:,.2f}",
            f"     ({len(assets.pension_accounts)} accounts)",
            f"  🏦 Fixed Income: ₹{assets.total_fixed_income_value:,.2f}",
            f"     ({len(assets.fixed_income_accounts)} deposits)",
            f"  🏠 Real Estate: ₹{assets.total_real_estate_value:,.2f}",
            f"     ({len(assets.real_estate_assets)} properties)",
            f"  🪙 Other Assets: ₹{assets.total_other_assets_value:,.2f}",
            f"     ({len(assets.other_assets)} items)",
            f"  🎯 Total Assets: ₹{assets.total_assets:,.2f}",
            f"  💎 Net Worth: ₹{assets.net_worth:,.2f}",
            "",
        ])

    # Add shared liabilities if present
    if "SHARED" in aggregated:
        assets = aggregated["SHARED"]
        if assets.total_liabilities > 0:
            lines.extend([
                "📋 Shared/Family Liabilities",
                "-" * 40,
                f"  ⚠️ Total Liabilities: ₹{assets.total_liabilities:,.2f}",
                f"     ({len(assets.liabilities)} transactions)",
                "",
            ])

    # Add unknown if present
    if "UNKNOWN" in aggregated:
        assets = aggregated["UNKNOWN"]
        lines.extend([
            "⚠️ UNMAPPED ACCOUNTS",
            "-" * 40,
            f"  Bank Balance: ₹{assets.total_bank_balance:,.2f}",
            f"  Equity Value: ₹{assets.total_equity_value:,.2f}",
            f"  MF Value: ₹{assets.total_mf_value:,.2f}",
            f"  Pension Value: ₹{assets.total_pension_value:,.2f}",
            f"  Fixed Income: ₹{assets.total_fixed_income_value:,.2f}",
            f"  Real Estate: ₹{assets.total_real_estate_value:,.2f}",
            f"  Other Assets: ₹{assets.total_other_assets_value:,.2f}",
            "",
            "  Note: Update pan_config.py to map these accounts",
            "",
        ])

    return "\n".join(lines)
