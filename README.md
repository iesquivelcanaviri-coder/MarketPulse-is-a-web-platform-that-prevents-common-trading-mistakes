# MarketPulse: Smart Trading Analysis Platform

## Project Overview

**MarketPulse** is an educational full-stack financial analysis application designed to bring several important parts of a trading-research workflow into one integrated web platform.

The project was developed as part of my **Full Stack Software Development** studies.

The purpose of MarketPulse is not to automatically trade money or provide investment advice. Instead, it provides an educational environment where a user can:

- inspect financial market data;
- understand  market conditions;
- research quantitative trading models;
- create and test strategies;
- examine historical strategy behaviour;
- calculate trade and portfolio risk;
- explore severe hypothetical market scenarios.

The application combines a Django web application, PostgreSQL database, external market-data APIs, client-side JavaScript, Bootstrap, REST APIs and optional analytical services such as MATLAB.

> **Important:** All backtests, strategy results, risk calculations, regime classifications and stress tests are educational simulations. They are not investment advice and do not guarantee future performance.


---

# 1. Background and Motivation

Financial markets produce a large amount of information.

A person researching a possible trading strategy may need to use several different tools just to answer relatively simple questions:

- What is happening in the market now?
- What historical data do I have?
- Is the market currently bullish, bearish or moving sideways?
- Which type of strategy could I investigate?
- How did that strategy behave historically?
- Is the historical performance stable or possibly overfitted?
- How much capital would be exposed if the trade moved against me?
- What could happen under a severe hypothetical market scenario?

These questions are related, but they are often answered using separate tools, spreadsheets, websites or scripts.
That fragmentation was the main problem I wanted MarketPulse to address.

The goal was to create one application where market data, strategy research and risk analysis are connected through a clear user workflow.


---

# 2. Core Problem Being Solved

MarketPulse addresses three main problems.


## 2.1 Fragmented Financial Analysis

Market research, historical data analysis, strategy testing and risk planning are often carried out separately.

MarketPulse brings these activities into a single application:

```text
Market Data
    ↓
Market Condition
    ↓
Strategy Research
    ↓
Backtesting
    ↓
Robustness Analysis
    ↓
Risk Planning
    ↓
Stress Testing
```


## 2.2 Difficulty Understanding Trading Risk

A trading strategy can appear profitable historically while still exposing a user to significant risk.

MarketPulse therefore treats risk as a separate and important part of the workflow.

The application allows a user to define:

```text
Trading Capital
    +
Maximum Risk Percentage
    ↓
Maximum Planned Loss
```

and then combine this with:

```text
Entry Price
    +
Stop-Loss
    ↓
Risk per Unit
```

to calculate:

```text
Maximum Planned Loss
    ÷
Risk per Unit
    ↓
Risk-Constrained Position Size
```


## 2.3 Misleading Historical Performance

A strategy can perform well historically simply because it was tuned too closely to one period of data.

MarketPulse therefore includes robustness and overfitting checks across different historical periods.

The aim is not to prove that a strategy will work in the future.

The aim is to encourage the user to question historical results rather than accepting one successful backtest at face value.


---

# 3. Project Goal

The main goal of MarketPulse is to create a **full-stack educational decision-support platform** that demonstrates how financial data can move through a modern web application.

The project connects:

```text
Browser
    ↓
Django Templates / JavaScript
    ↓
Django Views
    ↓
Application Services
    ↓
PostgreSQL / Neon
    ↓
External Market Data
    ↓
Analytical Engines
    ↓
Results returned to the user
```

The project demonstrates both software-development skills and understanding of application architecture.


---

# 4. Main User Workflow

The main MarketPulse navigation is intentionally organised around a research workflow.

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
```

Each section has a different responsibility.


## Home

The Home page introduces MarketPulse and provides access to the main parts of the application.


## Dashboard

The Dashboard provides a live market workspace.

It allows the user to:

- search financial assets;
- load current market information;
- inspect historical market behaviour;
- view professional financial charts;
- manage configurable alerts.

The dashboard communicates with MarketPulse's Django API rather than exposing external API credentials directly to the browser.


## Data

The Data section is responsible for historical market information.

It provides:

- market-data import;
- stored historical datasets;
- dataset inspection;
- market-condition analysis;
- market-regime classification.

The conceptual data flow is:

```text
Alpaca Market Data
        ↓
data_management
        ↓
