# ============================================================
# COMMUNITY - URLS
# ============================================================

from django.urls import path

from . import views


app_name = "community"


urlpatterns = [

    # --------------------------------------------------------
    # Community feed
    # --------------------------------------------------------

    path(
        "",
        views.feed,
        name="feed",
    ),


    # --------------------------------------------------------
    # Inbox
    # --------------------------------------------------------

    path(
        "inbox/",
        views.inbox,
        name="inbox",
    ),


    # --------------------------------------------------------
    # Compose private message
    # --------------------------------------------------------

    path(
        "inbox/compose/",
        views.compose_message,
        name="compose_message",
    ),


    # --------------------------------------------------------
    # Read private message
    # --------------------------------------------------------

    path(
        "inbox/<int:pk>/",
        views.message_detail,
        name="message_detail",
    ),

]