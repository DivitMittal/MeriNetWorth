"""Dividend income estimation module for equity holdings.

Estimates expected annual dividend income based on holdings and historical
dividend data. Dividend yield data is stored in config/dividend_yields.json.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Path to dividend yield data
_CONFIG_DIR = Path(__file__).parent.parent / "config"
_DIVIDEND_FILE = _CONFIG_DIR / "dividend_yields.json"

# Default dividend yield for stocks without data (conservative estimate)
DEFAULT_DIVIDEND_YIELD_PCT = 1.0

# Dividend TDS threshold and rate
DIVIDEND_TDS_THRESHOLD = 5000  # TDS applicable if dividend > ₹5,000
DIVIDEND_TDS_RATE = 10.0  # 10% TDS on dividends


@dataclass
class DividendEstimate:
    """Dividend estimate for a single holding."""
    isin: str
    name: str
    quantity: float
    current_value: float
    annual_dividend_per_share: float
    dividend_yield_pct: float
    estimated_annual_dividend: float
    has_dividend_data: bool
    frequency: str = "annual"


@dataclass
class DividendSummary:
    """Summary of dividend income for a portfolio."""
    total_holdings: int = 0
    holdings_with_dividend_data: int = 0
    holdings_without_data: int = 0

    total_portfolio_value: float = 0.0
    estimated_annual_dividend: float = 0.0
    average_dividend_yield: float = 0.0

    # TDS estimation
    estimated_tds: float = 0.0
    net_dividend_after_tds: float = 0.0

    # Top dividend payers
    top_dividend_stocks: list = field(default_factory=list)

    # All dividend estimates
    dividend_estimates: list = field(default_factory=list)


def _load_dividend_data() -> dict:
    """Load dividend yield data from JSON file."""
    if not _DIVIDEND_FILE.exists():
        return {}

    try:
        with open(_DIVIDEND_FILE, "r") as f:
            data = json.load(f)
            # Remove comment fields
            return {k: v for k, v in data.items() if not k.startswith("_")}
    except Exception as e:
        print(f"Warning: Could not load dividend data: {e}")
        return {}


# Load dividend data at module import
DIVIDEND_DATA: dict = _load_dividend_data()


def reload_dividend_data() -> None:
    """Reload dividend data from config file."""
    global DIVIDEND_DATA
    DIVIDEND_DATA = _load_dividend_data()


def get_dividend_info(isin: str) -> Optional[dict]:
    """Get dividend information for an ISIN.

    Args:
        isin: ISIN code of the security

    Returns:
        Dividend info dict or None if not found
    """
    return DIVIDEND_DATA.get(isin)


def estimate_dividend_for_holding(
    isin: str,
    name: str,
    quantity: float,
    current_value: float,
) -> DividendEstimate:
    """Estimate annual dividend for a single holding.

    Args:
        isin: ISIN code
        name: Security name
        quantity: Number of shares held
        current_value: Current market value of holding

    Returns:
        DividendEstimate with calculated values
    """
    dividend_info = get_dividend_info(isin)

    if dividend_info:
        annual_div = dividend_info.get("annual_dividend", 0)
        yield_pct = dividend_info.get("dividend_yield_pct", 0)
        frequency = dividend_info.get("frequency", "annual")
        has_data = True
        estimated_dividend = quantity * annual_div
    else:
        # Use default yield estimate based on current value
        annual_div = 0
        yield_pct = DEFAULT_DIVIDEND_YIELD_PCT
        frequency = "unknown"
        has_data = False
        estimated_dividend = current_value * (DEFAULT_DIVIDEND_YIELD_PCT / 100)

    return DividendEstimate(
        isin=isin,
        name=name,
        quantity=quantity,
        current_value=current_value,
        annual_dividend_per_share=annual_div,
        dividend_yield_pct=yield_pct,
        estimated_annual_dividend=estimated_dividend,
        has_dividend_data=has_data,
        frequency=frequency,
    )


def estimate_dividends_for_portfolio(
    holdings: list[dict],
) -> DividendSummary:
    """Estimate dividend income for entire portfolio.

    Args:
        holdings: List of holding dicts with 'isin', 'name', 'quantity', 'value' keys

    Returns:
        DividendSummary with aggregated dividend estimates
    """
    summary = DividendSummary()
    estimates = []

    for holding in holdings:
        isin = holding.get("isin", "")
        name = holding.get("name", "Unknown")
        quantity = holding.get("quantity", 0)
        # Handle both 'value' and 'total_value' keys
        value = holding.get("value", holding.get("total_value", 0))

        if not isin or quantity <= 0:
            continue

        estimate = estimate_dividend_for_holding(isin, name, quantity, value)
        estimates.append(estimate)

        summary.total_holdings += 1
        summary.total_portfolio_value += value
        summary.estimated_annual_dividend += estimate.estimated_annual_dividend

        if estimate.has_dividend_data:
            summary.holdings_with_dividend_data += 1
        else:
            summary.holdings_without_data += 1

    # Calculate average yield
    if summary.total_portfolio_value > 0:
        summary.average_dividend_yield = (
            summary.estimated_annual_dividend / summary.total_portfolio_value * 100
        )

    # Estimate TDS
    if summary.estimated_annual_dividend > DIVIDEND_TDS_THRESHOLD:
        summary.estimated_tds = summary.estimated_annual_dividend * (DIVIDEND_TDS_RATE / 100)
    summary.net_dividend_after_tds = summary.estimated_annual_dividend - summary.estimated_tds

    # Sort by dividend amount and get top payers
    estimates.sort(key=lambda x: x.estimated_annual_dividend, reverse=True)
    summary.dividend_estimates = estimates
    summary.top_dividend_stocks = [
        {
            "name": e.name,
            "isin": e.isin,
            "quantity": e.quantity,
            "dividend": e.estimated_annual_dividend,
            "yield_pct": e.dividend_yield_pct,
            "has_data": e.has_dividend_data,
        }
        for e in estimates[:10]
        if e.estimated_annual_dividend > 0
    ]

    return summary


def estimate_dividends_by_pan(
    aggregated_assets: dict,
    equity_data: Optional[dict] = None,
) -> dict[str, DividendSummary]:
    """Estimate dividends for each PAN holder.

    Args:
        aggregated_assets: Dict from asset_aggregator.aggregate_by_pan()
        equity_data: Full equity data dict (with holdings detail)

    Returns:
        Dict mapping PAN to DividendSummary
    """
    from .pan_config import find_pan_for_holder

    result = {}

    if not equity_data or "accounts" not in equity_data:
        return result

    # Group holdings by PAN
    holdings_by_pan: dict[str, list] = {}

    for account in equity_data["accounts"]:
        holder = account.get("holder_name", "")
        pan = find_pan_for_holder(holder)

        if not pan:
            pan = "UNKNOWN"

        if pan not in holdings_by_pan:
            holdings_by_pan[pan] = []

        # Add all holdings from this account
        for holding in account.get("holdings", []):
            holdings_by_pan[pan].append(holding)

    # Calculate dividend summary for each PAN
    for pan, holdings in holdings_by_pan.items():
        if holdings:
            result[pan] = estimate_dividends_for_portfolio(holdings)

    return result


def format_dividend_summary(summary: DividendSummary) -> str:
    """Format dividend summary as readable text.

    Args:
        summary: DividendSummary object

    Returns:
        Formatted string
    """
    lines = [
        "=== Dividend Income Estimate ===",
        "",
        f"Total Holdings: {summary.total_holdings}",
        f"  With dividend data: {summary.holdings_with_dividend_data}",
        f"  Without data (estimated): {summary.holdings_without_data}",
        "",
        f"Portfolio Value: ₹{summary.total_portfolio_value:,.2f}",
        f"Estimated Annual Dividend: ₹{summary.estimated_annual_dividend:,.2f}",
        f"Average Dividend Yield: {summary.average_dividend_yield:.2f}%",
        "",
        f"Estimated TDS (10%): ₹{summary.estimated_tds:,.2f}",
        f"Net Dividend (after TDS): ₹{summary.net_dividend_after_tds:,.2f}",
        "",
        "Top Dividend Payers:",
    ]

    for stock in summary.top_dividend_stocks[:5]:
        data_status = "✓" if stock["has_data"] else "~"
        lines.append(
            f"  {data_status} {stock['name'][:30]}: ₹{stock['dividend']:,.0f} "
            f"({stock['yield_pct']:.1f}%)"
        )

    return "\n".join(lines)
