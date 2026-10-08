# ============================================================
# COMMUNITY - URL CONFIGURATION
# ============================================================
#
# Framework mapping:
#
# Browser / Django Template
#          ↓
# marketpulse/urls.py
#          ↓
# community/urls.py
#          ↓
# community/views.py
#          ↓
# community/forms.py
#          ↓
# community/models.py
#          ↓
# Django ORM
#          ↓
# PostgreSQL / Neon
#
#
# PURPOSE:
#
# This file defines every URL route belonging to the
# MarketPulse Community application.
#
#
# COMMUNITY ARCHITECTURE:
#
# MarketPulse Community
#        │
#        ├── Community Feed
#        │       ↓
#        │   CommunityPost
#        │
#        └── Private Messaging
#                ↓
#             Inbox
#                ↓
#        Conversation List
#                ↓
#        Conversation Thread
#                ↓
#         PrivateMessage
#                ↓
#              Reply
#
#
# NEW PRIVATE-MESSAGING ARCHITECTURE:
#
# The original MarketPulse messaging system treated every
# PrivateMessage as a separate email-style object:
#
# Received Messages
# Sent Messages
#
#
# The updated architecture groups messages into continuous
# conversations:
#
# User1 ↔ User2
#       ↓
# Conversation
#       ↓
# PrivateMessage
# PrivateMessage
# PrivateMessage
# PrivateMessage
#
#
# This allows MarketPulse to provide a more modern,
# conversation-based messaging interface while keeping
# Django authentication and database access on the server.
#
#
# APPLICATION NAMESPACE:
#
# app_name = "community"
#
#
# Templates can therefore reference routes using:
#
# {% url 'community:feed' %}
#
# {% url 'community:inbox' %}
#
# {% url 'community:new_conversation' %}
#
# {% url 'community:conversation_detail' conversation.pk %}
#
#
# TRANSITION STRATEGY:
#
# The original email-style routes:
#
# community:compose_message
# community:message_detail
#
# are temporarily retained.
#
# This allows older templates and links to continue working
# while the application is migrated to Conversation threads.
#
# Once all templates, views and Home-page links use the new
# conversation workflow, the legacy routes can be removed.
#
# ============================================================


# ============================================================
# 1. IMPORTS
# ============================================================

from django.urls import path

from . import views


# ============================================================
# 2. APPLICATION NAMESPACE
# ============================================================

app_name = "community"


# ============================================================
# 3. COMMUNITY URL PATTERNS
# ============================================================