Django
        ↓
core.MarketData
        ↓
PostgreSQL / Neon
        ↓
MarketPulse analysis workflows
```


## Strategies

The Strategies section is the research area of MarketPulse.

It allows the user to:

- browse quantitative strategy models;
- inspect model requirements;
- create custom strategies;
- use stored market data;
- perform historical backtests;
- investigate strategy robustness;
- examine possible overfitting.

The main question answered by this section is:

> **Which quantitative approach do I want to research, and how has it behaved historically?**


## Risk

The Risk section focuses on capital exposure rather than market prediction.

The workflow is:

```text
1. Choose Market
        ↓
2. Set Risk Budget
        ↓
3. Define Trade
        ↓
4. Review Risk Plan
        ↓
5. Stress Test
```

The Risk workspace combines current market information, historical risk information and user-defined assumptions to calculate a hypothetical risk-controlled position.


---

# 5. Technology Stack

MarketPulse uses a combination of backend, frontend, database, external API and deployment technologies.


## Backend

- Python
- Django 5.2
- Django REST Framework


## Frontend

- Django Templates
- Bootstrap 5
- HTML5
- CSS
- JavaScript
- Font Awesome


## Database

- PostgreSQL
- Neon PostgreSQL
- SQLite local fallback


## Market Data

- Alpaca Market Data API


## Charts and Visualisation

- Lightweight Charts
- Chart.js where required


## Additional Frontend

- React
- Vite


## Optional Processing

- Celery
- Redis
- MATLAB


## Deployment

- Render
- Gunicorn
- WhiteNoise


---

# 6. Application Architecture

MarketPulse follows Django's Model-View-Template architecture together with service and API layers.

A simplified framework map is:

```text
Browser
    ↓
Django URL
    ↓
Django View
    ↓
Model / Service / Analysis Layer
    ↓
PostgreSQL / External API / MATLAB
    ↓
Django View
    ↓
Template
    ↓
Browser
```

For client-side API requests:

```text
Browser JavaScript
        ↓
MarketPulse Django REST API
        ↓
Django View / Service
        ↓
Alpaca Market Data API
        ↓
Django
        ↓
JSON Response
        ↓
JavaScript
        ↓
User Interface
```

This means external credentials remain on the server rather than being exposed to the client.


---

# 7. Django Project Structure

The project is divided into Django applications according to responsibility.

A simplified structure is:

```text
MarketPulse
│
├── accounts/
│
├── core/
│
├── data_management/
│
├── strategy_builder/
│
├── risk_management/
│
├── analysis_tools/
│
├── marketpulse/
│
├── templates/
│
├── static/
│
├── matlab/
│
├── frontend/
│
└── manage.py
```


---

# 8. Responsibility of Each Django Application


## `accounts`

Handles user-related functionality.

Responsibilities include:

- registration;
- login;
- logout;
- password reset;
- password change;
- user profile;
- user risk preferences.

Conceptually:

```text
User
    ↓
accounts/views.py
    ↓
accounts/forms.py
    ↓
accounts/models.py
    ↓
PostgreSQL
```


## `core`

Contains shared application models and functionality used across multiple sections.

This includes shared financial data and common functionality.

For example:

```text
Data Import
    ↓
core.MarketData
    ↓
PostgreSQL
    ↓
Strategies / Risk / Analysis
```

This allows one stored historical dataset to be reused by multiple application areas rather than repeatedly downloading or duplicating data.


## `data_management`

Responsible for acquiring, storing and presenting historical market data.

Typical flow:

```text
User selects asset
        ↓
data_management view
        ↓
Market data service
        ↓
Alpaca
        ↓
Data validation
        ↓
core.MarketData
        ↓
PostgreSQL
```

The stored data can then be used by strategy and risk calculations.


## `strategy_builder`

Responsible for quantitative strategy research.

The user can:

```text
Open Strategies
        ↓
Browse Model Library
        ↓
Inspect Model
        ↓
Create / Select Strategy
        ↓
Choose Stored Market Data
        ↓
Backtest
        ↓
Review Results
        ↓
Robustness Analysis
```


## `risk_management`

Responsible for trade and portfolio-risk planning.

It combines:

```text
User Risk Settings
        +
Current Market Information
        +
Historical Market Information
        +
Trade Assumptions
        ↓
Risk Calculation
        ↓
Position Size
        ↓
