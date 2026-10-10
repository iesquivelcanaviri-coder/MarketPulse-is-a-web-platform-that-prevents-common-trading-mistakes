# MarketPulse: Smart Trading Analysis Platform

## Project Overview

**MarketPulse** is an educational full-stack financial-analysis platform developed as part of a **Full Stack Software Development** project. It connects market-data retrieval, historical-data storage, quantitative model research, custom strategy creation, historical backtesting, risk planning, community messaging, REST APIs, and optional analytical services in one Django-based application.

MarketPulse is designed for research and learning. It does **not** place live trades, manage real money, or provide investment advice.

> **Educational disclaimer:** Market prices can be delayed or unavailable. Backtests, model descriptions, market-condition classifications, risk calculations, robustness analysis and stress tests are simplified educational simulations. Historical results do not guarantee future performance.

---

## 1. Problem and Motivation

Financial research is often fragmented across websites, spreadsheets, charting tools, notebooks and scripts. MarketPulse was created to demonstrate how those activities can be coordinated by one full-stack application.

The application is organised around questions such as:

- What market information is available now?
- What historical OHLCV data has been stored?
- What market condition does the stored history suggest?
- Which quantitative model should be researched?
- How can a custom strategy be defined and saved?
- How did the saved strategy behave historically?
- How much capital is exposed under a defined risk budget?
- How can hypothetical adverse conditions be explored?

The objective is not to predict markets. The objective is to demonstrate a structured software workflow for financial research.

---

## 2. Current User Workflow

The main Django application is organised around the following areas:

```text
Home
  ↓
Dashboard
  ↓
Data
  ↓
Strategies
  ↓
Risk

Supporting areas:
Accounts / Profile
Community / Private Messaging
REST API
```

### Home

The Home page introduces the application and surfaces entry points into the main research areas. It also includes community/inbox information for authenticated users.

### Dashboard

The Dashboard is the current-market workspace. It includes:

- Alpaca asset search;
- current stock/ETF snapshot information;
- historical chart requests;
- candlestick charts;
- line charts;
- Heikin-Ashi calculations;
- volume display;
- configurable alerts and alert rules.

The dashboard deliberately routes external market-data requests through Django so Alpaca credentials remain server-side.

Two chart selections are intentionally not implemented with the current equity feed:

- **Volume Profile** requires a dedicated calculation that is not currently enabled;
- **Futures Curve** requires futures contracts across expiries, which the current stock/ETF data source does not provide.

### Data

The Data workspace handles historical market-data import and reuse.

```text
User request
    ↓
data_management
    ↓
Alpaca service
    ↓
validated OHLCV observations
    ↓
core.MarketData
    ↓
PostgreSQL / SQLite
    ↓
Data / Strategies / Risk / Analysis
```

The current Data UI combines:

- Alpaca historical-data import;
- stored dataset selection;
- OHLCV review;
- market-condition analysis;
- strategy/model catalogue selection for research context.

Selecting a model in the Data workspace does **not** automatically execute the quantitative model. The model library is primarily metadata describing purpose, parameters, data requirements and implementation status.

### Strategies

The current Strategies workflow is:

```text
Open /strategy/
    ↓
Browse Strategy & Model Library
    ↓
Search / Filter / Compare
    ↓
Inspect Model Details
    ↓
My Strategies
    ↓
Create Strategy inline on the same page
    ↓
Save Strategy + Strategy Rules
    ↓
Run Historical Backtest
    ↓
Review Backtest Results
```

Strategy creation now happens inside **My Strategies** on the main `/strategy/` page. The legacy `/strategy/create/` route is retained only as a compatibility redirect back to the Strategies workspace.

The visible Strategies page no longer needs separate **Strategy Robustness** or **Stress Testing** panels. Robustness/overfitting and stress-test calculations remain in the backend analytical architecture where they can be reused without duplicating the main user workflow.

### Risk

The main Risk calculator is implemented as a separate authenticated workspace.

```text
Choose Market
    ↓
Set Trading Capital and Risk Budget
    ↓
Define Entry / Stop / Direction / Target
    ↓
Calculate Risk Plan
    ↓
Review Historical Context
```

Core calculations include maximum planned loss, risk per unit, position size and percentage-based stop loss.

The project also contains backend routes/views for strategy stress testing. During the latest code audit, the two templates expected by those active routes were missing from the supplied ZIP. This is documented as a known issue in `PROJECT_AUDIT.md` and `TESTING.md`; the README therefore does not claim that the Risk stress-test UI is currently complete.

