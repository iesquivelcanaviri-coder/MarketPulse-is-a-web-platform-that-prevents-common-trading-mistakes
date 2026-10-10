"""
MARKETPULSE - MARKET DATA IMPORT SERVICE
Framework: Python normalization helpers, Django ORM and the Alpaca service layer.
Flow: caller → Alpaca service → normalized OHLCV → core.MarketData → analytical features.
External HTTP communication and credentials remain in services/alpaca.py.
This module obtains and stores data; it does not run the Market Regime classifier.
"""
# ============================================================
# 1. PYTHON IMPORTS
# ============================================================
from datetime import date, datetime, timedelta  # I import date types and durations for date calculations.
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP  # I import decimal arithmetic, its exception and the rounding rule.
# ============================================================
# 2. DJANGO IMPORTS
# ============================================================
from django.db import transaction  # I import database transaction management.
from django.db.models import Count, Max, Min  # I import database aggregation functions.
from django.utils import timezone  # I import Django's timezone utilities.
from django.utils.dateparse import parse_date, parse_datetime  # I import helpers for parsing date and datetime strings.
# ============================================================
# 3. MODEL AND SERVICE IMPORTS
# ============================================================
from core.models import MarketData  # I import the model that stores historical observations.
from data_management.services.alpaca import (  # I import the existing external-provider service.
    AlpacaServiceError,  # I import the exception raised for service failures.
    get_historical_bars,  # I import the function that requests historical bars.
)  # I finish the service imports.
# ============================================================
# 4. CONSTANTS
# ============================================================
MARKET_CONDITION_MINIMUM_OBSERVATIONS = 60  # I set the default minimum observation count.
ANALYSIS_HISTORY_LOOKBACK_DAYS = 365  # I request this many calendar days when more history is needed.
RECENT_REFRESH_LOOKBACK_DAYS = 30  # I normally refresh this recent overlapping period.
MARKET_DATA_STALE_AFTER_DAYS = 7  # I consider stored data stale when its age exceeds seven days.
# ============================================================
# 5. SYMBOL NORMALIZATION
# ============================================================
def _normalise_symbol(symbol):  # I define a helper for standardizing symbols.
    """Return a nonempty, trimmed, uppercase symbol."""
    symbol = str(symbol or "").strip().upper()  # I handle a falsy value, convert to text and normalize it.
    if not symbol:  # I check whether normalization produced an empty string.
        raise ValueError("A market symbol is required.")  # I reject a missing symbol.
    return symbol  # I return the normalized value.
# ============================================================
# 6. DATE NORMALIZATION
# ============================================================
def _normalise_date_value(value, field_name):  # I accept a date value and a label used in errors.
    """Convert date objects, datetime objects or supported strings into a date."""
    if value is None:  # I check for a missing value.
        raise ValueError(f"{field_name} is required.")  # I identify the missing field.
    if isinstance(value, datetime):  # I check datetime before date because datetime is a date subclass.
        return value.date()  # I keep the date component without converting timezones.
    if isinstance(value, date):  # I check whether the value is already a date.
        return value  # I return the existing date.
    string_value = str(value).strip()  # I convert other input to trimmed text.
    parsed_date = parse_date(string_value)  # I first attempt to parse a date string.
    if parsed_date is not None:  # I check whether parsing returned a date.
        return parsed_date  # I return the parsed date.
    parsed_datetime = parse_datetime(string_value)  # I next attempt to parse a datetime string.
    if parsed_datetime is not None:  # I check whether parsing returned a datetime.
        return parsed_datetime.date()  # I return its date component.
    raise ValueError(  # I reject input that neither parser interpreted.
        (  # I begin the original error message.
            f"MarketPulse could not interpret "  # I introduce the parsing failure.
            f"{field_name}: {value}"  # I include the field label and input.
        )  # I finish the combined string.
    )  # I finish raising the error.
# ============================================================
# 7. PRICE DECIMAL CONVERSION
# ============================================================
def _to_price_decimal(value):  # I define a helper for converting and rounding a price.
    """Convert a price to Decimal and round it to four decimal places."""
    if value is None:  # I reject a missing price.
        raise ValueError("Market price cannot be empty.")  # I explain the missing value.
    try:  # I attempt conversion and rounding.
        decimal_value = Decimal(str(value))  # I construct a Decimal from the value's string representation.
        return decimal_value.quantize(  # I round to the exponent specified by the next argument.
            Decimal("0.0001"),  # I specify four decimal places.
            rounding=ROUND_HALF_UP,  # I round to nearest, with ties away from zero.
        )  # I return the rounded Decimal.
    except (InvalidOperation, ValueError, TypeError) as error:  # I catch the listed conversion or rounding errors.
        raise ValueError(f"Invalid market price value: {value}") from error  # I raise a clearer error while preserving its cause.