Stop-Loss
        ↓
Risk / Reward
        ↓
Stress Testing
```


## `analysis_tools`

Contains analytical functionality that can be reused by other Django applications.

Rather than making Analysis a completely separate user workflow, analytical functions can support other sections.

For example:

```text
Data
    ↓
Market Condition
    ↓
Market Regime Analysis
```

and:

```text
Strategies
    ↓
Robustness
    ↓
Overfitting Analysis
```

This keeps analytical logic separated from page presentation.


---

# 9. Market Data Architecture

MarketPulse separates external market data from the browser.

The browser does not communicate directly with Alpaca using private credentials.

Instead:

```text
Browser
    ↓
MarketPulse API Endpoint
    ↓
Django
    ↓
Alpaca Service
    ↓
Alpaca Market Data API
    ↓
Django
    ↓
JSON
    ↓
Browser
```

This architecture improves security because API credentials remain on the backend.


---

# 10. Current Market Data vs Historical Market Data

MarketPulse distinguishes between current market information and historical stored information.


## Current Market Information

Current information can be requested from Alpaca.

Examples include:

- latest trade;
- bid and ask;
- daily open;
- daily high;
- daily low;
- volume;
- previous close;
- asset information.


## Historical Market Information

Historical observations can be stored in MarketPulse's database.

Typical stored fields include:

```text
Symbol
Date
Open
High
Low
Close
Volume
```

These observations can then be reused for:

- market-condition analysis;
- backtesting;
- volatility calculations;
- drawdown calculations;
- Average True Range;
- risk analysis;
- robustness checks.

This makes historical analysis more reproducible because calculations can use a stored dataset.


---

# 11. Market Condition Analysis

MarketPulse includes market-condition analysis to help describe historical market behaviour.

Possible classifications include:

```text
Bull
Bear
Sideways
High Volatility
```

The purpose is not to predict the next market movement.

Instead, the regime gives additional context for strategy research.

Conceptually:

```text
Stored Historical Prices
        ↓
Analysis
        ↓
Trend / Volatility Measures
        ↓
Market Regime
        ↓
User Research Context
```


---

# 12. Strategy and Model Research

The strategy library uses progressive disclosure.

Instead of showing every technical detail at once, the workflow is:

```text
Model Category
    ↓
Model Summary
    ↓
More Details
    ↓
Data Requirements
    ↓
Parameters
    ↓
Historical Testing
```

This makes the strategy library easier to navigate while still allowing detailed inspection.


---

# 13. Backtesting

Backtesting is used to examine how a strategy would have behaved on historical data.

The project treats backtesting as a simulation rather than a prediction.

The implementation can account for realistic assumptions including:

- transaction costs;
- slippage;
- execution timing;
- market-session constraints;
- overnight price gaps;
- position sizing;
- historical data limitations.

Backtest results are stored and can be compared with later robustness analysis.


---

# 14. Overfitting and Robustness

A major issue with historical trading research is overfitting.

A strategy may perform strongly during one specific historical period but fail when evaluated elsewhere.

MarketPulse therefore supports testing across different windows or periods.

Conceptually:

```text
Strategy
    ↓
Historical Window A
Historical Window B
Historical Window C
    ↓
Compare Performance
    ↓
Stability / Overfitting Indicators
```

The purpose is to help the user ask:

> Is this strategy's performance reasonably stable, or does it depend too heavily on one specific historical sample?


---

# 15. Risk Management Framework

The Risk module begins with the amount a user is willing to lose rather than with the amount they want to buy.

The core calculation follows:

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

Finally:

```text
Maximum Planned Loss
        ÷
Risk per Unit
        ↓
Risk-Constrained Position Size
```

Available capital can also limit the final position size.

This provides a structured way to demonstrate risk-aware position sizing.


---

# 16. Historical Risk Metrics

Stored historical market data can also provide additional risk context.

MarketPulse can derive measures such as:

- Average True Range;
- annualised volatility;
- historical maximum drawdown;
- recent high;
- recent low;
- latest stored close.

These metrics give context to the user's hypothetical trade assumptions.


---

# 17. Stress Testing

A historical backtest only describes behaviour under historical conditions.

Risk can also be examined using hypothetical severe scenarios.

MarketPulse supports stress-testing concepts such as:

- market crashes;
- volatility spikes;
- liquidity problems;
- regime changes.

The aim is educational:

```text
Current Risk Plan
        ↓
