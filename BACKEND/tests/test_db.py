"""
test_db.py — Unit tests for the database access layer (db.py)
=============================================================
All tests use the in-memory `mem_conn` fixture so no files are written.
db functions that normally open their own connection are monkey-patched
to use the shared in-memory connection.
"""

import sqlite3

import pytest
from werkzeug.security import generate_password_hash

from tests.conftest import TEST_USERNAME, TEST_FULL_NAME, TEST_OPENING_BALANCE


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _get_balance(conn: sqlite3.Connection, customer_id: int) -> float:
    row = conn.execute(
        "SELECT balance FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()
    return row[0] if row else None


# --------------------------------------------------------------------------- #
# Tests                                                                        #
# --------------------------------------------------------------------------- #

class TestGetCustomerByUsername:
    def test_existing_user_returns_dict(self, mem_conn, monkeypatch):
        import db
        monkeypatch.setattr(db, "get_connection", lambda: mem_conn)
        result = db.get_customer_by_username(TEST_USERNAME)
        assert result is not None
        assert result["username"] == TEST_USERNAME
        assert result["full_name"] == TEST_FULL_NAME

    def test_unknown_user_returns_none(self, mem_conn, monkeypatch):
        import db
        monkeypatch.setattr(db, "get_connection", lambda: mem_conn)
        result = db.get_customer_by_username("nobody")
        assert result is None

    def test_row_has_required_keys(self, mem_conn, monkeypatch):
        import db
        monkeypatch.setattr(db, "get_connection", lambda: mem_conn)
        result = db.get_customer_by_username(TEST_USERNAME)
        for key in ("id", "username", "password_hash", "balance", "full_name"):
            assert key in result, f"Missing key: {key}"


class TestGetCustomerById:
    def test_existing_id_returns_dict(self, mem_conn, monkeypatch):
        import db
        monkeypatch.setattr(db, "get_connection", lambda: mem_conn)
        customer = db.get_customer_by_username(TEST_USERNAME)
        result = db.get_customer_by_id(customer["id"])
        assert result is not None
        assert result["username"] == TEST_USERNAME

    def test_nonexistent_id_returns_none(self, mem_conn, monkeypatch):
        import db
        monkeypatch.setattr(db, "get_connection", lambda: mem_conn)
        assert db.get_customer_by_id(99999) is None


class TestUpdateBalance:
    def test_balance_is_persisted(self, mem_conn, monkeypatch):
        import db
        monkeypatch.setattr(db, "get_connection", lambda: mem_conn)
        customer = db.get_customer_by_username(TEST_USERNAME)
        customer_id = customer["id"]
        db.update_balance(customer_id, 999.99)
        updated = db.get_customer_by_id(customer_id)
        assert updated["balance"] == pytest.approx(999.99)

    def test_balance_can_be_zero(self, mem_conn, monkeypatch):
        import db
        monkeypatch.setattr(db, "get_connection", lambda: mem_conn)
        customer = db.get_customer_by_username(TEST_USERNAME)
        db.update_balance(customer["id"], 0.0)
        updated = db.get_customer_by_id(customer["id"])
        assert updated["balance"] == pytest.approx(0.0)
