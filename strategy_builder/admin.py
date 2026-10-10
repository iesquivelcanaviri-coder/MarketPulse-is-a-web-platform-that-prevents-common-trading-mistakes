"""============================================================ STRATEGY ADMIN ============================================================"""

# ============================================================
# 1. IMPORT ADMIN TOOLS AND MODELS
# ============================================================
from django.contrib import admin  # Import: I access Django's administration tools and default admin site.
from .models import StrategyRule, BacktestTrade  # Relative import: I import the rule and simulated-trade models from this application.

# ============================================================
# 2. REGISTER MODELS WITH THE DEFAULT ADMIN INTERFACE
# ============================================================
admin.site.register(StrategyRule)  # Method call: I register strategy rules using Django's default ModelAdmin configuration.
admin.site.register(BacktestTrade)  # Method call: I register simulated trades using the default configuration.

# ============================================================
# 3. IMPORT THE STRATEGY LIBRARY MODEL
# ============================================================
from .models import StrategyLibraryItem  # Relative import: I import the model whose admin interface I customise below.

# ============================================================
# 4. REGISTER THE CUSTOM LIBRARY ADMIN CLASS
# ============================================================
@admin.register(StrategyLibraryItem)  # Decorator: I register the library model with the admin class defined immediately below.
class StrategyLibraryItemAdmin(admin.ModelAdmin):  # Class inheritance: I customise Django's ModelAdmin behaviour for library items.

    # --------------------------------------------------------
    # 4.1 COLUMNS DISPLAYED IN THE RECORD LIST
    # --------------------------------------------------------
    list_display = (  # Class attribute and tuple: I specify the columns shown on the library's admin list page.
        "name",  # String: I display the model's readable name.
        "category",  # String: I display its category.
        "implementation_status",  # String: I display its implementation status.
        "is_active",  # String: I display whether the library entry is active.
        "display_order",  # String: I display its ordering value.
    )  # Closing parenthesis: I finish the displayed-column tuple.

    # --------------------------------------------------------
    # 4.2 FILTERS FOR THE RECORD LIST
    # --------------------------------------------------------
    list_filter = (  # Class attribute and tuple: I specify fields used by the admin's list filters.
        "category",  # String: I allow filtering by model category.
        "implementation_status",  # String: I allow filtering by implementation status.
        "is_active",  # String: I allow filtering by active status.
    )  # Closing parenthesis: I finish the filter-field tuple.

    # --------------------------------------------------------
    # 4.3 SEARCHABLE FIELDS
    # --------------------------------------------------------
    search_fields = (  # Class attribute and tuple: I specify the fields searched by the admin search box.
        "name",  # String: I allow searching the model name.
        "code",  # String: I allow searching the internal model code.
        "description",  # String: I allow searching the description.
    )  # Closing parenthesis: I finish the searchable-field tuple.