### Community

The current project contains a `community` Django app that was missing from older README versions. It supports:

- community feed posts;
- private inbox;
- new conversations;
- conversation threads;
- compatibility routes from the older message architecture.

---

## 3. Technology Stack

### Backend

- Python 3.13 deployment target
- Django 5.2.17
- Django REST Framework
- Django ORM
- Gunicorn

### Frontend

- Django Templates
- Bootstrap 5
- HTML5
- CSS
- JavaScript
- Font Awesome
- TradingView Lightweight Charts on the Django Dashboard

### Additional Frontend

- React 18
- Vite 6
- Chart.js / `react-chartjs-2`

### Database

- PostgreSQL / Neon for production
- SQLite fallback for local development

### External / Optional Services

- Alpaca Market Data API
- Brevo email through Django Anymail
- MATLAB bridge, optional
- Celery + Redis, optional

### Deployment

- Render native Python Blueprint configuration
- WhiteNoise static-file serving
- Gunicorn WSGI server
- Dockerfile retained as an alternative deployment path

---

## 4. High-Level Architecture

MarketPulse follows Django's Model-View-Template architecture, with additional service, API and analysis layers.

```text
Browser
    ↓
Django URL Router
    ↓
Django View
    ↓
Forms / Models / Services / Analysis
    ↓
Django ORM / External API / Optional MATLAB
    ↓
Template or JSON Response
    ↓
Browser
```

For JavaScript / React requests:

```text
Browser / React
    ↓
/api/
    ↓
Django REST Framework
    ↓
Model or Server-side Service
    ↓
PostgreSQL / Alpaca / Optional MATLAB
    ↓
JSON Response
```

This design keeps API credentials and database access on the server.

---

## 5. Project Structure

```text
MarketPulse/
│
├── accounts/            # custom user, registration, profile, auth support
├── analysis_tools/      # reusable analytical models/functions
├── api/                 # Django REST Framework endpoints
├── community/           # feed, inbox and private conversations
├── core/                # shared models, home, dashboard, alerts, MATLAB bridge
├── data_management/     # Alpaca import, stored datasets, market condition
├── frontend/            # separate React/Vite API client
├── marketpulse/         # Django project settings, root URLs, WSGI/ASGI/Celery
├── matlab/              # optional MATLAB bridge functions
├── risk_management/     # risk forms, calculations, risk views
├── static/              # shared Django CSS and JavaScript source
├── strategy_builder/    # model library, strategy creation and backtesting
├── templates/           # project-level Django templates
├── build.sh             # Render build script
├── Dockerfile           # alternative container deployment
├── Procfile             # alternate Gunicorn process declaration
├── render.yaml          # active Render Blueprint definition
├── requirements.txt
└── manage.py
```

---

## 6. Django Application Responsibilities

### `accounts`

Handles the custom user model and account workflows.

Current responsibilities include:

- registration;
- login;
- logout;
- profile editing;
- password reset;
- password-change routes.

The password-reset templates are present. The latest audit found that the custom `password_change.html` and `password_change_done.html` templates referenced by active routes are missing from the supplied ZIP. That workflow must be fixed/retested before being marked complete.

### `core`

Contains shared application models and central pages, including:

- `MarketData`;
- `Strategy`;
- `Backtest` and related trades;
- alerts / alert rules;
- Home and Dashboard views;
- optional MATLAB bridge support.

### `data_management`

Coordinates historical market-data import and dataset presentation.

```text
DataImportForm
    ↓
data_management/views.py
    ↓
data_management/services/alpaca.py
    ↓
Alpaca
    ↓
data_management/utils.py
    ↓
core.MarketData
```

Management command `seed_marketpulse` creates/updates supporting seed data and makes Alpaca the active source.

### `strategy_builder`

Contains:

- strategy/model library metadata;
- inline custom strategy creation;
- strategy rules;
- historical backtesting;
- backtest result display;
- optional scheduled strategy monitoring task.

`seed_strategy_library` defines **37 catalogue entries across seven model categories**. Catalogue presence does not mean every model has an implemented execution engine; `implementation_status` distinguishes catalogue metadata from ready/experimental implementations.

### `risk_management`

Contains:

- risk form validation;
- position-size calculations;
- stop-loss calculations;
- historical market context;
- stress-test backend routes/views.

