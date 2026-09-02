"""
============================================================
MARKETPULSE - DATA MANAGEMENT SERVICES
============================================================

This package contains integrations between MarketPulse and
external market-data providers.

Current provider integrations:

1. Alpaca
   - Active US-equity universe
   - Asset search
   - Asset metadata
   - Latest trade
   - Latest quote
   - Bid / ask
   - Daily market snapshot

The purpose of the services package is to keep third-party
API communication separate from:

- Django views
- Forms
- Templates
- JavaScript
- Database models

This gives MarketPulse a cleaner service-layer architecture.
============================================================
"""


# ============================================================
# ALPACA SERVICE EXPORTS
# ============================================================

from .alpaca import (
    AlpacaServiceError,
    get_active_us_equities,
    search_assets,
    get_asset,
    get_stock_snapshot,
)


# ============================================================
# PUBLIC SERVICE INTERFACE
# ============================================================

__all__ = [
    "AlpacaServiceError",
    "get_active_us_equities",
    "search_assets",
    "get_asset",
    "get_stock_snapshot",
]