Severe Hypothetical Scenario
        ↓
Recalculate / Estimate Exposure
        ↓
Review Potential Consequences
```

Stress testing does not predict that such an event will occur.


---

# 18. Database Architecture

The production database is PostgreSQL.

MarketPulse uses a `DATABASE_URL` environment variable so the same Django application can connect to different environments.


## Production

```text
Django
    ↓
DATABASE_URL
    ↓
Neon PostgreSQL
```


## Local Development

For easier classroom demonstrations, SQLite can be used when `DATABASE_URL` is blank.

```text
DATABASE_URL supplied
        ↓
PostgreSQL

DATABASE_URL blank
        ↓
SQLite
```

The SQLite database is therefore a local-development fallback.

The intended production architecture remains PostgreSQL / Neon.


---

# 19. Authentication

MarketPulse includes a complete Django authentication workflow.

Implemented account features include:

- registration;
- login;
- logout;
- profile editing;
- password reset;
- password change.

Protected application pages use Django authentication controls such as:

```python
@login_required
```

This prevents unauthenticated users from accessing protected application functionality.


---

# 20. Password Reset and Email

Password-reset functionality uses Django's authentication framework together with an external email service.

The general flow is:

```text
User requests password reset
        ↓
Django generates secure reset token
        ↓
Email service
        ↓
User receives reset link
        ↓
Django validates token
        ↓
User creates new password
```

Email credentials and service configuration are stored in environment variables rather than hard-coded in the source code.


---

# 21. Front-End Architecture

The main Django interface uses:

- Bootstrap 5;
- Django templates;
- JavaScript;
- shared MarketPulse CSS.

The shared structure is:

```text
Bootstrap 5
    ↓
templates/base.html
    ↓
static/css/styles.css
    ↓
Shared MarketPulse Theme
    ↓
Home
Dashboard
Data
Strategies
Risk
Accounts
```

Bootstrap is responsible for most layout and responsive behaviour.

Custom CSS is used mainly for:

- MarketPulse colours;
- application-specific workspaces;
- specialist financial components;
- charts and visual refinements.


---

# 22. Responsive Design

MarketPulse is designed to work across different screen sizes.

The application uses Bootstrap breakpoints and responsive grids.

A typical layout changes from:

```text
Large Desktop
-------------------------------
Main Workspace | Side Panel
```

to:

```text
Tablet
-------------------------------
Main Workspace
Side Panel
```

and then:

```text
Phone
-------------------------------
Single-column content
```

Tables that cannot reasonably fit on small screens use horizontal scrolling inside their own container rather than forcing the entire page wider.


---

# 23. React / Vite Frontend

The project also contains a separate React/Vite frontend.

This demonstrates that MarketPulse's REST API can be consumed independently from Django templates.

The architecture is:

```text
React
    ↓
HTTP / JSON
    ↓
Django REST Framework
    ↓
Django Application
    ↓
Database / Services
```

The Django application remains the main backend.


---

# 24. Django REST Framework

Django REST Framework exposes selected MarketPulse data and functionality as JSON.

This allows different clients to communicate with the same backend.

For example:

```text
Django Template + JavaScript
            ↓
        REST API
            ↑
React Frontend
```

This separation makes the backend reusable.


---

# 25. MATLAB Integration

MarketPulse also contains an optional MATLAB analytical layer.

MATLAB is not responsible for running the website.

Django remains the main application framework.

The integration works as:

```text
Django
    ↓
core/matlab_bridge.py
    ↓
JSON input
    ↓
MATLAB
    ↓
matlab/marketpulse_bridge.m
    ↓
Specialist MATLAB Function
    ↓
JSON output
    ↓
Django
```

The MATLAB dispatcher currently supports analytical operations such as:

```text
risk
analysis
regime
```

The `matlab/README.md` file contains the detailed MATLAB integration documentation.


## Why MATLAB Is Optional

The core Django application should still operate when MATLAB is unavailable.

Therefore:

```text
MATLAB_ENABLED=True
        ↓
MATLAB integration available

MATLAB_ENABLED=False
        ↓
Django continues without MATLAB
```

This keeps the architecture modular and avoids tightly coupling the website to MATLAB.


---

# 26. Background Tasks

MarketPulse includes optional Celery and Redis support for work that may be better performed outside the normal request/response cycle.

Conceptually:

```text
Django Request
    ↓
