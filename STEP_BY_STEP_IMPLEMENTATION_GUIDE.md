# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)
> **Audience:** Developer implementing the application for the first time.
> **Style:** Plain-English logic and instructions. No raw source code.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Prerequisites Check

Before writing a single file, confirm that the following tools are available on the machine:

- **Python 3.11 or later** — run `python --version` to verify. The application uses f-strings and match syntax available only in modern Python versions.
- **pip** — Python's package manager, bundled with Python 3.11+. Run `pip --version` to confirm.
- **A terminal / command prompt** — PowerShell on Windows, Terminal on macOS/Linux.

### 1.2 Create the Project Folder Structure

Create two top-level folders at the root of the workspace:

- `FRONTEND/` — will hold all HTML templates.
- `BACKEND/` — will hold all Python source files and the SQLite database.

Inside `FRONTEND/`, create a sub-folder named `templates/`. Flask's Jinja2 engine looks for templates inside a folder called `templates` by default, so the name is mandatory.

The final skeleton should match the layout described in Section 4 of the Implementation Plan before any code is written.

### 1.3 Set Up a Python Virtual Environment

A virtual environment isolates the project's dependencies from the system-wide Python installation. This prevents version conflicts with other projects.

- Navigate into the `BACKEND/` folder in the terminal.
- Create a virtual environment using the built-in `venv` module. Give the environment a conventional name such as `venv`.
- Activate the virtual environment. On Windows the activation script is in `venv\Scripts\activate`; on macOS/Linux it is in `venv/bin/activate`. The terminal prompt will show the environment name when activation succeeds.
- The virtual environment folder (`venv/`) must be added to `.gitignore` so it is never committed to version control.

### 1.4 Install Dependencies

With the virtual environment active, install the two required packages:

- **Flask** — the web framework that handles routing, request/response, sessions, and template rendering.
- **Werkzeug** — Flask's underlying utility library; specifically, the `generate_password_hash` and `check_password_hash` functions are used for secure password handling. Werkzeug is installed automatically as a Flask dependency, but listing it explicitly in `requirements.txt` documents the intent.

After installing, create a `requirements.txt` file inside `BACKEND/` by running `pip freeze > requirements.txt`. This file allows any other developer to recreate the exact environment with `pip install -r requirements.txt`.

### 1.5 Initialise the Database

Write a `seed.py` script inside `BACKEND/` that, when run once, performs three things:

1. **Creates the database file** — Python's built-in `sqlite3` module creates `banking.db` automatically the first time a connection is opened to a file path that does not yet exist.
2. **Creates the customers table** — the table needs at minimum: a unique customer ID, a username, a hashed password, and an account balance stored as a decimal number.
3. **Inserts one demo customer record** — choose a demo username (e.g. `john_doe`) and a starting balance. Hash the password using Werkzeug's `generate_password_hash` before inserting it; never store the plain-text password.

Run `seed.py` once from the `BACKEND/` folder. Confirm `banking.db` appears on disk. Add `banking.db` to `.gitignore` so the database file is never pushed to the repository.

---

## 2. Backend Implementation

### 2.1 Database Access Layer — `db.py`

`db.py` is the single file that knows how to talk to `banking.db`. No other module should open a database connection directly. This separation means that if the database engine were ever swapped out, only `db.py` would need to change.

Implement three helper functions:

- **`get_connection()`** — opens and returns a connection to `banking.db`. Configure the connection to return rows as dictionary-like objects so view functions can access columns by name (e.g., `row["balance"]`) rather than by index position.
- **`get_customer_by_username(username)`** — queries the customers table for a row matching the given username and returns the full row, or `None` if no match is found. This is called during login.
- **`update_balance(customer_id, new_balance)`** — writes the new balance value back to the customers table for the given customer ID. This is called after every successful deposit or withdrawal.

Each function should open its own connection and close it before returning, or use Python's context manager (`with` statement) to ensure the connection is always released.

### 2.2 Flask Application Entry Point — `app.py`

`app.py` is the root of the Flask application. Its responsibilities are:

