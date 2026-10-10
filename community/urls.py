# ============================================================
# COMMUNITY - URL CONFIGURATION
# ============================================================
#
# SHORT PURPOSE:
#
# This file is the URL router for the Community application.
#
# It tells Django:
#
# "When the browser requests this Community URL,
# which function in community/views.py should run?"
#
# This file does NOT:
#
# - query the database directly
# - process forms directly
# - contain Community models
# - render the HTML itself
#
# Instead, it connects browser URLs to Django view functions.
#
#
# ============================================================
# FRAMEWORK MAPPING
# ============================================================
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
#          ↓
# Django Template
#          ↓
# Browser
#
#
# Example:
#
# User opens:
#
# /community/inbox/
#
#        ↓
#
# marketpulse/urls.py
#
# recognises:
#
# community/
#
#        ↓
#
# sends the remaining URL:
#
# inbox/
#
#        ↓
#
# community/urls.py
#
#        ↓
#
# matches:
#
# path("inbox/", views.inbox, name="inbox")
#
#        ↓
#
# community/views.py
#
#        ↓
#
# inbox()
#
#        ↓
#
# models / Django ORM / PostgreSQL
#
#        ↓
#
# community/inbox.html
#
#        ↓
#
# Browser
#
#
# ============================================================
# LECTURE CONNECTION:
# PROGRAMMING LANGUAGE FEATURES / CONCEPTS
# ============================================================
#
# This file demonstrates several programming concepts:
#
# 1. MODULES AND IMPORTS
#
# from django.urls import path
#
# Python imports reusable functionality from another module.
#
#
# 2. RELATIVE IMPORTS
#
# from . import views
#
# "." means the current Python package.
#
#
# 3. VARIABLES
#
# app_name = "community"
#
# urlpatterns = [...]
#
# Names are assigned values using "=".
#
#
# 4. STRINGS
#
# "community"
# "inbox/"
# "feed"
#
# Strings represent textual values.
#
#
# 5. LISTS
#
# urlpatterns = [...]
#
# A Python list stores multiple URL route objects.
#
#
# 6. FUNCTION CALLS
#
# path(...)
#
# path() is a Django function being called.
#
#
# 7. FUNCTION REFERENCES
#
# views.feed
# views.inbox
#
# These pass the function itself to Django.
#
# Notice that there are no brackets:
#
# views.feed
#
# NOT:
#
# views.feed()
#
# Django decides when the view function should execute.
#
#
# 8. POSITIONAL ARGUMENTS
#
# path(
#     "inbox/",
#     views.inbox,
# )
#
# The route and view are supplied according to their position
# in the path() function call.
#
#
# 9. KEYWORD ARGUMENTS
#
# name="inbox"
#
# The argument is explicitly identified by its parameter name.
#
#
# 10. NAMESPACES
#
# app_name = "community"
#
# Django can distinguish Community URLs from URLs in other
# applications.
#
#
# 11. PARAMETERS
#
# <int:pk>
#
# A changing value can be taken from the browser URL.
#
#
# 12. TYPE CONVERSION
#
# <int:pk>
#
# Django requires this part of the URL to be an integer.
#
#
# 13. FRAMEWORK ROUTING
#
# Django connects:
#
# URL
#   ↓
# View function
#
# This is an example of framework-controlled program flow.
#
#
# 14. SEPARATION OF CONCERNS
#
# urls.py   → routing
# views.py  → request / response logic
# forms.py  → input and validation
# models.py → database structure
# templates → presentation
#
# Each file has a different responsibility.
#
#
# ============================================================
# COMMUNITY ARCHITECTURE
# ============================================================
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
# ============================================================
# PRIVATE-MESSAGING ARCHITECTURE
# ============================================================
#
# OLD DESIGN:
#
# The original MarketPulse messaging system treated every
# PrivateMessage as a separate email-style object:
#
# Received Messages
# Sent Messages
#
#
# NEW DESIGN:
#
# Messages are grouped into continuous conversations:
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
# This gives MarketPulse a conversation-style messaging
# interface while Django authentication and database access
# remain on the server.
#
#
# ============================================================
# APPLICATION NAMESPACE
# ============================================================
#
# app_name = "community"
#
# Templates can reference routes using names such as:
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
# ============================================================
# TRANSITION STRATEGY
# ============================================================
#
# The original email-style routes:
#
# community:compose_message
# community:message_detail
#
# are temporarily retained.
#
# This allows older templates and links to continue working
# while the application moves to Conversation threads.
#
# Once all templates, views and Home-page links use the new
# conversation workflow, the legacy routes can be removed.
#
# ============================================================


# ============================================================
# 1. IMPORTS
# ============================================================
#
# LECTURE CONCEPT:
# Module import.
#
# django.urls is a Django Python module.
#
# "from ... import ..." lets this file use a specific object
# from another module without importing everything.
#
# path is Django's URL-routing function.
# ============================================================

