"""
MARKETPULSE - DATA MANAGEMENT VIEWS
Framework: Django views, forms, ORM, templates, messages and optional Celery.
Historical flow: Alpaca service → importer → core.MarketData → Data workspace.
Analysis flow: POST → optional Alpaca refresh → observation check → regime analyzer → redirect.
Market Condition results appear inside the Data workspace at #market-condition.
Alpaca is the primary provider; Yahoo Finance remains legacy compatibility only.
The internal analysis_tools app supplies analytics without a separate public Analysis tab.
"""
# ============================================================
# 1. PYTHON IMPORTS
# ============================================================
from datetime import timedelta  # I import a duration type for calculating date windows.
from urllib.parse import urlencode  # I import a helper that safely builds URL query strings.
# ============================================================
# 2. DJANGO IMPORTS
# ============================================================
from django.conf import settings  # I access the project's configured settings.
from django.contrib import messages  # I use Django's temporary user notification system.
from django.contrib.auth.decorators import login_required  # I import the decorator that requires authentication.
from django.shortcuts import redirect, render  # I import helpers for redirects and rendered HTML responses.
from django.urls import reverse  # I convert named routes into URL paths.
from django.utils import timezone  # I use Django's timezone-aware date utilities.
# ============================================================
# 3. PROJECT IMPORTS
# ============================================================
from core.models import MarketData  # I import the model containing stored historical market observations.
from .forms import DataImportForm  # I import the historical import form from this application.
from .models import DataImport, DataSource  # I import models for import jobs and provider configuration.
from .tasks import process_data_import  # I import the task that processes a saved import job.
from .utils import import_market_data  # I import the helper used to fetch and store historical data.
from strategy_builder.library import get_grouped_strategy_library  # I import the helper that groups library models.
from strategy_builder.models import StrategyLibraryItem  # I import the model used to find a selected library item.
from analysis_tools.analyzers import identify_market_regime  # I import the internal Market Regime analyzer.
from analysis_tools.models import MarketRegime  # I import the model containing saved classifications.
# ============================================================
# 4. DATA WORKSPACE CONSTANTS
# ============================================================
MARKET_CONDITION_MINIMUM_OBSERVATIONS = 60  # I require at least 60 rows in the analysis window.
MARKET_CONDITION_ANALYSIS_WINDOW_DAYS = 300  # I count observations within 300 calendar days of the latest stored date.
MARKET_CONDITION_REFRESH_DAYS = 365  # I request a historical refresh covering 365 calendar days.
# ============================================================
# 5. URL AND REDIRECT HELPERS
# ============================================================
def _build_data_workspace_url(symbol="", anchor="market-condition"):  # I define a helper with optional symbol and section arguments.
    """Build the Data workspace URL, optionally including a symbol and section."""
    data_page_url = reverse("data_management:import")  # I resolve the named Data workspace route.
    symbol = str(symbol or "").strip().upper()  # I use an empty fallback, convert to text, trim spaces and uppercase it.
    if symbol:  # I add a query parameter only when the normalized symbol is nonempty.
        query_string = urlencode({"symbol": symbol})  # I encode the symbol dictionary as a query string.
        data_page_url = (  # I replace the URL with one containing the query string.
            f"{data_page_url}"  # I retain the workspace path.
            f"?{query_string}"  # I append the encoded query; adjacent strings join automatically.
        )  # I finish the URL assignment.
    if anchor:  # I add a section fragment when an anchor was supplied.
        data_page_url = (  # I replace the URL with one containing the fragment.
            f"{data_page_url}"  # I retain the path and any query string.
            f"#{anchor}"  # I append the browser's target section.
        )  # I finish the fragment assignment.
    return data_page_url  # I return the completed URL.
def _redirect_to_data_workspace(symbol="", anchor="market-condition"):  # I define a reusable redirect helper.
    """Redirect to the main Data workspace."""
    return redirect(  # I return a redirect response.
        _build_data_workspace_url(  # I build its destination using the helper above.
            symbol=symbol,  # I pass the selected symbol by keyword.
            anchor=anchor,  # I pass the target section by keyword.
        )  # I finish building the destination.
    )  # I finish the redirect call.