# ============================================================
# 8. ALTERNATIVE BAR FIELD NAMES
# ============================================================
def _get_bar_value(bar, *possible_keys):  # I accept a bar and any number of candidate keys.
    """Return the first candidate value that is not None."""
    for key in possible_keys:  # I examine candidate keys in their supplied order.
        if key in bar:  # I check whether the dictionary contains this key.
            value = bar.get(key)  # I read its value.
            if value is not None:  # I accept values such as zero, but reject None.
                return value  # I return the first available value.
    return None  # I return None when no candidate supplies a value.
# ============================================================
# 9. MARKET BAR DATE
# ============================================================
def _get_bar_date(bar):  # I define a helper that extracts a bar's date.
    """Read date, timestamp or t and return its date component."""
    value = _get_bar_value(bar, "date", "timestamp", "t")  # I try the supported keys in order.
    if value is None:  # I check whether all supported date values were missing.
        raise ValueError(  # I reject a bar without a date.
            (  # I begin the error message.
                "Historical market bar does "  # I identify the record.
                "not contain a date."  # I explain the missing field.
            )  # I finish the combined string.
        )  # I finish raising the error.
    if isinstance(value, datetime):  # I check whether the value is already a datetime.
        return value.date()  # I return its date component.
    if isinstance(value, date):  # I check whether it is already a date.
        return value  # I return that date unchanged.
    value = str(value).strip()  # I convert other values to trimmed text.
    parsed_datetime = parse_datetime(value)  # I first try datetime parsing for bar timestamps.
    if parsed_datetime is not None:  # I check whether it succeeded.
        return parsed_datetime.date()  # I extract the date without timezone conversion.
    parsed_date = parse_date(value)  # I next try date parsing.
    if parsed_date is not None:  # I check whether it succeeded.
        return parsed_date  # I return the parsed date.
    raise ValueError(  # I reject an unrecognized date value.
        (  # I begin the error message.
            "MarketPulse could not interpret "  # I describe the failure.
            f"historical bar date: {value}"  # I include the unrecognized value.
        )  # I finish the combined string.
    )  # I finish raising the error.
# ============================================================
# 10. NORMALIZE ONE OHLCV BAR
# ============================================================
def _normalise_market_bar(bar):  # I define a helper for preparing one provider record.
    """Return a dictionary containing a date, Decimal OHLC prices and integer volume."""
    if not isinstance(bar, dict):  # I require the input to be a dictionary.
        raise ValueError(  # I reject other input types.
            (  # I begin the original message.
                "Historical market bar must "  # I describe the input requirement.
                "be a dictionary."  # I identify the required type.
            )  # I finish the combined string.
        )  # I finish raising the error.
    # --------------------------------------------------------
    # 10.1 READ OHLCV VALUES
    # --------------------------------------------------------
    open_price = _get_bar_value(bar, "open", "open_price", "o")  # I read the opening price using supported names.
    high_price = _get_bar_value(bar, "high", "high_price", "h")  # I read the high price.
    low_price = _get_bar_value(bar, "low", "low_price", "l")  # I read the low price.
    close_price = _get_bar_value(bar, "close", "close_price", "c")  # I read the closing price.
    volume = _get_bar_value(bar, "volume", "v")  # I read the volume.
    # --------------------------------------------------------
    # 10.2 REQUIRE ALL FOUR PRICES
    # --------------------------------------------------------
    if any(  # I check whether at least one required value is missing.
        value is None  # I test each value specifically against None.
        for value in [open_price, high_price, low_price, close_price]  # I iterate through the four prices.
    ):  # I begin the missing-price branch.
        raise ValueError(  # I reject incomplete OHLC data.
            (  # I begin the message.
                "Historical Alpaca bar is missing "  # I identify the problem.
                "one or more OHLC values."  # I identify the missing field group.
            )  # I finish the combined string.
        )  # I finish raising the error.
    # --------------------------------------------------------
    # 10.3 CONVERT AND VALIDATE PRICES
    # --------------------------------------------------------
    open_decimal = _to_price_decimal(open_price)  # I convert and round the opening price.
    high_decimal = _to_price_decimal(high_price)  # I convert and round the high price.
    low_decimal = _to_price_decimal(low_price)  # I convert and round the low price.
    close_decimal = _to_price_decimal(close_price)  # I convert and round the closing price.
    if any(  # I check whether any rounded price is nonpositive.
        price <= 0  # I test each price against zero.
        for price in [open_decimal, high_decimal, low_decimal, close_decimal]  # I iterate through the converted prices.
    ):  # I begin the nonpositive-price branch.
        raise ValueError(  # I reject nonpositive prices.
            (  # I begin the message.
                "Historical market prices "  # I identify the values.
                "must be greater than zero."  # I explain the requirement.
            )  # I finish the combined string.
        )  # I finish raising the error.
    if high_decimal < low_decimal:  # I check that the high is not below the low.
        raise ValueError(  # I reject an inconsistent range.
            (  # I begin the message.
                "Historical market bar contains "  # I identify the record.
                "a high price below its low price."  # I explain the inconsistency.
            )  # I finish the combined string.
        )  # I finish raising the error.
    # --------------------------------------------------------
    # 10.4 NORMALIZE VOLUME
    # --------------------------------------------------------
    try:  # I attempt integer conversion.
        volume = int(volume or 0)  # I use zero for a falsy value and convert the result to an integer.
    except (ValueError, TypeError, OverflowError):  # I catch the listed volume conversion errors.
        volume = 0  # I substitute zero when conversion fails.
    volume = max(0, volume)  # I prevent negative volume from being returned.
    return {  # I return the normalized record.
        "date": _get_bar_date(bar),  # I extract and normalize the date.
        "open_price": open_decimal,  # I provide the opening Decimal.
        "high_price": high_decimal,  # I provide the high Decimal.
        "low_price": low_decimal,  # I provide the low Decimal.
        "close_price": close_decimal,  # I provide the closing Decimal.
        "volume": volume,  # I provide nonnegative integer volume.
    }  # I finish the dictionary.
