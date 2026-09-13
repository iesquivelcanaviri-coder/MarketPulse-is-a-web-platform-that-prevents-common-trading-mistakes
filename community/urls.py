# ============================================================
# COMMUNITY - URL CONFIGURATION
# ============================================================
#
# Framework mapping:
#
# Browser / Django template
#          ↓
# marketpulse/urls.py
#          ↓
# community/urls.py
#          ↓
# community/views.py
#          ↓
# community/models.py
#          ↓
# PostgreSQL / Neon database
#
#
# This file contains all URL routes belonging to the
# MarketPulse Community application.
#
# The "community" namespace is used throughout templates.
#
# Example:
#
# {% url 'community:feed' %}
#
# community = app_name
# feed      = URL route name
#
# ============================================================


# ============================================================
# 1. IMPORTS
# ============================================================

from django.urls import path
# Imports Django's path() function.
# path() connects a browser URL to a Python view function.


from . import views
# Imports views.py from this same community application.
#
# This allows routes below to call:
#
# views.feed
# views.inbox
# views.compose_message
# views.message_detail


# ============================================================
# 2. APPLICATION NAMESPACE
# ============================================================

app_name = "community"
# Creates the namespace used by Django when reversing URLs.
#
# This is extremely important because templates use URLs such as:
#
# {% url 'community:feed' %}
#
# {% url 'community:inbox' %}
#
# {% url 'community:compose_message' %}
#
# Without app_name = "community", Django cannot identify
# these routes using the community namespace.


# ============================================================
# 3. COMMUNITY URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # COMMUNITY FEED
    # ========================================================
    #
    # Full URL:
    #
    # /community/
    #
    # View:
    #
    # community/views.py
    #     ↓
    # feed()
    #
    # Template:
    #
    # community/templates/community/feed.html
    #
    # Template URL reference:
    #
    # {% url 'community:feed' %}
    #
    # ========================================================

    path(
        "",
        views.feed,
        name="feed",
    ),


    # ========================================================
    # INBOX
    # ========================================================
    #
    # Full URL:
    #
    # /community/inbox/
    #
    # View:
    #
    # community/views.py
    #     ↓
    # inbox()
    #
    # Template:
    #
    # community/templates/community/inbox.html
    #
    # Template URL reference:
    #
    # {% url 'community:inbox' %}
    #
    # ========================================================

    path(
        "inbox/",
        views.inbox,
        name="inbox",
    ),


    # ========================================================
    # COMPOSE PRIVATE MESSAGE
    # ========================================================
    #
    # Full URL:
    #
    # /community/inbox/compose/
    #
    # View:
    #
    # community/views.py
    #     ↓
    # compose_message()
    #
    # Template:
    #
    # community/templates/community/compose_message.html
    #
    # Template URL reference:
    #
    # {% url 'community:compose_message' %}
    #
    # ========================================================

    path(
        "inbox/compose/",
        views.compose_message,
        name="compose_message",
    ),


    # ========================================================
    # READ PRIVATE MESSAGE
    # ========================================================
    #
    # Full URL example:
    #
    # /community/inbox/5/
    #
    # Here:
    #
    # 5 = database primary key of the message.
    #
    # View:
    #
    # community/views.py
    #     ↓
    # message_detail(request, pk)
    #
    # Template:
    #
    # community/templates/community/message_detail.html
    #
    # Template URL example:
    #
    # {% url 'community:message_detail' message.pk %}
    #
    # The <int:pk> part tells Django that this part
    # of the URL must contain an integer.
    #
    # ========================================================

    path(
        "inbox/<int:pk>/",
        views.message_detail,
        name="message_detail",
    ),

]