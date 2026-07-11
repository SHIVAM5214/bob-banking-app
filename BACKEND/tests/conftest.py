"""
conftest.py — Shared pytest fixtures
======================================
Provides:
  - an in-memory SQLite database pre-seeded with one demo customer
  - a Flask test client wired to that in-memory database

Every test module that imports app_client or db_conn automatically
receives a fresh, isolated environment — no files left on disk.
"""

import os
import sqlite3
import sys

import pytest
from werkzeug.security import generate_password_hash

# Make sure the BACKEND/ directory is on sys.path so fixtures can import
# app modules directly (db, auth, dashboard, app).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

# Demo credentials reused across all tests
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_pass_123"
TEST_FULL_NAME = "Test User"
TEST_OPENING_BALANCE = 500.00


def _create_schema(conn: sqlite3.Connection) -> None:
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


def _seed_customer(conn: sqlite3.Connection) -> int:
    """Insert the test customer and return its id."""
    cursor = conn.execute(
        "INSERT INTO customers (username, password_hash, full_name, balance) "
        "VALUES (?, ?, ?, ?)",
        (
            TEST_USERNAME,
            generate_password_hash(TEST_PASSWORD),
            TEST_FULL_NAME,
            TEST_OPENING_BALANCE,
        ),
    )
    conn.commit()
    return cursor.lastrowid


@pytest.fixture()
def mem_conn():
    """Yield a seeded in-memory SQLite connection.  Closed after the test."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _create_schema(conn)
    _seed_customer(conn)
    yield conn
    conn.close()


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    """Yield a Flask test client backed by a temp SQLite file.

    monkeypatch replaces db._DB_PATH so the real banking.db is never touched.
    """
    import db as db_module

    tmp_db = str(tmp_path / "test_banking.db")
    monkeypatch.setattr(db_module, "_DB_PATH", tmp_db)

    # Seed the temp database
    conn = sqlite3.connect(tmp_db)
    _create_schema(conn)
    _seed_customer(conn)
    conn.close()

    import app as app_module

    app_module.app.config["TESTING"] = True
    app_module.app.config["WTF_CSRF_ENABLED"] = False

    with app_module.app.test_client() as client:
        yield client
