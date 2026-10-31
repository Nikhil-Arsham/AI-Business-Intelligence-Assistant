"""Automated tests for supported analytics and request validation."""
import pandas as pd
import pytest
from backend.app import create_app
from backend.database import get_connection
from backend.data_loader import import_sales_data


@pytest.fixture()
def client(tmp_path):
    # A tiny isolated dataset makes tests repeatable and independent of the real CSV.
    csv_path = tmp_path / "test_sales.csv"
    pd.DataFrame([
        ["T1", "03-01-2026", "Laptop", "Electronics", "North", "Online", 2, 100, 0, "Completed"],
        ["T2", "05-02-2026", "Mouse", "Accessories", "South", "Retail", 3, 50, 0, "Completed"],
        ["T3", "06-02-2026", "Laptop", "Electronics", "North", "Online", 1, 100, 0, "Completed"],
        ["T4", "07-02-2026", "Monitor", "Electronics", "West", "Retail", 1, 500, 0, "Returned"],
        ["T5", "08-02-2026", "Broken", "Other", "East", "Online", 0, 20, 0, "Completed"],
    ], columns=[
        "Transaction_Id", "Order_date", "Product", "Category", "Region",
        "Sales_channel", "Quantity", "Unit_price", "Discount_amount", "Status"
    ]).to_csv(csv_path, index=False)

    db_path = tmp_path / "test.db"
    connection = get_connection(db_path)
    report = import_sales_data(connection, csv_path)
    connection.close()
    app = create_app({"TESTING": True, "DB_PATH": db_path, "CSV_PATH": csv_path})
    with app.test_client() as test_client:
        yield test_client, report


def test_total_revenue(client):
    test_client, _ = client
    response = test_client.post("/api/ask", json={"question": "What is the total revenue?"})
    assert response.status_code == 200
    assert response.get_json()["supporting_data"][0]["value"] == 450


def test_top_product(client):
    test_client, _ = client
    response = test_client.post("/api/ask", json={"question": "Which product generated the highest revenue?"})
    assert response.get_json()["supporting_data"][0]["product"] == "Laptop"


def test_monthly_trend(client):
    test_client, _ = client
    response = test_client.post("/api/ask", json={"question": "Show monthly revenue trend"})
    assert len(response.get_json()["supporting_data"]) == 2


def test_top_region(client):
    test_client, _ = client
    response = test_client.post("/api/ask", json={"question": "Which region generated the highest sales?"})
    assert response.get_json()["supporting_data"][0]["region"] == "North"


def test_invalid_empty_request(client):
    test_client, _ = client
    response = test_client.post("/api/ask", json={"question": "  "})
    assert response.status_code == 400


def test_unsupported_question(client):
    test_client, _ = client
    response = test_client.post("/api/ask", json={"question": "What is the weather today?"})
    assert response.status_code == 200
    assert response.get_json()["intent"] == "unsupported"


def test_cleaning_excludes_returned_and_zero_quantity(client):
    _, report = client
    assert report["input_rows"] == 5
    assert report["returned_rows_excluded"] == 1
    assert report["zero_or_negative_quantity_rows_excluded"] == 1
    assert report["valid_rows_imported"] == 3