# ============================================================
# 6. MARKET CONDITION DATASET STATUS
# ============================================================
def _get_market_condition_status(symbol):  # I define a helper that checks the selected dataset's row count.
    """Check readiness within a recent window relative to the latest stored observation."""
    symbol = str(symbol or "").strip().upper()  # I normalize the symbol and handle a missing value.
    default_status = {  # I prepare the status returned when no usable dataset is found.
        "ready": False,  # I initially mark the dataset as not ready.
        "total_observations": 0,  # I initially report no stored observations.
        "analysis_observations": 0,  # I initially report no observations inside the analysis window.
        "latest_record": None,  # I initially have no latest model instance.
        "latest_date": None,  # I initially have no latest date.
        "analysis_start_date": None,  # I initially have no window start date.
    }  # I finish the default status dictionary.
    if not symbol:  # I check whether the normalized symbol is empty.
        return default_status  # I exit early without querying the dataset.
    symbol_data = MarketData.objects.filter(symbol=symbol)  # I create a QuerySet for this symbol.
    total_observations = symbol_data.count()  # I count all stored rows for the symbol.
    latest_record = symbol_data.order_by("-date").first()  # I retrieve the newest dated row, or None.
    if latest_record is None:  # I handle a dataset with no matching row.
        default_status["total_observations"] = total_observations  # I retain the total count in the default result.
        return default_status  # I return the not-ready result.
    latest_date = latest_record.date  # I read the newest stored observation's date.
    analysis_start_date = latest_date - timedelta(  # I subtract a duration from that date.
        days=MARKET_CONDITION_ANALYSIS_WINDOW_DAYS  # I use the configured 300-calendar-day window.
    )  # I finish calculating the start date.
    analysis_observations = symbol_data.filter(  # I restrict the QuerySet to the analysis window.
        date__gte=analysis_start_date,  # I include dates greater than or equal to the start.
        date__lte=latest_date,  # I include dates less than or equal to the latest stored date.
    ).count()  # I count the rows inside these inclusive boundaries.
    return {  # I return the calculated status as a dictionary.
        "ready": analysis_observations >= MARKET_CONDITION_MINIMUM_OBSERVATIONS,  # I compare the count with the minimum.
        "total_observations": total_observations,  # I include the total dataset size.
        "analysis_observations": analysis_observations,  # I include the analysis-window count.
        "latest_record": latest_record,  # I include the latest model instance.
        "latest_date": latest_date,  # I include its date.
        "analysis_start_date": analysis_start_date,  # I include the analysis-window start.
    }  # I finish the status dictionary.
# ============================================================
# 7. ALPACA MARKET CONDITION REFRESH
# ============================================================
def _refresh_market_condition_data(symbol):  # I define a helper that requests recent daily history.
    """Reuse the historical importer and return the number of processed records."""
    symbol = str(symbol or "").strip().upper()  # I normalize the supplied symbol.
    if not symbol:  # I reject an empty normalized symbol.
        raise ValueError("A market symbol is required.")  # I raise an exception explaining the missing input.
    end_date = timezone.localdate()  # I obtain today's date in Django's active timezone.
    start_date = end_date - timedelta(  # I calculate the beginning of the refresh period.
        days=MARKET_CONDITION_REFRESH_DAYS  # I subtract the configured 365 days.
    )  # I finish the date calculation.
    return import_market_data(  # I call the importer and return its result.
        symbol=symbol,  # I identify the selected market.
        start_date=start_date,  # I supply the historical start date.
        end_date=end_date,  # I supply the historical end date.
        timeframe="1Day",  # I request daily bars.
    )  # I finish the import call.
