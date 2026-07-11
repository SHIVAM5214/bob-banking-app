"""
auth.py — Authentication Blueprint
====================================
Owns the /login and /logout routes and the login_required decorator.

Routes
------
GET  /login   — render the login form (redirect to /dashboard if already logged in)
POST /login   — process credentials, create session, redirect to /dashboard
GET  /logout  — clear session, redirect to /login

Decorator
---------
login_required(fn) — wraps any view function to enforce authentication.
                     Import and apply to every protected route.
"""

from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from db import get_customer_by_username

# ------------------------------------------------------------------ #
# Blueprint registration                                               #
# ------------------------------------------------------------------ #
auth_bp = Blueprint("auth", __name__)


# ------------------------------------------------------------------ #
# Auth guard — import this decorator in dashboard.py                  #
# ------------------------------------------------------------------ #
def login_required(fn):
    """Redirect unauthenticated requests to /login.

    Usage:
        @dashboard_bp.route("/dashboard")
        @login_required
        def dashboard():
            ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("customer_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already authenticated — skip the login form.
    if session.get("customer_id"):
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "GET":
        return render_template("login.html")

    # ---- POST: validate and authenticate ---- #
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Presence checks
    if not username or not password:
        flash("Username and password are required.", "error")
        return render_template("login.html")

    # Lookup customer
    customer = get_customer_by_username(username)

    # Generic message for both "not found" and "wrong password" to prevent
    # username enumeration.
    if customer is None or not check_password_hash(customer["password_hash"], password):
        flash("Invalid username or password.", "error")
        return render_template("login.html")

    # Credentials verified — write session and redirect.
    session["customer_id"] = customer["id"]
    session["username"] = customer["username"]
    return redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
