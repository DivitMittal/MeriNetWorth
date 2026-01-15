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

from src.config import OUTPUT_PATH, DATA_FILE, EQUITY_FILE, NETWORTH_FILE

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


BASE_PATH = Path(os.environ.get("BASE_PATH", "/Users/div/Projects/MeriNetWorth"))


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

    if equity_data:
        equity_value = equity_data.get("total_value", 0.0)
        total_networth += equity_value

    if mf_data:
        mf_value = mf_data.get("total_value", 0.0)
        total_networth += mf_value

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>Total Net Worth</h3>
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

    st.markdown("<br>", unsafe_allow_html=True)

    tab_bank, tab_equity, tab_mf = st.tabs(["Banks", "Equity", "Mutual Funds"])

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
