"""============================================================
RISK SNAPSHOT MODEL
Framework mapping: calculator results are persisted for audit/history.
============================================================"""  # Module docstring: describe the intended purpose of this model.

# ============================================================
# 1. IMPORTS — REUSE SETTINGS AND MODEL TOOLS
# ============================================================
from django.conf import settings  # Import: access project settings, including the configured user model.
from django.db import models  # Import: access Django's database field classes.
from core.models import TimeStampedModel  # Import: reuse the project's shared parent model.

# ============================================================
# 2. RISK SNAPSHOT — DEFINE THE MODEL CLASS
# ============================================================
class RiskSnapshot(TimeStampedModel):  # Class and inheritance: define a snapshot using the shared parent model.

    # --------------------------------------------------------
    # 2.1 USER RELATIONSHIP
    # --------------------------------------------------------
    user = models.ForeignKey(  # Field assignment: link each snapshot to one user.
        settings.AUTH_USER_MODEL,  # Setting reference: use the project's configured user model.
        on_delete=models.CASCADE,  # Keyword argument: deleting the user also deletes their related snapshots through Django.
        related_name='risk_snapshots',  # String argument: enable reverse access through user.risk_snapshots.
    )  # Close the relationship field definition.

    # --------------------------------------------------------
    # 2.2 ASSET SYMBOL
    # --------------------------------------------------------
    symbol = models.CharField(  # Field assignment: store the asset symbol as text.
        max_length=20,  # Integer argument: allow up to 20 characters.
        blank=True,  # Boolean argument: allow an empty symbol during validation.
    )  # Close the text field definition.

    # --------------------------------------------------------
    # 2.3 ACCOUNT BALANCE AND RISK PERCENTAGE
    # --------------------------------------------------------
    account_balance = models.DecimalField(  # Field assignment: store the account balance as a decimal number.
        max_digits=14,  # Allow up to 14 digits in total, including digits after the decimal point.
        decimal_places=2,  # Reserve two decimal places for the balance.
    )  # Close the account-balance field definition.
    risk_percentage = models.DecimalField(  # Field assignment: store the risk value supplied by other code.
        max_digits=8,  # Allow up to eight digits in total.
        decimal_places=6,  # Reserve six decimal places; this field does not convert percentages into fractions.
    )  # Close the risk-percentage field definition.

    # --------------------------------------------------------
    # 2.4 VOLATILITY
    # --------------------------------------------------------
    volatility = models.DecimalField(  # Field assignment: store a decimal volatility value.
        max_digits=10,  # Allow up to ten digits in total.
        decimal_places=6,  # Reserve six decimal places for precision.
        default=0,  # Default argument: use zero when a value is not supplied.
    )  # Close the volatility field definition.

    # --------------------------------------------------------
    # 2.5 RECOMMENDED POSITION SIZE
    # --------------------------------------------------------
    recommended_position_size = models.DecimalField(  # Field assignment: store the recommended position quantity.
        max_digits=14,  # Allow up to 14 digits in total.
        decimal_places=4,  # Reserve four decimal places, allowing fractional quantities.
    )  # Close the position-size field definition.

    # --------------------------------------------------------
    # 2.6 STOP-LOSS PRICE
    # --------------------------------------------------------
    stop_loss_price = models.DecimalField(  # Field assignment: store the calculated stop price.
        max_digits=14,  # Allow up to 14 digits in total.
        decimal_places=4,  # Reserve four decimal places for the price.
    )  # Close the stop-price field definition.