1. **Create the Flask app instance** — instantiate `Flask(__name__)`. Tell Flask where to find templates by pointing the `template_folder` parameter at `../FRONTEND/templates` (relative to the `BACKEND/` folder), since templates live outside the backend directory.
2. **Set the secret key** — Flask's session mechanism requires a secret key to sign session cookies. Set `app.secret_key` to a long, random string. For development this can be hardcoded; for production it must come from an environment variable.
3. **Register blueprints or import routes** — import the route functions from `auth.py` and `dashboard.py` so Flask is aware of them. Using Flask Blueprints is the recommended approach (each module registers its own Blueprint, and `app.py` registers those Blueprints onto the main app).
4. **Run the development server** — at the bottom of `app.py`, under the `if __name__ == "__main__"` guard, call `app.run(debug=True)` so the file can be run directly during development.

### 2.3 Authentication Routes — `auth.py`

`auth.py` owns two routes and one helper:

#### Login — `GET /login` and `POST /login`

- `GET /login` simply renders `login.html`. If the user already has an active session (i.e. they are already logged in), redirect them directly to `/dashboard` instead of showing the login form again.
- `POST /login` processes the submitted form. The logic is:
  1. Read `username` and `password` from the submitted form data.
  2. Call `get_customer_by_username(username)` from `db.py`.
  3. If no customer is found, flash an error message ("Invalid username or password") and re-render `login.html`. Using a generic message avoids confirming whether the username exists.
  4. If a customer is found, call Werkzeug's `check_password_hash` to compare the submitted password against the stored hash. If it does not match, flash the same generic error and re-render.
  5. If the hash matches, store the customer's ID and username in `flask.session` (e.g. `session["customer_id"]` and `session["username"]`), then redirect to `/dashboard`.

#### Logout — `GET /logout`

- Call `session.clear()` to remove all session data.
- Redirect to `/login`.

#### Auth Guard Helper

Write a small helper function (or use a Python decorator) that checks whether `session.get("customer_id")` exists. If it does not, redirect the caller to `/login`. Every protected route calls this guard as its very first action. This ensures that navigating directly to `/dashboard`, `/deposit`, or `/withdraw` without being logged in always bounces the user back to the login page.

### 2.4 Dashboard and Transaction Routes — `dashboard.py`

`dashboard.py` owns three routes. Each one must apply the auth guard before doing anything else.

#### Dashboard — `GET /dashboard`

1. Apply auth guard.
2. Read `customer_id` from the session.
3. Call a `get_customer_by_id(customer_id)` function in `db.py` (add this function alongside `get_customer_by_username`) to retrieve the current record.
4. Pass the customer's name and balance to `render_template("dashboard.html", ...)`.
5. Flask's `get_flashed_messages` mechanism will automatically surface any flash messages queued by a preceding deposit or withdrawal action.

#### Deposit — `POST /deposit`

1. Apply auth guard.
2. Read the `amount` field from the submitted form.
3. Pass the amount through the deposit validation rules (see Section 5).
4. If validation fails, flash an error message and redirect back to `/dashboard`.
5. If validation passes, retrieve the current balance, compute `new_balance = current_balance + amount`, call `update_balance(customer_id, new_balance)`, flash a success message ("Deposit successful"), and redirect to `/dashboard`.

#### Withdraw — `POST /withdraw`

1. Apply auth guard.
2. Read the `amount` field from the submitted form.
3. Pass the amount and the current balance through the withdrawal validation rules (see Section 5).
4. If validation fails (invalid amount or insufficient funds), flash an appropriate error message and redirect to `/dashboard`.
5. If validation passes, compute `new_balance = current_balance - amount`, call `update_balance(customer_id, new_balance)`, flash a success message ("Withdrawal successful"), and redirect to `/dashboard`.

### 2.5 Session Management

Flask sessions work by storing a signed cookie in the browser. The cookie contains the session data (customer ID, username) encrypted with the app's secret key, so the client cannot tamper with it.

Key session management rules for this application:

- **Write to the session only on successful login** — set `session["customer_id"]` and `session["username"]` once credentials are verified.
- **Read from the session on every protected request** — the auth guard reads `session.get("customer_id")` to decide whether the user is authenticated.
- **Clear the session on logout** — call `session.clear()` which removes all keys. Do not manually delete individual keys; clearing everything is safer.
- **Session lifetime** — by default Flask sessions expire when the browser is closed. For this workshop, the default behaviour is sufficient.

### 2.6 Error Handling

Use Flask's flash message mechanism rather than custom error pages for all user-facing errors. The pattern is:

- In the view function, call `flash("message text", "category")` where category is `"error"` for failures and `"success"` for confirmations.
- Redirect to the relevant page.
- In the template, iterate over `get_flashed_messages(with_categories=True)` and display each message in a Bootstrap alert component styled to match the category (e.g. `alert-danger` for errors, `alert-success` for successes).