### `analysis_tools`

Contains reusable analytical functions and stored analytical results for concepts such as:

- market regime classification;
- overfitting/robustness analysis;
- stress testing.

`analysis_tools` is installed as a Django application, but its URL configuration is **not currently included by the root URL router**. In the current architecture, its analyzers/models are primarily an internal service layer used by other applications. The old standalone analysis pages are therefore considered legacy/optional UI until intentionally re-enabled.

### `community`

Handles:

- feed posts;
- private conversations;
- inbox display;
- message threads;
- compatibility routes for the older message flow.

### `api`

Provides REST/JSON endpoints for:

- health checks;
- Dashboard market overview;
- stored market data;
- risk position-size calculation;
- optional MATLAB risk calculation;
- Alpaca asset search;
- Alpaca asset detail;
- Alpaca stock snapshots;
- Alpaca historical bars;
- user-scoped Strategy CRUD;
- user-scoped Backtest read access.

---

## 7. Market Data Architecture

The browser never receives private Alpaca credentials.

```text
Browser
    ↓
Django / DRF endpoint
    ↓
data_management.services.alpaca
    ↓
Alpaca API
    ↓
Normalised server response
    ↓
Browser / Database
```

The exact environment-variable names used by the current source are:

```env
ALPACA_API_KEY_ID=
ALPACA_API_SECRET_KEY=
ALPACA_TRADING_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_BASE_URL=https://data.alpaca.markets
ALPACA_DATA_FEED=iex
```

Older documentation using `ALPACA_API_KEY` or `ALPACA_SECRET_KEY` should not be used for this version of the project.

`requirements.txt` still contains `yfinance`, but no active project source file in the supplied ZIP imports or calls it. The current MarketPulse data-service implementation is Alpaca-based.

---

## 8. Historical Market Data

Stored OHLCV observations are represented through shared market-data models and can be reused by several workflows.

Typical data:

```text
Symbol
Date
Open
High
Low
Close
Volume
```

Stored history supports:

- dataset inspection;
- charts;
- market-condition analysis;
- backtesting;
- volatility context;
- drawdown context;
- risk calculations;
- analytical validation.

This central storage reduces repeated external downloads and keeps analysis reproducible against a known dataset.

---

## 9. Market Condition Analysis

Market condition is calculated from stored historical observations. The current analytical layer can describe regimes such as:

```text
Bull
Bear
Sideways
Volatile / High Volatility
```

The purpose is descriptive research context, not a prediction of future price direction.

---

## 10. Strategy & Model Library

The Strategy library uses progressive disclosure:

```text
Category
    ↓
Compact Model Summary
    ↓
More Details
    ↓
Purpose / Data Requirements / Parameters / Output
    ↓
Compare with other models
```

The current seed command contains seven categories:

1. trend-following;
2. mean-reversion;
3. momentum / oscillators;
4. factor models;
5. portfolio optimisation;
6. derivatives pricing;
7. simulation / Monte Carlo.

The library is a research catalogue. A model can exist as metadata without being numerically executable in the current application.

---

## 11. Custom Strategy Creation

Custom strategy creation is intentionally integrated into the main Strategies page.

```text
/strategy/
    ↓
My Strategies
    ↓
Create First Strategy / New Strategy
    ↓
StrategyCreateForm
    ↓
POST action=create_strategy
    ↓
Validation
    ↓
Strategy + StrategyRule records
    ↓
Redirect to /strategy/#myStrategiesSection
```

This avoids duplicate creation pages and keeps the workflow in one place.

---

## 12. Historical Backtesting

Backtesting is a simulation over stored historical data.

```text
Saved Strategy
    ↓
BacktestForm
    ↓
run_backtest()
    ↓
Backtest
    ↓
BacktestTrade records
    ↓
Results page
```

The code contains assumptions relating to risk and execution settings such as commission, slippage, position sizing and trading-rule parameters.

Backtesting should be treated as historical simulation, not prediction.

---

## 13. Risk Management

The basic risk framework starts with a loss budget.

```text
Trading Capital × Risk Percentage
        ↓
Maximum Planned Loss
```

Then:

```text
| Entry Price − Stop Price |
        ↓
Risk per Unit
```

Then:

```text
Maximum Planned Loss ÷ Risk per Unit
        ↓
Risk-Constrained Position Size
```

