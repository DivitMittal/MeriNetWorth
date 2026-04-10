import csv
import json
from datetime import date, datetime
from pathlib import Path

ASSET_LABELS = {
    "bank_balance": "Bank Balance",
    "equity_value": "Equity",
    "mf_value": "Mutual Funds",
    "pension_value": "Pension",
    "fixed_income_value": "Fixed Income",
    "real_estate_value": "Real Estate",
    "other_assets_value": "Other Assets",
}


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def calculate_asset_allocation(networth_data: dict) -> dict:
    summary = networth_data.get("summary", {})
    rows = []
    total_assets = 0.0

    for key, label in ASSET_LABELS.items():
        value = float(summary.get(key, 0) or 0)
        total_assets += value
        rows.append({"key": key, "category": label, "value": value})

    for row in rows:
        row["percentage"] = (row["value"] / total_assets * 100) if total_assets else 0.0

    return {"total_assets": total_assets, "allocation": rows}


def calculate_rebalance_suggestions(allocation_data: dict, targets: dict | None = None) -> dict:
    if not targets:
        return {"configured": False, "suggestions": []}

    total_assets = allocation_data.get("total_assets", 0.0)
    suggestions = []
    for row in allocation_data.get("allocation", []):
        target_pct = float(targets.get(row["key"], targets.get(row["category"], 0)) or 0)
        target_value = total_assets * target_pct / 100
        delta = target_value - row["value"]
        suggestions.append(
            {
                "category": row["category"],
                "current_pct": row["percentage"],
                "target_pct": target_pct,
                "current_value": row["value"],
                "target_value": target_value,
                "delta": delta,
            }
        )

    return {"configured": True, "suggestions": suggestions}


def calculate_fd_alerts(fixed_income_data: dict | None, today: date | None = None) -> dict:
    reference_date = today or date.today()
    alerts = []
    buckets = {"matured": 0, "next_30_days": 0, "next_90_days": 0, "later": 0, "unknown": 0}

    for deposit in (fixed_income_data or {}).get("deposits", []):
        maturity = _parse_date(deposit.get("maturity_date"))
        if maturity is None:
            bucket = "unknown"
            days_to_maturity = None
        else:
            days_to_maturity = (maturity - reference_date).days
            if days_to_maturity < 0:
                bucket = "matured"
            elif days_to_maturity <= 30:
                bucket = "next_30_days"
            elif days_to_maturity <= 90:
                bucket = "next_90_days"
            else:
                bucket = "later"

        buckets[bucket] += 1
        alerts.append(
            {
                **deposit,
                "days_to_maturity": days_to_maturity,
                "alert_bucket": bucket,
            }
        )

    alerts.sort(
        key=lambda item: item["days_to_maturity"]
        if item["days_to_maturity"] is not None
        else 999999
    )
    return {"generated_at": datetime.now().isoformat(), "buckets": buckets, "alerts": alerts}


def calculate_tax_harvesting_candidates(
    mf_data: dict | None, equity_data: dict | None = None
) -> dict:
    candidates = []
    missing_reasons = []

    for holding in (mf_data or {}).get("consolidated_holdings", []):
        invested = float(holding.get("invested_value", 0) or 0)
        current = float(holding.get("market_value", 0) or 0)
        if invested <= 0 or current <= 0:
            continue
        gain = current - invested
        candidates.append(
            {
                "asset_type": "Mutual Fund",
                "name": holding.get("scheme", "Unknown"),
                "account": holding.get("account", ""),
                "pan": holding.get("pan", ""),
                "invested_value": invested,
                "current_value": current,
                "gain": gain,
                "gain_pct": gain / invested * 100,
                "direction": "loss" if gain < 0 else "gain",
            }
        )

    if equity_data and equity_data.get("total_holdings", 0):
        missing_reasons.append(
            "Equity cost basis and holding-period data are unavailable in current statements."
        )
    if not candidates:
        missing_reasons.append("No mutual fund cost-basis candidates found.")

    candidates.sort(key=lambda item: item["gain"])
    return {"candidates": candidates, "missing_reasons": missing_reasons}


def calculate_goal_progress(goals_path: Path, total_networth: float) -> dict:
    if not goals_path.exists():
        return {"configured": False, "goals": []}

    goals = []
    with open(goals_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            target = float(
                str(row.get("Target Amount", "0")).replace(",", "").replace("₹", "") or 0
            )
            current = float(
                str(row.get("Current Amount", "")).replace(",", "").replace("₹", "")
                or total_networth
            )
            goals.append(
                {
                    "name": row.get("Name", "Goal"),
                    "target_amount": target,
                    "current_amount": current,
                    "target_date": row.get("Target Date", ""),
                    "progress_pct": (current / target * 100) if target else 0.0,
                }
            )

    return {"configured": True, "goals": goals}


def build_history_snapshot(period: str, networth_data: dict) -> dict:
    summary = networth_data.get("summary", {})
    return {
        "period": period,
        "generated_at": datetime.now().isoformat(),
        "total_networth": summary.get("total_networth", 0),
        "bank_balance": summary.get("bank_balance", 0),
        "equity_value": summary.get("equity_value", 0),
        "mf_value": summary.get("mf_value", 0),
        "pension_value": summary.get("pension_value", 0),
        "fixed_income_value": summary.get("fixed_income_value", 0),
        "real_estate_value": summary.get("real_estate_value", 0),
        "other_assets_value": summary.get("other_assets_value", 0),
        "liabilities": summary.get("liabilities", 0),
    }


def upsert_history_snapshot(history_file: Path, snapshot: dict) -> list[dict]:
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)
    else:
        history = []

    history = [item for item in history if item.get("period") != snapshot.get("period")]
    history.append(snapshot)
    history.sort(key=lambda item: item.get("period", ""))

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    return history


def build_planning_data(
    networth_data: dict,
    fixed_income_data: dict | None,
    mf_data: dict | None,
    equity_data: dict | None,
    goals_path: Path,
    targets: dict | None = None,
) -> dict:
    allocation = calculate_asset_allocation(networth_data)
    return {
        "generated_at": datetime.now().isoformat(),
        "allocation": allocation,
        "rebalancing": calculate_rebalance_suggestions(allocation, targets),
        "fd_alerts": calculate_fd_alerts(fixed_income_data),
        "tax_harvesting": calculate_tax_harvesting_candidates(mf_data, equity_data),
        "goals": calculate_goal_progress(
            goals_path,
            float(networth_data.get("summary", {}).get("total_networth", 0) or 0),
        ),
    }