For unexpected server errors (e.g. a database connection failure), register a Flask error handler for HTTP 500 that renders a plain "Something went wrong" message. This prevents internal stack traces from leaking to the browser.

---

## 3. Frontend Implementation

All templates live in `FRONTEND/templates/`. Flask's `render_template()` call looks in this folder. Every template shares the same Bootstrap CDN `<link>` tag in its `<head>` so styling is consistent. A base template (`base.html`) that all other templates extend is recommended to avoid duplicating the HTML boilerplate, but it is not mandatory for the workshop scope.

### 3.1 Bootstrap Layout Approach

Include Bootstrap 5 via its CDN `<link>` tag (stylesheet) in the `<head>` of every page. No JavaScript bundle is needed since the application does not use Bootstrap's JS components (modals, dropdowns, etc.).

Use Bootstrap's grid system (`container`, `row`, `col`) to centre content on the page. A narrow, centred card (`card`, `card-body`) provides a clean layout for forms. Navigation elements on the dashboard use Bootstrap's `navbar` or a simple `d-flex justify-content-between` arrangement.

### 3.2 Login Page — `login.html`

The login page is the application's entry point and the only page accessible without authentication.

**Layout:**
- A centred card on a neutral background.
- Application title ("Banking App" or similar) as a heading above the card.

**Form:**
- A text input labelled "Username" — `name="username"`, `type="text"`.
- A password input labelled "Password" — `name="password"`, `type="password"`.
- A submit button labelled "Login" using Bootstrap's `btn btn-primary` class.
- The form's `action` attribute points to `/login` and `method` is `POST`.

**Flash messages:**
- Above the form, loop over any flashed messages from the session and display each one in a Bootstrap `alert alert-danger` block so login errors are clearly visible.

### 3.3 Dashboard Page — `dashboard.html`

This is the customer's home screen after logging in.

**Layout:**
- A top bar or heading that greets the customer by name (injected by the template variable passed from Flask).
- A prominent card or panel showing the current account balance formatted as currency.

**Navigation:**
- A "Deposit" button or link pointing to the deposit form at `/deposit` (renders `deposit.html`).
- A "Withdraw" button or link pointing to the withdraw form at `/withdraw` (renders `withdraw.html`).
- A "Logout" link pointing to `/logout`.

**Flash messages:**
- Directly below the balance panel, display any flashed success or error messages from the preceding transaction. Use `alert-success` for success and `alert-danger` for errors.

### 3.4 Deposit Form — `deposit.html`

**Layout:**
- A centred card similar to the login page.
- A heading: "Deposit Funds".

**Form:**
- A single numeric input labelled "Amount" — `name="amount"`, `type="number"`, `min="0.01"`, `step="0.01"`.
- A "Deposit" submit button.
- A "Back to Dashboard" link below the button.
- `action="/deposit"`, `method="POST"`.

**Flash messages:**
- Display any error messages above the form in case the redirect back to this page carries an error (though the primary error display is on the dashboard).

### 3.5 Withdraw Form — `withdraw.html`

Structurally identical to the deposit form with the following differences:

- Heading: "Withdraw Funds".
- `action="/withdraw"`, `method="POST"`.
- Optionally display the current balance in the form so the customer knows their limit before entering an amount. Pass `balance` as a template variable from the withdraw route.

---

## 4. Integration Steps

### 4.1 Connect Flask to the Frontend Templates

Flask must know where the `templates/` folder lives. Because the `FRONTEND/templates/` directory is outside the `BACKEND/` folder, the Flask app instance must be created with an explicit `template_folder` path pointing to `../FRONTEND/templates`. This is set once in `app.py` and then all `render_template()` calls work by referencing file names alone (e.g. `render_template("login.html")`).

No additional configuration is needed. Jinja2 automatically resolves variable substitutions (e.g. `{{ balance }}`) and control structures (`{% for %}`, `{% if %}`) inside the templates.

### 4.2 Connect Flask to SQLite

Python's `sqlite3` module is part of the standard library — no installation required. The connection between Flask and SQLite is handled entirely inside `db.py`:

- The database file path is constructed as a path relative to `db.py`'s own location using `os.path` so that the path resolves correctly regardless of which directory the application is started from.
- The connection's `row_factory` is set to `sqlite3.Row` so that query results behave like dictionaries.
- Every function in `db.py` opens a connection, executes its query using parameterised placeholders (`?`), commits any writes, and closes the connection before returning. Using parameterised queries is the defence against SQL injection.