Create Background Task
    ↓
Celery
    ↓
Redis
    ↓
Worker
    ↓
Process Task
```

The integration remains optional so that the core application can still run without a Celery worker during normal local development.


---

# 27. Security Design

Several security principles are applied throughout the application.


## Environment Variables

Sensitive information is not intended to be committed to GitHub.

Examples include:

```text
SECRET_KEY
DATABASE_URL
ALPACA_API_KEY
ALPACA_SECRET_KEY
EMAIL credentials
```

These values belong in environment variables.


## API Credentials

External market-data credentials remain on the server.

The browser communicates with Django, and Django communicates with the external provider.


## CSRF Protection

Django forms use:

```django
{% csrf_token %}
```

to protect POST requests.


## Authentication

Protected areas require authenticated users.


---

# 28. Deployment Architecture

MarketPulse is designed for deployment on Render.

The production flow is approximately:

```text
GitHub
    ↓
Render
    ↓
build.sh
    ↓
Install Python dependencies
    ↓
collectstatic
    ↓
Database migrations
    ↓
Gunicorn
    ↓
Django Application
```

WhiteNoise is used to serve collected static files.


## Production Database

```text
Render
    ↓
DATABASE_URL
    ↓
Neon PostgreSQL
```


---

# 29. Static Files

Source static files live in:

```text
static/
```

During deployment Django collects them into:

```text
staticfiles/
```

The generated `staticfiles/` directory is not the source of the styles.

Changes should therefore be made in files such as:

```text
static/css/styles.css
static/js/app.js
```

and then processed through Django's static-file system.


---

# 30. Development Journey

MarketPulse evolved considerably during development.

The project did not begin with every integration and workflow already defined.

The development process involved progressively connecting separate parts of the application.


## Initial Application Structure

The first stage established:

- Django project configuration;
- user accounts;
- database models;
- page routing;
- templates;
- basic financial workflows.


## Database Development

The project then moved towards PostgreSQL / Neon for persistent production data while retaining SQLite as a convenient local-development fallback.


## Market Data Integration

A major development milestone was connecting MarketPulse to external financial-market information.

The current architecture uses Alpaca market data through Django services and API endpoints.

This allowed market information to become reusable across:

```text
Dashboard
Data
Risk
```

rather than creating unrelated market-data implementations in each page.


## Strategy Research

The strategy section developed into a model-research and backtesting workspace.

The challenge was not only performing calculations but presenting complex information without overwhelming the user.

This led to the use of progressive disclosure:

```text
Category
    ↓
Summary
    ↓
Details
    ↓
Testing
```


## Risk Integration

The Risk section was developed to connect market information with risk-controlled trade assumptions.

Instead of simply displaying a calculator, the interface was organised into a user workflow:

```text
Choose Market
    ↓
Set Risk Budget
    ↓
Define Trade
    ↓
Review Plan
    ↓
Stress Test
```


## Authentication and Password Reset

Authentication functionality was another important development area.

Registration, login, profile management and password reset required coordination between Django's authentication system, forms, routes, templates and email configuration.


## User Interface Consistency

As different sections developed independently, they initially had different visual styles and responsive behaviour.

The interface was later standardised around:

```text
Bootstrap 5
    ↓
base.html
    ↓
Shared MarketPulse Theme
```

The Data, Strategies, Risk, Dashboard, Home and Account sections now share the same overall dark application identity.


## Responsive Design

The larger research workspaces initially used desktop-oriented layouts.

These were progressively refactored to use:

- Bootstrap responsive columns;
- flexible grids;
- mobile breakpoints;
- shrinkable grid items;
- responsive tables;
- single-column phone layouts.

This allows the same application to operate on both large monitors and mobile devices.


---

# 31. Key Development Challenges

The project involved several challenges that helped shape the final architecture.


## Challenge: Connecting Multiple Technologies

MarketPulse combines Django, PostgreSQL, JavaScript, Bootstrap, external APIs, React and optional MATLAB processing.

The solution was to keep each technology responsible for a specific layer rather than mixing responsibilities.


## Challenge: External Market Data

External financial data should not expose private credentials in frontend JavaScript.

The solution was:

```text
Browser
    ↓
Django API
    ↓
Server-side Alpaca Service
    ↓
Alpaca
```

rather than:

```text
Browser
    ↓
