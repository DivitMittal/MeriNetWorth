"""
MeriNetWorth - Bank Account Dashboard
A web interface for visualizing consolidated bank account data
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import hmac
import os

# Page configuration
st.set_page_config(
    page_title="MeriNetWorth - Bank Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling with dark mode support
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
    /* Dark mode specific adjustments */
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


# Authentication function
def check_password():
    """Returns True if the user has entered correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        password = st.session_state.get("password", "")
        correct_password = os.environ.get("DASHBOARD_PASSWORD", "changeme123")

        if hmac.compare_digest(password, correct_password):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # First run or password not correct
    if st.session_state.get("password_correct", False):
        return True

    # Show login form
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
            st.error("😕 Password incorrect. Please try again.")

        st.info("💡 **Note**: Password is set via environment variable `DASHBOARD_PASSWORD`")

    return False


# Paths (configurable for different environments)
BASE_PATH = Path(os.environ.get("BASE_PATH", "/Users/div/Projects/MeriNetWorth"))
OUTPUT_PATH = BASE_PATH / "output"
DATA_FILE = OUTPUT_PATH / "bank_data.json"
EQUITY_FILE = OUTPUT_PATH / "equity_data.json"
NETWORTH_FILE = OUTPUT_PATH / "networth_data.json"


@st.cache_data
def load_data():
    """Load bank account data from JSON file"""
    if not DATA_FILE.exists():
        return None

    with open(DATA_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_equity_data():
    """Load equity holdings data from JSON file"""
    if not EQUITY_FILE.exists():
        return None

    with open(EQUITY_FILE, "r") as f:
        return json.load(f)


@st.cache_data
def load_networth_data():
    """Load combined networth data from JSON file"""
    if not NETWORTH_FILE.exists():
        return None

    with open(NETWORTH_FILE, "r") as f:
        return json.load(f)


def format_currency(amount):
    """Format amount in Indian currency format"""
    if amount >= 10000000:  # 1 Crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 Lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.2f}"


def sync_equity_prices():
    """
    Sync equity prices using Upstox API
    Returns: True if successful, False otherwise
    """
    import sys

    sys.path.append(str(BASE_PATH / "src"))

    try:
        from process_equity import (
            process_all_equity_statements,
            save_equity_json,
            combine_bank_and_equity_data,
        )

        # Process equity with price sync enabled
        equity_path = BASE_PATH / "data" / "10.25" / "equity"  # TODO: Make configurable
        equity_data = process_all_equity_statements(equity_path, sync_prices=True)

        # Save updated equity data
        save_equity_json(equity_data, OUTPUT_PATH)

        # Update combined networth if bank data exists
        bank_data = load_data()
        if bank_data:
            combine_bank_and_equity_data(bank_data, equity_data, OUTPUT_PATH)

        # Clear cache to reload fresh data
        load_equity_data.clear()
        load_networth_data.clear()

        return True
    except Exception as e:
        st.error(f"Error syncing prices: {str(e)}")
        return False


def main():
    # Check authentication first
    if not check_password():
        st.stop()

    # Header
    st.markdown('<h1 class="main-header">💰 MeriNetWorth</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="text-align: center; color: #666; font-size: 1.2rem;">Complete Net Worth Dashboard</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Load data
    data = load_data()
    equity_data = load_equity_data()
    networth_data = load_networth_data()

    if data is None:
        st.error(
            "⚠️ No bank data found! Please run the Jupyter notebook first to process bank statements."
        )
        st.info("📝 Run: `notebooks/bank_data_processor.ipynb`")
        return

    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/money-bag.png", width=80)
        st.title("Dashboard Controls")
        st.markdown("---")

        # Data refresh info
        generated_at = datetime.fromisoformat(data["generated_at"])
        st.info(f"📅 **Last Updated**\n\n{generated_at.strftime('%d %b %Y, %I:%M %p')}")

        # Filter options
        st.markdown("### 🔍 Filters")
        banks = list(data["banks"].keys())
        selected_banks = st.multiselect("Select Banks", options=banks, default=banks)

        # View options
        st.markdown("### 👁️ View Options")
        show_accounts = st.checkbox("Show Account Details", value=True)
        show_charts = st.checkbox("Show Charts", value=True)
        show_equity = st.checkbox("Show Equity Holdings", value=True if equity_data else False)

        # Equity sync button
        if equity_data:
            st.markdown("---")
            st.markdown("### 📈 Equity Actions")
            if st.button("🔄 Sync Prices (Upstox)", use_container_width=True):
                with st.spinner("Syncing prices..."):
                    if sync_equity_prices():
                        st.success("✅ Prices synced successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to sync prices")

        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        st.metric("Total Banks", len(data["banks"]))
        st.metric("Total Accounts", data["total_accounts"])
        if equity_data:
            st.metric("Equity Holdings", equity_data.get("total_holdings", 0))

    # Main content
    # Top metrics
    # Calculate total networth
    total_networth = data["total_balance"]
    equity_value = 0.0
    if equity_data:
        equity_value = equity_data.get("total_value", 0.0)
        total_networth += equity_value

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
        num_banks = len(data["banks"])
        num_holdings = equity_data.get("total_holdings", 0) if equity_data else 0
        st.markdown(
            f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <h3>Total Assets</h3>
            <h2>{num_banks + num_holdings}</h2>
            <p style="font-size: 0.9rem; margin-top: -10px;">{num_banks} Banks, {num_holdings} Holdings</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Filter data
    filtered_accounts = [acc for acc in data["accounts"] if acc["bank"] in selected_banks]

    # Charts section
    if show_charts:
        st.markdown("## 📊 Visual Analytics")

        tab1, tab2, tab3 = st.tabs(["🥧 Distribution", "📈 Comparison", "🎯 Details"])

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                # Pie chart
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
                # Sunburst chart showing bank → accounts
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
            # Bar chart
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

            # Treemap
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
            # Box plot showing balance distribution
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

    # Bank-wise summary
    st.markdown("## 🏦 Bank-wise Summary")

    for bank in selected_banks:
        bank_accounts = [acc for acc in filtered_accounts if acc["bank"] == bank]
        total = sum([acc["balance"] for acc in bank_accounts])

        with st.expander(
            f"**{bank}** - {format_currency(total)} ({len(bank_accounts)} accounts)", expanded=False
        ):
            for acc in bank_accounts:
                st.markdown(
                    f"""
                <div class="bank-card">
                    <strong>Account:</strong> {acc['account_number']}<br>
                    <strong>Holder:</strong> {acc['holder_name'] or 'N/A'}<br>
                    <strong>Balance:</strong> <span style="color: green; font-weight: bold;">{format_currency(acc['balance'])}</span><br>
                    <small style="color: #666;">Source: {acc['source_file']}</small>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    # Account details table
    if show_accounts:
        st.markdown("## 📋 All Accounts")
        df_display = pd.DataFrame(filtered_accounts)
        df_display["balance"] = df_display["balance"].apply(format_currency)
        df_display = df_display[["bank", "account_number", "holder_name", "balance", "source_file"]]
        df_display.columns = ["Bank", "Account Number", "Holder", "Balance", "Source File"]

        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Equity Holdings Section
    if show_equity and equity_data:
        st.markdown("---")
        st.markdown("## 📈 Equity Holdings")

        # Display equity summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Holdings", equity_data.get("total_holdings", 0))
        with col2:
            st.metric("Total Value", format_currency(equity_data.get("total_value", 0)))
        with col3:
            st.metric("Demat Accounts", equity_data.get("total_accounts", 0))

        # Display consolidated holdings
        if "consolidated_holdings" in equity_data and equity_data["consolidated_holdings"]:
            st.markdown("### 📊 Top Holdings")

            # Create DataFrame for display
            holdings_list = equity_data["consolidated_holdings"][:20]  # Top 20
            df_holdings = pd.DataFrame(holdings_list)

            # Format for display
            df_holdings["value_display"] = df_holdings["total_value"].apply(format_currency)
            df_holdings["price_display"] = df_holdings["last_price"].apply(lambda x: f"₹{x:,.2f}")
            df_holdings["qty_display"] = df_holdings["total_quantity"].apply(
                lambda x: f"{int(x):,}"
            )

            display_cols = ["name", "qty_display", "price_display", "value_display"]
            display_df = df_holdings[display_cols]
            display_df.columns = ["Security Name", "Quantity", "LTP", "Value"]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Equity pie chart
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

        # Display by depository
        if "accounts" in equity_data:
            st.markdown("### 🏦 Holdings by Demat Account")

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

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>💡 <strong>Tip:</strong> Use the sidebar filters to customize your view</p>
        <p style="font-size: 0.9rem;">MeriNetWorth Dashboard v1.0 | Built with Streamlit</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
