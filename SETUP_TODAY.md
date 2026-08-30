# MarketPulse - Quick Local Demo Setup

## ==================== 1. PYTHON 3.13.5 ====================
```bash
python3.13 -m venv .venv
source .venv/bin/activate
python --version
```
Expected: `Python 3.13.5`.

## ==================== 2. INSTALL PACKAGES ====================
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## ==================== 3. ENVIRONMENT ====================
```bash
cp .env.example .env
```
For the fastest local demo, leave `DATABASE_URL=` blank. Django will use local SQLite.
For Neon/PostgreSQL, paste the private Neon URL into `DATABASE_URL` in `.env`. Never commit `.env`.

## ==================== 4. DATABASE ====================
```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py seed_marketpulse
python manage.py createsuperuser
```

## ==================== 5. START DJANGO ====================
```bash
python manage.py runserver
```
Open `http://127.0.0.1:8000/`.

## ==================== 6. LECTURER DEMO ORDER ====================
1. Register/Login
2. Import AAPL historical data (2-3 years is useful)
3. Create a moving-average strategy
4. Run the realistic educational backtest
5. Use Risk Calculator
6. Run Overfitting analysis
7. Run Market Regime analysis
8. Run Stress Test
9. Show `/api/health/`
10. Show `frontend/` and `matlab/` integration files

## ==================== 7. REACT ====================
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
Open `http://localhost:5173/`.

## ==================== 8. MATLAB ====================
Leave `MATLAB_ENABLED=False` unless MATLAB is installed and the `matlab` command works.
The Django web app is intentionally not blocked by MATLAB installation/licensing.