The calculator tests in the project validate position sizing and stop-loss arithmetic with several example values.

---

## 14. Stress Testing and Robustness

MarketPulse contains internal analytical functions for:

- crash scenarios;
- volatility spikes;
- liquidity crises;
- regime changes;
- overfitting / robustness checks.

These remain backend analytical capabilities rather than mandatory visible panels in the current Strategies page.

**Audit status:** Risk stress-test routes are active, but their expected templates are missing from the supplied ZIP. Those pages should be treated as incomplete until the templates are restored or the routes are redesigned.

---

## 15. Community and Messaging

The community application adds social functionality to the financial-research project.

```text
Authenticated User
    ↓
Community Feed
    ↓
Posts

Authenticated User
    ↓
Inbox
    ↓
Conversation
    ↓
Private Messages
```

Conversation lookups enforce participant membership so users cannot simply change a URL ID to view another user's private thread.

---

## 16. Authentication and Email

MarketPulse uses Django authentication with a custom user model:

```python
AUTH_USER_MODEL = "accounts.User"
```

Implemented account architecture includes:

- registration;
- login;
- logout;
- profiles;
- password-reset token flow;
- password-change routes.

Email is configured through **Django Anymail with Brevo** when `BREVO_API_KEY` is present. Without a Brevo key, the project falls back to Django's console email backend for local development.

Relevant settings include:

```env
BREVO_API_KEY=
DEFAULT_FROM_EMAIL=
```

No real credentials should be committed to source control.

---

## 17. REST API

The current API prefix is:

```text
/api/
```

Important routes include:

```text
/api/health/
/api/dashboard/market-overview/
/api/market/latest/
/api/risk/position-size/
/api/matlab/risk/
/api/alpaca/assets/search/
/api/alpaca/assets/<symbol>/
/api/alpaca/stocks/<symbol>/snapshot/
/api/alpaca/stocks/<symbol>/history/
/api/strategies/
/api/backtests/
```

Permissions are deliberately mixed according to endpoint purpose. Some utility endpoints are public while Dashboard/Alpaca/user-owned resource endpoints require authentication. Strategy and Backtest ViewSets are restricted to authenticated users and scoped to the current user.

---

## 18. React / Vite Client

`frontend/` is a separate React client demonstrating that the Django API can be consumed independently from Django templates.

The current React components include:

- `Status` → `/api/health/`;
- `Market` → `/api/market/latest/` and Chart.js;
- `Risk` → `/api/risk/position-size/`.

The API base is configurable with:

```env
VITE_API_BASE=
```

and otherwise defaults locally to:

```text
http://127.0.0.1:8000/api
```

---

## 19. MATLAB Integration

MATLAB is optional.

```text
Django
    ↓
core/matlab_bridge.py
    ↓
JSON-compatible payload
    ↓
matlab/marketpulse_bridge.m
    ↓
MATLAB function
    ↓
Result
    ↓
Django
```

The dispatcher supports analytical operation families including:

```text
risk
analysis
regime
```

Configuration:

```env
MATLAB_ENABLED=False
MATLAB_COMMAND=matlab
```

The core Django application is designed to continue operating when MATLAB is disabled.

---

## 20. Celery and Redis

Celery is optional and controlled by project configuration.

```env
USE_CELERY=False
CELERY_BROKER_URL=redis://localhost:6379/0
```

The project contains background-task code, including scheduled strategy monitoring. A separate Celery worker is only needed when Celery-backed execution is enabled.

---

## 21. Database Architecture

### Production

```text
Django
    ↓
DATABASE_URL
    ↓
PostgreSQL / Neon
```

### Local fallback

When `DATABASE_URL` is empty:

```text
Django
    ↓
SQLite
    ↓
db.sqlite3 generated locally
```

The audited distribution intentionally does **not** include a local `db.sqlite3` file. Local databases can contain account/session/development records and should be regenerated with migrations and seed commands.

---

## 22. Security Design

Current security-related design includes:

- secrets read from environment variables;
- server-side Alpaca credentials;
- Django CSRF protection for forms;
- Django authentication for protected views;
- user ownership filters on user-specific resources;
- secure session/CSRF cookies when `DEBUG=False`;
- `X_FRAME_OPTIONS = "DENY"`;
- content-type sniffing protection;
- password validators;
- production `ALLOWED_HOSTS` configuration;
- controlled CORS origins for the React client.

Sensitive values should include at least:

