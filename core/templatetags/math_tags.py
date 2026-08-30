"""============================================================
TEMPLATE MATH FILTERS
Framework mapping: analysis result templates use `percentage` instead of an undefined `mul` filter.
============================================================"""
from django import template
register=template.Library()
@register.filter
def percentage(value):
    try:return float(value)*100
    except (TypeError,ValueError):return 0
