"""
MARKETPULSE - STRATEGY LIBRARY SEED COMMAND

Purpose:
Create or update the 37 predefined model-library entries.

Framework:
python manage.py seed_strategy_library
-> Command.handle()
-> StrategyLibraryItem
-> configured database
-> Strategies library and Data model selector.

Matching uses each entry's code.
Re-running overwrites the metadata supplied in defaults.
This command stores model metadata, not numerical implementations.
"""

# ============================================================
# 1. IMPORTS
# ============================================================
from django.core.management.base import BaseCommand  # Import: I use Django's base class for management commands.
from strategy_builder.models import StrategyLibraryItem  # Model import: I access the library's database records.

# ============================================================
# 2. LIBRARY DATA: LIST OF MODEL DICTIONARIES
# ============================================================
LIBRARY_ITEMS = [  # List assignment: I collect all predefined catalogue entries.

    # --------------------------------------------------------
    # 2.1 STOCHASTIC MODELS
    # --------------------------------------------------------
    {  # Dictionary: I begin the GBM catalogue entry.
        "code": "gbm",  # String identifier: I use this code to match the database record.
        "name": "Geometric Brownian Motion (GBM)",  # String: I store the displayed model name.
        "category": "stochastic",  # Category code: I group this entry with stochastic models.
        "display_order": 1,  # Integer: I set its position within the category.
        "description": (  # Grouping: I begin the model's descriptive text.
            "Simulates asset-price paths using continuous "  # String: I preserve the first part of the description.
            "compound growth and normally distributed shocks."  # Adjacent string: Python joins this to the preceding text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Price-path simulation and baseline stochastic modelling.",  # String: I describe the intended research use.
        "default_parameters": {  # Nested dictionary: I store the initial model settings.
            "horizon_days": 30,  # Integer value: I store the simulation horizon.
            "simulations": 1000,  # Integer value: I store the requested simulation count.
            "drift": 0.08,  # Float value: I store the drift setting.
            "volatility": 0.20,  # Float value: I store the volatility setting.
        },  # Closing brace: I finish the parameter dictionary.
        "data_requirements": ["close_price"],  # List of strings: I identify the required data input.
        "output_type": "Simulated price paths and terminal-price distribution.",  # String: I describe the expected output.
    },  # Closing brace and comma: I finish this list entry.
    {  # Dictionary: I begin the mean-reversion entry.
        "code": "ornstein_uhlenbeck",  # Identifier: I define the entry's lookup code.
        "name": "Ornstein-Uhlenbeck Mean Reversion",  # String: I store the readable name.
        "category": "stochastic",  # Category code: I assign the stochastic family.
        "display_order": 2,  # Integer: I set the category display position.
        "description": (  # Grouping: I begin the description.
            "Models a process that tends to return toward "  # String: I begin the original text.
            "a long-run equilibrium level."  # Adjacent string: I complete the description.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Mean-reversion modelling and statistical trading research.",  # String: I store the intended purpose.
        "default_parameters": {  # Dictionary: I store the model settings.
            "horizon_days": 30,  # Integer: I store the horizon.
            "mean_reversion_speed": 0.50,  # Float: I store the reversion-speed setting.
            "long_run_mean": 0.0,  # Float: I store the equilibrium setting.
            "volatility": 0.20,  # Float: I store the volatility setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the required data field.
        "output_type": "Mean-reverting simulated paths and distribution.",  # String: I describe expected results.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the jump-diffusion entry.
        "code": "merton_jump_diffusion",  # Identifier: I define its lookup code.
        "name": "Merton Jump-Diffusion",  # String: I store the readable name.
        "category": "stochastic",  # Category: I assign the stochastic family.
        "display_order": 3,  # Integer: I set its category position.
        "description": "Extends GBM by adding sudden random price jumps.",  # String: I preserve the description.
        "purpose": "Model discontinuous market moves and jump risk.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store the simulation settings.
            "horizon_days": 30,  # Integer: I store the horizon.
            "simulations": 1000,  # Integer: I store the simulation count.
            "drift": 0.08,  # Float: I store the drift setting.
            "volatility": 0.20,  # Float: I store the volatility setting.
            "jump_intensity": 0.10,  # Float: I store the jump-intensity setting.
            "jump_mean": -0.02,  # Signed float: I store the mean jump setting.
            "jump_volatility": 0.10,  # Float: I store the jump-volatility setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the required input.
        "output_type": "Jump-diffusion paths and terminal distribution.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Heston simulation entry.
        "code": "heston_stochastic_volatility",  # Identifier: I define its lookup code.
        "name": "Heston Stochastic Volatility",  # String: I store the displayed name.
        "category": "stochastic",  # Category: I assign the stochastic family.
        "display_order": 4,  # Integer: I set its display position.
        "description": (  # Grouping: I begin the description.
            "Models asset prices while allowing volatility itself "  # String: I begin the original text.
            "to vary stochastically through time."  # Adjacent string: I finish the description.
        ),  # Closing parenthesis: I finish the text.
        "purpose": "Price and volatility simulation.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store model settings.
            "horizon_days": 30,  # Integer: I store the horizon.
            "simulations": 1000,  # Integer: I store the simulation count.
            "initial_variance": 0.04,  # Float: I store initial variance.
            "mean_reversion_speed": 2.0,  # Float: I store the reversion-speed setting.
            "long_run_variance": 0.04,  # Float: I store long-run variance.
            "vol_of_vol": 0.30,  # Float: I store the volatility-of-volatility setting.
            "correlation": -0.70,  # Signed float: I store the correlation setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the required input.
        "output_type": "Price paths, volatility paths and distributions.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Vasicek entry.
        "code": "vasicek",  # Identifier: I define its lookup code.
        "name": "Vasicek Interest-Rate Model",  # String: I store the displayed name.
        "category": "stochastic",  # Category: I assign the stochastic family.
        "display_order": 5,  # Integer: I set its display position.
        "description": "Mean-reverting stochastic model for interest rates.",  # String: I preserve the description.
        "purpose": "Interest-rate path simulation.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store the rate-model settings.
            "initial_rate": 0.03,  # Float: I store the starting rate.
            "long_run_rate": 0.035,  # Float: I store the equilibrium rate.
            "mean_reversion_speed": 0.50,  # Float: I store the reversion-speed setting.
            "rate_volatility": 0.01,  # Float: I store the rate-volatility setting.
            "horizon_years": 1,  # Integer: I store the horizon in years.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["interest_rate_series"],  # List: I identify the required rate series.
        "output_type": "Simulated interest-rate paths.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the CIR entry.
        "code": "cir",  # Identifier: I define its lookup code.
        "name": "Cox-Ingersoll-Ross (CIR)",  # String: I store the displayed name.
        "category": "stochastic",  # Category: I assign the stochastic family.
        "display_order": 6,  # Integer: I set its display position.
        "description": (  # Grouping: I begin the description.
            "Mean-reverting interest-rate model designed to "  # String: I begin the original text.
            "maintain non-negative rates under standard conditions."  # Adjacent string: I finish the description.
        ),  # Closing parenthesis: I finish the text.
        "purpose": "Interest-rate and fixed-income simulation.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store rate-model settings.
            "initial_rate": 0.03,  # Float: I store the starting rate.
            "long_run_rate": 0.035,  # Float: I store the long-run rate.
            "mean_reversion_speed": 0.50,  # Float: I store the reversion-speed setting.
            "rate_volatility": 0.10,  # Float: I store the rate-volatility setting.
            "horizon_years": 1,  # Integer: I store the horizon.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["interest_rate_series"],  # List: I identify the required input.
        "output_type": "Simulated non-negative interest-rate paths.",  # String: I preserve the expected-output description.
    },  # Closing brace: I finish the entry.

    # --------------------------------------------------------
    # 2.2 TIME-SERIES MODELS
    # --------------------------------------------------------
    {  # Dictionary: I begin the ARIMA entry.
        "code": "arima",  # Identifier: I define its lookup code.
        "name": "ARIMA",  # String: I store the displayed name.
        "category": "time_series",  # Category: I assign the time-series family.
        "display_order": 1,  # Integer: I set its category position.
        "description": (  # Grouping: I begin the description.
            "Autoregressive Integrated Moving Average model "  # String: I begin the original text.
            "for univariate time-series forecasting."  # Adjacent string: I complete the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Forecast future prices, returns or other market series.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store forecasting settings.
            "p": 1,  # Integer: I store the autoregressive order.
            "d": 1,  # Integer: I store the differencing order.
            "q": 1,  # Integer: I store the moving-average order.
            "forecast_steps": 20,  # Integer: I store the requested forecast length.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the input.
        "output_type": "Forecast values and confidence intervals.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the SARIMA entry.
        "code": "sarima",  # Identifier: I define its lookup code.
        "name": "SARIMA",  # String: I store the displayed name.
        "category": "time_series",  # Category: I assign the time-series family.
        "display_order": 2,  # Integer: I set its display position.
        "description": (  # Grouping: I begin the description.
            "Seasonal extension of ARIMA for series containing "  # String: I begin the original text.
            "repeating seasonal patterns."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Time-series forecasting with seasonality.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store non-seasonal and seasonal settings.
            "p": 1,  # Integer: I store the non-seasonal autoregressive order.
            "d": 1,  # Integer: I store the non-seasonal differencing order.
            "q": 1,  # Integer: I store the non-seasonal moving-average order.
            "P": 1,  # Case-sensitive key: I store the seasonal autoregressive order.
            "D": 0,  # Case-sensitive key: I store the seasonal differencing order.
            "Q": 1,  # Case-sensitive key: I store the seasonal moving-average order.
            "seasonal_period": 5,  # Integer: I store the seasonal period.
            "forecast_steps": 20,  # Integer: I store the forecast length.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the input.
        "output_type": "Seasonal forecasts and confidence intervals.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the GARCH entry.
        "code": "garch",  # Identifier: I define its lookup code.
        "name": "GARCH Family",  # String: I store the displayed name.
        "category": "time_series",  # Category: I assign the time-series family.
        "display_order": 3,  # Integer: I set its position.
        "description": "Models volatility clustering using conditional variance.",  # String: I preserve the description.
        "purpose": "Forecast market volatility and support risk analysis.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I preserve the model's parameter names.
            "p": 1,  # Integer: I store the p setting.
            "q": 1,  # Integer: I store the q setting.
            "forecast_steps": 20,  # Integer: I store the forecast length.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price", "returns"],  # List: I identify both required inputs.
        "output_type": "Conditional volatility forecast.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Kalman-filter entry.
        "code": "kalman_filter",  # Identifier: I define its lookup code.
        "name": "Kalman Filter",  # String: I store the displayed name.
        "category": "time_series",  # Category: I assign the time-series family.
        "display_order": 4,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Recursive state-space estimator used to infer "  # String: I begin the original text.
            "latent market states from noisy observations."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Trend estimation, smoothing and dynamic relationships.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store filter settings.
            "process_variance": 0.0001,  # Float: I store the process-variance setting.
            "measurement_variance": 0.01,  # Float: I store the measurement-variance setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the input.
        "output_type": "Filtered state estimates and trend.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the VAR entry.
        "code": "var",  # Identifier: I define its lookup code.
        "name": "Vector Autoregression (VAR)",  # String: I store the displayed name.
        "category": "time_series",  # Category: I assign the time-series family.
        "display_order": 5,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Multivariate time-series model where several variables "  # String: I begin the original text.
            "jointly explain their historical dynamics."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Forecast interactions among multiple assets or variables.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store forecasting settings.
            "lags": 5,  # Integer: I store the lag count.
            "forecast_steps": 20,  # Integer: I store the forecast length.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["multiple_return_series"],  # List: I identify the required multivariate data.
        "output_type": "Multivariate forecasts and impulse relationships.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.

    # --------------------------------------------------------
    # 2.3 MACHINE LEARNING MODELS
    # --------------------------------------------------------
    {  # Dictionary: I begin the random-forest entry.
        "code": "random_forest",  # Identifier: I define its lookup code.
        "name": "Random Forest",  # String: I store the displayed name.
        "category": "machine_learning",  # Category: I assign the machine-learning family.
        "display_order": 1,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Ensemble of decision trees for market classification "  # String: I begin the original text.
            "or regression."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Predict buy/sell probabilities, returns or direction.",  # String: I store the intended purpose.
        "default_parameters": {  # Dictionary: I store model-training settings.
            "estimators": 200,  # Integer: I store the estimator-count setting.
            "max_depth": 8,  # Integer: I store the tree-depth limit.
            "test_size": 0.20,  # Float: I store the test-data fraction.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price", "returns", "technical_features"],  # List: I store the required inputs.
        "output_type": "Predictions, probabilities, feature importance and PnL.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the XGBoost entry.
        "code": "xgboost",  # Identifier: I define its lookup code.
        "name": "XGBoost",  # String: I store the displayed name.
        "category": "machine_learning",  # Category: I assign the machine-learning family.
        "display_order": 2,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Gradient-boosted decision-tree model for structured "  # String: I begin the original text.
            "financial features."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Market direction or return prediction.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store training settings.
            "estimators": 200,  # Integer: I store the estimator-count setting.
            "max_depth": 4,  # Integer: I store the depth limit.
            "learning_rate": 0.05,  # Float: I store the learning-rate setting.
            "test_size": 0.20,  # Float: I store the test-data fraction.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price", "returns", "technical_features"],  # List: I store required inputs.
        "output_type": "Predictions, probabilities, importance and PnL.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the SVM entry.
        "code": "svm",  # Identifier: I define its lookup code.
        "name": "Support Vector Machine (SVM)",  # String: I store the displayed name.
        "category": "machine_learning",  # Category: I assign the machine-learning family.
        "display_order": 3,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Margin-based machine-learning model for classification "  # String: I begin the original text.
            "or regression."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Predict market direction using engineered features.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store training settings.
            "kernel": "rbf",  # String value: I store the kernel selection.
            "C": 1.0,  # Case-sensitive key and float: I preserve the regularisation setting.
            "test_size": 0.20,  # Float: I store the test-data fraction.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price", "returns", "technical_features"],  # List: I store required inputs.
        "output_type": "Classification metrics, signals and strategy PnL.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the LSTM entry.
        "code": "lstm",  # Identifier: I define its lookup code.
        "name": "LSTM Neural Network",  # String: I store the displayed name.
        "category": "machine_learning",  # Category: I assign the machine-learning family.
        "display_order": 4,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Recurrent neural-network architecture designed "  # String: I begin the original text.
            "for sequential data."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Learn temporal patterns in financial time series.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store training settings.
            "lookback": 60,  # Integer: I store the input-window setting.
            "epochs": 20,  # Integer: I store the training-epoch count.
            "batch_size": 32,  # Integer: I store the batch-size setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price", "returns"],  # List: I store required inputs.
        "output_type": "Forecasts, prediction error and derived signals.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Transformer entry.
        "code": "transformer",  # Identifier: I define its lookup code.
        "name": "Transformer Time-Series Model",  # String: I store the displayed name.
        "category": "machine_learning",  # Category: I assign the machine-learning family.
        "display_order": 5,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Attention-based architecture for learning complex "  # String: I begin the original text.
            "temporal dependencies."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Financial sequence forecasting and signal prediction.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store training settings.
            "lookback": 60,  # Integer: I store the input-window setting.
            "epochs": 20,  # Integer: I store the epoch count.
            "attention_heads": 4,  # Integer: I store the attention-head count.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price", "returns", "technical_features"],  # List: I store required inputs.
        "output_type": "Forecasts, probabilities and model evaluation.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the reinforcement-learning entry.
        "code": "reinforcement_learning",  # Identifier: I define its lookup code.
        "name": "Basic Reinforcement-Learning Trading Bot",  # String: I store the displayed name.
        "category": "machine_learning",  # Category: I assign the machine-learning family.
        "display_order": 6,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Agent learns trading actions from rewards generated "  # String: I begin the original text.
            "by a simulated market environment."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Research sequential trading decisions.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store environment and training settings.
            "episodes": 100,  # Integer: I store the training-episode count.
            "initial_capital": 10000,  # Integer: I store the starting-capital setting.
            "transaction_cost": 0.001,  # Float: I store the transaction-cost setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["open_price", "high_price", "low_price", "close_price", "volume"],  # List: I preserve all five required inputs.
        "output_type": "Actions, rewards, equity curve and PnL.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.

    # --------------------------------------------------------
    # 2.4 FACTOR MODELS
    # --------------------------------------------------------
    {  # Dictionary: I begin the three-factor entry.
        "code": "fama_french_3",  # Identifier: I define its lookup code.
        "name": "Fama-French 3-Factor Model",  # String: I store the displayed name.
        "category": "factor",  # Category: I assign the factor family.
        "display_order": 1,  # Integer: I set its position.
        "description": "Explains returns using market, size and value factors.",  # String: I preserve the description.
        "purpose": "Estimate factor exposures and abnormal return.",  # String: I store the purpose.
        "default_parameters": {},  # Empty dictionary: I supply no predefined parameters.
        "data_requirements": ["asset_returns", "market_factor", "SMB", "HML", "risk_free_rate"],  # List: I preserve the required series names and their order.
        "output_type": "Alpha, factor betas, t-statistics and R-squared.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the five-factor entry.
        "code": "fama_french_5",  # Identifier: I define its lookup code.
        "name": "Fama-French 5-Factor Model",  # String: I store the displayed name.
        "category": "factor",  # Category: I assign the factor family.
        "display_order": 2,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Extends the three-factor model with profitability "  # String: I begin the original text.
            "and investment factors."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Estimate broader systematic factor exposures.",  # String: I store the purpose.
        "default_parameters": {},  # Empty dictionary: I supply no predefined parameters.
        "data_requirements": ["asset_returns", "market_factor", "SMB", "HML", "RMW", "CMA", "risk_free_rate"],  # List: I preserve the required series.
        "output_type": "Alpha, five factor betas and regression diagnostics.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Carhart entry.
        "code": "carhart_4",  # Identifier: I define its lookup code.
        "name": "Carhart 4-Factor Model",  # String: I store the displayed name.
        "category": "factor",  # Category: I assign the factor family.
        "display_order": 3,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Adds a momentum factor to the Fama-French "  # String: I begin the original text.
            "three-factor framework."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Measure return exposure to market, size, value and momentum.",  # String: I store the purpose.
        "default_parameters": {},  # Empty dictionary: I supply no predefined parameters.
        "data_requirements": ["asset_returns", "market_factor", "SMB", "HML", "momentum_factor", "risk_free_rate"],  # List: I preserve required inputs.
        "output_type": "Alpha, four factor betas and regression diagnostics.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the momentum-factor entry.
        "code": "momentum_factor",  # Identifier: I define its lookup code.
        "name": "Momentum Factor",  # String: I store the displayed name.
        "category": "factor",  # Category: I assign the factor family.
        "display_order": 4,  # Integer: I set its position.
        "description": "Ranks securities according to recent relative performance.",  # String: I preserve the description.
        "purpose": "Test cross-sectional or time-series momentum exposure.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store the lookback setting.
            "lookback_months": 12,  # Integer: I store twelve months.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["multiple_asset_returns"],  # List: I identify the required inputs.
        "output_type": "Momentum scores, rankings and factor returns.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the quality-factor entry.
        "code": "quality_factor",  # Identifier: I define its lookup code.
        "name": "Quality Factor",  # String: I store the displayed name.
        "category": "factor",  # Category: I assign the factor family.
        "display_order": 5,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Ranks companies using profitability, balance-sheet "  # String: I begin the original text.
            "or earnings-quality characteristics."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Construct and analyse quality-factor exposure.",  # String: I store the purpose.
        "default_parameters": {},  # Empty dictionary: I supply no predefined parameters.
        "data_requirements": ["fundamental_data", "asset_returns"],  # List: I identify required inputs.
        "output_type": "Quality scores, factor exposure and performance.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the low-volatility entry.
        "code": "low_volatility_factor",  # Identifier: I define its lookup code.
        "name": "Low-Volatility Factor",  # String: I store the displayed name.
        "category": "factor",  # Category: I assign the factor family.
        "display_order": 6,  # Integer: I set its position.
        "description": "Ranks assets according to realised volatility.",  # String: I preserve the description.
        "purpose": "Investigate defensive low-volatility portfolio behaviour.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store the lookback setting.
            "lookback_days": 60,  # Integer: I store the lookback length.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["multiple_asset_returns"],  # List: I identify required inputs.
        "output_type": "Volatility ranking, portfolio return and risk.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.

    # --------------------------------------------------------
    # 2.5 PORTFOLIO OPTIMISATION
    # --------------------------------------------------------
    {  # Dictionary: I begin the mean-variance entry.
        "code": "markowitz_mean_variance",  # Identifier: I define its lookup code.
        "name": "Markowitz Mean-Variance",  # String: I store the displayed name.
        "category": "portfolio",  # Category: I assign the portfolio family.
        "display_order": 1,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Optimises portfolio weights using expected returns "  # String: I begin the original text.
            "and the covariance matrix."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Find portfolios balancing expected return and risk.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store the rate setting.
            "risk_free_rate": 0.02,  # Float: I store the risk-free-rate setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["multiple_asset_returns"],  # List: I identify required inputs.
        "output_type": "Asset weights, expected return, volatility and Sharpe ratio.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the efficient-frontier entry.
        "code": "efficient_frontier",  # Identifier: I define its lookup code.
        "name": "Efficient Frontier",  # String: I store the displayed name.
        "category": "portfolio",  # Category: I assign the portfolio family.
        "display_order": 2,  # Integer: I set its position.
        "description": "Calculates the set of mean-variance efficient portfolios.",  # String: I preserve the description.
        "purpose": "Visualise optimal risk-return combinations.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store the frontier setting.
            "frontier_points": 50,  # Integer: I store the requested point count.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["multiple_asset_returns"],  # List: I identify required inputs.
        "output_type": "Efficient-frontier curve and portfolio weights.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Black-Litterman entry.
        "code": "black_litterman",  # Identifier: I define its lookup code.
        "name": "Black-Litterman",  # String: I store the displayed name.
        "category": "portfolio",  # Category: I assign the portfolio family.
        "display_order": 3,  # Integer: I set its position.
        "description": "Combines market equilibrium returns with investor views.",  # String: I preserve the description.
        "purpose": "Generate more stable portfolio allocations.",  # String: I store the intended purpose.
        "default_parameters": {  # Dictionary: I store the model setting.
            "tau": 0.05,  # Float: I preserve the tau parameter.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["multiple_asset_returns", "market_weights", "investor_views"],  # List: I preserve required inputs.
        "output_type": "Posterior expected returns and portfolio weights.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the risk-parity entry.
        "code": "risk_parity",  # Identifier: I define its lookup code.
        "name": "Risk Parity",  # String: I store the displayed name.
        "category": "portfolio",  # Category: I assign the portfolio family.
        "display_order": 4,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Allocates capital so assets contribute more equally "  # String: I begin the original text.
            "to overall portfolio risk."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Construct risk-balanced portfolios.",  # String: I store the purpose.
        "default_parameters": {},  # Empty dictionary: I supply no predefined parameters.
        "data_requirements": ["multiple_asset_returns"],  # List: I identify required inputs.
        "output_type": "Risk-balanced weights and risk contributions.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.

    # --------------------------------------------------------
    # 2.6 DERIVATIVES PRICING
    # --------------------------------------------------------
    {  # Dictionary: I begin the Black-Scholes entry.
        "code": "black_scholes",  # Identifier: I define its lookup code.
        "name": "Black-Scholes",  # String: I store the displayed name.
        "category": "derivatives",  # Category: I assign the derivatives family.
        "display_order": 1,  # Integer: I set its position.
        "description": "Closed-form option-pricing model for European options.",  # String: I preserve the description.
        "purpose": "Calculate theoretical option prices and Greeks.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store pricing settings.
            "option_type": "call",  # String value: I select the call-option setting.
            "strike": 100,  # Integer: I store the strike-price setting.
            "time_to_maturity": 1.0,  # Float: I store the maturity setting.
            "risk_free_rate": 0.03,  # Float: I store the rate setting.
            "volatility": 0.20,  # Float: I store the volatility setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["spot_price"],  # List: I identify the required input.
        "output_type": "Fair value and Greeks.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the binomial-tree entry.
        "code": "binomial_tree",  # Identifier: I define its lookup code.
        "name": "Binomial Option-Pricing Tree",  # String: I store the displayed name.
        "category": "derivatives",  # Category: I assign the derivatives family.
        "display_order": 2,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Discrete-time option-pricing model based on "  # String: I begin the original text.
            "up/down price movements."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Price European and potentially American options.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store pricing settings.
            "steps": 100,  # Integer: I store the tree-step count.
            "strike": 100,  # Integer: I store the strike setting.
            "time_to_maturity": 1.0,  # Float: I store the maturity setting.
            "risk_free_rate": 0.03,  # Float: I store the rate setting.
            "volatility": 0.20,  # Float: I store the volatility setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["spot_price"],  # List: I identify the input.
        "output_type": "Option fair value and pricing tree.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Heston-pricing entry.
        "code": "heston_option_pricing",  # Identifier: I distinguish this entry from Heston path simulation.
        "name": "Heston Option Pricing",  # String: I store the displayed name.
        "category": "derivatives",  # Category: I assign the derivatives family.
        "display_order": 3,  # Integer: I set its position.
        "description": "Option-pricing framework based on stochastic volatility.",  # String: I preserve the description.
        "purpose": "Price options where volatility is allowed to vary.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store pricing settings.
            "strike": 100,  # Integer: I store the strike setting.
            "time_to_maturity": 1.0,  # Float: I store the maturity setting.
            "risk_free_rate": 0.03,  # Float: I store the rate setting.
            "initial_variance": 0.04,  # Float: I store the initial variance.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["spot_price"],  # List: I identify the input.
        "output_type": "Option fair value under stochastic volatility.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Monte Carlo option-pricing entry.
        "code": "monte_carlo_option_pricing",  # Identifier: I define its lookup code.
        "name": "Monte Carlo Option Pricing",  # String: I store the displayed name.
        "category": "derivatives",  # Category: I assign the derivatives family.
        "display_order": 4,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Values derivatives by averaging discounted payoffs "  # String: I begin the original text.
            "across simulated price paths."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Price derivatives using simulation.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store simulation and pricing settings.
            "simulations": 10000,  # Integer: I store the simulation count.
            "strike": 100,  # Integer: I store the strike setting.
            "time_to_maturity": 1.0,  # Float: I store the maturity setting.
            "risk_free_rate": 0.03,  # Float: I store the rate setting.
            "volatility": 0.20,  # Float: I store the volatility setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["spot_price"],  # List: I identify the required input.
        "output_type": "Estimated option value and payoff distribution.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.

    # --------------------------------------------------------
    # 2.7 SIMULATION AND MONTE CARLO
    # --------------------------------------------------------
    {  # Dictionary: I begin the Monte Carlo GBM entry.
        "code": "monte_carlo_gbm",  # Identifier: I define its lookup code.
        "name": "Monte Carlo GBM",  # String: I store the displayed name.
        "category": "monte_carlo",  # Category: I assign the simulation family.
        "display_order": 1,  # Integer: I set its position.
        "description": "Runs many geometric Brownian-motion simulations.",  # String: I preserve the description.
        "purpose": "Estimate future asset-price distributions.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store simulation settings.
            "simulations": 5000,  # Integer: I store the simulation count.
            "horizon_days": 252,  # Integer: I store the horizon.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the input.
        "output_type": "Price-path distribution and terminal percentiles.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Monte Carlo Heston entry.
        "code": "monte_carlo_heston",  # Identifier: I define its lookup code.
        "name": "Monte Carlo Heston",  # String: I store the displayed name.
        "category": "monte_carlo",  # Category: I assign the simulation family.
        "display_order": 2,  # Integer: I set its position.
        "description": "Monte Carlo simulation with stochastic volatility.",  # String: I preserve the description.
        "purpose": "Model price uncertainty and changing volatility.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store simulation settings.
            "simulations": 5000,  # Integer: I store the simulation count.
            "horizon_days": 252,  # Integer: I store the horizon.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the input.
        "output_type": "Price and volatility distributions.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the Monte Carlo jump-diffusion entry.
        "code": "monte_carlo_jump_diffusion",  # Identifier: I define its lookup code.
        "name": "Monte Carlo Jump-Diffusion",  # String: I store the displayed name.
        "category": "monte_carlo",  # Category: I assign the simulation family.
        "display_order": 3,  # Integer: I set its position.
        "description": "Monte Carlo simulation including discontinuous price jumps.",  # String: I preserve the description.
        "purpose": "Evaluate outcomes containing crash or jump risk.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store simulation settings.
            "simulations": 5000,  # Integer: I store the simulation count.
            "horizon_days": 252,  # Integer: I store the horizon.
            "jump_intensity": 0.10,  # Float: I store the jump-intensity setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["close_price"],  # List: I identify the input.
        "output_type": "Jump-risk price distribution.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the tail-risk entry.
        "code": "monte_carlo_var_es",  # Identifier: I define its lookup code.
        "name": "Monte Carlo VaR / Expected Shortfall",  # String: I store the displayed name.
        "category": "monte_carlo",  # Category: I assign the simulation family.
        "display_order": 4,  # Integer: I set its position.
        "description": "Simulates portfolio outcomes to estimate tail-loss metrics.",  # String: I preserve the description.
        "purpose": "Measure Value at Risk and Expected Shortfall.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store risk-simulation settings.
            "simulations": 10000,  # Integer: I store the simulation count.
            "confidence_level": 0.95,  # Float: I store the confidence-level setting.
            "horizon_days": 1,  # Integer: I store the horizon.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["returns"],  # List: I identify the required return series.
        "output_type": "VaR, Expected Shortfall and loss distribution.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the equity-bootstrap entry.
        "code": "monte_carlo_equity_bootstrap",  # Identifier: I define its lookup code.
        "name": "Monte Carlo Equity Curve / Bootstrapping",  # String: I store the displayed name.
        "category": "monte_carlo",  # Category: I assign the simulation family.
        "display_order": 5,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Resamples historical strategy returns to generate "  # String: I begin the original text.
            "alternative equity-curve paths."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Assess strategy robustness and sequencing risk.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store resampling settings.
            "simulations": 5000,  # Integer: I store the simulation count.
            "block_size": 5,  # Integer: I store the resampling-block setting.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["strategy_returns"],  # List: I identify the required strategy return series.
        "output_type": "Equity-curve distribution, drawdown and terminal wealth.",  # String: I describe expected output.
    },  # Closing brace: I finish the entry.
    {  # Dictionary: I begin the portfolio-scenario entry.
        "code": "monte_carlo_portfolio",  # Identifier: I define its lookup code.
        "name": "Monte Carlo Portfolio Scenarios",  # String: I store the displayed name.
        "category": "monte_carlo",  # Category: I assign the simulation family.
        "display_order": 6,  # Integer: I set its position.
        "description": (  # Grouping: I begin the description.
            "Simulates correlated portfolio asset returns under "  # String: I begin the original text.
            "many possible scenarios."  # Adjacent string: I finish the text.
        ),  # Closing parenthesis: I finish the description.
        "purpose": "Assess portfolio uncertainty and downside risk.",  # String: I store the purpose.
        "default_parameters": {  # Dictionary: I store simulation settings.
            "simulations": 5000,  # Integer: I store the simulation count.
            "horizon_days": 252,  # Integer: I store the horizon.
        },  # Closing brace: I finish parameters.
        "data_requirements": ["multiple_asset_returns", "portfolio_weights"],  # List: I preserve both required inputs.
        "output_type": "Portfolio return distribution, VaR and scenario outcomes.",  # String: I describe expected output.
    },  # Closing brace: I finish the final catalogue entry.
]  # Closing bracket: I finish the complete library list.

# ============================================================
# 3. DJANGO MANAGEMENT COMMAND
# ============================================================
class Command(BaseCommand):  # Class inheritance: I define the Command class Django discovers for this filename.
    help = (  # Class attribute: I provide the command's help description.
        "Create or update the complete "  # String: I begin the original help text.
        "MarketPulse strategy/model library."  # Adjacent string: I finish the help text.
    )  # Closing parenthesis: I finish the help attribute.

    # --------------------------------------------------------
    # 3.1 COMMAND ENTRY POINT AND COUNTERS
    # --------------------------------------------------------
    def handle(  # Method definition: Django calls this method when the command runs.
        self,  # Instance parameter: I access this command object's tools.
        *args,  # Variable positional arguments: I accept extra positional inputs without using them here.
        **options,  # Variable keyword arguments: I accept Django's command options without using them here.
    ):  # Signature boundary: I begin the command's execution body.
        created_count = 0  # Integer assignment: I initialise the new-record counter.
        updated_count = 0  # Integer assignment: I initialise the existing-record counter.

        # ----------------------------------------------------
        # 3.2 PREPARE EACH ENTRY'S UPDATE VALUES
        # ----------------------------------------------------
        for item in LIBRARY_ITEMS:  # Iteration: I process every catalogue dictionary in order.
            code = item["code"]  # Dictionary indexing: I read the unique lookup code.
            defaults = {  # Dictionary comprehension: I build the fields to create or update.
                key: value  # Key-value expression: I retain each selected metadata pair.
                for key, value in item.items()  # Iteration and tuple unpacking: I inspect the dictionary's entries.
                if key != "code"  # Filter condition: I exclude the code because it is supplied separately as the lookup.
            }  # Closing brace: I finish the defaults dictionary.

            # ------------------------------------------------
            # 3.3 CREATE OR UPDATE THE DATABASE RECORD
            # ------------------------------------------------
            _, created = (  # Tuple unpacking: I ignore the returned object by convention and keep the created Boolean.
                StrategyLibraryItem.objects  # Model manager: I access Django's database operations.
                .update_or_create(  # ORM method: I update the matching record or create it if absent.
                    code=code,  # Keyword argument: I match the record using its code.
                    defaults=defaults,  # Keyword argument: I supply the metadata fields to write.
                )  # Closing call: I finish the database operation.
            )  # Closing parenthesis: I finish unpacking the operation's result.
            if created:  # Boolean condition: I check whether a new record was created.
                created_count += 1  # Augmented assignment: I increase the new-record counter.
            else:  # Alternative branch: I handle an existing record.
                updated_count += 1  # Augmented assignment: I count the existing record, even if its supplied values were unchanged.

        # ----------------------------------------------------
        # 3.4 DISPLAY THE TERMINAL SUMMARY
        # ----------------------------------------------------
        self.stdout.write(  # Method call: I write output through Django's command output interface.
            self.style.SUCCESS(  # Styling method: I apply Django's success-message styling where supported.
                (  # Grouping parentheses: I combine the summary strings.
                    "MarketPulse strategy library complete. "  # String: I announce completion.
                    f"Created: {created_count}. "  # Formatted string: I insert the new-record count.
                    f"Updated: {updated_count}. "  # Formatted string: I insert the existing-record count.
                    f"Total: {len(LIBRARY_ITEMS)}."  # Function call and interpolation: I display the number of entries in this file.
                )  # Closing parenthesis: I finish the summary text.
            )  # Closing call: I finish success styling.
        )  # Closing call: I finish writing the terminal message.