
from fastapi import FastAPI, HTTPException
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Create API application
# --------------------------------------------------

app = FastAPI(
    title="Project FORESIGHT Scoring Service",
    description="Returns demand planning and inventory risk results for SKUs.",
    version="1.0.0"
)

# --------------------------------------------------
# Load processed risk data
# --------------------------------------------------

DATA_PATH = (
    Path(__file__).resolve().parent
    / "../data/processed/final_risk.csv"
).resolve()

risk_data = pd.read_csv(DATA_PATH)

# --------------------------------------------------
# Single-SKU scoring endpoint
# --------------------------------------------------

@app.get("/score/{sku}")
def score_sku(sku: str):

    result = risk_data[
        risk_data["SKU"].str.upper() == sku.upper()
    ]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=f"SKU '{sku}' not found."
        )

    row = result.iloc[0]

    return {
        "SKU": row["SKU"],
        "Product_Name": row["Product_Name"],
        "Risk_Level": row["Risk_Level"],
        "Forecast_Units_4_Week": round(
            float(row["Cumulative_Forecast"]), 2
        ),
        "Available_Supply": round(
            float(row["Available_Supply"]), 2
        ),
        "Projected_Balance": round(
            float(row["Projected_Balance"]), 2
        ),
        "Recommended_Order_Qty": int(
            round(row["Recommended_Order_Qty"])
        ),
        "Sales_At_Risk": round(
            float(row["Sales_At_Risk"]), 2
        ),
        "Capital_Locked_Overstock": round(
            float(row["Capital_Locked_Overstock"]), 2
        ),
        "Recommended_Action": row["Recommended_Action"]
    }




# --------------------------------------------------
# Batch SKU scoring endpoint
# --------------------------------------------------

@app.get("/score-batch")
def score_batch(skus: str):

    # Convert comma-separated SKU input into a clean list.
    requested_skus = [
        item.strip().upper()
        for item in skus.split(",")
        if item.strip()
    ]

    if not requested_skus:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one SKU."
        )

    results = []

    for requested_sku in requested_skus:

        match = risk_data[
            risk_data["SKU"].str.upper() == requested_sku
        ]

        if match.empty:
            continue

        row = match.iloc[0]

        results.append({
            "SKU": row["SKU"],
            "Product_Name": row["Product_Name"],
            "Risk_Level": row["Risk_Level"],
            "Forecast_Units_4_Week": round(
                float(row["Cumulative_Forecast"]), 2
            ),
            "Available_Supply": round(
                float(row["Available_Supply"]), 2
            ),
            "Projected_Balance": round(
                float(row["Projected_Balance"]), 2
            ),
            "Recommended_Order_Qty": int(
                round(row["Recommended_Order_Qty"])
            ),
            "Sales_At_Risk": round(
                float(row["Sales_At_Risk"]), 2
            ),
            "Capital_Locked_Overstock": round(
                float(row["Capital_Locked_Overstock"]), 2
            ),
            "Recommended_Action": row["Recommended_Action"]
        })

    return {
        "requested_count": len(requested_skus),
        "matched_count": len(results),
        "results": results
    }


# --------------------------------------------------
# Health check endpoint
# --------------------------------------------------

@app.get("/")
def health_check():

    return {
        "service": "Project FORESIGHT Scoring Service",
        "status": "running",
        "sku_count": int(risk_data["SKU"].nunique())
    }