urlpatterns = [


    # ========================================================
    # 3.1 COMMUNITY FEED
    # ========================================================
    #
    # Browser URL:
    #
    # /community/
    #
    #
    # Purpose:
    #
    # Display public MarketPulse community posts.
    #
    #
    # Framework flow:
    #
    # Browser
    #     ↓
    # marketpulse/urls.py
    #     ↓
    # community/urls.py
    #     ↓
    # views.feed()
    #     ↓
    # CommunityPost
    #     ↓
    # Django ORM
    #     ↓
    # PostgreSQL / Neon
    #     ↓
    # community/feed.html
    #
    #
    # Template reference:
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
    # 3.2 CONVERSATION INBOX
    # ========================================================
    #
    # Browser URL:
    #
    # /community/inbox/
    #
    #
    # Purpose:
    #
    # Display all conversations belonging to the
    # authenticated user.
    #
    #
    # OLD DESIGN:
    #
    # Received Messages
    # Sent Messages
    #
    #
    # NEW DESIGN:
    #
    # Conversations
    #
    # User2
    #     Latest message...
    #
    # User3
    #     Latest message...
    #
    # User4
    #     Latest message...
    #
    #
    # Each conversation appears once rather than every
    # PrivateMessage appearing independently.
    #
    #
    # Framework flow:
    #
    # Browser
    #     ↓
    # views.inbox()
    #     ↓
    # Conversation.objects
    #     ↓
    # filter(participants=request.user)
    #     ↓
    # Django ORM
    #     ↓
    # PostgreSQL / Neon
    #     ↓
    # community/inbox.html
    #
    #
    # Template reference:
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
    # 3.3 START NEW CONVERSATION
    # ========================================================
    #
    # Browser URL:
    #
    # /community/inbox/new/
    #
    #
    # Purpose:
    #
    # Start a new private conversation with another
    # registered MarketPulse user.
    #
    #
    # The recipient is selected only when the conversation
    # begins.
    #
    # Future replies remain inside the same Conversation.
    #
    #
    # User workflow:
    #
    # User1
    #     ↓
    # New Conversation
    #     ↓
    # Select User2
    #     ↓
    # Write first message
    #     ↓
    # Conversation created
    #     ↓
    # User1 + User2 added as participants
    #     ↓
    # First PrivateMessage created
    #     ↓
    # Conversation thread opened
    #
    #
    # Framework flow:
    #
    # Browser
    #     ↓
    # views.new_conversation()
    #     ↓
    # NewConversationForm
    #     ↓
    # Conversation
    #     ↓
    # Conversation.participants
    #     ↓
    # PrivateMessage
    #     ↓
    # Django ORM
    #     ↓
    # PostgreSQL / Neon
    #     ↓
    # Redirect:
    # community:conversation_detail
    #
    #
    # Template reference:
    #
    # {% url 'community:new_conversation' %}
    #
    # ========================================================

    path(
        "inbox/new/",
        views.new_conversation,
        name="new_conversation",
    ),


    # ========================================================
    # 3.4 CONVERSATION THREAD
    # ========================================================
    #
    # Browser URL example:
    #
    # /community/inbox/conversation/12/
    #
    #
    # Here:
    #
    # 12
    #
    # is the primary key of a Conversation.
    #
    # It is NOT the primary key of one individual
    # PrivateMessage.
    #
    #
    # Example:
    #
    # Conversation 12
    #
    # User1 ↔ User2
    #
    # User2:
    #     Hello.
    #
    # You:
    #     Hi.
    #
    # User2:
    #     Have you looked at AAPL?
    #
    # You:
    #     Yes, I tested the strategy yesterday.
    #
    #
    # GET flow:
    #
    # Browser
    #     ↓
    # /community/inbox/conversation/<pk>/
    #     ↓
    # views.conversation_detail()
    #     ↓
    # Conversation.objects
    #     ↓
    # Security filter:
    # participants=request.user
    #     ↓
    # Conversation.messages
    #     ↓
    # PrivateMessage objects
    #     ↓
    # community/message_thread.html
    #
    #
    # POST reply flow:
    #
    # MessageReplyForm
    #     ↓
    # Validate body
    #     ↓
    # PrivateMessage created
    #     ↓
    # Associated with same Conversation
    #     ↓
    # Redirect back to conversation thread
    #
    #
    # Template reference:
    #
    # {% url 'community:conversation_detail' conversation.pk %}
    #
    #
    # SECURITY REQUIREMENT:
    #
    # conversation_detail() must only return a Conversation
    # where request.user is one of the participants.
    #
    #
    # Correct pattern:
    #
    # get_object_or_404(
    #     Conversation,
    #     pk=pk,
    #     participants=request.user,
    # )
    #
    #
    # This prevents one authenticated user from manually
    # changing the conversation ID in the browser and reading
    # another user's private thread.
    #
    # ========================================================

    path(
        "inbox/conversation/<int:pk>/",
        views.conversation_detail,
        name="conversation_detail",
    ),


    # ========================================================
    # 3.5 LEGACY COMPOSE MESSAGE
    # ========================================================
    #
    # Browser URL:
    #
    # /community/inbox/compose/
    #
    #
    # Original purpose:
    #
    # Create one independent PrivateMessage using:
    #
    # recipient
    # subject
    # body
    #
    #
    # This route is temporarily retained while the new
    # Conversation architecture is introduced.
    #
    #
    # Existing templates may still reference:
    #
    # {% url 'community:compose_message' %}
    #
    #
    # For example, an older Home-page button may still use:
    #
    # New Message
    #     ↓
    # community:compose_message
    #
    #
    # FINAL REPLACEMENT:
    #
    # community:new_conversation
    #
    #
    # When all templates use the new conversation workflow,
    # this route and its view can be removed.
    #
    # ========================================================

    path(
        "inbox/compose/",
        views.compose_message,
        name="compose_message",
    ),


    # ========================================================
    # 3.6 LEGACY INDIVIDUAL MESSAGE DETAIL
    # ========================================================
    #
    # Browser URL example:
    #
    # /community/inbox/5/
    #
    #
    # Here:
    #
    # 5
    #
    # is a PrivateMessage primary key.
    #
    #
    # Original purpose:
    #
    # Display one individual received message.
    #
    #
    # This route remains temporarily so older links continue
    # working during the migration.
    #
    #
    # FINAL REPLACEMENT:
    #
    # /community/inbox/conversation/<pk>/
    #
    #
    # The new route displays the complete conversation rather
    # than an isolated message.
    #
    #
    # IMPORTANT ROUTE ORDER:
    #
    # Keep this generic:
    #
    # inbox/<int:pk>/
    #
    # AFTER the more specific routes:
    #
    # inbox/new/
    # inbox/conversation/<int:pk>/
    # inbox/compose/
    #
    # This keeps the routing structure clear and prevents the
    # generic legacy route from becoming confusing.
    #
    # ========================================================

    path(
        "inbox/<int:pk>/",
        views.message_detail,
        name="message_detail",
    ),

]