# ============================================================
# 11. STORED DATASET STATUS
# ============================================================
def get_stored_market_data_status(symbol):  # I define a public helper for summarizing one dataset.
    """Return the total stored row count and earliest/latest dates for a symbol."""
    symbol = _normalise_symbol(symbol)  # I validate and normalize the symbol.
    summary = MarketData.objects.filter(symbol=symbol).aggregate(  # I aggregate all stored rows for this symbol.
        observation_count=Count("pk"),  # I count primary keys.
        earliest_date=Min("date"),  # I find the earliest date.
        latest_date=Max("date"),  # I find the latest date.
    )  # I finish the aggregation.
    return {  # I return a structured summary.
        "symbol": symbol,  # I include the normalized symbol.
        "observation_count": summary["observation_count"] or 0,  # I provide the count with a zero fallback.
        "earliest_date": summary["earliest_date"],  # I provide the earliest date or None.
        "latest_date": summary["latest_date"],  # I provide the latest date or None.
    }  # I finish the summary dictionary.
# ============================================================
# 12. IMPORT AND PERSIST ALPACA DATA
# ============================================================
def import_alpaca_market_data(symbol, start_date, end_date, timeframe="1Day"):  # I accept a symbol, date range and optional timeframe.
    """Fetch bars, normalize valid records and persist them by symbol and date."""
    symbol = _normalise_symbol(symbol)  # I normalize the market identifier.
    start_date = _normalise_date_value(start_date, "start date")  # I normalize the start date.
    end_date = _normalise_date_value(end_date, "end date")  # I normalize the end date.
    if start_date >= end_date:  # I require the start date to precede the end date.
        raise ValueError(  # I reject an invalid range.
            (  # I begin the message.
                "The start date must be "  # I identify the first boundary.
                "earlier than the end date."  # I explain the required ordering.
            )  # I finish the combined string.
        )  # I finish raising the error.
    # --------------------------------------------------------
    # 12.1 FETCH THROUGH THE SERVICE LAYER
    # --------------------------------------------------------
    try:  # I handle the service's specific exception.
        bars = get_historical_bars(  # I request historical records through the existing service.
            symbol=symbol,  # I supply the normalized symbol.
            start_date=start_date,  # I supply the start date.
            end_date=end_date,  # I supply the end date.
            timeframe=timeframe,  # I pass through the requested timeframe.
        )  # I finish the service call.
    except AlpacaServiceError as error:  # I catch a service failure.
        raise ValueError(  # I translate it into a ValueError for callers.
            (  # I begin the message.
                f"Alpaca could not return historical "  # I describe the failed operation.
                f"market data for {symbol}: {error}"  # I include the symbol and service error.
            )  # I finish the combined string.
        ) from error  # I preserve the original exception as the cause.
    if not bars:  # I check whether the service returned a falsy result.
        raise ValueError(  # I reject an empty result.
            (  # I begin the message.
                "No historical Alpaca market data "  # I describe the missing data.
                f"was returned for {symbol}."  # I identify the requested market.
            )  # I finish the combined string.
        )  # I finish raising the error.
    # --------------------------------------------------------
    # 12.2 NORMALIZE BEFORE WRITING TO THE DATABASE
    # --------------------------------------------------------
    normalised_bars = []  # I create a list for accepted records.
    for bar in bars:  # I examine each provider record.
        try:  # I attempt to normalize this record.
            normalised_bar = _normalise_market_bar(bar)  # I validate and convert its fields.
        except ValueError:  # I handle records rejected with ValueError.
            continue  # I skip this record and move to the next one.
        if (  # I check whether the date falls outside the requested period.
            normalised_bar["date"] < start_date  # I reject dates before the start.
            or normalised_bar["date"] > end_date  # I reject dates after the end.
        ):  # I begin the out-of-range branch.
            continue  # I skip this record.
        normalised_bars.append(normalised_bar)  # I retain the accepted record.
    if not normalised_bars:  # I check whether any accepted record remains.
        raise ValueError(  # I reject an import with no valid observations.
            (  # I begin the message.
                f"Alpaca returned data for {symbol}, "  # I identify the returned dataset.
                "but MarketPulse could not process any "  # I describe the normalization failure.
                "valid historical observations."  # I finish the explanation.
            )  # I finish the combined string.
        )  # I finish raising the error.
    # --------------------------------------------------------
    # 12.3 STORE ACCEPTED RECORDS IN ONE TRANSACTION
    # --------------------------------------------------------
    count = 0  # I initialize the number of processed records.
    with transaction.atomic():  # I group these writes into a database transaction.
        for normalised_bar in normalised_bars:  # I process every accepted record.
            MarketData.objects.update_or_create(  # I update a matching row or create one.
                symbol=symbol,  # I match the market symbol.
                date=normalised_bar["date"],  # I match the observation date.
                defaults={  # I supply the values to create or update.
                    "open_price": normalised_bar["open_price"],  # I store the normalized opening price.
                    "high_price": normalised_bar["high_price"],  # I store the normalized high price.
                    "low_price": normalised_bar["low_price"],  # I store the normalized low price.
                    "close_price": normalised_bar["close_price"],  # I store the normalized closing price.
                    "volume": normalised_bar["volume"],  # I store the normalized volume.
                },  # I finish the defaults dictionary.
            )  # I finish the update-or-create call.
            count += 1  # I count this processed bar, whether it created or updated a row.
    return count  # I return the processed-bar count after the transaction succeeds.
