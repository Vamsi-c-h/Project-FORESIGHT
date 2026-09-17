
import streamlit as st
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Project FORESIGHT",
    page_icon="📦",
    layout="wide"
)

# --------------------------------------------------
# Load processed risk data
# --------------------------------------------------

DATA_PATH = (
    Path(__file__).resolve().parent
    / "../data/processed/final_risk.csv"
).resolve()

risk_data = pd.read_csv(DATA_PATH)

def format_inr(value):
    value = float(value)
    if abs(value) >= 1e7:
        return f"₹{value / 1e7:.2f} Cr"
    if abs(value) >= 1e5:
        return f"₹{value / 1e5:.2f} lakh"
    return f"₹{value:,.0f}"


# --------------------------------------------------
# Dashboard title
# --------------------------------------------------

st.title("📦 Project FORESIGHT")
st.subheader("Inventory Demand & Risk Planning Dashboard")

st.markdown(
    "Use this dashboard to identify stockout risk, "
    "replenishment needs, and excess inventory."
)

# --------------------------------------------------
# Key metrics
# --------------------------------------------------

total_skus = risk_data["SKU"].nunique()

stockout_skus = (
    risk_data["Risk_Level"] == "Stockout Risk"
).sum()

replenishment_skus = (
    risk_data["Risk_Level"] == "Replenishment Risk"
).sum()

overstock_skus = (
    risk_data["Risk_Level"] == "Overstock Risk"
).sum()

healthy_skus = (
    risk_data["Risk_Level"] == "Healthy"
).sum()

sales_at_risk = risk_data["Sales_At_Risk"].sum()

capital_locked = risk_data[
    "Capital_Locked_Overstock"
].sum()

# --------------------------------------------------
# KPI cards
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total SKUs", total_skus)
col2.metric("🔴 Stockout Risk", stockout_skus)
col3.metric("🟠 Replenishment Risk", replenishment_skus)
col4.metric("🔵 Overstock Risk", overstock_skus)

st.divider()

col5, col6 = st.columns(2)

col5.metric(
    "Estimated Sales at Risk",
    format_inr(sales_at_risk)
)

col6.metric(
    "Capital Locked in Overstock",
    format_inr(capital_locked)
)

# --------------------------------------------------
# Risk distribution
# --------------------------------------------------

st.subheader("Risk Distribution")

risk_counts = (
    risk_data["Risk_Level"]
    .value_counts()
    .rename_axis("Risk Level")
    .reset_index(name="SKU Count")
)

st.bar_chart(
    risk_counts.set_index("Risk Level")
)

# --------------------------------------------------
# Planning Summary
# --------------------------------------------------

st.subheader("Planning Summary")

st.write(
    f"**{stockout_skus} SKUs** are currently projected "
    "to face stockout risk over the planning horizon."
)

st.write(
    f"**{replenishment_skus} SKUs** require review or "
    "replenishment based on the reorder-point rule."
)

st.write(
    f"**{overstock_skus} SKUs** show potential excess "
    "inventory relative to forecast demand and safety stock."
)

# --------------------------------------------------
# What Do I Reorder?
# --------------------------------------------------

st.divider()

st.subheader("🚨 What Do I Reorder?")

st.markdown(
    "Priority replenishment list based on projected demand, "
    "available supply, and safety stock."
)

reorder_data = risk_data[
    risk_data["Risk_Level"].isin(
        ["Stockout Risk", "Replenishment Risk"]
    )
].copy()

reorder_data = reorder_data[
    [
        "Priority",
        "SKU",
        "Product_Name",
        "Risk_Level",
        "Cumulative_Forecast",
        "Available_Supply",
        "Projected_Balance",
        "Recommended_Order_Qty",
        "Sales_At_Risk",
        "Recommended_Action"
    ]
].sort_values(
    ["Priority", "Recommended_Order_Qty"],
    ascending=[True, False]
)

# Format the table for easier reading
reorder_display = reorder_data.copy()

reorder_display["Cumulative_Forecast"] = (
    reorder_display["Cumulative_Forecast"].round(0).astype(int)
)

reorder_display["Available_Supply"] = (
    reorder_display["Available_Supply"].round(0).astype(int)
)

reorder_display["Projected_Balance"] = (
    reorder_display["Projected_Balance"].round(0).astype(int)
)

reorder_display["Sales_At_Risk"] = (
    reorder_display["Sales_At_Risk"].apply(format_inr)
)

reorder_display = reorder_display.rename(
    columns={
        "Priority": "Priority",
        "SKU": "SKU",
        "Product_Name": "Product",
        "Risk_Level": "Risk",
        "Cumulative_Forecast": "4-Week Forecast",
        "Available_Supply": "Available Supply",
        "Projected_Balance": "Projected Balance",
        "Recommended_Order_Qty": "Order Qty",
        "Sales_At_Risk": "Sales at Risk",
        "Recommended_Action": "Action"
    }
)

