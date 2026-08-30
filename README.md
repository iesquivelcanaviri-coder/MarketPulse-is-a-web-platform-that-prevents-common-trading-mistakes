# MarketPulse: Smart Trading Analysis Platform

MarketPulse is an educational full-stack finance application built with **Python 3.13.5, Django 5.2, PostgreSQL, Django REST Framework, React, Bootstrap, Chart.js, yfinance, Celery/Redis and MATLAB integration**.

> Backtests and risk calculations are educational simulations, not investment advice or guarantees of future performance.

## Implemented features
- Registration, login, logout and editable user risk profile.
- PostgreSQL/Neon database configuration through `DATABASE_URL`.
- Historical OHLCV import through yfinance.
- IF/THEN moving-average strategy builder.
- Backtesting with transaction costs, slippage, next-session-open execution, overnight gap exposure, market-session constraints, volume-capacity limits and partial fills.
- Position sizing, stop loss, risk/reward and volatility-adjusted risk.
- Overfitting checks across multiple historical windows.
- Bull/bear/sideways/high-volatility regime identification.
- Crash, volatility-spike, liquidity-crisis and regime-change stress tests.
- Django REST Framework API and separate React/Vite frontend.
- Optional Celery/Redis background tasks.
- Optional MATLAB execution bridge that does not prevent Django from running when MATLAB is disabled.
- Render/Gunicorn/WhiteNoise deployment support.

## Local setup on macOS
```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```
For the fastest local demo, leave `DATABASE_URL=` blank and Django uses SQLite. For PostgreSQL/Neon, set your private `DATABASE_URL`. Set a proper `SECRET_KEY`, then:
```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py seed_marketpulse
python manage.py createsuperuser
python manage.py runserver
```
Open `http://127.0.0.1:8000/`.

## React
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/`.

## MATLAB
Set `MATLAB_ENABLED=True` and ensure the `matlab` command is available. Django calls scripts in `/matlab` through `core/matlab_bridge.py`.

## Tests
```bash
python manage.py test
```

See `FRAMEWORK_MAP.md` for the complete file interaction map.


## Local database fallback
For reliable classroom testing, MarketPulse uses SQLite only when `DATABASE_URL` is blank. The production architecture remains PostgreSQL/Neon: as soon as a PostgreSQL `DATABASE_URL` is supplied, Django switches to PostgreSQL automatically.