# ============================================================
# 13. PROVIDER-NEUTRAL IMPORT ENTRY POINT
# ============================================================
def import_market_data(symbol, start_date, end_date, timeframe="1Day"):  # I expose an importer without a provider-specific name.
    """Delegate historical imports to the current Alpaca implementation."""
    return import_alpaca_market_data(  # I delegate the work and return its processed count.
        symbol=symbol,  # I pass through the symbol.
        start_date=start_date,  # I pass through the start date.
        end_date=end_date,  # I pass through the end date.
        timeframe=timeframe,  # I pass through the timeframe.
    )  # I finish the delegated call.
# ============================================================
# 14. ENSURE DATA FOR ANALYSIS
# ============================================================
def ensure_market_data_for_analysis(  # I define a helper that can extend or refresh a dataset.
    symbol,  # I receive the market symbol.
    minimum_observations=MARKET_CONDITION_MINIMUM_OBSERVATIONS,  # I default to the configured minimum.
    force_refresh=False,  # I allow callers to explicitly request a refresh.
):  # I finish the function signature.
    """Check total stored observations and freshness, refresh if needed, and return status."""
    symbol = _normalise_symbol(symbol)  # I validate and normalize the symbol.
    # --------------------------------------------------------
    # 14.1 NORMALIZE THE MINIMUM COUNT
    # --------------------------------------------------------
    try:  # I attempt to interpret the supplied minimum as an integer.
        minimum_observations = int(minimum_observations)  # I convert the requirement.
    except (TypeError, ValueError):  # I catch the listed conversion failures.
        minimum_observations = MARKET_CONDITION_MINIMUM_OBSERVATIONS  # I fall back to the default.
    minimum_observations = max(2, minimum_observations)  # I enforce a minimum requirement of at least two.
    # --------------------------------------------------------
    # 14.2 CHECK EXISTING SIZE AND FRESHNESS
    # --------------------------------------------------------
    before = get_stored_market_data_status(symbol)  # I summarize the dataset before any refresh.
    observation_count_before = before["observation_count"]  # I read its total row count.
    latest_stored_date = before["latest_date"]  # I read its latest date.
    needs_more_history = observation_count_before < minimum_observations  # I compare the total count with the requirement.
    today = timezone.localdate()  # I obtain today's date in Django's active timezone.
    if latest_stored_date is None:  # I handle a dataset with no latest date.
        data_is_stale = True  # I treat missing data as stale.
    else:  # I calculate the age of the existing dataset.
        age_in_days = (today - latest_stored_date).days  # I calculate its age in calendar days.
        data_is_stale = age_in_days > MARKET_DATA_STALE_AFTER_DAYS  # I mark it stale only when the age exceeds seven days.
    should_refresh = needs_more_history or data_is_stale or force_refresh  # I refresh when any of these conditions is truthy.
    records_processed = 0  # I initialize the count for a possible import.
    # --------------------------------------------------------
    # 14.3 CHOOSE THE REFRESH PERIOD
    # --------------------------------------------------------
    if should_refresh:  # I fetch data only when a refresh is needed or requested.
        if needs_more_history:  # I choose a longer period for an undersized dataset.
            refresh_start_date = today - timedelta(  # I calculate the longer start date.
                days=ANALYSIS_HISTORY_LOOKBACK_DAYS  # I subtract 365 calendar days.
            )  # I finish the calculation.
        else:  # I choose a recent overlap when enough total rows already exist.
            refresh_start_date = today - timedelta(  # I calculate the normal refresh start.
                days=RECENT_REFRESH_LOOKBACK_DAYS  # I subtract 30 calendar days.
            )  # I finish the calculation.
            if (  # I check whether a larger missing period needs recovery.
                latest_stored_date is not None  # I require a latest stored date.
                and latest_stored_date < refresh_start_date  # I check whether it predates the normal refresh window.
            ):  # I begin the extended-gap branch.
                refresh_start_date = latest_stored_date - timedelta(days=7)  # I start seven days before the latest stored observation.
        if refresh_start_date >= today:  # I ensure the start precedes the end.
            refresh_start_date = today - timedelta(days=1)  # I fall back to a one-day range.
        records_processed = import_market_data(  # I reuse the provider-neutral importer.
            symbol=symbol,  # I supply the selected market.
            start_date=refresh_start_date,  # I supply the chosen start date.
            end_date=today,  # I supply today's date as the end.
            timeframe="1Day",  # I request daily records.
        )  # I store the number of processed records.
    # --------------------------------------------------------
    # 14.4 RECHECK AND RETURN STATUS
    # --------------------------------------------------------
    after = get_stored_market_data_status(symbol)  # I summarize the stored dataset again.
    observation_count = after["observation_count"]  # I read the resulting total count.
    analysis_ready = observation_count >= minimum_observations  # I decide readiness using the total stored count.
    return {  # I return a dictionary explaining the result.
        "symbol": symbol,  # I include the normalized symbol.
        "minimum_observations": minimum_observations,  # I include the effective requirement.
        "observation_count_before": observation_count_before,  # I include the original count.
        "observation_count": observation_count,  # I include the resulting count.
        "earliest_date": after["earliest_date"],  # I include the earliest stored date.
        "latest_date": after["latest_date"],  # I include the latest stored date.
        "refreshed": should_refresh,  # I report the refresh decision after successful completion.
        "records_processed": records_processed,  # I report the number of processed import records.
        "analysis_ready": analysis_ready,  # I report whether the total count meets the requirement.
    }  # I finish the status dictionary.
