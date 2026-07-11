"""
db.py — Database Access Layer
==============================
Single point of contact with banking.db.
No other module opens a database connection directly.

Functions
---------
get_connection()                        -> sqlite3.Connection
get_customer_by_username(username)      -> dict | None
get_customer_by_id(customer_id)         -> dict | None
update_balance(customer_id, new_balance)-> None
"""

import os
import sqlite3

# Absolute path to banking.db, resolved relative to this file so the app
# can be started from any working directory.
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banking.db")


def get_connection() -> sqlite3.Connection:
    """Open and return a connection to banking.db.

    Rows are returned as sqlite3.Row objects so columns are accessible by
    name (e.g. row["balance"]) instead of by positional index.
    """
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_customer_by_username(username: str):
    """Return the customer row matching *username*, or None if not found.

    Used by the login route to verify credentials.
    Parameterised query prevents SQL injection.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, username, password_hash, balance, full_name "
            "FROM customers WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
    # sqlite3.Row is not usable outside a connection context once the
    # connection is closed, so convert to a plain dict before returning.
    return dict(row) if row else None


def get_customer_by_id(customer_id: int):
    """Return the customer row matching *customer_id*, or None if not found.

    Used by the dashboard route to load the current balance after login.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, username, password_hash, balance, full_name "
            "FROM customers WHERE id = ?",
            (customer_id,),
        )
        row = cursor.fetchone()
    return dict(row) if row else None


def update_balance(customer_id: int, new_balance: float) -> None:
    """Persist *new_balance* for the given *customer_id*.

    Called after every validated deposit or withdrawal.
    The balance is stored as REAL (IEEE 754 double) in SQLite; for a
    production application a DECIMAL / integer-cents approach is preferred,
    but it is adequate for this workshop scope.
    """
    with get_connection() as conn:
        conn.execute(
            "UPDATE customers SET balance = ? WHERE id = ?",
            (new_balance, customer_id),
        )
        conn.commit()