st.dataframe(
    reorder_display,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# SKU Forecast Explorer
# --------------------------------------------------

st.divider()

st.subheader("📈 SKU Forecast Explorer")

st.markdown(
    "Compare actual demand with the Random Forest forecast "
    "for the held-out evaluation period."
)

# Load forecast results
FORECAST_PATH = (
    Path(__file__).resolve().parent
    / "../data/processed/forecast_results.csv"
).resolve()

forecast_data = pd.read_csv(FORECAST_PATH)

# Convert date column
forecast_data["Date"] = pd.to_datetime(
    forecast_data["Date"]
)

# SKU selector
selected_sku = st.selectbox(
    "Select SKU",
    sorted(forecast_data["SKU"].unique())
)

# Filter selected SKU
sku_forecast = (
    forecast_data[
        forecast_data["SKU"] == selected_sku
    ]
    .sort_values("Date")
    .copy()
)

# Prepare chart data
forecast_chart = sku_forecast[
    ["Date", "Units_Sold", "Forecast_Units"]
].set_index("Date")

forecast_chart = forecast_chart.rename(
    columns={
        "Units_Sold": "Actual Demand",
        "Forecast_Units": "Forecast"
    }
)

# Display chart
st.line_chart(
    forecast_chart
)

# Display detailed forecast table
st.markdown("**Forecast Details**")

forecast_display = sku_forecast[
    [
        "Date",
        "Units_Sold",
        "Forecast_Units"
    ]
].copy()

forecast_display["Date"] = (
    forecast_display["Date"]
    .dt.strftime("%Y-%m-%d")
)

forecast_display["Units_Sold"] = (
    forecast_display["Units_Sold"]
    .round(0)
    .astype(int)
)

forecast_display["Forecast_Units"] = (
    forecast_display["Forecast_Units"]
    .round(1)
)

forecast_display = forecast_display.rename(
    columns={
        "Date": "Week",
        "Units_Sold": "Actual Demand",
        "Forecast_Units": "Forecast"
    }
)

st.dataframe(
    forecast_display,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# SKU Planning Detail
# --------------------------------------------------

st.divider()

st.subheader("🔎 SKU Planning Detail")

st.markdown(
    "Select a SKU to view its forecast, inventory position, "
    "risk, and recommended action."
)

selected_planning_sku = st.selectbox(
    "Select SKU for planning detail",
    sorted(risk_data["SKU"].unique()),
    key="planning_sku"
)

selected_row = risk_data[
    risk_data["SKU"] == selected_planning_sku
].iloc[0]

# Risk and action
st.markdown(
    f"### {selected_row['Product_Name']} — {selected_row['SKU']}"
)

st.write(
    f"**Risk Level:** {selected_row['Risk_Level']}"
)

st.write(
    f"**Recommended Action:** "
    f"{selected_row['Recommended_Action']}"
)

# Planning metrics
detail_col1, detail_col2, detail_col3 = st.columns(3)

detail_col1.metric(
    "4-Week Forecast",
    f"{selected_row['Cumulative_Forecast']:.0f} units"
)

detail_col2.metric(
    "Available Supply",
    f"{selected_row['Available_Supply']:.0f} units"
)

detail_col3.metric(
    "Projected Balance",
    f"{selected_row['Projected_Balance']:.0f} units"
)

detail_col4, detail_col5, detail_col6 = st.columns(3)

detail_col4.metric(
    "Recommended Order",
    f"{selected_row['Recommended_Order_Qty']:.0f} units"
)

detail_col5.metric(
    "Sales at Risk",
    format_inr(selected_row["Sales_At_Risk"])
)

detail_col6.metric(
    "Capital Locked",
    format_inr(selected_row["Capital_Locked_Overstock"])
)

# --------------------------------------------------
# Overstock section
# --------------------------------------------------

st.divider()

st.subheader("📦 Overstock Watchlist")

overstock_data = risk_data[
    risk_data["Risk_Level"] == "Overstock Risk"
].copy()

overstock_data = overstock_data[
    [
        "SKU",
        "Product_Name",
        "Excess_Units",
        "Cost_Price",
        "Capital_Locked_Overstock",
        "Recommended_Action"
    ]
].sort_values(
    "Capital_Locked_Overstock",
    ascending=False
)

overstock_display = overstock_data.copy()

overstock_display["Excess_Units"] = (
    overstock_display["Excess_Units"].round(0).astype(int)
)

overstock_display["Cost_Price"] = (
    overstock_display["Cost_Price"].round(2)
)

overstock_display["Capital_Locked_Overstock"] = (
    overstock_display["Capital_Locked_Overstock"].apply(format_inr)
)

overstock_display = overstock_display.rename(
    columns={
        "Product_Name": "Product",
        "Excess_Units": "Excess Units",
        "Cost_Price": "Cost Price",
        "Capital_Locked_Overstock": "Capital Locked",
        "Recommended_Action": "Action"
    }
)

st.dataframe(
    overstock_display,
    use_container_width=True,
    hide_index=True
)
