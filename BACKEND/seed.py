"""
seed.py — Database Initialisation Script
=========================================
Run ONCE from the BACKEND/ folder to create banking.db and insert a
demo customer account.

Usage:
    python seed.py

Re-running is safe: the script uses CREATE TABLE IF NOT EXISTS and only
inserts the demo row when the table is empty, so existing data is never
overwritten.
"""

import os
import sqlite3

from werkzeug.security import generate_password_hash

# --------------------------------------------------------------------------- #
# Configuration — change the demo credentials here if needed                  #
# --------------------------------------------------------------------------- #
DEMO_USERNAME = "john_doe"
DEMO_PASSWORD = "password123"
DEMO_FULL_NAME = "John Doe"
DEMO_OPENING_BALANCE = 1000.00
# --------------------------------------------------------------------------- #

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banking.db")


def init_db() -> None:
    """Create the customers table if it does not already exist."""
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            full_name     TEXT    NOT NULL,
            balance       REAL    NOT NULL DEFAULT 0.0
        )
        """
    )
    conn.commit()
    conn.close()
    print(f"[seed] Table 'customers' ready  ->  {_DB_PATH}")


def seed_demo_customer() -> None:
    """Insert the demo customer only if the table is empty."""
    conn = sqlite3.connect(_DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

    if count > 0:
        print("[seed] Demo customer already exists — skipping insert.")
        conn.close()
        return

    hashed = generate_password_hash(DEMO_PASSWORD)
    conn.execute(
        "INSERT INTO customers (username, password_hash, full_name, balance) "
        "VALUES (?, ?, ?, ?)",
        (DEMO_USERNAME, hashed, DEMO_FULL_NAME, DEMO_OPENING_BALANCE),
    )
    conn.commit()
    conn.close()
    print(
        f"[seed] Demo customer created:\n"
        f"       username : {DEMO_USERNAME}\n"
        f"       password : {DEMO_PASSWORD}\n"
        f"       balance  : ${DEMO_OPENING_BALANCE:,.2f}"
    )


if __name__ == "__main__":
    init_db()
    seed_demo_customer()
    print("[seed] Done.")
