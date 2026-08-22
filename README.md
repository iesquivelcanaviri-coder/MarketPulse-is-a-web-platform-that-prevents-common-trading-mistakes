# MarketPulse: A Smart Trading Platform

MarketPulse is a web application that prevents common trading mistakes by acting as a smart assistant for traders. Unlike typical charting tools that just show data, our platform focuses on the real reasons traders lose money - overfitting, poor risk management, and emotional decisions.

## Features

### Core Features
- **Smart Model Testing**: Cross-validation across different time periods with automatic warnings when models appear "too perfect"
- **Risk Management Tools**: Automatic position sizing calculator, maximum daily loss limits, and volatility-adjusted risk rules
- **Realistic Backtesting**: Transaction cost simulation, overnight gap modeling, and market-hours constraints
- **Market Change Detection**: Bull/bear/sideways market identification with volatility regime alerts

### Secondary Features
- **Execution Simulation**: Slippage modeling, bid-ask spread simulation, and partial fill probability
- **Rule Automation**: IF/THEN rule builder with continuous monitoring and emotional bias prevention

## Technology Stack

- **Backend**: Django 5.0.2
- **Frontend**: Bootstrap 5, Chart.js
- **Database**: PostgreSQL
- **Task Queue**: Celery with Redis
- **Data Source**: Yahoo Finance API

## Installation

1. Clone the repository:
```bash