# ============================================================
# 8. MAIN DATA WORKSPACE VIEW
# ============================================================
@login_required  # I require the visitor to be logged in before running this view.
def data_import(request):  # I define the view that receives the browser's request.
    """Provide imports, OHLCV data, dataset switching, models, history and Market Condition."""
    # --------------------------------------------------------
    # 8.1 ENSURE ALPACA EXISTS AND DISABLE LEGACY PROVIDER
    # --------------------------------------------------------
    alpaca_source, _created = DataSource.objects.update_or_create(  # I unpack the provider object and whether it was created.
        name="Alpaca",  # I use the provider name to find an existing record.
        defaults={  # I supply values to set when creating or updating it.
            "url": "https://alpaca.markets/",  # I store the provider's website.
            "api_key_required": True,  # I mark this provider as requiring credentials.
            "is_active": True,  # I ensure Alpaca is active.
        },  # I finish the defaults dictionary.
    )  # I finish the update-or-create operation.
    DataSource.objects.filter(name="Yahoo Finance").update(  # I find legacy Yahoo Finance provider records.
        is_active=False  # I deactivate those records.
    )  # I finish the database update.
    # --------------------------------------------------------
    # 8.2 BUILD AND RESTRICT THE IMPORT FORM
    # --------------------------------------------------------
    form = DataImportForm(  # I create the form instance.
        request.POST or None,  # I bind nonempty POST data; otherwise I create an unbound form.
        initial={  # I provide initial form values.
            "source": alpaca_source.pk,  # I initially select the Alpaca provider's primary key.
        },  # I finish the initial values dictionary.
    )  # I finish constructing the form.
    if "source" in form.fields:  # I check that this form includes a source field.
        form.fields["source"].queryset = DataSource.objects.filter(  # I restrict the available source records.
            pk=alpaca_source.pk,  # I allow only the Alpaca provider.
            is_active=True,  # I require that provider to be active.
        )  # I finish the restricted QuerySet.
        form.fields["source"].initial = alpaca_source.pk  # I set the field's initial selection.
    # --------------------------------------------------------
    # 8.3 SAVE A VALID MANUAL IMPORT REQUEST
    # --------------------------------------------------------
    if request.method == "POST" and form.is_valid():  # I proceed only for POST requests with valid form data.
        import_job = form.save(commit=False)  # I create the model instance without saving it yet.
        import_job.user = request.user  # I associate the job with the authenticated user.
        import_job.source = alpaca_source  # I enforce Alpaca as the provider.
        import_job.symbol = import_job.symbol.strip().upper()  # I normalize the job's symbol.
        import_job.save()  # I save the configured job to the database.
        # ----------------------------------------------------
        # 8.4 PROCESS THROUGH CELERY OR DIRECT EXECUTION
        # ----------------------------------------------------
        if getattr(settings, "USE_CELERY", False):  # I read the optional Celery flag, defaulting to False.
            process_data_import.delay(import_job.pk)  # I submit the job ID to Celery for background processing.
            messages.info(  # I add an informational notification.
                request,  # I attach the message to this request.
                (  # I begin the message text.
                    f"{import_job.symbol} historical market "  # I insert the job's symbol.
                    "data import from Alpaca has been submitted."  # I explain that the job was submitted.
                ),  # I finish the combined message.
            )  # I finish the notification call.
        else:  # I use direct processing when Celery is disabled.
            process_data_import(import_job.pk)  # I run the task directly with the saved job ID.
            import_job.refresh_from_db()  # I reload fields that processing may have changed.
            if import_job.status == "completed":  # I check whether processing completed successfully.
                messages.success(  # I add a success notification.
                    request,  # I attach it to this request.
                    (  # I begin the message text.
                        f"{import_job.symbol} imported "  # I insert the imported symbol.
                        "successfully from Alpaca. "  # I describe the successful import.
                        f"{import_job.records_imported} "  # I insert the number of processed records.
                        "historical market observations "  # I describe those records.
                        "were processed."  # I finish the message.
                    ),  # I finish the combined string.
                )  # I finish the success notification.
            else:  # I handle a status other than completed.
                messages.error(  # I add an error notification.
                    request,  # I attach it to this request.
                    (  # I begin the message text.
                        f"{import_job.symbol} Alpaca import "  # I identify the affected symbol.
                        "failed. "  # I report the failure.
                        f"{import_job.error_message}"  # I include the stored explanation.
                    ),  # I finish the combined message.
                )  # I finish the error notification.
        # ----------------------------------------------------
        # 8.5 REDIRECT TO THE IMPORTED SYMBOL
        # ----------------------------------------------------
        data_page_url = reverse("data_management:import")  # I resolve the Data workspace URL.
        query_string = urlencode({"symbol": import_job.symbol})  # I encode the imported symbol as a query parameter.
        return redirect(  # I return a redirect response after handling the valid submission.
            f"{data_page_url}"  # I retain the workspace path.
            f"?{query_string}"  # I append the selected symbol.
        )  # I finish the redirect.
    # --------------------------------------------------------
    # 8.6 CHOOSE THE DISPLAYED SYMBOL
    # --------------------------------------------------------
    selected_symbol = request.GET.get("symbol", "").strip().upper()  # I read and normalize the optional URL symbol.
    if not selected_symbol:  # I try the user's latest completed import when no symbol was supplied.
        latest_import = DataImport.objects.filter(  # I select eligible import jobs.
            user=request.user,  # I restrict them to this user.
            status="completed",  # I require completed imports.
        ).order_by("-created_at").first()  # I retrieve the most recently created matching job.
        if latest_import:  # I check whether a matching import exists.
            selected_symbol = latest_import.symbol.strip().upper()  # I use its normalized symbol.
    if not selected_symbol:  # I try the latest shared market record if a symbol is still missing.
        latest_market_record = MarketData.objects.order_by("-date").first()  # I retrieve the newest market row across symbols.
        if latest_market_record:  # I check whether any market record exists.
            selected_symbol = latest_market_record.symbol.strip().upper()  # I use its normalized symbol.
    # --------------------------------------------------------
    # 8.7 LOAD THE SELECTED HISTORICAL DATASET
    # --------------------------------------------------------
    market_data = MarketData.objects.none()  # I start with an empty QuerySet.
    total_records = 0  # I initialize the total row count.
    earliest_record = None  # I initialize the earliest record placeholder.
    latest_record = None  # I initialize the latest record placeholder.
    if selected_symbol:  # I query historical rows when a symbol is available.
        all_symbol_data = MarketData.objects.filter(symbol=selected_symbol)  # I select all rows for the symbol.
        total_records = all_symbol_data.count()  # I count the full dataset.
        earliest_record = all_symbol_data.order_by("date").first()  # I retrieve the earliest dated row.
        latest_record = all_symbol_data.order_by("-date").first()  # I retrieve the latest dated row.
        market_data = all_symbol_data.order_by("-date")[:250]  # I prepare at most 250 newest rows for display.
    # --------------------------------------------------------
    # 8.8 AVAILABLE SYMBOLS AND PERSONAL IMPORT HISTORY
    # --------------------------------------------------------
    available_symbols = MarketData.objects.order_by("symbol").values_list(  # I order shared market data and select symbol values.
        "symbol",  # I select this field.
        flat=True,  # I request individual values rather than one-item tuples.
    ).distinct()  # I remove duplicate symbols.
    recent_imports = DataImport.objects.filter(  # I select this user's import jobs.
        user=request.user  # I filter by the authenticated user.
    ).select_related("source").order_by("-created_at")[:10]  # I include provider data and limit the newest jobs to ten.
    # --------------------------------------------------------
    # 8.9 MODEL LIBRARY AND SELECTED MODEL
    # --------------------------------------------------------
    strategy_categories = get_grouped_strategy_library()  # I obtain the grouped strategy and model library.
    selected_model_code = request.GET.get("model", "").strip()  # I read and trim the optional model code.
    selected_model = None  # I start without a selected model.
    if selected_model_code:  # I look up a model only when a code was supplied.
        selected_model = StrategyLibraryItem.objects.filter(  # I query the model library.
            code=selected_model_code,  # I match the requested code.
            is_active=True,  # I require the item to be active.
        ).first()  # I retrieve the first match or None.
    dataset_available = bool(selected_symbol and total_records > 0)  # I require both a symbol and stored rows.
    model_selected = selected_model is not None  # I record whether the model lookup found an item.
    # --------------------------------------------------------
    # 8.10 MARKET CONDITION READINESS AND SAVED RESULT
    # --------------------------------------------------------
    market_condition_status = _get_market_condition_status(selected_symbol)  # I calculate dataset readiness.
    market_condition_ready = market_condition_status["ready"]  # I extract the readiness Boolean.
    market_condition_observation_count = market_condition_status["analysis_observations"]  # I extract the window's row count.
    latest_regime = None  # I start without a saved classification.
    if selected_symbol:  # I query classifications when a symbol is available.
        latest_regime = MarketRegime.objects.filter(  # I restrict saved classifications.
            symbol=selected_symbol  # I match the selected market.
        ).order_by("-date", "-created_at").first()  # I retrieve the latest dated result, using creation time to break ties.
    market_condition_is_current = False  # I initially mark the result as not current.
    if latest_regime and latest_record:  # I compare dates only when both records exist.
        market_condition_is_current = latest_regime.date == latest_record.date  # I check whether the result matches the latest stored date.
    # --------------------------------------------------------
    # 8.11 PROVIDER AND FEED LABELS
    # --------------------------------------------------------
    market_data_provider = "Alpaca"  # I set the provider label passed to the template.
    market_data_feed = str(getattr(settings, "ALPACA_DATA_FEED", "iex")).upper()  # I read the configured feed and uppercase its label.
    # --------------------------------------------------------
    # 8.12 TEMPLATE CONTEXT
    # --------------------------------------------------------
    context = {  # I collect the values the template can access.
        # Import form and provider information.
        "form": form,  # I provide the import form, including any validation errors.
        "market_data_provider": market_data_provider,  # I provide the provider label.
        "market_data_feed": market_data_feed,  # I provide the feed label.
        "alpaca_source": alpaca_source,  # I provide the provider model instance.
        # Selected historical dataset.
        "selected_symbol": selected_symbol,  # I provide the selected market symbol.
        "market_data": market_data,  # I provide the limited historical display QuerySet.
        "total_records": total_records,  # I provide the full dataset's row count.
        "earliest_record": earliest_record,  # I provide the oldest observation.
        "latest_record": latest_record,  # I provide the newest observation.
        "available_symbols": available_symbols,  # I provide the dataset-switching choices.
        # Import history and model selection.
        "recent_imports": recent_imports,  # I provide the user's ten newest import jobs.
        "strategy_categories": strategy_categories,  # I provide the grouped library.
        "selected_model": selected_model,  # I provide the selected model or None.
        "model_selected": model_selected,  # I provide the model-selection Boolean.
        "dataset_available": dataset_available,  # I provide the dataset-availability Boolean.
        # Market Condition information.
        "latest_regime": latest_regime,  # I provide the latest saved classification.
        "market_condition_ready": market_condition_ready,  # I provide the observation-count readiness flag.
        "market_condition_is_current": market_condition_is_current,  # I provide the stored-date comparison result.
        "market_condition_minimum_observations": MARKET_CONDITION_MINIMUM_OBSERVATIONS,  # I provide the required minimum.
        "market_condition_observation_count": market_condition_observation_count,  # I provide the analysis-window count.
        "market_condition_latest_data_date": market_condition_status["latest_date"],  # I provide the latest stored date.
        "market_condition_analysis_start_date": market_condition_status["analysis_start_date"],  # I provide the window start date.
    }  # I finish the context dictionary.
    return render(request, "data_management/import.html", context)  # I render the main Data workspace with these values.