# ============================================================
# 15. MARKET CONDITION CONVENIENCE WRAPPER
# ============================================================
def prepare_market_condition_data(symbol, force_refresh=False):  # I provide a wrapper using the Market Condition minimum.
    """Prepare historical data without running the analytical classifier."""
    return ensure_market_data_for_analysis(  # I delegate preparation and return its status.
        symbol=symbol,  # I pass the selected symbol.
        minimum_observations=MARKET_CONDITION_MINIMUM_OBSERVATIONS,  # I use the shared minimum of 60.
        force_refresh=force_refresh,  # I pass through the caller's refresh option.
    )  # I finish the delegated call.
# ============================================================
# 16. LEGACY IMPORT COMPATIBILITY
# ============================================================
def import_yahoo_finance_data(symbol, start_date, end_date):  # I preserve an older callable name for existing imports.
    """Use the current Alpaca-backed importer despite this legacy function name."""
    return import_market_data(  # I delegate to the current provider-neutral importer.
        symbol=symbol,  # I pass through the symbol.
        start_date=start_date,  # I pass through the start date.
        end_date=end_date,  # I pass through the end date.
        timeframe="1Day",  # I request daily bars.
    )  # I finish the delegated call.
# ============================================================
# 17. PERIOD-TO-DATE-RANGE HELPER
# ============================================================
def _period_to_dates(period):  # I define a helper for converting supported period labels.
    """Translate a period label into an approximate calendar-day date range."""
    end_date = timezone.localdate()  # I use today's local date as the end.
    period_days = {  # I define the existing period-to-day mapping.
        "5d": 5,  # I map five days to five calendar days.
        "1mo": 31,  # I approximate one month as 31 days.
        "3mo": 93,  # I approximate three months as 93 days.
        "6mo": 186,  # I approximate six months as 186 days.
        "1y": 366,  # I use the existing one-year value of 366 days.
        "2y": 732,  # I use the existing two-year value of 732 days.
        "5y": 1830,  # I use the existing five-year value of 1,830 days.
    }  # I finish the mapping.
    days = period_days.get(period, 31)  # I use 31 days when the period is not in the mapping.
    start_date = end_date - timedelta(days=days)  # I subtract the selected duration.
    return (start_date, end_date)  # I return the two dates as a tuple.
