"""
dashboard.py — Protected Dashboard & Transaction Blueprint
===========================================================
All routes here require an active session.  The login_required decorator
from auth.py is applied to every route.

Routes
------
GET  /dashboard  — show balance + flash messages
GET  /deposit    — render deposit form
POST /deposit    — process deposit, update balance, redirect to /dashboard
GET  /withdraw   — render withdraw form
POST /withdraw   — process withdrawal, update balance, redirect to /dashboard
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from auth import login_required
from db import get_customer_by_id, update_balance
from validation import validate_deposit, validate_withdrawal

# ------------------------------------------------------------------ #
# Blueprint registration                                               #
# ------------------------------------------------------------------ #
dashboard_bp = Blueprint("dashboard", __name__)


# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #
@dashboard_bp.route("/")
@login_required
def index():
    """Root URL — redirect to /dashboard."""
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    """Main home screen: shows current balance and any flash messages."""
    customer_id = session["customer_id"]
    customer = get_customer_by_id(customer_id)
    return render_template(
        "dashboard.html",
        full_name=customer["full_name"],
        balance=customer["balance"],
    )


@dashboard_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "GET":
        return render_template("deposit.html")

    # ---- POST: validate then update ---- #
    raw_amount = request.form.get("amount", "")
    amount, error = validate_deposit(raw_amount)

    if error:
        flash(error, "error")
        return redirect(url_for("dashboard.dashboard"))

    customer_id = session["customer_id"]
    customer = get_customer_by_id(customer_id)
    # Read authoritative balance from DB — never trust form data.
    new_balance = round(customer["balance"] + amount, 2)
    update_balance(customer_id, new_balance)

    flash(f"Deposit of ${amount:,.2f} successful. New balance: ${new_balance:,.2f}", "success")
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    customer_id = session["customer_id"]
    customer = get_customer_by_id(customer_id)

    if request.method == "GET":
        return render_template("withdraw.html", balance=customer["balance"])

    # ---- POST: validate then update ---- #
    raw_amount = request.form.get("amount", "")
    amount, error = validate_withdrawal(raw_amount, customer["balance"])

    if error:
        flash(error, "error")
        return redirect(url_for("dashboard.dashboard"))

    new_balance = round(customer["balance"] - amount, 2)
    update_balance(customer_id, new_balance)

    flash(f"Withdrawal of ${amount:,.2f} successful. New balance: ${new_balance:,.2f}", "success")
    return redirect(url_for("dashboard.dashboard"))
