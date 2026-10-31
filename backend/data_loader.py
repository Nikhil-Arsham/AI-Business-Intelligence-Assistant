"""Load, validate, clean, and import the supplied CSV file."""
from pathlib import Path
import pandas as pd
from backend.database import create_table

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = ROOT_DIR / "data" / "sales_data.csv"


def clean_sales_data(csv_path=DEFAULT_CSV_PATH):
    """Return valid completed sales and a small cleaning report.

    Policy: exclude returned transactions, rows with missing/invalid required
    values, and rows with quantity <= 0. Revenue = quantity * unit price - discount.
    """
    frame = pd.read_csv(csv_path)
    required = [
        "Transaction_Id", "Order_date", "Product", "Category", "Region",
        "Sales_channel", "Quantity", "Unit_price", "Discount_amount", "Status"
    ]
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")

    original_count = len(frame)
    frame["Order_date"] = pd.to_datetime(
        frame["Order_date"], format="%d-%m-%Y", errors="coerce"
    )
    for column in ["Quantity", "Unit_price", "Discount_amount"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    returned_count = int(frame["Status"].astype(str).str.strip().str.lower().eq("returned").sum())
    completed = frame[frame["Status"].astype(str).str.strip().str.lower() == "completed"].copy()

    required_values = [
        "Transaction_Id", "Order_date", "Product", "Category", "Region",
        "Sales_channel", "Quantity", "Unit_price", "Discount_amount"
    ]
    before_validation = len(completed)
    completed = completed.dropna(subset=required_values)
    invalid_count = before_validation - len(completed)

    zero_or_negative_count = int((completed["Quantity"] <= 0).sum())
    completed = completed[completed["Quantity"] > 0].copy()
    completed = completed[completed["Unit_price"] >= 0]
    completed = completed[completed["Discount_amount"] >= 0]

    completed["revenue"] = (
        completed["Quantity"] * completed["Unit_price"] - completed["Discount_amount"]
    )
    # A discount greater than the line value is not accepted as a valid sale.
    completed = completed[completed["revenue"] >= 0].copy()

    report = {
        "input_rows": original_count,
        "returned_rows_excluded": returned_count,
        "rows_with_missing_or_invalid_required_values_excluded": invalid_count,
        "zero_or_negative_quantity_rows_excluded": zero_or_negative_count,
        "valid_rows_imported": len(completed),
    }
    return completed, report


def import_sales_data(connection, csv_path=DEFAULT_CSV_PATH):
    """Replace table contents with the cleaned dataset and return import report."""
    create_table(connection)
    cleaned, report = clean_sales_data(csv_path)
    connection.execute("DELETE FROM sales")
    records = [
        (
            str(row.Transaction_Id), row.Order_date.strftime("%Y-%m-%d"),
            str(row.Product), str(row.Category), str(row.Region),
            str(row.Sales_channel), int(row.Quantity), float(row.Unit_price),
            float(row.Discount_amount), str(row.Status), float(row.revenue)
        )
        for row in cleaned.itertuples(index=False)
    ]
    connection.executemany("""
        INSERT INTO sales (
            transaction_id, order_date, product, category, region,
            sales_channel, quantity, unit_price, discount_amount, status, revenue
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    connection.commit()
    return report