# ============================================================
# 18. GET RECENT DATA WITHOUT PERSISTING IT
# ============================================================
def get_latest_data(symbol, period="1mo"):  # I accept a symbol and an optional period label.
    """Return normalized historical records without writing them to MarketData."""
    try:  # I handle an invalid or empty symbol.
        symbol = _normalise_symbol(symbol)  # I validate and normalize it.
    except ValueError:  # I catch symbol validation failures.
        return []  # I return an empty list.
    start_date, end_date = _period_to_dates(period)  # I unpack the calculated date range.
    # --------------------------------------------------------
    # 18.1 FETCH THROUGH THE ALPACA SERVICE
    # --------------------------------------------------------
    try:  # I handle the service's specific error.
        bars = get_historical_bars(  # I request temporary historical records.
            symbol=symbol,  # I supply the normalized symbol.
            start_date=start_date,  # I supply the calculated start.
            end_date=end_date,  # I supply the calculated end.
            timeframe="1Day",  # I request daily bars.
        )  # I finish the service call.
    except AlpacaServiceError:  # I catch the service failure.
        return []  # I return an empty list rather than propagating this exception.
    if not bars:  # I check whether any bars were returned.
        return []  # I return an empty list when none were supplied.
    # --------------------------------------------------------
    # 18.2 NORMALIZE THE RETURNED RECORDS
    # --------------------------------------------------------
    results = []  # I create the output list.
    for bar in bars:  # I examine each provider record.
        try:  # I attempt normalization.
            normalised_bar = _normalise_market_bar(bar)  # I validate and convert the record.
        except ValueError:  # I catch records rejected with ValueError.
            continue  # I skip that record and continue the loop.
        results.append(  # I append a presentation-friendly dictionary.
            {  # I begin the output record.
                "date": normalised_bar["date"].isoformat(),  # I convert the date to ISO text.
                "open": float(normalised_bar["open_price"]),  # I convert the opening Decimal to a float.
                "high": float(normalised_bar["high_price"]),  # I convert the high Decimal to a float.
                "low": float(normalised_bar["low_price"]),  # I convert the low Decimal to a float.
                "close": float(normalised_bar["close_price"]),  # I convert the closing Decimal to a float.
                "volume": normalised_bar["volume"],  # I retain the integer volume.
            }  # I finish the output record.
        )  # I finish appending it.
    # --------------------------------------------------------
    # 18.3 ORDER THE RESULTS
    # --------------------------------------------------------
    results.sort(key=lambda item: item["date"])  # I sort the list in place by ISO date, oldest first.
    return results  # I return the normalized, ordered records.