```text
SECRET_KEY
DATABASE_URL
ALPACA_API_KEY_ID
ALPACA_API_SECRET_KEY
BREVO_API_KEY
```

---

## 23. Responsive Design

The Django interface uses Bootstrap responsive utilities plus custom CSS. Multi-column workspaces progressively collapse for smaller screens, and wide tables should scroll within their own container instead of forcing page-level horizontal overflow.

Responsive behaviour should be included in manual testing because visual layout cannot be completely verified by backend unit tests.

---

## 24. Deployment

The active Render Blueprint uses Render's **native Python runtime**, not Docker:

```text
render.yaml
    ↓
./build.sh
    ↓
pip install -r requirements.txt
    ↓
collectstatic
    ↓
migrate
    ↓
gunicorn marketpulse.wsgi:application
```

`Dockerfile` and `Procfile` are retained as valid alternative deployment artefacts, but they are redundant when the application is deployed strictly through the current `render.yaml` native-Python Blueprint.

### Render Variables

The Blueprint directly declares/configures:

```text
PYTHON_VERSION
DEBUG
SECRET_KEY
DATABASE_URL
ALLOWED_HOSTS
```

Application integrations also require environment variables to be added in Render when used, for example:

```text
ALPACA_API_KEY_ID
ALPACA_API_SECRET_KEY
BREVO_API_KEY
DEFAULT_FROM_EMAIL
CORS_ALLOWED_ORIGINS
MATLAB_ENABLED
MATLAB_COMMAND
USE_CELERY
CELERY_BROKER_URL
```

---

## 25. Local Setup

### Create a virtual environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Create `.env`

Create a local `.env` file. Do not commit it.

Minimal development example:

```env
SECRET_KEY=replace-with-local-development-key
DEBUG=True
DATABASE_URL=

ALPACA_API_KEY_ID=
ALPACA_API_SECRET_KEY=

BREVO_API_KEY=
DEFAULT_FROM_EMAIL=

MATLAB_ENABLED=False
USE_CELERY=False
```

### Database setup

```bash
python manage.py migrate
```

Seed MarketPulse support data:

```bash
python manage.py seed_marketpulse
```

Seed the strategy/model catalogue:

```bash
python manage.py seed_strategy_library
```

Create an administrator if required:

```bash
python manage.py createsuperuser
```

### Start Django

```bash
python manage.py runserver
```

or, if port 8000 is already occupied:

```bash
python manage.py runserver 8001
```

---

## 26. React Development

```bash
cd frontend
npm install
npm run dev
```

Default Vite development URL:

```text
http://localhost:5173/
```

---

## 27. Static Files

Source files live under:

```text
static/
```

Production collection:

```bash
python manage.py collectstatic --noinput
```

Generated `staticfiles/` content should not be edited or committed as application source.

---

## 28. Testing

Testing is an explicit course requirement. The supplied assignment requires automated testing using Python `unittest`; Django's `TestCase` and `SimpleTestCase` build on Python's unittest framework.

The supplied ZIP currently contains **13 automated test methods** across:

- accounts;
- core;
- data management;
- strategy builder;
- risk management;
- analysis tools;
- API health.

Run all Django tests with:

```bash
python manage.py test --verbosity=2
```

Run Django's system check with:

```bash
python manage.py check
```

### Important audit note

During this ZIP inspection, every Python source file successfully compiled with Python's `compileall`. The complete Django test suite and `manage.py check` could **not** be executed in the inspection environment because Django was not installed there and external package installation was unavailable. Therefore this README does **not** claim that the current suite passes.

Testing should be documented using both:

1. **automated tests** for repeatable logic, form validation, models, routes, permissions and APIs;
2. **manual feature testing** for browser workflows, JavaScript behaviour, responsive design, external-service behaviour and production deployment.

The complete test inventory, manual test matrix, result-recording format and recommended additional automated tests are documented in:

```text
TESTING.md
```

Do not mark a test as PASS until it has actually been run and observed.

---

## 29. Current Automated Test Inventory

| App | Current automated coverage |
|---|---|
| `accounts` | custom user registration |
| `core` | Strategy `rule_config` persistence |
| `data_management` | invalid date range, valid date range, lowercase ticker input |
| `strategy_builder` | invalid fast/slow period validation |
| `risk_management` | two position-size examples and three stop-loss examples |
| `analysis_tools` | market-regime analysis test |
| `api` | health endpoint |

