"""SQLite database setup and connection helpers."""
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT_DIR / "backend" / "sales.db"


def get_connection(db_path=DEFAULT_DB_PATH):
    """Open a SQLite connection and return rows that can be read by column name."""
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def create_table(connection):
    """Create the sales table if it does not already exist."""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            transaction_id TEXT PRIMARY KEY,
            order_date TEXT NOT NULL,
            product TEXT NOT NULL,
            category TEXT NOT NULL,
            region TEXT NOT NULL,
            sales_channel TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount_amount REAL NOT NULL,
            status TEXT NOT NULL,
            revenue REAL NOT NULL
        )
    """)
    connection.commit()
