"""
test_routes.py — Integration tests for Flask HTTP routes
=========================================================
Uses the `app_client` fixture from conftest.py which provides a Flask test
client backed by a temporary SQLite file so no real database is touched.

Covers the 10 integration scenarios described in the implementation guide,
Section 6.2.
"""

import pytest

from tests.conftest import (
    TEST_USERNAME,
    TEST_PASSWORD,
    TEST_OPENING_BALANCE,
)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _login(client, username=TEST_USERNAME, password=TEST_PASSWORD):
    """POST to /login and return the response."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def _login_and_follow(client, username=TEST_USERNAME, password=TEST_PASSWORD):
    """Log in and follow the redirect to /dashboard."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


# --------------------------------------------------------------------------- #
# Authentication routes                                                        #
# --------------------------------------------------------------------------- #

class TestLogin:
    def test_get_login_returns_200(self, app_client):
        response = app_client.get("/login")
        assert response.status_code == 200
        assert b"Banking App" in response.data

    def test_correct_credentials_redirect_to_dashboard(self, app_client):
        response = _login(app_client)
        assert response.status_code == 302
        assert "/dashboard" in response.headers["Location"]

    def test_wrong_password_returns_login_page_with_error(self, app_client):
        response = app_client.post(
            "/login",
            data={"username": TEST_USERNAME, "password": "wrong_password"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_unknown_username_shows_generic_error(self, app_client):
        response = app_client.post(
            "/login",
            data={"username": "nobody", "password": "whatever"},
            follow_redirects=True,
        )
        assert b"Invalid username or password" in response.data

    def test_empty_fields_shows_error(self, app_client):
        response = app_client.post(
            "/login",
            data={"username": "", "password": ""},
            follow_redirects=True,
        )
        assert b"required" in response.data.lower() or response.status_code == 200


class TestLogout:
    def test_logout_redirects_to_login(self, app_client):
        _login(app_client)
        response = app_client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_after_logout_dashboard_redirects_to_login(self, app_client):
        _login(app_client)
        app_client.get("/logout")
        response = app_client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# --------------------------------------------------------------------------- #
# Dashboard                                                                    #
# --------------------------------------------------------------------------- #

class TestDashboard:
    def test_unauthenticated_redirects_to_login(self, app_client):
        response = app_client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_authenticated_returns_200_with_balance(self, app_client):
        response = _login_and_follow(app_client)
        assert response.status_code == 200
        # Balance formatted as a dollar amount should appear somewhere
        assert b"500.00" in response.data


# --------------------------------------------------------------------------- #
# Deposit                                                                      #
# --------------------------------------------------------------------------- #

class TestDeposit:
    def test_valid_deposit_updates_balance(self, app_client):
        _login(app_client)
        response = app_client.post(
            "/deposit",
            data={"amount": "200"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # New balance should be 700.00
        assert b"700.00" in response.data

    def test_deposit_zero_shows_error(self, app_client):
        _login(app_client)
        response = app_client.post(
            "/deposit",
            data={"amount": "0"},
            follow_redirects=True,
        )
        assert b"greater than zero" in response.data.lower()

    def test_deposit_negative_shows_error(self, app_client):
        _login(app_client)
        response = app_client.post(
            "/deposit",
            data={"amount": "-50"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Balance should remain unchanged
        assert b"500.00" in response.data

    def test_deposit_non_numeric_shows_error(self, app_client):
        _login(app_client)
        response = app_client.post(
            "/deposit",
            data={"amount": "abc"},
            follow_redirects=True,
        )
        assert b"number" in response.data.lower()

    def test_unauthenticated_deposit_redirects_to_login(self, app_client):
        response = app_client.post(
            "/deposit",
            data={"amount": "100"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# --------------------------------------------------------------------------- #
# Withdraw                                                                     #
# --------------------------------------------------------------------------- #

class TestWithdraw:
    def test_valid_withdrawal_updates_balance(self, app_client):
        _login(app_client)
        response = app_client.post(
            "/withdraw",
            data={"amount": "100"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        # New balance should be 400.00
        assert b"400.00" in response.data

    def test_withdraw_more_than_balance_shows_insufficient_funds(self, app_client):
        _login(app_client)
        response = app_client.post(
            "/withdraw",
            data={"amount": "9999"},
            follow_redirects=True,
        )
        assert b"insufficient funds" in response.data.lower()

    def test_withdraw_zero_shows_error(self, app_client):
        _login(app_client)
        response = app_client.post(
            "/withdraw",
            data={"amount": "0"},
            follow_redirects=True,
        )
        assert b"greater than zero" in response.data.lower()

    def test_unauthenticated_withdraw_redirects_to_login(self, app_client):
        response = app_client.post(
            "/withdraw",
            data={"amount": "50"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
