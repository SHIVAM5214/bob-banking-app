"""
app.py — Flask Application Entry Point
=======================================
Creates the Flask app, configures it, registers blueprints, and starts
the development server when run directly.

Start the app from the BACKEND/ folder:
    python app.py
    — or —
    flask run
"""

import os

from flask import Flask, redirect, url_for

from auth import auth_bp
from dashboard import dashboard_bp

# --------------------------------------------------------------------------- #
# App factory                                                                  #
# --------------------------------------------------------------------------- #

# Templates live in FRONTEND/templates/ which is one level above BACKEND/.
_TEMPLATE_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "FRONTEND",
    "templates",
)

app = Flask(__name__, template_folder=_TEMPLATE_FOLDER)

# Secret key signs the session cookie.  Read from environment in production;
# fall back to a dev-only default that must never reach a public server.
app.secret_key = os.environ.get("SECRET_KEY", "dev-banking-secret-key-change-in-prod")

# --------------------------------------------------------------------------- #
# Blueprint registration                                                       #
# --------------------------------------------------------------------------- #
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)


# --------------------------------------------------------------------------- #
# Global error handlers                                                        #
# --------------------------------------------------------------------------- #
@app.errorhandler(404)
def not_found(e):
    return redirect(url_for("auth.login"))


@app.errorhandler(500)
def server_error(e):
    # Return a plain message — never expose the stack trace in production.
    return "An unexpected error occurred. Please try again later.", 500


# --------------------------------------------------------------------------- #
# Development server entry point                                               #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    app.run(debug=True)
