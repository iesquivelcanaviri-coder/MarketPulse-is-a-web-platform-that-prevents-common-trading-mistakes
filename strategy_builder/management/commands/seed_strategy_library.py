"""
============================================================
MARKETPULSE - STRATEGY LIBRARY SEED COMMAND
============================================================

Framework mapping:

python manage.py seed_strategy_library
        ↓
This management command
        ↓
StrategyLibraryItem model
        ↓
Database
        ↓
Strategies tab + Data tab selector

The command uses update_or_create(), so it can safely be run
again when descriptions or default parameters are updated.
============================================================
"""

from django.core.management.base import BaseCommand

from strategy_builder.models import StrategyLibraryItem


# ============================================================
# STRATEGY / MODEL LIBRARY
# ============================================================

LIBRARY_ITEMS = [

    # ========================================================
    # 1. STOCHASTIC MODELS
    # ========================================================

    {
        "code": "gbm",
        "name": "Geometric Brownian Motion (GBM)",
        "category": "stochastic",
        "display_order": 1,
        "description":
            "Simulates asset-price paths using continuous "
            "compound growth and normally distributed shocks.",
        "purpose":
            "Price-path simulation and baseline stochastic modelling.",
        "default_parameters": {
            "horizon_days": 30,
            "simulations": 1000,
            "drift": 0.08,
            "volatility": 0.20,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Simulated price paths and terminal-price distribution.",
    },

    {
        "code": "ornstein_uhlenbeck",
        "name": "Ornstein-Uhlenbeck Mean Reversion",
        "category": "stochastic",
        "display_order": 2,
        "description":
            "Models a process that tends to return toward "
            "a long-run equilibrium level.",
        "purpose":
            "Mean-reversion modelling and statistical trading research.",
        "default_parameters": {
            "horizon_days": 30,
            "mean_reversion_speed": 0.50,
            "long_run_mean": 0.0,
            "volatility": 0.20,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Mean-reverting simulated paths and distribution.",
    },

    {
        "code": "merton_jump_diffusion",
        "name": "Merton Jump-Diffusion",
        "category": "stochastic",
        "display_order": 3,
        "description":
            "Extends GBM by adding sudden random price jumps.",
        "purpose":
            "Model discontinuous market moves and jump risk.",
        "default_parameters": {
            "horizon_days": 30,
            "simulations": 1000,
            "drift": 0.08,
            "volatility": 0.20,
            "jump_intensity": 0.10,
            "jump_mean": -0.02,
            "jump_volatility": 0.10,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Jump-diffusion paths and terminal distribution.",
    },

    {
        "code": "heston_stochastic_volatility",
        "name": "Heston Stochastic Volatility",
        "category": "stochastic",
        "display_order": 4,
        "description":
            "Models asset prices while allowing volatility itself "
            "to vary stochastically through time.",
        "purpose":
            "Price and volatility simulation.",
        "default_parameters": {
            "horizon_days": 30,
            "simulations": 1000,
            "initial_variance": 0.04,
            "mean_reversion_speed": 2.0,
            "long_run_variance": 0.04,
            "vol_of_vol": 0.30,
            "correlation": -0.70,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Price paths, volatility paths and distributions.",
    },

    {
        "code": "vasicek",
        "name": "Vasicek Interest-Rate Model",
        "category": "stochastic",
        "display_order": 5,
        "description":
            "Mean-reverting stochastic model for interest rates.",
        "purpose":
            "Interest-rate path simulation.",
        "default_parameters": {
            "initial_rate": 0.03,
            "long_run_rate": 0.035,
            "mean_reversion_speed": 0.50,
            "rate_volatility": 0.01,
            "horizon_years": 1,
        },
        "data_requirements": [
            "interest_rate_series",
        ],
        "output_type":
            "Simulated interest-rate paths.",
    },

    {
        "code": "cir",
        "name": "Cox-Ingersoll-Ross (CIR)",
        "category": "stochastic",
        "display_order": 6,
        "description":
            "Mean-reverting interest-rate model designed to "
            "maintain non-negative rates under standard conditions.",
        "purpose":
            "Interest-rate and fixed-income simulation.",
        "default_parameters": {
            "initial_rate": 0.03,
            "long_run_rate": 0.035,
            "mean_reversion_speed": 0.50,
            "rate_volatility": 0.10,
            "horizon_years": 1,
        },
        "data_requirements": [
            "interest_rate_series",
        ],
        "output_type":
            "Simulated non-negative interest-rate paths.",
    },


    # ========================================================
    # 2. TIME-SERIES MODELS
    # ========================================================

    {
        "code": "arima",
        "name": "ARIMA",
        "category": "time_series",
        "display_order": 1,
        "description":
            "Autoregressive Integrated Moving Average model "
            "for univariate time-series forecasting.",
        "purpose":
            "Forecast future prices, returns or other market series.",
        "default_parameters": {
            "p": 1,
            "d": 1,
            "q": 1,
            "forecast_steps": 20,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Forecast values and confidence intervals.",
    },

    {
        "code": "sarima",
        "name": "SARIMA",
        "category": "time_series",
        "display_order": 2,
        "description":
            "Seasonal extension of ARIMA for series containing "
            "repeating seasonal patterns.",
        "purpose":
            "Time-series forecasting with seasonality.",
        "default_parameters": {
            "p": 1,
            "d": 1,
            "q": 1,
            "P": 1,
            "D": 0,
            "Q": 1,
            "seasonal_period": 5,
            "forecast_steps": 20,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Seasonal forecasts and confidence intervals.",
    },

    {
        "code": "garch",
        "name": "GARCH Family",
        "category": "time_series",
        "display_order": 3,
        "description":
            "Models volatility clustering using conditional variance.",
        "purpose":
            "Forecast market volatility and support risk analysis.",
        "default_parameters": {
            "p": 1,
            "q": 1,
            "forecast_steps": 20,
        },
        "data_requirements": [
            "close_price",
            "returns",
        ],
        "output_type":
            "Conditional volatility forecast.",
    },

    {
        "code": "kalman_filter",
        "name": "Kalman Filter",
        "category": "time_series",
        "display_order": 4,
        "description":
            "Recursive state-space estimator used to infer "
            "latent market states from noisy observations.",
        "purpose":
            "Trend estimation, smoothing and dynamic relationships.",
        "default_parameters": {
            "process_variance": 0.0001,
            "measurement_variance": 0.01,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Filtered state estimates and trend.",
    },

    {
        "code": "var",
        "name": "Vector Autoregression (VAR)",
        "category": "time_series",
        "display_order": 5,
        "description":
            "Multivariate time-series model where several variables "
            "jointly explain their historical dynamics.",
        "purpose":
            "Forecast interactions among multiple assets or variables.",
        "default_parameters": {
            "lags": 5,
            "forecast_steps": 20,
        },
        "data_requirements": [
            "multiple_return_series",
        ],
        "output_type":
            "Multivariate forecasts and impulse relationships.",
    },


    # ========================================================
    # 3. MACHINE LEARNING MODELS
    # ========================================================

    {
        "code": "random_forest",
        "name": "Random Forest",
        "category": "machine_learning",
        "display_order": 1,
        "description":
            "Ensemble of decision trees for market classification "
            "or regression.",
        "purpose":
            "Predict buy/sell probabilities, returns or direction.",
        "default_parameters": {
            "estimators": 200,
            "max_depth": 8,
            "test_size": 0.20,
        },
        "data_requirements": [
            "close_price",
            "returns",
            "technical_features",
        ],
        "output_type":
            "Predictions, probabilities, feature importance and PnL.",
    },

    {
        "code": "xgboost",
        "name": "XGBoost",
        "category": "machine_learning",
        "display_order": 2,
        "description":
            "Gradient-boosted decision-tree model for structured "
            "financial features.",
        "purpose":
            "Market direction or return prediction.",
        "default_parameters": {
            "estimators": 200,
            "max_depth": 4,
            "learning_rate": 0.05,
            "test_size": 0.20,
        },
        "data_requirements": [
            "close_price",
            "returns",
            "technical_features",
        ],
        "output_type":
            "Predictions, probabilities, importance and PnL.",
    },

    {
        "code": "svm",
        "name": "Support Vector Machine (SVM)",
        "category": "machine_learning",
        "display_order": 3,
        "description":
            "Margin-based machine-learning model for classification "
            "or regression.",
        "purpose":
            "Predict market direction using engineered features.",
        "default_parameters": {
            "kernel": "rbf",
            "C": 1.0,
            "test_size": 0.20,
        },
        "data_requirements": [
            "close_price",
            "returns",
            "technical_features",
        ],
        "output_type":
            "Classification metrics, signals and strategy PnL.",
    },

    {
        "code": "lstm",
        "name": "LSTM Neural Network",
        "category": "machine_learning",
        "display_order": 4,
        "description":
            "Recurrent neural-network architecture designed "
            "for sequential data.",
        "purpose":
            "Learn temporal patterns in financial time series.",
        "default_parameters": {
            "lookback": 60,
            "epochs": 20,
            "batch_size": 32,
        },
        "data_requirements": [
            "close_price",
            "returns",
        ],
        "output_type":
            "Forecasts, prediction error and derived signals.",
    },

    {
        "code": "transformer",
        "name": "Transformer Time-Series Model",
        "category": "machine_learning",
        "display_order": 5,
        "description":
            "Attention-based architecture for learning complex "
            "temporal dependencies.",
        "purpose":
            "Financial sequence forecasting and signal prediction.",
        "default_parameters": {
            "lookback": 60,
            "epochs": 20,
            "attention_heads": 4,
        },
        "data_requirements": [
            "close_price",
            "returns",
            "technical_features",
        ],
        "output_type":
            "Forecasts, probabilities and model evaluation.",
    },

    {
        "code": "reinforcement_learning",
        "name": "Basic Reinforcement-Learning Trading Bot",
        "category": "machine_learning",
        "display_order": 6,
        "description":
            "Agent learns trading actions from rewards generated "
            "by a simulated market environment.",
        "purpose":
            "Research sequential trading decisions.",
        "default_parameters": {
            "episodes": 100,
            "initial_capital": 10000,
            "transaction_cost": 0.001,
        },
        "data_requirements": [
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "volume",
        ],
        "output_type":
            "Actions, rewards, equity curve and PnL.",
    },


    # ========================================================
    # 4. FACTOR MODELS
    # ========================================================

    {
        "code": "fama_french_3",
        "name": "Fama-French 3-Factor Model",
        "category": "factor",
        "display_order": 1,
        "description":
            "Explains returns using market, size and value factors.",
        "purpose":
            "Estimate factor exposures and abnormal return.",
        "default_parameters": {},
        "data_requirements": [
            "asset_returns",
            "market_factor",
            "SMB",
            "HML",
            "risk_free_rate",
        ],
        "output_type":
            "Alpha, factor betas, t-statistics and R-squared.",
    },

    {
        "code": "fama_french_5",
        "name": "Fama-French 5-Factor Model",
        "category": "factor",
        "display_order": 2,
        "description":
            "Extends the three-factor model with profitability "
            "and investment factors.",
        "purpose":
            "Estimate broader systematic factor exposures.",
        "default_parameters": {},
        "data_requirements": [
            "asset_returns",
            "market_factor",
            "SMB",
            "HML",
            "RMW",
            "CMA",
            "risk_free_rate",
        ],
        "output_type":
            "Alpha, five factor betas and regression diagnostics.",
    },

    {
        "code": "carhart_4",
        "name": "Carhart 4-Factor Model",
        "category": "factor",
        "display_order": 3,
        "description":
            "Adds a momentum factor to the Fama-French "
            "three-factor framework.",
        "purpose":
            "Measure return exposure to market, size, value and momentum.",
        "default_parameters": {},
        "data_requirements": [
            "asset_returns",
            "market_factor",
            "SMB",
            "HML",
            "momentum_factor",
            "risk_free_rate",
        ],
        "output_type":
            "Alpha, four factor betas and regression diagnostics.",
    },

    {
        "code": "momentum_factor",
        "name": "Momentum Factor",
        "category": "factor",
        "display_order": 4,
        "description":
            "Ranks securities according to recent relative performance.",
        "purpose":
            "Test cross-sectional or time-series momentum exposure.",
        "default_parameters": {
            "lookback_months": 12,
        },
        "data_requirements": [
            "multiple_asset_returns",
        ],
        "output_type":
            "Momentum scores, rankings and factor returns.",
    },

    {
        "code": "quality_factor",
        "name": "Quality Factor",
        "category": "factor",
        "display_order": 5,
        "description":
            "Ranks companies using profitability, balance-sheet "
            "or earnings-quality characteristics.",
        "purpose":
            "Construct and analyse quality-factor exposure.",
        "default_parameters": {},
        "data_requirements": [
            "fundamental_data",
            "asset_returns",
        ],
        "output_type":
            "Quality scores, factor exposure and performance.",
    },

    {
        "code": "low_volatility_factor",
        "name": "Low-Volatility Factor",
        "category": "factor",
        "display_order": 6,
        "description":
            "Ranks assets according to realised volatility.",
        "purpose":
            "Investigate defensive low-volatility portfolio behaviour.",
        "default_parameters": {
            "lookback_days": 60,
        },
        "data_requirements": [
            "multiple_asset_returns",
        ],
        "output_type":
            "Volatility ranking, portfolio return and risk.",
    },


    # ========================================================
    # 5. PORTFOLIO OPTIMISATION
    # ========================================================

    {
        "code": "markowitz_mean_variance",
        "name": "Markowitz Mean-Variance",
        "category": "portfolio",
        "display_order": 1,
        "description":
            "Optimises portfolio weights using expected returns "
            "and the covariance matrix.",
        "purpose":
            "Find portfolios balancing expected return and risk.",
        "default_parameters": {
            "risk_free_rate": 0.02,
        },
        "data_requirements": [
            "multiple_asset_returns",
        ],
        "output_type":
            "Asset weights, expected return, volatility and Sharpe ratio.",
    },

    {
        "code": "efficient_frontier",
        "name": "Efficient Frontier",
        "category": "portfolio",
        "display_order": 2,
        "description":
            "Calculates the set of mean-variance efficient portfolios.",
        "purpose":
            "Visualise optimal risk-return combinations.",
        "default_parameters": {
            "frontier_points": 50,
        },
        "data_requirements": [
            "multiple_asset_returns",
        ],
        "output_type":
            "Efficient-frontier curve and portfolio weights.",
    },

    {
        "code": "black_litterman",
        "name": "Black-Litterman",
        "category": "portfolio",
        "display_order": 3,
        "description":
            "Combines market equilibrium returns with investor views.",
        "purpose":
            "Generate more stable portfolio allocations.",
        "default_parameters": {
            "tau": 0.05,
        },
        "data_requirements": [
            "multiple_asset_returns",
            "market_weights",
            "investor_views",
        ],
        "output_type":
            "Posterior expected returns and portfolio weights.",
    },

    {
        "code": "risk_parity",
        "name": "Risk Parity",
        "category": "portfolio",
        "display_order": 4,
        "description":
            "Allocates capital so assets contribute more equally "
            "to overall portfolio risk.",
        "purpose":
            "Construct risk-balanced portfolios.",
        "default_parameters": {},
        "data_requirements": [
            "multiple_asset_returns",
        ],
        "output_type":
            "Risk-balanced weights and risk contributions.",
    },


    # ========================================================
    # 6. DERIVATIVES PRICING
    # ========================================================

    {
        "code": "black_scholes",
        "name": "Black-Scholes",
        "category": "derivatives",
        "display_order": 1,
        "description":
            "Closed-form option-pricing model for European options.",
        "purpose":
            "Calculate theoretical option prices and Greeks.",
        "default_parameters": {
            "option_type": "call",
            "strike": 100,
            "time_to_maturity": 1.0,
            "risk_free_rate": 0.03,
            "volatility": 0.20,
        },
        "data_requirements": [
            "spot_price",
        ],
        "output_type":
            "Fair value and Greeks.",
    },

    {
        "code": "binomial_tree",
        "name": "Binomial Option-Pricing Tree",
        "category": "derivatives",
        "display_order": 2,
        "description":
            "Discrete-time option-pricing model based on "
            "up/down price movements.",
        "purpose":
            "Price European and potentially American options.",
        "default_parameters": {
            "steps": 100,
            "strike": 100,
            "time_to_maturity": 1.0,
            "risk_free_rate": 0.03,
            "volatility": 0.20,
        },
        "data_requirements": [
            "spot_price",
        ],
        "output_type":
            "Option fair value and pricing tree.",
    },

    {
        "code": "heston_option_pricing",
        "name": "Heston Option Pricing",
        "category": "derivatives",
        "display_order": 3,
        "description":
            "Option-pricing framework based on stochastic volatility.",
        "purpose":
            "Price options where volatility is allowed to vary.",
        "default_parameters": {
            "strike": 100,
            "time_to_maturity": 1.0,
            "risk_free_rate": 0.03,
            "initial_variance": 0.04,
        },
        "data_requirements": [
            "spot_price",
        ],
        "output_type":
            "Option fair value under stochastic volatility.",
    },

    {
        "code": "monte_carlo_option_pricing",
        "name": "Monte Carlo Option Pricing",
        "category": "derivatives",
        "display_order": 4,
        "description":
            "Values derivatives by averaging discounted payoffs "
            "across simulated price paths.",
        "purpose":
            "Price derivatives using simulation.",
        "default_parameters": {
            "simulations": 10000,
            "strike": 100,
            "time_to_maturity": 1.0,
            "risk_free_rate": 0.03,
            "volatility": 0.20,
        },
        "data_requirements": [
            "spot_price",
        ],
        "output_type":
            "Estimated option value and payoff distribution.",
    },


    # ========================================================
    # 7. SIMULATION & MONTE CARLO
    # ========================================================

    {
        "code": "monte_carlo_gbm",
        "name": "Monte Carlo GBM",
        "category": "monte_carlo",
        "display_order": 1,
        "description":
            "Runs many geometric Brownian-motion simulations.",
        "purpose":
            "Estimate future asset-price distributions.",
        "default_parameters": {
            "simulations": 5000,
            "horizon_days": 252,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Price-path distribution and terminal percentiles.",
    },

    {
        "code": "monte_carlo_heston",
        "name": "Monte Carlo Heston",
        "category": "monte_carlo",
        "display_order": 2,
        "description":
            "Monte Carlo simulation with stochastic volatility.",
        "purpose":
            "Model price uncertainty and changing volatility.",
        "default_parameters": {
            "simulations": 5000,
            "horizon_days": 252,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Price and volatility distributions.",
    },

    {
        "code": "monte_carlo_jump_diffusion",
        "name": "Monte Carlo Jump-Diffusion",
        "category": "monte_carlo",
        "display_order": 3,
        "description":
            "Monte Carlo simulation including discontinuous price jumps.",
        "purpose":
            "Evaluate outcomes containing crash or jump risk.",
        "default_parameters": {
            "simulations": 5000,
            "horizon_days": 252,
            "jump_intensity": 0.10,
        },
        "data_requirements": [
            "close_price",
        ],
        "output_type":
            "Jump-risk price distribution.",
    },

    {
        "code": "monte_carlo_var_es",
        "name": "Monte Carlo VaR / Expected Shortfall",
        "category": "monte_carlo",
        "display_order": 4,
        "description":
            "Simulates portfolio outcomes to estimate tail-loss metrics.",
        "purpose":
            "Measure Value at Risk and Expected Shortfall.",
        "default_parameters": {
            "simulations": 10000,
            "confidence_level": 0.95,
            "horizon_days": 1,
        },
        "data_requirements": [
            "returns",
        ],
        "output_type":
            "VaR, Expected Shortfall and loss distribution.",
    },

    {
        "code": "monte_carlo_equity_bootstrap",
        "name": "Monte Carlo Equity Curve / Bootstrapping",
        "category": "monte_carlo",
        "display_order": 5,
        "description":
            "Resamples historical strategy returns to generate "
            "alternative equity-curve paths.",
        "purpose":
            "Assess strategy robustness and sequencing risk.",
        "default_parameters": {
            "simulations": 5000,
            "block_size": 5,
        },
        "data_requirements": [
            "strategy_returns",
        ],
        "output_type":
            "Equity-curve distribution, drawdown and terminal wealth.",
    },

    {
        "code": "monte_carlo_portfolio",
        "name": "Monte Carlo Portfolio Scenarios",
        "category": "monte_carlo",
        "display_order": 6,
        "description":
            "Simulates correlated portfolio asset returns under "
            "many possible scenarios.",
        "purpose":
            "Assess portfolio uncertainty and downside risk.",
        "default_parameters": {
            "simulations": 5000,
            "horizon_days": 252,
        },
        "data_requirements": [
            "multiple_asset_returns",
            "portfolio_weights",
        ],
        "output_type":
            "Portfolio return distribution, VaR and scenario outcomes.",
    },

]


# ============================================================
# DJANGO MANAGEMENT COMMAND
# ============================================================

class Command(BaseCommand):

    help = (
        "Create or update the complete "
        "MarketPulse strategy/model library."
    )


    def handle(
        self,
        *args,
        **options,
    ):

        created_count = 0

        updated_count = 0


        # ----------------------------------------------------
        # Save each library item
        # ----------------------------------------------------

        for item in LIBRARY_ITEMS:

            code = item["code"]

            defaults = {
                key: value
                for key, value in item.items()
                if key != "code"
            }


            _, created = (
                StrategyLibraryItem.objects
                .update_or_create(
                    code=code,
                    defaults=defaults,
                )
            )


            if created:

                created_count += 1

            else:

                updated_count += 1


        # ----------------------------------------------------
        # Terminal confirmation
        # ----------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "MarketPulse strategy library complete. "
                    f"Created: {created_count}. "
                    f"Updated: {updated_count}. "
                    f"Total: {len(LIBRARY_ITEMS)}."
                )
            )
        )