# Banking Web Application — Implementation Plan

> **Document type:** Planning only. No schema, SQL, API contracts, or implementation code.
> **Status:** Ready for Review

---

## 1. Solution Overview

### Objective

Build a lightweight, browser-based Banking Web Application that allows customers to securely log in, view their account balance, and perform basic transactions (deposit / withdraw), with a clean logout flow.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login and session management | Admin / bank-teller portal |
| Dashboard with balance display | Multi-account support |
| Deposit and withdraw transactions | Transfers between accounts |
| Logout | Password reset / registration flow |
| SQLite-backed persistence | External payment gateways |

### Users

- **Bank Customer** — the single end-user persona. Authenticated customers can view their balance and initiate deposit or withdrawal transactions.

### Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | A customer can log in with a username and password. |
| FR-02 | Authenticated customers are redirected to a personalised dashboard. |
| FR-03 | The dashboard displays the customer's current account balance. |
| FR-04 | A customer can deposit a positive monetary amount. |
| FR-05 | A customer can withdraw an amount up to their available balance. |
| FR-06 | A customer can log out and their session is invalidated. |
| FR-07 | Unauthenticated access to protected pages redirects to the login page. |

### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | The UI is responsive and renders correctly on desktop browsers via Bootstrap. |
| NFR-02 | Passwords are stored as cryptographic hashes — never plain text. |
| NFR-03 | Session tokens are server-side (Flask session) and expire on logout. |
| NFR-04 | All form inputs are validated server-side before any database write. |
| NFR-05 | The SQLite database file is stored inside the BACKEND folder and excluded from version control. |
| NFR-06 | The application must be runnable locally with a single `flask run` command after setup. |

### Assumptions

- A single pre-seeded customer account is sufficient for the workshop / demo scope.
- No HTTPS is required for local development; production hardening is out of scope.
- Bootstrap is loaded via CDN — no front-end build tooling (Node/npm) is needed.
- Python 3.11+ and pip are available in the local environment.
- SQLite is the only database; no migration tooling is required.

---

## 2. High-Level Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BROWSER (Client)                             │
│                                                                     │
│   HTML Pages served by Flask + Bootstrap CSS (via CDN)             │
│   Forms submit POST requests; links trigger GET requests           │
└──────────────────────────┬──────────────────────────────────────────┘
                           │  HTTP (localhost)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND  (Python Flask)                        │
│                                                                     │
│   Routes → View Functions → Business Logic → DB Access Layer       │
│   Flask Session middleware manages authentication state            │
└──────────────────────────┬──────────────────────────────────────────┘
                           │  SQLite Python driver (sqlite3)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DATABASE  (SQLite — banking.db)                   │
│                                                                     │
│   Stores: customer credentials (hashed) and account balances       │
└─────────────────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

```
Browser                Flask Backend              SQLite DB
   │                        │                         │
   │── POST /login ────────>│                         │
   │                        │── query customer ──────>│
   │                        │<─ row returned ─────────│
   │<─ redirect /dashboard ─│                         │
   │                        │                         │
   │── GET /dashboard ─────>│                         │
   │                        │── fetch balance ───────>│
   │                        │<─ balance value ─────────│
   │<─ render dashboard ────│                         │
   │                        │                         │
   │── POST /deposit ──────>│                         │
   │                        │── update balance ──────>│
   │                        │<─ success ───────────────│
   │<─ redirect /dashboard ─│                         │
   │                        │                         │
   │── POST /withdraw ─────>│                         │
   │                        │── validate + update ───>│
   │                        │<─ success / error ───────│
   │<─ redirect /dashboard ─│                         │
   │                        │                         │
   │── GET /logout ────────>│                         │
   │                        │── clear session         │
   │<─ redirect /login ─────│                         │
```

### Request Lifecycle

1. **Browser** submits an HTML form or follows a link.
2. **Flask Router** matches the URL and HTTP method to a view function.
3. **View Function** validates the incoming data and enforces authentication.
4. **Business Logic Layer** executes the operation (login check, balance update, etc.).
5. **Database Access Layer** reads from or writes to `banking.db` via Python's `sqlite3` module.
6. **View Function** renders a Jinja2 template (or issues a redirect) and returns the HTTP response.
7. **Browser** displays the rendered HTML page.

---

## 3. Component Design

### Frontend Responsibilities (`FRONTEND/`)

- Provide all HTML templates rendered by Flask's Jinja2 engine.
- Use Bootstrap classes for layout, form styling, and responsive behaviour.
- Display server-side flash messages (success / error feedback) to the user.
- Submit all data to the backend via standard HTML form POST — no client-side JavaScript logic required.

| Page | Purpose |
|---|---|
| `login.html` | Username/password form |
| `dashboard.html` | Balance display, links to deposit/withdraw/logout |
| `deposit.html` | Deposit amount form |
| `withdraw.html` | Withdraw amount form |

### Backend Responsibilities (`BACKEND/`)

- Expose HTTP routes for every user-facing action.
- Manage the Flask application factory, configuration, and secret key.
- Handle session creation on login and session destruction on logout.
- Validate all user inputs before touching the database.
- Hash passwords on seed and compare hashes on login — never store or compare plain-text passwords.
- Return appropriate HTTP redirects to maintain the Post/Redirect/Get pattern.

| Module | Responsibility |
|---|---|
| `app.py` | Flask app entry point, route registration |
| `auth.py` | Login / logout view functions |
| `dashboard.py` | Dashboard, deposit, withdraw view functions |
| `db.py` | Database connection helper and query functions |
| `seed.py` | One-time script to create and seed `banking.db` |

### Database Responsibilities (`BACKEND/banking.db`)