### 4.3 Wire Blueprints in `app.py`

If Flask Blueprints are used (recommended), the wiring sequence in `app.py` is:

1. Import the Blueprint object from `auth.py` and register it on the app with `app.register_blueprint(auth_blueprint)`.
2. Import the Blueprint object from `dashboard.py` and register it with `app.register_blueprint(dashboard_blueprint)`.
3. The template folder and secret key must be set on the app instance before blueprints are registered.

If Blueprints are not used (simpler flat approach), import the route functions from `auth.py` and `dashboard.py` after the app instance is created — Python's module-level `@app.route` decorators self-register when the module is imported.

### 4.4 Post/Redirect/Get Pattern

Every `POST` route (login, deposit, withdraw) must end with a `redirect()` call rather than a `render_template()` call. This prevents the browser from re-submitting the form if the user refreshes the page after a transaction. The pattern is:

- Handle the POST logic (validate, update database, flash message).
- Redirect to the relevant GET route (`/dashboard` for transactions, `/login` for logout).
- The GET route renders the template and the flash message appears there.

---

## 5. Validation Rules

All validation happens in the backend view functions **before** any database operation. Never rely on the browser's HTML `min`/`type` attributes alone — these can be bypassed.

### 5.1 Login Validation

| Check | Failure Action |
|---|---|
| Username field is not empty | Flash error, re-render login |
| Password field is not empty | Flash error, re-render login |
| Username exists in the database | Flash generic error ("Invalid credentials"), re-render login |
| Submitted password matches the stored hash | Flash generic error, re-render login |

Use the same generic error message ("Invalid username or password") for both "username not found" and "password mismatch" cases. Distinguishing between the two would allow an attacker to enumerate valid usernames.

### 5.2 Balance Validation

The balance is retrieved fresh from the database at the start of every deposit and withdrawal request. Never trust a balance value submitted via the form — always read the authoritative value from the database.

### 5.3 Deposit Checks

| Check | Failure Action |
|---|---|
| Amount field is present and not empty | Flash error: "Please enter an amount" |
| Amount can be parsed as a number | Flash error: "Amount must be a number" |
| Amount is greater than zero | Flash error: "Deposit amount must be greater than zero" |
| Amount has at most two decimal places | Flash error: "Amount cannot have more than two decimal places" |

If all checks pass, proceed to update the balance.

### 5.4 Withdrawal Checks

| Check | Failure Action |
|---|---|
| Amount field is present and not empty | Flash error: "Please enter an amount" |
| Amount can be parsed as a number | Flash error: "Amount must be a number" |
| Amount is greater than zero | Flash error: "Withdrawal amount must be greater than zero" |
| Amount has at most two decimal places | Flash error: "Amount cannot have more than two decimal places" |
| Amount does not exceed the current balance | Flash error: "Insufficient funds" |

If all checks pass, proceed to update the balance.

---

## 6. Testing

### 6.1 Unit Tests

Unit tests verify individual functions in isolation, without a running Flask server or a real database.

**What to test:**

- **`db.py` functions** — test `get_customer_by_username` with a known username and with an unknown username. Test `update_balance` by setting a balance and immediately reading it back. Use an in-memory SQLite database (`:memory:`) for these tests so they leave no files on disk.
- **Validation logic** — if the deposit and withdrawal checks are extracted into standalone helper functions, test every boundary condition: zero amount, negative amount, amount exceeding balance, non-numeric input, too many decimal places.
- **Password hashing** — verify that `check_password_hash(generate_password_hash("secret"), "secret")` returns `True`, and that `check_password_hash(hash, "wrong")` returns `False`.

**Test file location:** `BACKEND/tests/test_db.py` and `BACKEND/tests/test_validation.py`.

**Framework:** Use `pytest`. Each test function name must start with `test_`. Run all tests with `pytest` from the `BACKEND/` folder.

### 6.2 Integration Tests

Integration tests verify the full HTTP request/response cycle using Flask's built-in test client, which simulates a browser without actually starting a server.

**What to test:**

