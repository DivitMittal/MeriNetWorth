import streamlit as st
import pandas as pd
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import hmac
import os
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.config import OUTPUT_PATH, DATA_FILE, EQUITY_FILE, NETWORTH_FILE, LIABILITIES_FILE, PENSION_FILE, FIXED_INCOME_FILE, REAL_ESTATE_FILE, OTHER_ASSETS_FILE
from src.pan_config import get_holder_info, get_all_pans, get_holder_name
from src.asset_aggregator import aggregate_by_pan, AggregatedAssets
from src.tax_computation import compute_tax_for_individual, TaxBreakdown
from src.dividend_estimator import estimate_dividends_by_pan, DividendSummary

st.set_page_config(
    page_title="MeriNetWorth - Complete Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .bank-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 10px;
        backdrop-filter: blur(10px);
    }
    [data-testid="stAppViewContainer"] {
        background-color: #0e1117;
    }
    [data-testid="stSidebar"] {
        background-color: #262730;
    }
</style>
""",
    unsafe_allow_html=True,
)


def check_password():
    def password_entered():
        password = st.session_state.get("password", "")
        correct_password = os.environ.get("DASHBOARD_PASSWORD", "changeme123")

        if hmac.compare_digest(password, correct_password):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown(
        '<h1 style="text-align: center;">🔐 MeriNetWorth Login</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align: center; color: #666;">Enter password to access your financial dashboard</p>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            label_visibility="collapsed",
            placeholder="Enter your password",
        )

        if st.session_state.get("password_correct") is False:
            st.error("Password incorrect. Please try again.")

        st.info("Password is set via environment variable `DASHBOARD_PASSWORD`")

    return False


BASE_PATH = Path(os.environ.get("BASE_PATH", Path(__file__).parent.parent))


@st.cache_data
def load_data():
    if not DATA_FILE.exists():
        return None

    with open(DATA_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_equity_data():
    if not EQUITY_FILE.exists():
        return None

    with open(EQUITY_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_networth_data():
    if not NETWORTH_FILE.exists():
        return None

    with open(NETWORTH_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_mf_data():
    mf_file = OUTPUT_PATH / "mf_data.json"
    if not mf_file.exists():
        return None

    with open(mf_file, "r") as f:
        return json.load(f)


@st.cache_data
def load_liabilities_data():
    if not LIABILITIES_FILE.exists():
        return None

    with open(LIABILITIES_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_pension_data():
    if not PENSION_FILE.exists():
        return None
    with open(PENSION_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_fixed_income_data():
    if not FIXED_INCOME_FILE.exists():
        return None
    with open(FIXED_INCOME_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_real_estate_data():
    if not REAL_ESTATE_FILE.exists():
        return None
    with open(REAL_ESTATE_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_other_assets_data():
    if not OTHER_ASSETS_FILE.exists():
        return None
    with open(OTHER_ASSETS_FILE, "r") as f:
        return json.load(f)



def format_currency(amount):
    if amount >= 10000000:
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.2f}"


def filter_by_search(items: list, search_query: str, search_fields: list) -> tuple[list, bool]:
    if not search_query:
        return items, True

    search_lower = search_query.lower()
    filtered = [
        item for item in items
        if any(search_lower in str(item.get(field, "")).lower() for field in search_fields)
    ]
    return filtered, len(filtered) > 0


def display_search_results(count: int, search_query: str, item_type: str = "holding") -> None:
    if count > 0:
        st.info(f"Found {count} {item_type}(s) matching '{search_query}'")
    else:
        st.warning(f"No {item_type}s found matching '{search_query}'")


def limit_results(items: list, limit: int, is_searching: bool) -> list:
    return items if is_searching else items[:limit]


def sync_equity_prices():
    import sys

    sys.path.append(str(BASE_PATH / "src"))

    try:
        from process_equity import (
            process_all_equity_statements,
            save_equity_json,
            combine_bank_and_equity_data,
        )

        equity_path = BASE_PATH / "data" / "10.25" / "equity"
        equity_data = process_all_equity_statements(equity_path, sync_prices=True)

        save_equity_json(equity_data, OUTPUT_PATH)

        bank_data = load_data()
        if bank_data:
            combine_bank_and_equity_data(bank_data, equity_data, OUTPUT_PATH)

        load_equity_data.clear()
        load_networth_data.clear()

        return True
    except Exception as e:
        st.error(f"Error syncing prices: {str(e)}")
        return False


def main():
    if not check_password():
        st.stop()

    st.markdown('<h1 class="main-header">💰 MeriNetWorth</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #666; font-size: 1.2rem;">Complete Net Worth Dashboard</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    data = load_data()
    equity_data = load_equity_data()
    mf_data = load_mf_data()
    networth_data = load_networth_data()
    liabilities_data = load_liabilities_data()
    pension_data = load_pension_data()
    fixed_income_data = load_fixed_income_data()
    real_estate_data = load_real_estate_data()
    other_assets_data = load_other_assets_data()

    if data is None:
        st.error(
            "No bank data found! Please run the Jupyter notebook first to process bank statements."
        )
        st.info("Run: `notebooks/bank_data_processor.ipynb`")
        return

    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/money-bag.png", width=80)
        st.title("Dashboard Controls")
        st.markdown("---")

        generated_at = datetime.fromisoformat(data["generated_at"])
        st.info(f"Last Updated\n\n{generated_at.strftime('%d %b %Y, %I:%M %p')}")

        st.markdown("### Filters")
        banks = list(data["banks"].keys())
        selected_banks = st.multiselect("Select Banks", options=banks, default=banks)

        st.markdown("### Search")
        search_bank = st.text_input("Bank Search", placeholder="Account, holder, or bank name...", key="search_bank")
        search_equity = st.text_input("Equity Search", placeholder="Security name or ISIN...", key="search_equity")
        search_mf = st.text_input("MF Search", placeholder="Scheme name or folio...", key="search_mf")

        st.markdown("### View Options")
        show_accounts = st.checkbox("Show Account Details", value=True)
        show_charts = st.checkbox("Show Charts", value=True)

        if equity_data:
            st.markdown("---")
            st.markdown("### Equity Actions")
            if st.button("Sync Prices (Upstox)", use_container_width=True):
                with st.spinner("Syncing prices..."):
                    if sync_equity_prices():
                        st.success("Prices synced successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to sync prices")

        st.markdown("---")
        st.markdown("### Quick Stats")
        st.metric("Total Banks", len(data["banks"]))
        st.metric("Bank Accounts", data["total_accounts"])
        if equity_data:
            st.metric("Equity Holdings", equity_data.get("total_holdings", 0))
        if mf_data:
            st.metric("MF Holdings", mf_data.get("total_holdings", 0))

    total_networth = data["total_balance"]
    equity_value = 0.0
    mf_value = 0.0
    pension_value = 0.0
    fixed_income_value = 0.0
    real_estate_value = 0.0
    other_assets_value = 0.0
    total_liabilities = 0.0

    if equity_data:
        equity_value = equity_data.get("total_value", 0.0)
        total_networth += equity_value

    if mf_data:
        mf_value = mf_data.get("total_value", 0.0)
        total_networth += mf_value

    if pension_data:
        pension_value = pension_data.get("total_value", 0.0)
        total_networth += pension_value

    if fixed_income_data:
        fixed_income_value = fixed_income_data.get("total_principal", 0.0)
        total_networth += fixed_income_value

    if real_estate_data:
        real_estate_value = real_estate_data.get("total_value", 0.0)
        total_networth += real_estate_value

    if other_assets_data:
        other_assets_value = other_assets_data.get("total_value", 0.0)
        total_networth += other_assets_value

    if liabilities_data:
        total_liabilities = liabilities_data.get("total_liability", 0.0)
        total_networth -= total_liabilities

    col1, col2, col3, col4, col5 = st.columns(5)


    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Net Worth</h3>
            <h2>{format_currency(total_networth)}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>Bank Balance</h3>
            <h2>{format_currency(data['total_balance'])}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3>Equity Value</h3>
            <h2>{format_currency(equity_value)}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
            <h3>Mutual Funds</h3>
            <h2>{format_currency(mf_value)}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col5:
        liability_color = "#ff6b6b" if total_liabilities > 0 else "#4CAF50"
        st.markdown(
            f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);">
            <h3>Liabilities</h3>
            <h2>-{format_currency(total_liabilities)}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    tab_bank, tab_equity, tab_mf, tab_pension, tab_fixed_income, tab_real_estate, tab_other, tab_liabilities, tab_tax = st.tabs([
        "Banks", "Equity", "Mutual Funds", "Pension", "Fixed Income", "Real Estate", "Other Assets", "Liabilities", "Tax Computation"
    ])

    with tab_bank:
        filtered_accounts = [acc for acc in data["accounts"] if acc["bank"] in selected_banks]

        bank_search_fields = ["account_number", "holder_name", "first_holder", "second_holder", "bank"]
        filtered_accounts, has_results = filter_by_search(filtered_accounts, search_bank, bank_search_fields)

        if search_bank:
            display_search_results(len(filtered_accounts), search_bank, "account")

        if show_charts:
            st.markdown("## Visual Analytics")

            tab1, tab2, tab3 = st.tabs(["Distribution", "Comparison", "Details"])

            with tab1:
                col1, col2 = st.columns(2)

                with col1:
                    bank_balances = {
                        bank: sum([acc["balance"] for acc in filtered_accounts if acc["bank"] == bank])
                        for bank in selected_banks
                    }

                    fig = px.pie(
                        values=list(bank_balances.values()),
                        names=list(bank_balances.keys()),
                        title="Balance Distribution by Bank",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set3,
                    )
                    fig.update_traces(textposition="inside", textinfo="percent+label")
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    df_accounts = pd.DataFrame(filtered_accounts)
                    fig = px.sunburst(
                        df_accounts,
                        path=["bank", "account_number"],
                        values="balance",
                        title="Account Hierarchy",
                        color="balance",
                        color_continuous_scale="Viridis",
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tab2:
                bank_data = []
                for bank in selected_banks:
                    balance = sum([acc["balance"] for acc in filtered_accounts if acc["bank"] == bank])
                    accounts = len([acc for acc in filtered_accounts if acc["bank"] == bank])
                    bank_data.append({"Bank": bank, "Balance": balance, "Accounts": accounts})

                df_banks = pd.DataFrame(bank_data)

                fig = go.Figure(
                    data=[
                        go.Bar(
                            name="Balance",
                            x=df_banks["Bank"],
                            y=df_banks["Balance"],
                            marker_color="indianred",
                        ),
                        go.Bar(
                            name="Accounts (x10000)",
                            x=df_banks["Bank"],
                            y=df_banks["Accounts"] * 10000,
                            marker_color="lightseagreen",
                        ),
                    ]
                )
                fig.update_layout(
                    title="Balance vs Number of Accounts by Bank",
                    barmode="group",
                    xaxis_title="Bank",
                    yaxis_title="Amount (₹)",
                )
                st.plotly_chart(fig, use_container_width=True)

                df_accounts = pd.DataFrame(filtered_accounts)
                fig = px.treemap(
                    df_accounts,
                    path=["bank", "holder_name", "account_number"],
                    values="balance",
                    title="Balance Treemap",
                    color="balance",
                    color_continuous_scale="RdYlGn",
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab3:
                df_accounts = pd.DataFrame(filtered_accounts)
                fig = px.box(
                    df_accounts,
                    x="bank",
                    y="balance",
                    title="Balance Distribution by Bank",
                    color="bank",
                    points="all",
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("## Bank-wise Summary")

        for bank in selected_banks:
            bank_accounts = [acc for acc in filtered_accounts if acc["bank"] == bank]
            total = sum([acc["balance"] for acc in bank_accounts])

            with st.expander(
                f"**{bank}** - {format_currency(total)} ({len(bank_accounts)} accounts)", expanded=False
            ):
                for acc in bank_accounts:
                    holder_info = []
                    if acc.get('first_holder'):
                        holder_info.append(f"<strong>First Holder:</strong> {acc['first_holder']}")
                    if acc.get('second_holder'):
                        holder_info.append(f"<strong>Second Holder:</strong> {acc['second_holder']}")
                    if acc.get('nominee'):
                        holder_info.append(f"<strong>Nominee:</strong> {acc['nominee']}")

                    holder_html = "<br>".join(holder_info) if holder_info else f"<strong>Holder:</strong> {acc.get('holder_name') or 'N/A'}"

                    st.markdown(
                        f"""
                    <div class="bank-card">
                        <strong>Account:</strong> {acc['account_number']}<br>
                        {holder_html}<br>
                        <strong>Balance:</strong> <span style="color: green; font-weight: bold;">{format_currency(acc['balance'])}</span><br>
                        <small style="color: #666;">Source: {acc['source_file']}</small>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        if show_accounts:
            st.markdown("## All Accounts")
            df_display = pd.DataFrame(filtered_accounts)
            df_display["balance"] = df_display["balance"].apply(format_currency)

            columns = ["bank", "account_number"]
            column_names = ["Bank", "Account Number"]

            if "first_holder" in df_display.columns:
                columns.append("first_holder")
                column_names.append("First Holder")
            if "second_holder" in df_display.columns:
                columns.append("second_holder")
                column_names.append("Second Holder")
            if "nominee" in df_display.columns:
                columns.append("nominee")
                column_names.append("Nominee")

            columns.extend(["balance", "source_file"])
            column_names.extend(["Balance", "Source File"])

            df_display = df_display[columns]
            df_display.columns = column_names

            st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab_equity:
        if equity_data:
            st.markdown("## Equity Holdings")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Holdings", equity_data.get("total_holdings", 0))
            with col2:
                st.metric("Total Value", format_currency(equity_data.get("total_value", 0)))
            with col3:
                st.metric("Demat Accounts", equity_data.get("total_accounts", 0))

            if "consolidated_holdings" in equity_data and equity_data["consolidated_holdings"]:
                st.markdown("### Top Holdings")

                holdings_list = equity_data["consolidated_holdings"]
                equity_search_fields = ["name", "isin"]
                holdings_list, has_results = filter_by_search(holdings_list, search_equity, equity_search_fields)

                if search_equity:
                    display_search_results(len(holdings_list), search_equity, "holding")

                holdings_list = limit_results(holdings_list, 20, bool(search_equity))

                df_holdings = pd.DataFrame(holdings_list)

                df_holdings["value_display"] = df_holdings["total_value"].apply(format_currency)
                df_holdings["price_display"] = df_holdings["last_price"].apply(lambda x: f"₹{x:,.2f}")
                df_holdings["qty_display"] = df_holdings["total_quantity"].apply(
                    lambda x: f"{int(x):,}"
                )

                display_cols = ["name", "qty_display", "price_display", "value_display"]
                display_df = df_holdings[display_cols]
                display_df.columns = ["Security Name", "Quantity", "LTP", "Value"]

                st.dataframe(display_df, use_container_width=True, hide_index=True)

                if len(holdings_list) > 0:
                    fig = px.pie(
                        df_holdings.head(10),
                        values="total_value",
                        names="name",
                        title="Top 10 Holdings Distribution",
                        hole=0.4,
                    )
                    fig.update_traces(textposition="inside", textinfo="percent+label")
                    st.plotly_chart(fig, use_container_width=True)

            if "accounts" in equity_data:
                st.markdown("### Holdings by Demat Account")

                for account in equity_data["accounts"]:
                    depository = account.get("depository", "Unknown")
                    client_id = account.get("client_id", "")
                    holder = account.get("holder_name", "")
                    value = account.get("total_value", 0)
                    count = account.get("total_holdings", 0)

                    title = f"**{depository}** - {holder} ({client_id})"
                    subtitle = f"{format_currency(value)} ({count} holdings)"

                    with st.expander(f"{title} - {subtitle}", expanded=False):
                        if "holdings" in account and account["holdings"]:
                            for holding in account["holdings"]:
                                st.markdown(
                                    f"""
                                <div class="bank-card">
                                    <strong>{holding.get('name', 'N/A')}</strong><br>
                                    ISIN: {holding.get('isin', 'N/A')}<br>
                                    Quantity: {int(holding.get('quantity', 0)):,} |
                                    LTP: ₹{holding.get('last_price', 0):,.2f} |
                                    Value: <span style="color: green; font-weight: bold;">{format_currency(holding.get('value', 0))}</span>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
        else:
            st.info("No equity data available. Process equity statements to view holdings.")

    with tab_mf:
        if mf_data:
            st.markdown("## Mutual Fund Holdings")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Holdings", mf_data.get("total_holdings", 0))
            with col2:
                st.metric("Total Value", format_currency(mf_data.get("total_value", 0)))
            with col3:
                st.metric("Total Accounts", mf_data.get("total_accounts", 0))

            if "accounts" in mf_data:
                all_holdings = []
                for account in mf_data["accounts"]:
                    for holding in account.get("soa_holdings", []):
                        all_holdings.append({
                            "scheme": holding.get("scheme", ""),
                            "folio": holding.get("folio", ""),
                            "units": holding.get("units", 0),
                            "nav": holding.get("nav", 0),
                            "market_value": holding.get("market_value", 0),
                            "invested_value": holding.get("invested_value", 0),
                        })

                if all_holdings:
                    mf_search_fields = ["scheme", "folio"]
                    all_holdings, has_results = filter_by_search(all_holdings, search_mf, mf_search_fields)

                    if search_mf:
                        display_search_results(len(all_holdings), search_mf, "holding")

                    all_holdings.sort(key=lambda x: x["market_value"], reverse=True)

                    st.markdown("### Top Holdings")

                    display_holdings = limit_results(all_holdings, 20, bool(search_mf))
                    df_mf = pd.DataFrame(display_holdings)

                    df_mf["value_display"] = df_mf["market_value"].apply(format_currency)
                    df_mf["invested_display"] = df_mf["invested_value"].apply(format_currency)
                    df_mf["nav_display"] = df_mf["nav"].apply(lambda x: f"₹{x:,.2f}")
                    df_mf["units_display"] = df_mf["units"].apply(lambda x: f"{x:,.2f}")
                    df_mf["gain"] = ((df_mf["market_value"] - df_mf["invested_value"]) / df_mf["invested_value"] * 100).apply(lambda x: f"{x:+.2f}%")

                    display_cols = ["scheme", "units_display", "nav_display", "invested_display", "value_display", "gain"]
                    display_df = df_mf[display_cols]
                    display_df.columns = ["Scheme Name", "Units", "NAV", "Invested", "Current Value", "Returns"]

                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                    if len(all_holdings) > 0:
                        fig = px.pie(
                            df_mf.head(10),
                            values="market_value",
                            names="scheme",
                            title="Top 10 MF Holdings Distribution",
                            hole=0.4,
                        )
                        fig.update_traces(textposition="inside", textinfo="percent+label")
                        st.plotly_chart(fig, use_container_width=True)

                    top_10 = df_mf.head(10).copy()
                    top_10["gain_pct"] = ((top_10["market_value"] - top_10["invested_value"]) / top_10["invested_value"] * 100)

                    fig = px.bar(
                        top_10,
                        x="scheme",
                        y="gain_pct",
                        title="Top 10 Holdings Performance (%)",
                        labels={"scheme": "Scheme", "gain_pct": "Returns (%)"},
                        color="gain_pct",
                        color_continuous_scale=["red", "yellow", "green"],
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("### Holdings by Account")

                for account in mf_data["accounts"]:
                    pan = account.get("pan", "")
                    holder = account.get("holder_name", "")
                    soa_holdings = account.get("soa_holdings", [])
                    total_soa_value = sum(h.get("market_value", 0) for h in soa_holdings)

                    title = f"**{holder}** ({pan})"
                    subtitle = f"{format_currency(total_soa_value)} ({len(soa_holdings)} holdings)"

                    with st.expander(f"{title} - {subtitle}", expanded=False):
                        if soa_holdings:
                            for holding in soa_holdings:
                                gain = holding.get("market_value", 0) - holding.get("invested_value", 0)
                                gain_pct = (gain / holding.get("invested_value", 1)) * 100 if holding.get("invested_value", 0) > 0 else 0
                                gain_color = "green" if gain >= 0 else "red"

                                st.markdown(
                                    f"""
                                <div class="bank-card">
                                    <strong>{holding.get('scheme', 'N/A')}</strong><br>
                                    Folio: {holding.get('folio', 'N/A')} | Units: {holding.get('units', 0):,.2f}<br>
                                    NAV: ₹{holding.get('nav', 0):,.2f} (as of {holding.get('nav_date', 'N/A')})<br>
                                    Invested: {format_currency(holding.get('invested_value', 0))} |
                                    Current: <span style="color: green; font-weight: bold;">{format_currency(holding.get('market_value', 0))}</span><br>
                                    Gain: <span style="color: {gain_color}; font-weight: bold;">{format_currency(gain)} ({gain_pct:+.2f}%)</span>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
        else:
            st.info("No mutual fund data available. Process MF statements to view holdings.")

    with tab_pension:
        st.markdown("## Pension (NPS/EPF)")
        if pension_data and "accounts" in pension_data:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Value", format_currency(pension_data.get("total_value", 0)))
            with col2:
                st.metric("Accounts", pension_data.get("account_count", 0))

            st.markdown("### Accounts")
            for acc in pension_data["accounts"]:
                st.markdown(
                    f"""
                    <div class="bank-card">
                        <strong>{acc.get('name', 'Unknown')}</strong> ({acc.get('type', 'NPS')})<br>
                        <strong>Value:</strong> <span style="color: green; font-weight: bold;">{format_currency(acc.get('value', 0))}</span><br>
                        <small>Source: {acc.get('source_file')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No pension data available.")

    with tab_fixed_income:
        st.markdown("## Fixed Income (Term Deposits)")
        if fixed_income_data and "deposits" in fixed_income_data:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Principal", format_currency(fixed_income_data.get("total_principal", 0)))
            with col2:
                st.metric("Total Deposits", fixed_income_data.get("deposit_count", 0))

            if "by_bank" in fixed_income_data:
                st.markdown("### By Bank")
                bank_data = []
                for bank, info in fixed_income_data["by_bank"].items():
                    bank_data.append({"Bank": bank, "Amount": info["principal"], "Count": info["count"]})

                if bank_data:
                    df_fd_bank = pd.DataFrame(bank_data)
                    fig = px.pie(df_fd_bank, values="Amount", names="Bank", title="FD Distribution", hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Deposit Details")
            for dep in fixed_income_data["deposits"]:
                amount_val = dep.get('amount') if 'amount' in dep else dep.get('Amount', 0)
                holders_val = dep.get('holders') or dep.get('Holders', '')
                st.markdown(
                    f"""
                    <div class="bank-card">
                        <strong>{dep.get('bank')}</strong> - {dep.get('fd_number', 'N/A')}<br>
                        Amount: {format_currency(amount_val)} | Rate: {dep.get('interest_rate')}%<br>
                        Maturity: {dep.get('maturity_date')} | Holders: {holders_val}<br>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No fixed income data available.")

    with tab_real_estate:
        st.markdown("## Real Estate")
        if real_estate_data and "assets" in real_estate_data:
            st.metric("Total Value", format_currency(real_estate_data.get("total_value", 0)))

            st.markdown("### Properties")
            for prop in real_estate_data["assets"]:
                st.markdown(
                    f"""
                    <div class="bank-card">
                        <strong>{prop.get('name')}</strong><br>
                        Value: {format_currency(prop.get('value', 0))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No real estate data available.")

    with tab_other_assets:
        st.markdown("## Other Assets")
        if other_assets_data and "assets" in other_assets_data:
            st.metric("Total Value", format_currency(other_assets_data.get("total_value", 0)))

            st.markdown("### Assets")
            for asset in other_assets_data["assets"]:
                st.markdown(
                    f"""
                    <div class="bank-card">
                        <strong>{asset.get('name')}</strong><br>
                        Value: {format_currency(asset.get('value', 0))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No other assets data available.")

    with tab_liabilities:
        st.markdown("## Liabilities & Obligations")

        if liabilities_data and liabilities_data.get("liabilities"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Liability", format_currency(liabilities_data.get("total_liability", 0)))
            with col2:
                st.metric("Total Receivable", format_currency(liabilities_data.get("total_receivable", 0)))
            with col3:
                net_pos = liabilities_data.get("net_position", 0)
                net_color = "green" if net_pos >= 0 else "red"
                st.metric("Net Position", format_currency(abs(net_pos)),
                         delta="Receivable" if net_pos >= 0 else "Payable",
                         delta_color="normal" if net_pos >= 0 else "inverse")

            st.markdown("### Liability Details")

            for liability_file in liabilities_data.get("liabilities", []):
                source = liability_file.get("source_file", "Unknown")
                net_liability = liability_file.get("net_liability", 0)
                txn_count = liability_file.get("transaction_count", 0)

                with st.expander(f"**{source}** - Net Liability: {format_currency(net_liability)} ({txn_count} transactions)", expanded=True):
                    transactions = liability_file.get("transactions", [])

                    if transactions:
                        # Create a dataframe for display
                        df_txn = pd.DataFrame(transactions)

                        # Format for display
                        df_display = df_txn.copy()
                        df_display["amount_display"] = df_display["amount_inr"].apply(
                            lambda x: f"₹{x:,.2f}" if x >= 0 else f"-₹{abs(x):,.2f}"
                        )
                        df_display["type"] = df_display["amount_inr"].apply(
                            lambda x: "Received" if x > 0 else "Owed"
                        )

                        # Select and rename columns
                        display_cols = ["date", "beneficiary", "amount_display", "type"]
                        display_df = df_display[display_cols]
                        display_df.columns = ["Date", "Description", "Amount", "Type"]

                        st.dataframe(display_df, use_container_width=True, hide_index=True)

                        # Summary by type
                        received = sum(t["amount_inr"] for t in transactions if t["amount_inr"] > 0)
                        owed = abs(sum(t["amount_inr"] for t in transactions if t["amount_inr"] < 0))

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(
                                f"""
                                <div class="bank-card" style="border-left-color: #4CAF50;">
                                    <strong>Total Received/Paid Back:</strong> <span style="color: green;">{format_currency(received)}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with col2:
                            st.markdown(
                                f"""
                                <div class="bank-card" style="border-left-color: #e74c3c;">
                                    <strong>Total Owed:</strong> <span style="color: red;">{format_currency(owed)}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
        else:
            st.info("No liabilities data available. Process liabilities to view details.")
            st.markdown("""
            **To add liabilities:**
            1. Add CSV files to `data/MM.YY/liabilities/`
            2. Run the liability parser to generate `output/liabilities_data.json`

            **Expected CSV format:**
            - Date, Beneficiary, Amount (INR), Amount (Euro), Exchange Rate
            - Negative amounts = money owed, Positive amounts = money received/paid back
            """)

    with tab_tax:
        st.markdown("## Tax Computation by PAN")
        st.markdown(
            """
            <div style="background: rgba(255,193,7,0.1); padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 20px;">
                <strong>⚠️ Disclaimer:</strong> This is an <strong>ESTIMATE</strong> for informational purposes only.
                Actual tax liability depends on realized gains, other income sources, deductions claimed, and professional tax advice.
                Tax rules shown are for FY 2025-26 (AY 2026-27).
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Aggregate assets by PAN
        aggregated = aggregate_by_pan(
            bank_data=data,
            equity_data=equity_data,
            mf_data=mf_data,
            pension_data=pension_data,
            fixed_income_data=fixed_income_data,
            real_estate_data=real_estate_data,
            other_assets_data=other_assets_data,
            liabilities_data=liabilities_data
        )

        # Estimate dividends by PAN
        dividend_estimates = estimate_dividends_by_pan(aggregated, equity_data)

        # Filter out UNKNOWN if present
        valid_pans = [pan for pan in aggregated.keys() if pan != "UNKNOWN"]

        if not valid_pans:
            st.warning("No PAN mappings found. Please configure src/pan_config.py with holder-to-PAN mappings.")
        else:
            # Summary cards for all PANs
            st.markdown("### Individual Net Worth Summary")

            cols = st.columns(min(len(valid_pans), 3))
            for idx, pan in enumerate(valid_pans):
                assets = aggregated[pan]
                with cols[idx % 3]:
                    st.markdown(
                        f"""
                        <div class="metric-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); margin-bottom: 15px;">
                            <h4>{assets.holder_name}</h4>
                            <p style="font-size: 0.8rem; opacity: 0.8;">PAN: {pan}</p>
                            <h3>{format_currency(assets.total_assets)}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("---")

            # Detailed tax computation for each PAN
            for pan in valid_pans:
                assets = aggregated[pan]
                holder_info = get_holder_info(pan)

                if not holder_info:
                    continue

                # Compute tax
                mf_gains = {
                    "invested": assets.total_mf_invested,
                    "current": assets.total_mf_value,
                }

                # Get dividend estimate for this PAN
                div_summary = dividend_estimates.get(pan)
                dividend_income = div_summary.estimated_annual_dividend if div_summary else 0
                dividend_tds = div_summary.estimated_tds if div_summary else 0

                tax_breakdown = compute_tax_for_individual(
                    pan=pan,
                    holder_info=holder_info,
                    bank_balance=assets.total_bank_balance,
                    bank_accounts=assets.bank_accounts,
                    equity_value=assets.total_equity_value,
                    mf_value=assets.total_mf_value,
                    nps_value=assets.total_pension_value,
                    mf_gains=mf_gains,
                    dividend_income=dividend_income,
                    dividend_tds=dividend_tds,
                )

                # Expandable section for each person
                with st.expander(
                    f"**{assets.holder_name}** ({pan}) - Net Worth: {format_currency(assets.total_assets)}",
                    expanded=len(valid_pans) <= 2
                ):
                    # Asset breakdown
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### Asset Breakdown")

                        asset_data = {
                            "Category": ["Bank Balance", "Equity Holdings", "Mutual Funds", "Pension/NPS", "Fixed Income", "Real Estate", "Other Assets"],
                            "Value": [
                                assets.total_bank_balance,
                                assets.total_equity_value,
                                assets.total_mf_value,
                                assets.total_pension_value,
                                assets.total_fixed_income_value,
                                assets.total_real_estate_value,
                                assets.total_other_assets_value
                            ],
                        }
                        df_assets = pd.DataFrame(asset_data)
                        df_assets["Display"] = df_assets["Value"].apply(format_currency)

                        # Pie chart of assets
                        non_zero = df_assets[df_assets["Value"] > 0]
                        if len(non_zero) > 0:
                            fig = px.pie(
                                non_zero,
                                values="Value",
                                names="Category",
                                hole=0.4,
                                color_discrete_sequence=px.colors.qualitative.Set2,
                            )
                            fig.update_traces(textposition="inside", textinfo="percent+label")
                            fig.update_layout(
                                showlegend=False,
                                margin=dict(t=10, b=10, l=10, r=10),
                                height=250,
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        # Asset details
                        st.markdown(
                            f"""
                            <div class="bank-card">
                                <strong>🏦 Bank Balance:</strong> {format_currency(assets.total_bank_balance)}<br>
                                <small>({len(assets.bank_accounts)} accounts)</small>
                            </div>
                            <div class="bank-card">
                                <strong>📈 Equity Holdings:</strong> {format_currency(assets.total_equity_value)}<br>
                                <small>({assets.total_equity_holdings} holdings in {len(assets.demat_accounts)} demat accounts)</small>
                            </div>
                            <div class="bank-card">
                                <strong>💰 Mutual Funds:</strong> {format_currency(assets.total_mf_value)}<br>
                                <small>Invested: {format_currency(assets.total_mf_invested)} | Gain: {format_currency(assets.mf_unrealized_gain)}</small>
                            </div>
                            <div class="bank-card">
                                <strong>👴 Pension/NPS:</strong> {format_currency(assets.total_pension_value)}<br>
                                <small>({len(assets.pension_accounts)} accounts)</small>
                            </div>
                            <div class="bank-card">
                                <strong>🏦 Fixed Income:</strong> {format_currency(assets.total_fixed_income_value)}<br>
                                <small>({len(assets.fixed_income_accounts)} deposits)</small>
                            </div>
                            <div class="bank-card">
                                <strong>🏠 Real Estate:</strong> {format_currency(assets.total_real_estate_value)}<br>
                                <small>({len(assets.real_estate_assets)} properties)</small>
                            </div>
                            <div class="bank-card">
                                <strong>🪙 Other Assets:</strong> {format_currency(assets.total_other_assets_value)}<br>
                                <small>({len(assets.other_assets)} items)</small>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Top dividend stocks section
                        if div_summary and div_summary.top_dividend_stocks:
                            st.markdown("#### Top Dividend Stocks")
                            st.markdown(
                                f"""
                                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                                    <small>
                                        <strong>Annual Dividend (Est.):</strong> {format_currency(div_summary.estimated_annual_dividend)}<br>
                                        <strong>Avg Yield:</strong> {div_summary.average_dividend_yield:.2f}% |
                                        <strong>Stocks with data:</strong> {div_summary.holdings_with_dividend_data}/{div_summary.total_holdings}
                                    </small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            for stock in div_summary.top_dividend_stocks[:5]:
                                data_icon = "✓" if stock["has_data"] else "~"
                                st.markdown(
                                    f"""
                                    <div class="bank-card" style="padding: 8px;">
                                        <strong>{data_icon} {stock['name'][:25]}</strong><br>
                                        <small>Qty: {stock['quantity']:,.0f} | Dividend: {format_currency(stock['dividend'])} ({stock['yield_pct']:.1f}%)</small>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    with col2:
                        st.markdown("#### Estimated Tax (FY 2025-26)")

                        regime_color = "#4CAF50" if tax_breakdown.tax_regime == "new" else "#2196F3"
                        st.markdown(
                            f"""
                            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                                <p><strong>Tax Regime:</strong> <span style="color: {regime_color}; font-weight: bold;">{tax_breakdown.tax_regime.upper()}</span></p>
                                <p><strong>Assessment Year:</strong> {tax_breakdown.assessment_year}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Estimated income
                        st.markdown("**Estimated Income:**")

                        # Build interest breakdown display
                        if tax_breakdown.interest_by_bank:
                            # Show bank-wise breakdown
                            interest_details = []
                            for bank, info in tax_breakdown.interest_by_bank.items():
                                interest_details.append(
                                    f"&nbsp;&nbsp;• {bank}: {format_currency(info['total_interest'])} "
                                    f"(Bal: {format_currency(info['total_balance'])})"
                                )
                            breakdown_html = "<br>".join(interest_details)
                            description = "Based on bank-specific interest rates"
                        else:
                            breakdown_html = ""
                            description = "Based on 4% assumed rate on bank balance"

                        st.markdown(
                            f"""
                            <div class="bank-card">
                                <strong>Interest Income (Est.):</strong> {format_currency(tax_breakdown.estimated_interest)}<br>
                                <small>{description}</small>
                                {f"<br><small>{breakdown_html}</small>" if breakdown_html else ""}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Dividend income section
                        if tax_breakdown.estimated_dividend > 0:
                            st.markdown(
                                f"""
                                <div class="bank-card">
                                    <strong>💰 Dividend Income (Est.):</strong> {format_currency(tax_breakdown.estimated_dividend)}<br>
                                    <small>TDS @10%: {format_currency(tax_breakdown.dividend_tds)} | Net: {format_currency(tax_breakdown.estimated_dividend - tax_breakdown.dividend_tds)}</small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        if tax_breakdown.unrealized_ltcg > 0:
                            st.markdown(
                                f"""
                                <div class="bank-card">
                                    <strong>Unrealized LTCG (MF):</strong> {format_currency(tax_breakdown.unrealized_ltcg)}<br>
                                    <small>Tax @12.5% if realized (after ₹1.25L exemption)</small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        # Tax computation
                        st.markdown("**Tax Computation:**")

                        tax_color = "#4CAF50" if tax_breakdown.total_tax == 0 else "#FF9800"
                        st.markdown(
                            f"""
                            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;">
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr><td>Taxable Income:</td><td style="text-align: right;">{format_currency(tax_breakdown.taxable_income)}</td></tr>
                                    <tr><td>Basic Tax:</td><td style="text-align: right;">{format_currency(tax_breakdown.basic_tax)}</td></tr>
                                    <tr><td>Surcharge:</td><td style="text-align: right;">{format_currency(tax_breakdown.surcharge)}</td></tr>
                                    <tr><td>Cess (4%):</td><td style="text-align: right;">{format_currency(tax_breakdown.cess)}</td></tr>
                                    <tr style="border-top: 1px solid #666;"><td><strong>Total Tax:</strong></td><td style="text-align: right; color: {tax_color};"><strong>{format_currency(tax_breakdown.total_tax)}</strong></td></tr>
                                    <tr><td>TDS Deducted (Est.):</td><td style="text-align: right;">- {format_currency(tax_breakdown.tds_deducted)}</td></tr>
                                    <tr style="border-top: 1px solid #666;"><td><strong>Net Payable:</strong></td><td style="text-align: right;"><strong>{format_currency(tax_breakdown.net_tax_payable)}</strong></td></tr>
                                </table>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Notes
                        if tax_breakdown.notes:
                            st.markdown("**Notes:**")
                            for note in tax_breakdown.notes:
                                st.markdown(f"- {note}")

            # Unmapped accounts warning
            if "UNKNOWN" in aggregated:
                unknown = aggregated["UNKNOWN"]
                st.markdown("---")
                st.warning(
                    f"""
                    **⚠️ Unmapped Accounts Found**

                    The following accounts could not be mapped to a PAN:
                    - Bank Balance: {format_currency(unknown.total_bank_balance)} ({len(unknown.bank_accounts)} accounts)
                    - Equity Value: {format_currency(unknown.total_equity_value)} ({len(unknown.demat_accounts)} demat accounts)

                    Please update `src/pan_config.py` with the correct holder name mappings.
                    """
                )

                # Show unmapped account details
                with st.expander("View Unmapped Account Details"):
                    if unknown.bank_accounts:
                        st.markdown("**Bank Accounts:**")
                        for acc in unknown.bank_accounts:
                            st.markdown(f"- {acc['bank']}: {acc['holder_name']} - {format_currency(acc['balance'])}")

                    if unknown.demat_accounts:
                        st.markdown("**Demat Accounts:**")
                        for acc in unknown.demat_accounts:
                            st.markdown(f"- {acc['depository']} ({acc['dp_id']}): {acc['holder_name']} - {format_currency(acc['total_value'])}")

    st.markdown("---")
    st.markdown(
        """
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>Use the sidebar filters to customize your view</p>
        <p style="font-size: 0.9rem;">MeriNetWorth Dashboard v1.0 | Built with Streamlit</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