- Persist customer account records (credentials + balance) across application restarts.
- Enforce data integrity at the storage layer.
- Remain fully self-contained as a single file — no server process required.

---

## 4. Folder Structure

```
banking-workshop/
├── FRONTEND/
│   └── templates/               # Jinja2 HTML templates (rendered by Flask)
│       ├── login.html
│       ├── dashboard.html
│       ├── deposit.html
│       └── withdraw.html
│
├── BACKEND/
│   ├── app.py                   # Flask application factory and route wiring
│   ├── auth.py                  # Authentication routes (login, logout)
│   ├── dashboard.py             # Protected routes (dashboard, deposit, withdraw)
│   ├── db.py                    # Database access helpers
│   ├── seed.py                  # Database initialisation and seed script
│   ├── banking.db               # SQLite database file (git-ignored)
│   └── requirements.txt         # Python dependencies (Flask, Werkzeug)
│
├── docs/
│   └── demo-setup/              # Workshop setup guides and CI template
│
└── IMPLEMENTATION_PLAN.md       # This document
```

### Responsibility of Each Folder

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | All user-visible HTML pages; pure presentation layer |
| `BACKEND/app.py` | Single entry point; wires together routes, config, and the Flask instance |
| `BACKEND/auth.py` | Owns the login and logout flow; creates and destroys the session |
| `BACKEND/dashboard.py` | Owns all post-login screens; enforces the auth guard on every route |
| `BACKEND/db.py` | Centralises all SQL interactions; keeps data logic out of view functions |
| `BACKEND/seed.py` | Runs once to create tables and insert the demo customer record |
| `BACKEND/banking.db` | Runtime data store; excluded from version control |
| `docs/demo-setup/` | Workshop instructions, CI/CD config, and MCP setup guides |

---

## 5. Module Breakdown

### 5.1 Authentication Module

**Goal:** Allow a registered customer to prove their identity and receive a server-managed session.

- **Login flow** — accepts username + password, looks up the customer record, verifies the password hash, and creates a session entry on success.
- **Logout flow** — clears the server-side session and redirects to the login page.
- **Auth guard** — a decorator or helper function that every protected route uses to redirect unauthenticated requests to `/login`.

### 5.2 Dashboard Module

**Goal:** Give the authenticated customer a single home screen that surfaces their account status and navigation to all actions.

- Fetches the current balance for the logged-in customer.
- Displays the customer's name and balance prominently.
- Provides navigation links to Deposit, Withdraw, and Logout.
- Shows flash messages for the result of the most recent transaction.

### 5.3 Account Management Module

**Goal:** Maintain the customer's account record and expose balance information to other modules.

- Retrieves the account balance for a given customer.
- Updates the balance following a validated transaction.
- Acts as the interface between view functions and the database access layer — no view function writes directly to the database.

### 5.4 Transactions Module

**Goal:** Implement deposit and withdrawal business rules and apply them to the account.

- **Deposit** — validates that the amount is a positive number, then credits the account.
- **Withdraw** — validates that the amount is positive and does not exceed the current balance, then debits the account.
- Both operations produce a success or error flash message that the dashboard displays after the Post/Redirect/Get redirect.

---

## 6. Implementation Roadmap

### Development Phases

```
Phase 1 — Environment & Project Scaffolding
  ├── Set up Python virtual environment
  ├── Install Flask and Werkzeug
  ├── Create FRONTEND/ and BACKEND/ folder structure
  └── Initialise banking.db via seed script
  Dependency: None — starting point

Phase 2 — Database & Data Access Layer
  ├── Implement db.py (connection helper, customer query, balance update)
  └── Verify seed.py creates a valid demo account
  Dependency: Phase 1 complete

Phase 3 — Authentication (Backend + Frontend)
  ├── Implement auth.py routes (POST /login, GET /logout)
  ├── Build login.html template with Bootstrap form
  └── Validate login flow end-to-end (correct + incorrect credentials)
  Dependency: Phase 2 complete

Phase 4 — Dashboard & Transaction Routes (Backend + Frontend)
  ├── Implement dashboard.py (GET /dashboard, POST /deposit, POST /withdraw)
  ├── Build dashboard.html, deposit.html, withdraw.html templates
  ├── Apply auth guard to all three routes
  └── Validate deposit and withdrawal flows including edge cases
  Dependency: Phase 3 complete

Phase 5 — Integration Testing & Polish
  ├── End-to-end walkthrough of the full user journey
  ├── Verify Bootstrap responsiveness across page templates
  ├── Confirm session expiry on logout
  └── Review flash message display for all success and error paths
  Dependency: Phase 4 complete

Phase 6 — CI/CD Setup & Repository Push
  ├── Initialise git repository and configure .gitignore
  ├── Push to GitHub
  └── Add GitHub Actions workflow (banking-app-ci.yml)
  Dependency: Phase 5 complete
```

### Estimated Effort

| Phase | Effort |
|---|---|
| Phase 1 — Scaffolding | Low |
| Phase 2 — Data Access Layer | Low–Medium |
| Phase 3 — Authentication | Medium |
| Phase 4 — Dashboard & Transactions | Medium–High |
| Phase 5 — Integration & Polish | Low–Medium |
| Phase 6 — CI/CD & Repository | Low |

### Dependencies

| Phase | Depends On |
|---|---|
| Phase 2 | Phase 1 (virtual env + folder structure must exist) |
| Phase 3 | Phase 2 (customer lookup requires a seeded database) |
| Phase 4 | Phase 3 (auth guard requires a working session mechanism) |
| Phase 5 | Phase 4 (all routes and templates must exist before integration test) |
| Phase 6 | Phase 5 (only push working, tested code) |

---

*End of Implementation Plan*