- `GET /login` returns a 200 status code and the login page HTML.
- `POST /login` with correct credentials redirects (302) to `/dashboard`.
- `POST /login` with incorrect credentials returns the login page with an error message.
- `GET /dashboard` without a session redirects (302) to `/login`.
- `GET /dashboard` with a valid session returns a 200 and the balance.
- `POST /deposit` with a valid amount updates the balance and redirects to `/dashboard`.
- `POST /deposit` with a zero or negative amount returns an error message.
- `POST /withdraw` with a valid amount updates the balance and redirects.
- `POST /withdraw` with an amount exceeding the balance returns an "Insufficient funds" error.
- `GET /logout` clears the session and redirects to `/login`.

**Test file location:** `BACKEND/tests/test_routes.py`.

**Setup:** Each integration test should use a fresh in-memory or temporary SQLite database seeded with a known customer record so tests are independent of each other.

### 6.3 Manual Testing Checklist

Run through this checklist end-to-end in a real browser before considering the application complete.

**Authentication:**
- [ ] Navigating to `http://127.0.0.1:5000/` redirects to `/login`.
- [ ] Submitting the form with an incorrect password shows the generic error message on the login page.
- [ ] Submitting the form with the correct credentials lands on the dashboard.
- [ ] The dashboard displays the correct customer name and opening balance.

**Session security:**
- [ ] Copying the `/dashboard` URL and opening it in a new private/incognito window redirects to `/login`.
- [ ] Clicking Logout and then pressing the browser Back button redirects to `/login` (session has been cleared).

**Deposit:**
- [ ] Entering a valid positive amount increases the displayed balance by exactly that amount.
- [ ] A green success alert appears on the dashboard after a successful deposit.
- [ ] Entering zero shows an error without changing the balance.
- [ ] Entering a negative number shows an error without changing the balance.
- [ ] Submitting a blank amount shows an error without changing the balance.

**Withdraw:**
- [ ] Entering a valid amount less than the balance decreases the displayed balance by exactly that amount.
- [ ] A green success alert appears after a successful withdrawal.
- [ ] Entering an amount greater than the balance shows "Insufficient funds" without changing the balance.
- [ ] Entering zero or a negative number shows an error.

**Logout:**
- [ ] Clicking Logout redirects to the login page.
- [ ] After logout, the session cookie no longer grants access to `/dashboard`.

---

## 7. Deployment

### 7.1 Run Locally

The standard local development workflow is:

1. Open a terminal and navigate to the `BACKEND/` folder.
2. Activate the virtual environment (`venv\Scripts\activate` on Windows, `source venv/bin/activate` on macOS/Linux).
3. Ensure `banking.db` exists — if not, run `python seed.py` to create and seed it.
4. Start the Flask development server with `flask run` (Flask auto-detects `app.py`) or `python app.py`.
5. Open `http://127.0.0.1:5000/login` in a browser.

The development server reloads automatically when Python files change, so there is no need to restart it during development.

### 7.2 Environment Variable for the Secret Key

The Flask secret key must not be hardcoded for any environment beyond local development. The correct approach is:

- Read the secret key from an environment variable: `app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-key")`.
- In production, set the `SECRET_KEY` environment variable on the hosting platform before starting the process.
- The `"dev-fallback-key"` default is acceptable for local development only.

### 7.3 Production Considerations

The Flask built-in development server (`flask run`) is **not suitable for production**. For a real deployment the following changes are necessary:

| Concern | Recommendation |
|---|---|
| WSGI server | Replace the dev server with Gunicorn (`gunicorn app:app`) or uWSGI |
| HTTPS | Serve the application behind a reverse proxy (Nginx, Caddy) that handles TLS termination |
| Secret key | Load from an environment variable or a secrets manager; rotate regularly |
| Database | SQLite is adequate for single-user demos; consider PostgreSQL for concurrent production workloads |
| Debug mode | Set `FLASK_DEBUG=0` (or `app.run(debug=False)`) — debug mode exposes an interactive debugger to anyone who can reach the server |
| Static files | If static assets are added (CSS, images), serve them via the reverse proxy rather than Flask |

### 7.4 CI/CD Pipeline

The repository includes a GitHub Actions workflow file (`docs/demo-setup/banking-app-ci.yml`) that:

- Triggers on every push to `main` and `feature/**` branches, and on pull requests to `main`.
- Sets up Python 3.11 and installs dependencies from `requirements.txt`.
- Runs `pytest` if a `tests/` directory exists.

To activate the pipeline, copy `banking-app-ci.yml` to `.github/workflows/banking-app-ci.yml` in the repository root and push to GitHub. The workflow will execute automatically on the next push.

---

*End of Step-by-Step Implementation Guide*