Private Alpaca credentials
```

which would be insecure.


## Challenge: Reusing Historical Data

Different sections need access to the same market history.

The solution was to store data centrally using Django models and PostgreSQL so that Data, Strategies and Risk can operate on the same historical information.


## Challenge: Keeping Analytical Logic Separate

Market calculations can become difficult to maintain when placed directly inside templates or views.

The project therefore separates responsibilities between:

```text
Views
Models
Forms
Services
Analysis Tools
Templates
JavaScript
```

so individual parts can be maintained independently.


## Challenge: Responsive Financial Workspaces

Financial interfaces often contain large grids, tables and statistics that look good on a large desktop but can overflow smaller screens.

The solution was to combine Bootstrap responsiveness with carefully controlled custom layouts.

Large multi-column components progressively collapse to fewer columns and eventually one column on phones.


## Challenge: Optional External Components

MATLAB, Celery and Redis may not be installed in every development or deployment environment.

These components were designed as optional integrations so they do not prevent the main Django application from operating.


---

# 32. Current Implemented Features

MarketPulse currently includes:

- user registration;
- login and logout;
- editable user profile;
- password reset and password change;
- PostgreSQL / Neon database support;
- SQLite local-development fallback;
- Alpaca market-data integration;
- live asset search;
- current market snapshots;
- stored historical OHLCV data;
- market-condition analysis;
- bull / bear / sideways regime analysis;
- strategy and model library;
- custom strategy creation;
- historical strategy backtesting;
- transaction-cost and execution assumptions;
- risk-controlled position sizing;
- stop-loss calculations;
- risk / reward calculations;
- volatility-related risk context;
- robustness testing;
- overfitting analysis;
- stress-testing workflows;
- Django REST Framework APIs;
- responsive Bootstrap interface;
- separate React / Vite frontend;
- optional Celery / Redis support;
- optional MATLAB analytical bridge;
- Render deployment configuration;
- Gunicorn production server;
- WhiteNoise static-file handling.


---

# 33. Local Setup on macOS

Create and activate a virtual environment:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Do not commit real secrets to GitHub.


---

# 34. Environment Configuration

Typical environment variables include:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_URL=

ALPACA_API_KEY=
ALPACA_SECRET_KEY=

MATLAB_ENABLED=False
MATLAB_COMMAND=matlab
```

Additional email, Render, Redis or deployment variables may also be required depending on which optional services are enabled.


---

# 35. Local Database Fallback

For convenient classroom testing, MarketPulse can use SQLite when `DATABASE_URL` is blank.

```text
DATABASE_URL blank
        ↓
SQLite
```

When a PostgreSQL connection is supplied:

```text
DATABASE_URL supplied
        ↓
PostgreSQL / Neon
```

This means the production architecture remains PostgreSQL while local demonstrations can run without requiring an external database connection.


---

# 36. Django Setup

Run Django's system check:

```bash
python manage.py check
```

Apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Seed development data where required:

```bash
python manage.py seed_marketpulse
```

Create an administrator:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```


---

# 37. React Frontend

The React / Vite frontend is located in:

```text
frontend/
```

Install dependencies:

```bash
cd frontend
npm install
```

Start Vite:

```bash
npm run dev
```

The development frontend is normally available at:

```text
http://localhost:5173/
```


---

# 38. MATLAB

MATLAB integration is optional.

To enable it locally:

```env
MATLAB_ENABLED=True
MATLAB_COMMAND=matlab
```

The MATLAB executable must be available to the environment running Django.

The communication path is:

```text
Django
    ↓
core/matlab_bridge.py
    ↓
matlab/marketpulse_bridge.m
    ↓
MATLAB analytical function
```

For detailed MATLAB documentation, see:

```text
matlab/README.md
```


---

# 39. Tests

Run the Django test suite with:

```bash
python manage.py test
```

Before deployment, the project should also pass:

```bash
python manage.py check
```


---

# 40. Production Static Files

To test static-file collection locally:

```bash
python manage.py collectstatic --noinput
```

The generated files are placed in:

```text
staticfiles/
```

Source files should continue to be edited under:

```text
static/
```


---

# 41. Overall Framework Interaction

The complete project can be summarised as:

```text
                         USER
                           │
                           ▼
                    Web Browser
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
     Django Templates               React / Vite
     Bootstrap + JS                     │
             │                           │
             └─────────────┬─────────────┘
                           ▼
                 Django URL Routing
                           │
                           ▼
                     Django Views
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       Forms            Services       REST API
          │                │                │
          │                ▼                │
          │          Alpaca Market Data     │
          │                                 │
          └──────────────┬──────────────────┘
                         ▼
                    Django Models
                         │
                         ▼
                  PostgreSQL / Neon
                         │
              ┌──────────┴───────────┐
              │                      │
              ▼                      ▼
        Analysis Tools        MATLAB Bridge
                                     │
                                     ▼
                                   JSON
                                     │
                                     ▼
                                   MATLAB
                                     │
                                     ▼
                                   Result
                                     │
                                     ▼
                                   Django
                                     │
                                     ▼
                                    User
