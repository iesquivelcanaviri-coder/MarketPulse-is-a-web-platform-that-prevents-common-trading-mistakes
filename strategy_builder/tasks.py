"""============================================================ OPTIONAL CELERY STRATEGY MONITORING: latest stored data → dashboard Alert. ============================================================"""

# ============================================================
# 1. IMPORTS
# ============================================================
from celery import shared_task  # Import: I bring in the decorator that registers a reusable Celery task.
from core.models import Alert, MarketData, Strategy  # Model imports: I access alerts, stored market data and strategies through Django's ORM.

# ============================================================
# 2. REGISTER THE BACKGROUND TASK
# ============================================================
@shared_task  # Decorator: I register this function as a Celery task that can be queued for a worker.
def monitor_active_strategies():  # Function definition: I define the monitoring task without input parameters.

    # --------------------------------------------------------
    # 2.1 INITIALISE THE ALERT COUNTER
    # --------------------------------------------------------
    n = 0  # Variable assignment and integer: I start the number of created alerts at zero.

    # --------------------------------------------------------
    # 2.2 LOOP THROUGH ACTIVE STRATEGIES AND RULES
    # --------------------------------------------------------
    for s in Strategy.objects.filter(is_active=True).prefetch_related('rules'):  # Iteration and method chaining: I retrieve active strategies and prefetch their related rules.
        for r in s.rules.filter(is_active=True):  # Nested loop and filtering: I process each active rule; this filtered query does not reuse the unfiltered prefetch cache.

            # ------------------------------------------------
            # 2.3 RETRIEVE A STORED MARKET-DATA RECORD
            # ------------------------------------------------
            last = MarketData.objects.filter(symbol=r.symbol).first()  # Query and assignment: I get the first matching record; whether it is latest depends on the model's ordering.

            # ------------------------------------------------
            # 2.4 CREATE AN ALERT WHEN DATA EXISTS
            # ------------------------------------------------
            if last:  # Conditional and truthiness: I continue only when a matching market-data record exists.
                Alert.objects.create(  # ORM method call: I create and save an Alert database record.
                    user=s.user,  # Keyword argument and attribute access: I assign the alert to the strategy's user.
                    alert_type='strategy',  # String literal: I classify the alert as a strategy alert.
                    title=f'{s.name} monitoring update',  # Formatted string: I insert the strategy name into the alert title.
                    message=f'Latest {r.symbol} close: {last.close_price}',  # Formatted string: I insert the rule's symbol and the retrieved close price.
                )  # Closing parenthesis: I finish creating the alert.
                n += 1  # Augmented assignment: I increase the counter after an alert is successfully created.

    # --------------------------------------------------------
    # 2.5 RETURN THE NUMBER OF CREATED ALERTS
    # --------------------------------------------------------
    return n  # Return statement: I provide the alert count as the task's result.