This is a useful base, but it is not complete end-to-end coverage. The highest-priority additions are authentication/authorization, inline strategy creation, user ownership, backtest views, API permissions and mocked external-service behaviour.

---

## 30. Known Issues Found by the ZIP Audit

The detailed audit is in `PROJECT_AUDIT.md`. The most important current blockers are:

- `accounts/password_change.html` is referenced by an active route but missing;
- `accounts/password_change_done.html` is referenced by an active route but missing;
- `risk_management/stress_test.html` is referenced by an active route but missing;
- `risk_management/stress_test_results.html` is referenced by an active route but missing.

These should be fixed before the project is described as fully functional in production.

The audit also identified obsolete/generated files and removed them from the cleaned copy, including bytecode caches, local SQLite databases, an obvious backup view file, a timestamped backup-template directory and several templates no longer rendered by active routes.

---

## 31. Repository Cleanup

The cleaned project copy removes generated or clearly obsolete artefacts while preserving migrations, tests, active templates, deployment configuration and optional integrations.

High-confidence removed items include:

```text
__pycache__/
*.pyc
local db.sqlite3 files
risk_management/views_WRONG_BACKUP.py
analysis_tools/templates 19-32-13-515/
strategy_builder/templates/strategy_builder/create.html
strategy_builder/templates/strategy_builder/robustness.html
data_management/templates/data_management/market_condition.html
risk_management/templates/risk_management/dashboard.html
community/templates/community/message_detail.html
```

`db.sqlite3` and `db.sqlite3.*` are now included in `.gitignore` for the audited copy.

Files such as `analysis_tools/views.py`, `analysis_tools/urls.py`, the project-level `templates/analysis_tools/`, `Dockerfile` and `Procfile` were **not** automatically deleted because they can still serve intentional legacy/optional workflows. Their status is explained in the audit.

---

## 32. Development Challenges and Learning

Important development challenges included:

### External API security

The solution was to proxy external market-data requests through Django instead of embedding provider credentials in browser code.

### Reusing historical data

The solution was central storage through shared Django models rather than separate datasets for every application area.

### Managing complex research workflows

The Strategies workspace was simplified using progressive disclosure and same-page custom strategy creation.

### Authentication and email

Password-reset behaviour required Django token views, templates, email configuration and provider credentials to work together correctly.

### Responsive financial interfaces

Large charts, tables and model libraries required responsive layout rules beyond a desktop-only design.

### Optional integrations

MATLAB and Celery/Redis were kept optional so the core Django application can still run without them.

### Testing and verification

The project now separates automated tests from manual browser/deployment testing and documents both instead of treating a single `python manage.py test` command as proof that every UI feature works.

---

## 33. Educational Purpose

MarketPulse demonstrates:

- front-end development;
- backend development;
- Django Model-View-Template architecture;
- relational database design;
- form validation;
- authentication and authorization;
- API integration;
- REST API design;
- browser JavaScript;
- React API consumption;
- external service isolation;
- automated testing;
- manual functional testing;
- responsive design;
- production deployment;
- separation of concerns.

The financial domain provides a realistic context for applying these full-stack concepts.

---

## 34. Documentation

```text
README.md
    → project overview, architecture, setup and current status

TESTING.md
    → automated tests, manual test matrix and test evidence plan

PROJECT_AUDIT.md
    → detailed ZIP inspection, cleanup decisions and known issues
```

---

## 35. Project Summary

MarketPulse demonstrates how a full-stack application can coordinate several responsibilities while keeping them separated internally:

```text
Market Data
    informs
Market Condition

Market Data
    supports
Strategy Research

Strategy Research
    creates
Saved Strategies

Saved Strategies
    support
Historical Backtesting

Market Data
    supports
Risk Planning

Django APIs
    support
Django JavaScript + React

Shared Models / Services / Analysis
    support
multiple user workflows
```

Django coordinates the main application. PostgreSQL / Neon provides persistent production storage. Alpaca supplies external market information through a server-side service layer. Bootstrap and JavaScript provide the main web interface. Django REST Framework provides reusable APIs. React demonstrates a separate API consumer. Brevo supports email when configured. MATLAB and Celery/Redis remain optional analytical/background-processing extensions. Render supplies the production hosting configuration.

The project is therefore a practical demonstration of **full-stack architecture, integration, testing, security and deployment** in a financial-research context.