from django.urls import path  # Import Django's path() function so URL patterns can be created.

# LECTURE CONCEPT:
# Relative import / Python package.
#
# "." means:
#
# "Look inside the current community package."
#
# views is the community/views.py module.
#
# The functions referenced later, such as views.feed and
# views.inbox, therefore come from community/views.py.

from . import views  # Import this app's views module so routes can point to its view functions.


# ============================================================
# 2. APPLICATION NAMESPACE
# ============================================================
#
# LECTURE CONCEPT:
# Variable assignment + string.
#
# app_name is a Python variable.
#
# "=" assigns the string "community" to that variable.
#
# Django uses this value as the namespace for the URLs in this
# application.
#
# Therefore:
#
# name="feed"
#
# becomes:
#
# community:feed
#
# inside Django templates and redirect() calls.
#
# This is useful because another Django application could also
# have a URL called "feed".
# ============================================================

app_name = "community"  # Store the Django URL namespace for this application in a Python variable.


# ============================================================
# 3. COMMUNITY URL PATTERNS
# ============================================================
#
# LECTURE CONCEPT:
# Variable + list data structure.
#
# urlpatterns is a normal Python variable.
#
# The square brackets:
#
# [...]
#
# create a Python LIST.
#
# The list contains multiple objects returned by Django's
# path() function.
#
# Django looks specifically for a variable called urlpatterns
# when it loads a URL configuration module.
#
#
# GENERAL STRUCTURE:
#
# path(
#     URL_PATTERN,
#     VIEW_FUNCTION,
#     name=ROUTE_NAME,
# )
#
#
# Example:
#
# path(
#     "inbox/",
#     views.inbox,
#     name="inbox",
# )
#
# means:
#
# URL:
# inbox/
#
#        ↓
#
# Python function:
# views.inbox
#
#        ↓
#
# Django route name:
# community:inbox
# ============================================================