# ============================================================
# 9. IMPORT HISTORY VIEW
# ============================================================
@login_required  # I require authentication before showing import history.
def import_history(request):  # I define the history page's request handler.
    """Display the authenticated user's historical import jobs."""
    imports = DataImport.objects.filter(  # I select the relevant import jobs.
        user=request.user  # I restrict history to the authenticated user.
    ).select_related("source").order_by("-created_at")  # I include provider data and order newest jobs first.
    context = {  # I prepare the history template's values.
        "imports": imports,  # I provide the import QuerySet under the current key.
        "jobs": imports,  # I preserve the older template-compatible key.
    }  # I finish the context dictionary.
    return render(request, "data_management/history.html", context)  # I render the user's history page.
# ============================================================
# 10. MARKET CONDITION ANALYSIS ACTION
# ============================================================
@login_required  # I require authentication before running this action.
def market_condition(request):  # I define the request handler for Market Condition analysis.
    """On POST, optionally refresh data, check readiness, run analysis and redirect."""
    # --------------------------------------------------------
    # 10.1 READ THE SYMBOL AND REQUIRE POST
    # --------------------------------------------------------
    selected_symbol = (  # I choose the first truthy symbol value.
        request.POST.get("symbol")  # I first check submitted form data.
        or request.GET.get("symbol")  # I next check the URL query string.
        or ""  # I finally fall back to an empty string.
    )  # I finish selecting the raw symbol.
    selected_symbol = selected_symbol.strip().upper()  # I normalize the selected symbol.
    if request.method != "POST":  # I prevent non-POST requests from running the analysis.
        return _redirect_to_data_workspace(symbol=selected_symbol)  # I return to the workspace instead.
    if not selected_symbol:  # I check whether the required symbol is missing.
        messages.error(  # I add an error notification.
            request,  # I attach the message to this request.
            (  # I begin the message.
                "Please select a market dataset before "  # I explain the missing selection.
                "running Market Condition analysis."  # I identify the requested action.
            ),  # I finish the combined string.
        )  # I finish the notification.
        return _redirect_to_data_workspace()  # I redirect without a selected symbol.
    # --------------------------------------------------------
    # 10.2 ATTEMPT A RECENT ALPACA REFRESH
    # --------------------------------------------------------
    refresh_error = None  # I initially have no refresh error.
    refreshed_records = 0  # I initially have no processed refresh records.
    if getattr(settings, "ALPACA_CONFIGURED", False):  # I attempt the refresh only when the configuration flag is truthy.
        try:  # I allow refresh failures to be handled without immediately stopping analysis.
            refreshed_records = _refresh_market_condition_data(selected_symbol)  # I refresh daily data and retain the processed count.
        except Exception as error:  # I catch an exception raised by the refresh.
            refresh_error = str(error)  # I store its text for later messaging.
    else:  # I handle missing Alpaca configuration.
        refresh_error = "Alpaca credentials are not configured."  # I record the reason no refresh was attempted.
    # --------------------------------------------------------
    # 10.3 RECHECK DATASET READINESS
    # --------------------------------------------------------
    market_condition_status = _get_market_condition_status(selected_symbol)  # I check stored rows after the refresh attempt.
    observation_count = market_condition_status["analysis_observations"]  # I extract the recent-window count.
    if not market_condition_status["ready"]:  # I stop when the minimum row count is not met.
        if refresh_error:  # I include refresh problems when one was recorded.
            messages.error(  # I add the combined readiness and refresh error.
                request,  # I attach it to this request.
                (  # I begin the message text.
                    f"{selected_symbol} currently has "  # I identify the selected symbol.
                    f"{observation_count} usable recent "  # I insert the counted observations.
                    "historical observations. "  # I describe the count.
                    f"At least "  # I introduce the minimum.
                    f"{MARKET_CONDITION_MINIMUM_OBSERVATIONS} "  # I insert the required count.
                    "are required. "  # I explain the requirement.
                    "MarketPulse also could not refresh "  # I report the refresh problem.
                    "enough recent Alpaca data: "  # I introduce its explanation.
                    f"{refresh_error}"  # I insert the recorded error.
                ),  # I finish the combined message.
            )  # I finish the error notification.
        else:  # I report insufficient observations without a refresh error.
            messages.error(  # I add a readiness error notification.
                request,  # I attach it to this request.
                (  # I begin the message.
                    f"{selected_symbol} currently has "  # I identify the selected market.
                    f"{observation_count} usable recent "  # I insert its observation count.
                    "historical observations. "  # I describe those observations.
                    f"At least "  # I introduce the minimum.
                    f"{MARKET_CONDITION_MINIMUM_OBSERVATIONS} "  # I insert the required count.
                    "are required before MarketPulse can "  # I explain the readiness requirement.
                    "calculate the Market Condition."  # I finish the explanation.
                ),  # I finish the combined message.
            )  # I finish the notification.
        return _redirect_to_data_workspace(symbol=selected_symbol)  # I return to the selected dataset without running the analyzer.
    # --------------------------------------------------------
    # 10.4 CONTINUE WITH STORED DATA IF REFRESH FAILED
    # --------------------------------------------------------
    if refresh_error:  # I warn the user when stored data is sufficient but the refresh did not succeed.
        messages.warning(  # I add a warning notification.
            request,  # I attach it to this request.
            (  # I begin the message.
                "MarketPulse could not refresh the latest "  # I explain the unavailable refresh.
                f"Alpaca data for {selected_symbol}. "  # I identify the affected symbol.
                "The Market Condition will therefore be "  # I explain how analysis will continue.
                "calculated from the sufficient historical "  # I describe the available dataset.
                "data already stored in PostgreSQL."  # I finish the original message.
            ),  # I finish the combined string.
        )  # I finish the warning.
    # --------------------------------------------------------
    # 10.5 RUN THE INTERNAL ANALYZER
    # --------------------------------------------------------
    try:  # I handle failures raised during analysis or its result messaging.
        regime_result = identify_market_regime(selected_symbol)  # I call the analyzer for the selected symbol.
        if regime_result:  # I treat a truthy returned result as success.
            if refreshed_records and not refresh_error:  # I check whether records were refreshed without a recorded error.
                messages.success(  # I report refresh and analysis success.
                    request,  # I attach the message to this request.
                    (  # I begin the message.
                        f"{selected_symbol} market data was "  # I identify the selected market.
                        "refreshed from Alpaca and Market "  # I report the refresh.
                        "Condition analysis completed "  # I report the analysis.
                        "successfully."  # I finish the success message.
                    ),  # I finish the combined string.
                )  # I finish the notification.
            else:  # I report analysis success without claiming a successful record refresh.
                messages.success(  # I add a success notification.
                    request,  # I attach it to this request.
                    (  # I begin the message.
                        "Market Condition analysis completed "  # I describe the successful action.
                        f"for {selected_symbol}."  # I identify the selected symbol.
                    ),  # I finish the combined string.
                )  # I finish the notification.
        else:  # I handle an analyzer that returned a falsy result.
            messages.error(  # I explain that no classification was produced.
                request,  # I attach the message to this request.
                (  # I begin the message.
                    "MarketPulse received sufficient stored "  # I describe the row-count check.
                    f"data for {selected_symbol}, but the "  # I identify the market.
                    "internal Market Regime engine could not "  # I describe the analytical problem.
                    "produce a classification. "  # I explain the missing result.
                    "Please check the historical dataset for "  # I suggest inspecting the dataset.
                    "missing or invalid observations."  # I finish the original explanation.
                ),  # I finish the combined message.
            )  # I finish the notification.
    except Exception as error:  # I catch an exception raised inside the analysis block.
        messages.error(  # I add an analysis failure notification.
            request,  # I attach it to this request.
            (  # I begin the message.
                "Market Condition analysis could not be "  # I describe the failure.
                f"completed for {selected_symbol}: {error}"  # I include the symbol and exception text.
            ),  # I finish the combined string.
        )  # I finish the error notification.
    return _redirect_to_data_workspace(symbol=selected_symbol)  # I return to the selected dataset's Market Condition section.
# ============================================================
# 11. LEGACY MARKET CONDITION RESULTS ROUTE
# ============================================================
@login_required  # I require authentication before following this compatibility route.
def market_condition_results(request):  # I define the handler retained for older links.
    """Redirect older results links to the Market Condition panel in the Data workspace."""
    selected_symbol = request.GET.get("symbol", "").strip().upper()  # I read and normalize an optional query-string symbol.
    if not selected_symbol:  # I look for a saved classification when no symbol was supplied.
        latest_regime = MarketRegime.objects.order_by(  # I order classifications across all symbols.
            "-date",  # I put the latest classification date first.
            "-created_at",  # I use creation time as the secondary ordering.
        ).first()  # I retrieve the first result or None.
        if latest_regime:  # I check whether a saved classification exists.
            selected_symbol = latest_regime.symbol.strip().upper()  # I use that classification's normalized symbol.
    return _redirect_to_data_workspace(symbol=selected_symbol)  # I redirect to the main workspace's Market Condition section.