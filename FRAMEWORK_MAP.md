# MarketPulse Framework Map

## Main request flow
Browser / React → `marketpulse/urls.py` → app `urls.py` → app `views.py` → forms/services → Django models → PostgreSQL → HTML or JSON response.

## Integration map
- `accounts`: custom user + risk profile.
- `core`: shared market data, strategy, backtest and alert models; home/dashboard; MATLAB bridge.
- `data_management`: yfinance import and optional Celery background processing.
- `strategy_builder`: IF/THEN moving-average rules plus execution/backtest simulation.
- `risk_management`: position sizing, stop loss, risk/reward and volatility-adjusted risk.
- `analysis_tools`: overfitting, market regimes and stress testing.
- `api`: Django REST Framework endpoints consumed by `/frontend` React app.
- `matlab`: MATLAB calculations called by `core/matlab_bridge.py` when enabled.

Every substantive file also contains a subtitle-style comment explaining its framework role.


## Commenting convention
Python, HTML, CSS, JavaScript and MATLAB source files include subtitle-style framework notes. JSON files such as `frontend/package.json` cannot legally contain comments, so their mapping is documented in `frontend/README.md` and this file instead.