urlpatterns = [  # Create the Python list that stores all Community URL routes.

    # ========================================================
    # 3.1 COMMUNITY FEED
    # ========================================================
    #
    # Browser URL:
    #
    # /community/
    #
    #
    # PURPOSE:
    #
    # Display public MarketPulse community posts.
    #
    #
    # FRAMEWORK FLOW:
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
    # TEMPLATE REFERENCE:
    #
    # {% url 'community:feed' %}
    #
    #
    # LECTURE CONCEPTS:
    #
    # Function call:
    #
    # path(...)
    #
    # Strings:
    #
    # ""
    # "feed"
    #
    # Function reference:
    #
    # views.feed
    #
    # Notice:
    #
    # views.feed
    #
    # is supplied WITHOUT ().
    #
    # We are giving Django a reference to the function.
    #
    # Django calls the function later when a matching HTTP
    # request arrives.
    #
    # The empty string:
    #
    # ""
    #
    # means the root of this app's URL configuration.
    #
    # Because marketpulse/urls.py already handles:
    #
    # community/
    #
    # the resulting URL is:
    #
    # /community/
    # ========================================================

    path(  # Call Django's path() function to create the Community Feed URL route.
        "",  # Match the root URL of the Community app after /community/.
        views.feed,  # Send the matching HTTP request to the feed view function.
        name="feed",  # Give the route the reusable Django name community:feed.
    ),  # Finish the path() function call and add its returned route object to urlpatterns.

    # ========================================================
    # 3.2 CONVERSATION INBOX
    # ========================================================
    #
    # Browser URL:
    #
    # /community/inbox/
    #
    #
    # PURPOSE:
    #
    # Display all conversations belonging to the authenticated
    # user.
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
    # Each conversation appears once rather than every
    # PrivateMessage appearing independently.
    #
    #
    # FRAMEWORK FLOW:
    #
    # Browser
    #     ↓
    # /community/inbox/
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
    # TEMPLATE REFERENCE:
    #
    # {% url 'community:inbox' %}
    #
    #
    # LECTURE CONCEPT:
    #
    # "inbox/" is a string literal representing the URL path.
    #
    # views.inbox is a reference to the Python function Django
    # should execute.
    #
    # name="inbox" is a keyword argument.
    #
    # Because app_name is "community", Django can identify this
    # route as:
    #
    # community:inbox
    # ========================================================

    path(  # Create the URL route for the conversation inbox.
        "inbox/",  # Match /community/inbox/ after the project's Community prefix.
        views.inbox,  # Pass the HTTP request to the inbox view in community/views.py.
        name="inbox",  # Register the reusable URL name community:inbox.
    ),  # Finish this inbox URL-pattern object.

    # ========================================================
    # 3.3 START NEW CONVERSATION
    # ========================================================
    #
    # Browser URL:
    #
    # /community/inbox/new/
    #
    #
    # PURPOSE:
    #
    # Start a new private conversation with another registered
    # MarketPulse user.
    #
    # The recipient is selected only when the conversation
    # begins.
    #
    # Future replies remain inside the same Conversation.
    #
    #
    # USER WORKFLOW:
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
    # FRAMEWORK FLOW:
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
    # TEMPLATE REFERENCE:
    #
    # {% url 'community:new_conversation' %}
    #
    #
    # LECTURE CONNECTION:
    #
    # This demonstrates separation of concerns.
    #
    # urls.py only chooses the view.
    #
    # It does NOT create Conversation or PrivateMessage
    # objects itself.
    #
    # Those operations happen later in the view/model layer.
    #
    # Route:
    #
    # "inbox/new/"
    #
    #        ↓
    #
    # View reference:
    #
    # views.new_conversation
    # ========================================================

    path(  # Create the route used when the user starts a new private conversation.
        "inbox/new/",  # Match the browser URL /community/inbox/new/.
        views.new_conversation,  # Send the request to the new_conversation view function.
        name="new_conversation",  # Register this route as community:new_conversation.
    ),  # Finish this new-conversation URL-pattern object.

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
    # GET FLOW:
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
    # POST REPLY FLOW:
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
    # TEMPLATE REFERENCE:
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
    # This prevents one authenticated user from manually
    # changing the conversation ID in the browser and reading
    # another user's private thread.
    #
    #
    # --------------------------------------------------------
    # LECTURE CONCEPT: PARAMETER + TYPE CONVERSION
    # --------------------------------------------------------
    #
    # <int:pk>
    #
    # has two important parts:
    #
    # int
    #
    # tells Django the URL value must be an integer.
    #
    # pk
    #
    # is the variable name Django passes into the view.
    #
    # Example browser URL:
    #
    # /community/inbox/conversation/12/
    #
    # Django extracts:
    #
    # pk = 12
    #
    # The view can therefore have a parameter such as:
    #
    # def conversation_detail(request, pk):
    #
    # This connects URL input to Python function parameters.
    # ========================================================

    path(  # Create the dynamic route used to open one Conversation thread.
        "inbox/conversation/<int:pk>/",  # Match the URL and convert its changing pk section into an integer.
        views.conversation_detail,  # Send the request and extracted pk value to conversation_detail.
        name="conversation_detail",  # Register the route as community:conversation_detail.
    ),  # Finish the dynamic conversation URL-pattern object.

    # ========================================================
    # 3.5 LEGACY COMPOSE MESSAGE
    # ========================================================
    #
    # Browser URL:
    #
    # /community/inbox/compose/
    #
    #
    # ORIGINAL PURPOSE:
    #
    # Create one independent PrivateMessage using:
    #
    # recipient
    # subject
    # body
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
    # When all templates use the new conversation workflow,
    # this route and its view can be removed.
    #
    #
    # --------------------------------------------------------
    # LECTURE CONCEPT: BACKWARD COMPATIBILITY
    # --------------------------------------------------------
    #
    # This route shows an important software-development idea.
    #
    # A new system does not always replace the old system
    # immediately.
    #
    # Existing code may still depend on an older interface.
    #
    # Keeping this named URL temporarily allows old templates
    # to continue working while the architecture is migrated.
    # ========================================================

    path(  # Create the older URL route for composing an individual message.
        "inbox/compose/",  # Match the legacy /community/inbox/compose/ browser URL.
        views.compose_message,  # Send the request to the existing compose_message view function.
        name="compose_message",  # Keep the older community:compose_message URL name available.
    ),  # Finish the legacy compose-message URL-pattern object.

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
    # ORIGINAL PURPOSE:
    #
    # Display one individual received message.
    #
    # This route remains temporarily so older links continue
    # working during the migration.
    #
    #
    # FINAL REPLACEMENT:
    #
    # /community/inbox/conversation/<pk>/
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
    #
    # --------------------------------------------------------
    # LECTURE CONCEPT: ORDER / CONTROL FLOW
    # --------------------------------------------------------
    #
    # urlpatterns is a list and therefore has an order.
    #
    # Django checks URL patterns in order until a matching
    # route is found.
    #
    # More specific routes should therefore remain clearly
    # defined before this generic integer-based legacy route.
    #
    #
    # --------------------------------------------------------
    # LECTURE CONCEPT: DYNAMIC INPUT
    # --------------------------------------------------------
    #
    # <int:pk>
    #
    # means that values such as:
    #
    # 1
    # 5
    # 24
    #
    # can become part of the URL while using the same route.
    #
    # Django converts that part into an integer and passes it
    # to views.message_detail.
    # ========================================================

    path(  # Create the legacy dynamic route for opening one individual PrivateMessage.
        "inbox/<int:pk>/",  # Match an integer message primary key from /community/inbox/<number>/.
        views.message_detail,  # Send the request and extracted pk to the message_detail view.
        name="message_detail",  # Keep the legacy route accessible as community:message_detail.
    ),  # Finish the final URL-pattern object.

]  # Close the urlpatterns Python list containing all Community routes.