"""============================================================
TEMPLATE MATH FILTERS

WHAT THIS FILE IS FOR:
This file creates a custom Django template filter called "percentage".
It changes a decimal value such as 0.75 into 75.0 so templates can
display percentage-style results more easily.

FRAMEWORK MAPPING:
analysis result templates use `percentage` instead of an undefined `mul` filter.

MARKETPULSE DATA FLOW:
Python / analysis calculation
        ↓
Django View
        ↓
Template Context
        ↓
Django HTML Template
        ↓
{% load math_tags %}
        ↓
{{ value|percentage }}
        ↓
percentage(value)
        ↓
Decimal value * 100
        ↓
Percentage displayed to the user

PROGRAMMING LANGUAGE FEATURES / CONCEPTS USED:
- Module importing
- Objects
- Function decorators
- Functions
- Parameters
- Type conversion
- Arithmetic operators
- Return values
- Exception handling
- Exception types

These are building blocks that make up the Python programming language.
============================================================"""

# ============================================================
# 1. DJANGO TEMPLATE IMPORT
# ============================================================
from django import template  # IMPORT / MODULE: imports Django's template tools so this Python file can create a custom template filter.

# ============================================================
# 2. CREATE THE TEMPLATE FILTER LIBRARY
# ============================================================
register=template.Library()  # OBJECT CREATION: creates a Django Library object where custom template filters can be registered.

# ============================================================
# 3. REGISTER THE CUSTOM PERCENTAGE FILTER
# ============================================================
@register.filter  # DECORATOR: tells Django to register the function below as a template filter called "percentage".

# ============================================================
# 4. PERCENTAGE FUNCTION
# ============================================================
def percentage(value):  # FUNCTION / PARAMETER: defines reusable behaviour and receives one input value from the Django template.

    # ========================================================
    # 5. TRY THE PERCENTAGE CALCULATION
    # ========================================================
    try:return float(value)*100  # TRY / TYPE CONVERSION / ARITHMETIC / RETURN: converts the input to a float, multiplies it by 100, and returns the result.

    # ========================================================
    # 6. HANDLE INVALID VALUES
    # ========================================================
    except (TypeError,ValueError):return 0  # EXCEPTION HANDLING: catches invalid types or values and safely returns 0 instead of crashing the template.