```

This architecture allows each technology to have a clearly defined responsibility.


---

# 42. Separation of Concerns

A major design principle in MarketPulse is separation of concerns.

```text
Templates
    → presentation

Bootstrap / CSS
    → layout and visual design

JavaScript
    → browser interaction

Views
    → request handling and workflow control

Forms
    → validation and user input

Models
    → persisted application data

Services
    → external systems such as Alpaca

Analysis Tools
    → reusable analytical logic

REST API
    → JSON communication

PostgreSQL
    → persistent storage

MATLAB
    → optional numerical analysis
```

This structure reduces duplication and makes the project easier to understand, test and maintain.


---

# 43. Educational Purpose

MarketPulse is an educational project.

Its purpose is to demonstrate:

- full-stack software-development principles;
- Django framework architecture;
- relational database integration;
- frontend and backend communication;
- external API integration;
- financial-data processing;
- REST API design;
- responsive interface design;
- modular analytical services;
- deployment configuration.

The financial functionality provides a realistic domain through which these software-development concepts can be demonstrated.


---

# 44. Disclaimer

MarketPulse is intended for educational and research purposes only.

Market data can be delayed, incomplete or unavailable.

Historical performance does not guarantee future performance.

Backtesting, regime classification, position sizing, risk calculations and stress testing are simplified analytical simulations.

Nothing in MarketPulse should be interpreted as financial, trading or investment advice.


---

# 45. Additional Documentation

For a more detailed map of file interactions, see:

```text
FRAMEWORK_MAP.md
```

For MATLAB-specific documentation, see:

```text
matlab/README.md
```

These documents complement this main README:

```text
README.md
    → overall project, purpose, architecture and setup

FRAMEWORK_MAP.md
    → detailed application file interaction map

matlab/README.md
    → MATLAB-specific architecture and integration
```


---

# 46. Project Summary

MarketPulse began as an idea to create a clearer way of connecting market information, strategy research and risk analysis.

It evolved into a modular full-stack application where:

```text
Data
    informs
Strategy Research

Strategy Research
    informs
Historical Testing

Historical Testing
    informs
Robustness Analysis

Market Data
    informs
Risk Planning

Risk Planning
    informs
Stress Testing
```

The project demonstrates how different software technologies can work together while maintaining clear responsibilities.

At its centre, Django coordinates the application.

PostgreSQL stores persistent data.

Alpaca supplies external market information.

Bootstrap and JavaScript provide the interactive user interface.

Django REST Framework provides reusable APIs.

React demonstrates an alternative API consumer.

MATLAB provides an optional analytical engine.

Render provides the production deployment environment.

The result is a single educational platform designed to help a user move logically from **market information**, to **strategy investigation**, to **risk awareness**.
```

A few important improvements here compared with your original README:

Your original said:

```text
Historical OHLCV import through yfinance.
```

I would **not keep that as the main current architecture statement** if your current application is now using Alpaca, because you have spent a substantial part of the project moving the live/current market-data flow to Alpaca. The README above therefore describes Alpaca as the current market-data integration.

It also makes a very important architectural distinction for your lecturer:

```text
Browser
→ Django
→ Alpaca
```

rather than the browser contacting Alpaca directly. That demonstrates that you understand **why the service/API layer exists**, not just that you managed to make an API call.

The same is true for MATLAB:

```text
Django
→ Python bridge
→ JSON
→ MATLAB
→ JSON
→ Django
```

and for stored market data:

```text
Data Management
→ core.MarketData
→ PostgreSQL
→ reused by Strategies and Risk
```

That is the kind of explanation that shows you understand the **framework as a connected system**, rather than seeing every Django app as an isolated folder.