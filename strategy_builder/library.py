"""
============================================================
MARKETPULSE - STRATEGY LIBRARY SERVICE
============================================================

Purpose:
Group active library models into non-empty categories.

Framework interaction:
StrategyLibraryItem database records
-> get_grouped_strategy_library()
-> calling views
-> Django templates.

Shared service:
The Data and Strategies views can reuse this grouping logic.
============================================================
"""

# ============================================================
# 1. IMPORT THE LIBRARY MODEL
# ============================================================
from .models import StrategyLibraryItem  # Relative import: I import the library model from this application's models module.

# ============================================================
# 2. DEFINE THE SHARED GROUPING FUNCTION
# ============================================================
def get_grouped_strategy_library():  # Function definition: I create a reusable function with no input parameters.
    grouped_categories = []  # Variable assignment and list: I start an empty collection for the category groups.

    # --------------------------------------------------------
    # 2.1 FOLLOW THE CATEGORY-CHOICE ORDER
    # --------------------------------------------------------
    for category_code, category_label in (  # Loop and tuple unpacking: I read each category's stored code and display label.
        StrategyLibraryItem.CATEGORY_CHOICES  # Class attribute: I use the category list defined on the model.
    ):  # Loop boundary: I begin the indented code that runs for each category.

        # ----------------------------------------------------
        # 2.2 RETRIEVE AND SORT ACTIVE CATEGORY ITEMS
        # ----------------------------------------------------
        items = list(  # Assignment and conversion: I evaluate the database QuerySet and store its records in a Python list.
            StrategyLibraryItem.objects  # Model manager: I start a database query for library records.
            .filter(  # Method chaining: I restrict the query to matching records.
                category=category_code,  # Keyword argument: I select records belonging to the current category.
                is_active=True,  # Boolean filter: I select only active library entries.
            )  # Closing parenthesis: I finish the query filters.
            .order_by(  # QuerySet method: I define the order of models within this category.
                "display_order",  # String argument: I sort first by ascending display-order value.
                "name",  # String argument: I sort entries with equal display orders by name.
            )  # Closing parenthesis: I finish the ordering call.
        )  # Closing parenthesis: I finish converting the QuerySet into a list.

        # ----------------------------------------------------
        # 2.3 INCLUDE ONLY NON-EMPTY CATEGORIES
        # ----------------------------------------------------
        if items:  # Conditional and truthiness: I continue only when the category contains active models.
            grouped_categories.append(  # List method: I add one category dictionary to the result collection.
                {  # Dictionary literal: I group the category information into named entries.
                    "code": category_code,  # Key-value pair: I store the category's internal code.
                    "label": category_label,  # Key-value pair: I store its readable display label.
                    "items": items,  # Key-value pair: I store the sorted list of model instances.
                }  # Closing brace: I finish the category dictionary.
            )  # Closing parenthesis: I finish adding the category to the result list.

    # --------------------------------------------------------
    # 2.4 RETURN THE GROUPED LIBRARY
    # --------------------------------------------------------
    return grouped_categories  # Return statement: I give the calling view the completed list of category dictionaries.