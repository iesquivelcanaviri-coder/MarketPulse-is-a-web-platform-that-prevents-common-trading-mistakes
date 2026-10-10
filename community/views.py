# ============================================================
# COMMUNITY - VIEWS
# ============================================================
#
# FILE PURPOSE:
#
# This file contains the Django view logic for the MarketPulse
# Community application.
#
# In simple words:
#
# Browser request
#       ↓
# community/urls.py
#       ↓
# community/views.py
#       ↓
# Forms + Models
#       ↓
# Django ORM
#       ↓
# PostgreSQL / Neon
#       ↓
# HTML Template
#       ↓
# Browser response
#
# DJANGO FRAMEWORK:
#
# MarketPulse uses Django's MVT architecture:
#
# MODEL
#     community/models.py
#         ↓
#     CommunityPost
#     Conversation
#     PrivateMessage
#
# VIEW
#     community/views.py
#         ↓
#     This file
#
# TEMPLATE
#     community/templates/community/
#         ↓
#     feed.html
#     inbox.html
#     compose_message.html
#     message_thread.html
#
# URL ROUTING
#     community/urls.py
#         ↓
#     calls these view functions
#
# ============================================================
# PROGRAMMING LANGUAGE CONCEPTS USED IN THIS FILE
# ============================================================
#
# IMPORTS
#     Reuse code supplied by Django and this application.
#
# VARIABLES
#     Store values such as posts, forms, conversations,
#     messages, users, and querysets.
#
# FUNCTIONS
#     Reusable blocks of instructions such as feed(),
#     inbox(), and conversation_detail().
#
# PARAMETERS
#     Values received by functions, for example request and pk.
#
# RETURN VALUES
#     Send a value/result back from a function.
#
# CONDITIONALS
#     if / elif / else control which code executes.
#
# LOOPS
#     for repeats instructions for multiple objects.
#
# COLLECTIONS
#     Lists, sets, dictionaries, and QuerySets store groups
#     of values or objects.
#
# OBJECTS
#     Django model objects represent database records.
#
# ATTRIBUTES
#     object.attribute accesses information stored on objects.
#
# METHODS
#     object.method() asks an object to perform an operation.
#
# DECORATORS
#     @login_required changes/protects a function without
#     rewriting the function itself.
#
# BOOLEAN LOGIC
#     and / or / not combine True/False conditions.
#
# COMPREHENSIONS
#     Compact syntax for creating collections.
#
# CONTEXT MANAGERS
#     with transaction.atomic() controls a database transaction.
#
# ORM
#     Django converts Python model operations into SQL queries.
#
# ============================================================
# MARKETPULSE COMMUNITY ARCHITECTURE
# ============================================================
#
# Community Feed
#       ↓
# CommunityPost
#       ↓
# Django ORM
#       ↓
# PostgreSQL / Neon
#
# Private Messaging
#       ↓
# Conversation
#       ↓
# Participants
#       ↓
# PrivateMessage
#       ↓
# Django ORM
#       ↓
# PostgreSQL / Neon
#
# ============================================================
# CONVERSATION WORKFLOW
# ============================================================
#
# User
#     ↓
# Inbox
#     ↓
# Conversation List
#     ↓
# Select Conversation
#     ↓
# Complete Message Thread
#     ↓
# Reply
#     ↓
# Message saved to same Conversation
#
# ============================================================
# TRANSITION ARCHITECTURE
# ============================================================
#
# PrivateMessage currently still contains:
#
# - conversation
# - sender
# - recipient
# - subject
# - body
# - created_at
# - is_read
#
# recipient and subject are retained temporarily so existing
# MarketPulse messages and older functionality remain
# compatible while the application moves from email-style
# messages to continuous conversation threads.
#
# ============================================================
# IMPORTANT
# ============================================================
#
# Conversation.updated_at uses auto_now=True, but saving a
# related PrivateMessage does not automatically save the
# Conversation itself.
#
# Therefore this module explicitly updates updated_at whenever
# a new message is sent.
#
# This allows the most recently active conversation to appear
# first in the Inbox.
#
# ============================================================

# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

from django.contrib import messages  # Import Django's temporary user-notification system.
from django.contrib.auth.decorators import (  # Import authentication decorators from Django.
    login_required,  # Protect views so only authenticated users can access them.
)
from django.db import transaction  # Import Django database transaction management.
from django.db.models import (  # Import tools used to build and optimise database queries.
    Prefetch,  # Preload related objects using a customised queryset.
    Q,  # Build complex database conditions using AND/OR logic.
)
from django.shortcuts import (  # Import common Django view helper functions.
    get_object_or_404,  # Get one database object or return an HTTP 404 response.
    redirect,  # Return an HTTP redirect response.
    render,  # Combine a template and context data into an HTTP response.
)
from django.utils import timezone  # Import Django's timezone-aware date/time tools.

# ============================================================
# 2. COMMUNITY IMPORTS
# ============================================================

from .forms import (  # Import forms from the current community Django application.
    CommunityPostForm,  # Form used to create a community post.
    MessageReplyForm,  # Form used to reply inside a conversation.
    NewConversationForm,  # Form used to start a new conversation.
)
from .models import (  # Import database model classes from this Django application.
    CommunityPost,  # Model representing one community feed post.
    Conversation,  # Model representing a private conversation/thread.
    PrivateMessage,  # Model representing one private message.
)

# ============================================================
# 3. PRIVATE HELPER FUNCTIONS
# ============================================================
#
# PROGRAMMING CONCEPT:
#
# Helper functions contain reusable logic that other view
# functions can call.
#
# The leading "_" is a Python naming convention meaning:
#
#     "This function is intended for internal use."
#
# ============================================================

# ============================================================
# 3.1 GET OTHER PARTICIPANT
# ============================================================

def _get_other_participant(  # Define a reusable Python function.
    conversation,  # Parameter containing the Conversation object.
    current_user,  # Parameter containing the currently logged-in user.
):
    """
    Return the participant other than current_user.

    MarketPulse currently supports direct one-to-one
    conversations.

    Example:

        Conversation
            ↓
        User1 + User2

    If User1 is the authenticated user:

        current_user = User1

    this function returns:

        User2

    If no other participant exists, return None.
    """

    if (  # Begin a conditional statement for invalid input.
        conversation is None  # Check whether no Conversation object was supplied.
        or current_user is None  # OR check whether no current user was supplied.
        or not getattr(  # OR check whether the user does not have a valid primary key.
            current_user,  # Object whose attribute we want to inspect.
            "pk",  # Name of the primary-key attribute.
            None,  # Default value if the attribute does not exist.
        )
    ):
        return None  # Stop the function and return no participant.

    return (  # Return the result of the following Django ORM query.
        conversation  # Start with the current Conversation object.
        .participants  # Access its related participants manager.
        .exclude(  # Remove a participant matching the supplied condition.
            pk=current_user.pk,  # Exclude the currently logged-in user's primary key.
        )
        .order_by(  # Sort the remaining participant records.
            "username",  # Sort alphabetically by username.
        )
        .first()  # Return the first result, or None if there is no result.
    )

# ============================================================
# 3.2 FIND EXISTING DIRECT CONVERSATION
# ============================================================

def _find_direct_conversation(  # Define a helper for locating an existing direct conversation.
    user,  # First User object supplied to the function.
    other_user,  # Second User object supplied to the function.
):
    """
    Find an existing one-to-one conversation containing
    exactly the supplied two users.

    Example:

        User1 ↔ User2

    If that conversation already exists, reuse it rather than
    creating another duplicate conversation.

    This keeps one continuous chat thread between the same
    pair of MarketPulse users.
    """

    # --------------------------------------------------------
    # 3.2.1 VALIDATE USERS
    # --------------------------------------------------------
    #
    # PROGRAMMING CONCEPT:
    # Boolean expressions combine several validation rules.
    # --------------------------------------------------------

    if (  # Start validation condition.
        user is None  # Check whether the first user is missing.
        or other_user is None  # Check whether the second user is missing.
        or not getattr(  # Check whether the first user has no valid primary key.
            user,  # Inspect the first user object.
            "pk",  # Look for its primary-key attribute.
            None,  # Return None if that attribute does not exist.
        )
        or not getattr(  # Check whether the second user has no valid primary key.
            other_user,  # Inspect the second user object.
            "pk",  # Look for its primary-key attribute.
            None,  # Return None if that attribute does not exist.
        )
        or user.pk == other_user.pk  # Prevent comparing a user with themselves.
    ):
        return None  # No valid direct conversation can exist for these inputs.

    # --------------------------------------------------------
    # 3.2.2 FIND CONVERSATIONS CONTAINING BOTH USERS
    # --------------------------------------------------------
    #
    # PROGRAMMING CONCEPT:
    # Method chaining passes each QuerySet operation into the
    # next operation.
    # --------------------------------------------------------

    candidates = (  # Assign the resulting QuerySet to the variable candidates.
        Conversation.objects  # Access the Conversation model's database manager.
        .filter(  # Filter Conversation records.
            participants=user,  # Keep conversations containing the first user.
        )
        .filter(  # Apply a second filter.
            participants=other_user,  # Also require the other user to participate.
        )
        .prefetch_related(  # Efficiently preload related participant records.
            "participants",  # Name of the related field to preload.
        )
        .distinct()  # Remove duplicate Conversation rows from the query result.
    )

    # --------------------------------------------------------
    # 3.2.3 CONFIRM EXACTLY THESE TWO USERS
    # --------------------------------------------------------

    for conversation in candidates:  # Loop through every candidate Conversation object.
        participant_ids = {  # Create a Python set containing participant IDs.
            participant.pk  # Put each participant's primary key into the set.
            for participant  # Start a set-comprehension loop variable.
            in conversation.participants.all()  # Loop through all participants in this conversation.
        }

        if participant_ids == {  # Compare the participant set with the expected set.
            user.pk,  # Expected primary key of the first user.
            other_user.pk,  # Expected primary key of the second user.
        }:
            return conversation  # Return the matching Conversation and stop searching.

    return None  # Return None when no exact direct conversation was found.

# ============================================================
# 3.3 COMPATIBILITY SUBJECT
# ============================================================

def _conversation_subject(  # Define a helper function for generating/reusing a subject.
    conversation,  # Conversation for which a subject is required.
    other_user,  # Other participant used when creating a default subject.
):
    """
    Return an internal compatibility subject.

    The new conversation interface no longer asks the user to
    enter a subject for every message.

    However:

        PrivateMessage.subject

    still exists in the transitional database model.

    Therefore MarketPulse creates an internal subject so older
    code and existing database structure remain compatible.
    """

    # --------------------------------------------------------
    # 3.3.1 REUSE AN EXISTING CONVERSATION SUBJECT
    # --------------------------------------------------------

    existing_message = (  # Store the newest message containing a subject.
        PrivateMessage.objects  # Access the PrivateMessage database manager.
        .filter(  # Filter PrivateMessage records.
            conversation=conversation,  # Only messages belonging to this conversation.
        )
        .exclude(  # Exclude records matching the following condition.
            subject="",  # Ignore messages with an empty subject.
        )
        .order_by(  # Sort matching messages.
            "-created_at",  # Minus means newest date first.
        )
        .first()  # Return the first result or None.
    )

    if (  # Check whether a suitable message exists.
        existing_message  # Test whether existing_message is truthy/not None.
        and existing_message.subject  # Also require that it contains a subject.
    ):
        return existing_message.subject[:150]  # Return at most the first 150 characters.

    # --------------------------------------------------------
    # 3.3.2 OTHERWISE GENERATE A DEFAULT SUBJECT
    # --------------------------------------------------------

    if other_user:  # Check whether another user object exists.
        return (  # Return a dynamically generated string.
            f"Conversation with "  # First part of an f-string expression.
            f"{other_user.username}"  # Insert the other user's username.
        )[:150]  # Limit the resulting string to 150 characters.

    return "MarketPulse Conversation"  # Return a fallback subject when no other user exists.

# ============================================================
# 3.4 UPDATE CONVERSATION ACTIVITY
# ============================================================

def _touch_conversation(  # Define a helper that updates conversation activity time.
    conversation,  # Conversation object supplied to the helper.
):
    """
    Update Conversation.updated_at whenever a new message is
    created.

    This ensures the most recently active conversation appears
    at the top of the Inbox.
    """

    if (  # Validate the supplied Conversation object.
        conversation is None  # Check whether the conversation is missing.
        or conversation.pk is None  # Check whether it has not been saved to the database.
    ):
        return  # Exit the function without doing anything.

    current_time = timezone.now()  # Store the current timezone-aware date/time in a variable.

    Conversation.objects.filter(  # Find the matching Conversation database row.
        pk=conversation.pk,  # Match its primary key.
    ).update(  # Perform a direct SQL-style update through Django ORM.
        updated_at=current_time,  # Replace updated_at with the current time.
    )

    # --------------------------------------------------------
    # 3.4.1 KEEP CURRENT PYTHON OBJECT SYNCHRONISED
    # --------------------------------------------------------

    conversation.updated_at = (  # Update the in-memory Python object's attribute too.
        current_time  # Store the same current time on the object.
    )

# ============================================================
# 4. COMMUNITY FEED VIEW
# ============================================================
#
# DJANGO FLOW:
#
# Browser
#     ↓
# URL pattern
#     ↓
# feed(request)
#     ↓
# CommunityPostForm
#     ↓
# CommunityPost model
#     ↓
# Django ORM
#     ↓
# PostgreSQL
#     ↓
# feed.html
#
# PROGRAMMING CONCEPTS:
#
# - decorator
# - function
# - parameter
# - variable
# - conditional
# - object
# - method
# - return value
# - dictionary
#
# ============================================================

@login_required  # Decorator: require an authenticated user before running feed().
def feed(request):  # Define the feed view; Django supplies the HTTP request object.
    """
    Display the MarketPulse Community Feed and allow an
    authenticated user to publish a CommunityPost.

    Framework flow:

        Browser
            ↓
        community:feed
            ↓
        feed()
            ↓
        CommunityPostForm
            ↓
        CommunityPost
            ↓
        PostgreSQL
            ↓
        community/feed.html
    """

    # ========================================================
    # 4.1 FETCH COMMUNITY POSTS
    # ========================================================

    posts = (  # Store a QuerySet of CommunityPost objects.
        CommunityPost.objects  # Access the CommunityPost model's database manager.
        .select_related(  # Fetch a related foreign-key object in the same database query.
            "author",  # Load each post's author efficiently.
        )
        .all()  # Return all CommunityPost records.
    )

    # ========================================================
    # 4.2 CREATE COMMUNITY POST
    # ========================================================

    if request.method == "POST":  # Check whether the browser submitted form data using HTTP POST.
        form = CommunityPostForm(  # Create a form object containing submitted data.
            request.POST,  # Pass Django's dictionary-like POST data into the form.
        )

        if form.is_valid():  # Run form validation and continue only when data is valid.
            post = form.save(  # Create a CommunityPost model object from the form.
                commit=False,  # Do not save it to the database yet.
            )

            post.author = (  # Assign the post's author attribute.
                request.user  # Use the currently authenticated user.
            )

            post.save()  # Save the completed CommunityPost object to the database.

            messages.success(  # Add a temporary success notification for the user.
                request,  # Attach the notification to this HTTP request/session.
                (  # Group adjacent strings as one Python expression.
                    "Your community post "  # First part of the message string.
                    "has been published."  # Second part of the message string.
                ),
            )

            # ------------------------------------------------
            # POST / REDIRECT / GET
            #
            # Prevent duplicate submission if browser refreshes.
            # ------------------------------------------------

            return redirect(  # Return an HTTP redirect instead of rendering immediately.
                "community:feed",  # Resolve the named community feed URL.
            )

    # ========================================================
    # 4.3 GET - EMPTY FORM
    # ========================================================

    else:  # Run this branch when the request is not POST.
        form = (  # Assign a blank form object to the variable form.
            CommunityPostForm()  # Create an empty CommunityPostForm for the page.
        )

    # ========================================================
    # 4.4 RENDER FEED
    # ========================================================

    return render(  # Return an HTTP response generated from a Django template.
        request,  # Supply the current HTTP request.
        "community/feed.html",  # Template file Django should render.
        {  # Begin the context dictionary sent to the template.
            "posts":  # Dictionary key available inside the template.
                posts,  # QuerySet value assigned to the posts template variable.
            "form":  # Dictionary key available inside the template.
                form,  # Form object assigned to the form template variable.
        },
    )

# ============================================================
# 5. INBOX / CONVERSATION LIST VIEW
# ============================================================
#
# FRAMEWORK FLOW:
#
# Browser
#     ↓
# inbox()
#     ↓
# Conversation model
#     ↓
# PrivateMessage model
#     ↓
# Django ORM
#     ↓
# PostgreSQL
#     ↓
# inbox.html
#
# ============================================================

@login_required  # Require the user to be authenticated before opening their inbox.
def inbox(request):  # Define the inbox Django view.
    """
    Display all private conversations belonging to the
    authenticated user.

    Previous architecture:

        Received Messages
        Sent Messages

    Updated architecture:

        Conversations
            ↓
        User2
        User3
        User4

    Each Conversation is prepared with:

        conversation.other_user
        conversation.last_message
        conversation.unread_count

    These values are used by:

        community/templates/community/inbox.html
    """

    # ========================================================
    # 5.1 FETCH USER CONVERSATIONS
    # ========================================================

    conversations = (  # Store the resulting Conversation QuerySet.
        Conversation.objects  # Access the Conversation model manager.

        # ----------------------------------------------------
        # SECURITY
        #
        # Only conversations containing the authenticated
        # user are returned.
        # ----------------------------------------------------

        .filter(  # Restrict the QuerySet using a database condition.
            participants=request.user,  # Require the current user to be a participant.
        )

        # ----------------------------------------------------
        # LOAD RELATED DATA EFFICIENTLY
        # ----------------------------------------------------

        .prefetch_related(  # Load many-to-many/reverse related objects efficiently.
            "participants",  # Preload all users participating in each conversation.
            Prefetch(  # Create a customised prefetch instruction.
                "messages",  # Related field that should be prefetched.
                queryset=(  # Supply the customised PrivateMessage QuerySet.
                    PrivateMessage.objects  # Access the PrivateMessage model manager.
                    .select_related(  # Join foreign-key relationships efficiently.
                        "sender",  # Load sender User objects in the same query.
                        "recipient",  # Load recipient User objects in the same query.
                    )

                    # -----------------------------------------
                    # Inbox needs newest message first
                    # -----------------------------------------

                    .order_by(  # Sort prefetched messages.
                        "-created_at",  # Newest message first.
                    )
                ),
                to_attr=  # Store prefetched messages on a custom Python attribute.
                    "inbox_messages",  # Attribute name used later in this view.
            ),
        )

        # ----------------------------------------------------
        # MOST RECENTLY ACTIVE CONVERSATION FIRST
        # ----------------------------------------------------

        .order_by(  # Sort Conversation records.
            "-updated_at",  # Put the newest activity first.
        )
        .distinct()  # Remove duplicate database rows.
    )

    # ========================================================
    # 5.2 PREPARE CONVERSATION DATA FOR TEMPLATE
    # ========================================================

    conversation_list = []  # Create an empty Python list to hold prepared conversations.

    for conversation in conversations:  # Loop through each Conversation returned by the ORM.

        # ----------------------------------------------------
        # OTHER PARTICIPANT
        # ----------------------------------------------------

        conversation.other_user = (  # Create a temporary attribute for template use.
            _get_other_participant(  # Call the helper function defined earlier.
                conversation,  # Pass the current Conversation object.
                request.user,  # Pass the authenticated User object.
            )
        )

        # ----------------------------------------------------
        # PREFETCHED MESSAGES
        #
        # Already ordered:
        #
        # newest
        #   ↓
        # oldest
        # ----------------------------------------------------

        prefetched_messages = getattr(  # Safely read an object's attribute.
            conversation,  # Object whose attribute should be retrieved.
            "inbox_messages",  # Attribute created by Prefetch().
            [],  # Use an empty list if that attribute does not exist.
        )

        # ----------------------------------------------------
        # LAST MESSAGE
        # ----------------------------------------------------

        conversation.last_message = (  # Add a temporary last_message attribute.
            prefetched_messages[0]  # List indexing: element zero is the newest message.
            if prefetched_messages  # Conditional expression: use it when list is non-empty.
            else None  # Otherwise store None.
        )

        # ----------------------------------------------------
        # UNREAD INCOMING MESSAGE COUNT
        # ----------------------------------------------------

        conversation.unread_count = sum(  # Count matching messages using sum().
            1  # Produce the number 1 for every matching message.
            for message  # Begin a generator-expression loop.
            in prefetched_messages  # Examine every prefetched message.
            if (  # Include the value only when this condition is True.
                message.recipient_id  # Get the message recipient's database ID.
                ==
                request.user.pk  # Compare it with the current user's primary key.
                and  # Both Boolean conditions must be True.
                not message.is_read  # Require the message to still be unread.
            )
        )

        conversation_list.append(  # Call the Python list append() method.
            conversation,  # Add this prepared conversation to the list.
        )

    # ========================================================
    # 5.3 LEGACY MESSAGE COUNT
    # ========================================================
    #
    # Existing PrivateMessage records created before the
    # Conversation model may still contain:
    #
    # conversation = NULL
    #
    # They remain safely stored in the database until the
    # migration step assigns them to Conversation records.
    #
    # Q OBJECTS:
    #
    # Q(sender=user) | Q(recipient=user)
    #
    # "|" means OR at the database-query level.
    # ========================================================

    legacy_message_count = (  # Store the number of legacy messages.
        PrivateMessage.objects  # Access the PrivateMessage database manager.
        .filter(  # Apply the first database filter.
            conversation__isnull=True,  # Require conversation to contain SQL NULL.
        )
        .filter(  # Apply another database condition.
            Q(  # Build the first side of an OR condition.
                sender=request.user,  # Message was sent by the current user.
            )
            |  # Combine Q objects using OR.
            Q(  # Build the second side of the OR condition.
                recipient=request.user,  # Message was received by the current user.
            )
        )
        .count()  # Ask the database to count matching records.
    )

    # ========================================================
    # 5.4 TOTAL UNREAD MESSAGES
    # ========================================================

    total_unread = sum(  # Add together the unread counts from all conversations.
        conversation.unread_count  # Value contributed by each Conversation object.
        for conversation  # Generator-expression loop variable.
        in conversation_list  # Loop through prepared conversations.
    )

    # ========================================================
    # 5.5 RENDER INBOX
    # ========================================================

    return render(  # Render and return the Inbox HTML page.
        request,  # Current HTTP request.
        "community/inbox.html",  # Template to display.
        {  # Context dictionary supplied to the template.
            "conversations":  # Template variable name.
                conversation_list,  # Prepared Conversation objects.
            "total_unread":  # Template variable name.
                total_unread,  # Total number of unread messages.
            "legacy_message_count":  # Template variable name.
                legacy_message_count,  # Number of old messages not yet assigned to threads.
        },
    )

# ============================================================
# 6. START NEW CONVERSATION VIEW
# ============================================================
#
# IMPORTANT PROGRAMMING CONCEPT:
#
# transaction.atomic()
#
# Everything inside the transaction should succeed together.
# If a database error occurs, Django can roll the transaction
# back rather than leaving only part of the conversation saved.
#
# ============================================================

@login_required  # Require authentication before starting a private conversation.
def new_conversation(request):  # Define the view responsible for creating conversations.
    """
    Start a new direct conversation with another MarketPulse
    user.

    If the two users already have a direct conversation:

        existing Conversation
            ↓
        reuse it
            ↓
        add message

    Otherwise:

        create Conversation
            ↓
        add both participants
            ↓
        create first PrivateMessage

    This prevents duplicate chat threads between the same
    two users.
    """

    # ========================================================
    # 6.1 POST REQUEST
    # ========================================================

    if request.method == "POST":  # Check whether the user submitted the form.
        form = NewConversationForm(  # Construct a bound form from the submitted request.
            request.POST,  # Pass submitted POST data.
            sender=request.user,  # Pass the logged-in user as an extra form argument.
        )

        if form.is_valid():  # Continue only if all form-validation rules pass.
            recipient = (  # Store the validated recipient User object.
                form.cleaned_data[  # Access Django form data after validation.
                    "recipient"  # Retrieve the value belonging to the recipient field.
                ]
            )

            body = (  # Store the validated message body.
                form.cleaned_data[  # Access validated form values.
                    "body"  # Retrieve the value belonging to the body field.
                ]
                .strip()  # Remove whitespace from the beginning and end of the string.
            )

            # =================================================
            # 6.1.1 DEFENCE-IN-DEPTH:
            # PREVENT SELF-MESSAGING
            # =================================================
            #
            # NewConversationForm already performs this check.
            #
            # The view checks it again so the business rule is
            # also protected here.
            #
            # PROGRAMMING CONCEPT:
            # Repeating an important security/business check at
            # multiple application layers is defence-in-depth.
            # =================================================

            if (  # Begin the self-message validation condition.
                recipient.pk  # Get the selected recipient's primary key.
                ==
                request.user.pk  # Compare it with the current user's primary key.
            ):
                form.add_error(  # Add a validation error to the existing form object.
                    "recipient",  # Attach the error to the recipient field.
                    (  # Create one message from adjacent strings.
                        "You cannot start a "  # First part of the error message.
                        "conversation with yourself."  # Second part of the error message.
                    ),
                )

            # =================================================
            # 6.1.2 PREVENT EMPTY MESSAGE
            # =================================================

            elif not body:  # Otherwise check whether body is empty after strip().
                form.add_error(  # Add an error without throwing an exception.
                    "body",  # Attach the error to the message-body field.
                    "Please enter a message.",  # Human-readable validation message.
                )

            # =================================================
            # 6.1.3 CREATE / REUSE CONVERSATION
            # =================================================

            else:  # Run when recipient and body both pass the extra checks.
                with transaction.atomic():  # Start an atomic database transaction.

                    # -----------------------------------------
                    # Find existing one-to-one thread
                    # -----------------------------------------

                    conversation = (  # Store an existing Conversation or None.
                        _find_direct_conversation(  # Call the helper defined earlier.
                            request.user,  # First participant is the logged-in user.
                            recipient,  # Second participant is the selected recipient.
                        )
                    )

                    conversation_created = (  # Store a Boolean True/False value.
                        conversation is None  # True means an existing conversation was not found.
                    )

                    # -----------------------------------------
                    # Create new conversation when necessary
                    # -----------------------------------------

                    if conversation_created:  # Run only if no existing conversation was found.
                        conversation = (  # Store the newly created Conversation object.
                            Conversation.objects.create()  # Insert a Conversation row in the database.
                        )

                        conversation.participants.add(  # Add users to the many-to-many relationship.
                            request.user,  # Add the logged-in user.
                            recipient,  # Add the selected recipient.
                        )

                    # -----------------------------------------
                    # Generate compatibility subject
                    # -----------------------------------------

                    subject = (  # Store the returned compatibility subject.
                        _conversation_subject(  # Call the helper function defined earlier.
                            conversation,  # Pass the current Conversation.
                            recipient,  # Pass the other participant.
                        )
                    )

                    # -----------------------------------------
                    # Save first/new message
                    # -----------------------------------------

                    PrivateMessage.objects.create(  # Create and immediately save a PrivateMessage.
                        conversation=  # Set the conversation foreign-key field.
                            conversation,  # Associate the message with this thread.
                        sender=  # Set the sender foreign-key field.
                            request.user,  # Current user sends the message.
                        recipient=  # Set the recipient foreign-key field.
                            recipient,  # Selected user receives the message.
                        subject=  # Set the compatibility subject field.
                            subject,  # Use the subject created above.
                        body=  # Set the message body field.
                            body,  # Save the cleaned message text.
                    )

                    # -----------------------------------------
                    # Update conversation activity
                    # -----------------------------------------

                    _touch_conversation(  # Call the timestamp helper function.
                        conversation,  # Update this conversation's activity time.
                    )

                # =================================================
                # 6.1.4 SUCCESS MESSAGE
                # =================================================

                if conversation_created:  # Check whether this was a brand-new conversation.
                    messages.success(  # Add a temporary Django success message.
                        request,  # Associate it with the current request/session.
                        (  # Create one string from several f-strings.
                            f"Conversation with "  # Beginning of success message.
                            f"{recipient.username} "  # Insert recipient username dynamically.
                            f"has been started."  # End of success message.
                        ),
                    )

                else:  # Run when the conversation already existed.
                    messages.success(  # Add another temporary success notification.
                        request,  # Associate notification with the current request.
                        (  # Combine the following f-string pieces.
                            f"Message sent to "  # Beginning of message.
                            f"{recipient.username}."  # Insert recipient username.
                        ),
                    )

                # =================================================
                # 6.1.5 OPEN CONVERSATION THREAD
                # =================================================

                return redirect(  # Return a redirect response to the browser.
                    "community:conversation_detail",  # Named URL of the conversation thread.
                    pk=conversation.pk,  # Supply the Conversation primary key to the URL.
                )

    # ========================================================
    # 6.2 GET REQUEST
    # ========================================================

    else:  # Run when the browser requests the page normally using GET.
        form = NewConversationForm(  # Create an empty new-conversation form.
            sender=request.user,  # Tell the form who the current sender is.
        )

    # ========================================================
    # 6.3 RENDER NEW-CONVERSATION FORM
    # ========================================================

    return render(  # Render the new-conversation page.
        request,  # Current HTTP request.
        "community/compose_message.html",  # Template responsible for the form interface.
        {  # Context dictionary sent to the template.
            "form":  # Template variable name.
                form,  # Send the form object to the template.
            "conversation_mode":  # Template variable name.
                True,  # Boolean value telling the template conversation mode is active.
        },
    )

# ============================================================
# 7. CONVERSATION THREAD VIEW
# ============================================================
#
# SECURITY FLOW:
#
# URL contains conversation ID
#       ↓
# queryset requires participants=request.user
#       ↓
# get_object_or_404()
#       ↓
# User gets conversation OR HTTP 404
#
# ============================================================

@login_required  # Require authentication before accessing private conversation messages.
def conversation_detail(  # Define a view for one complete conversation.
    request,  # HTTP request supplied by Django.
    pk,  # Conversation primary key captured from the URL.
):
    """
    Display one complete private Conversation and process
    replies.

    SECURITY:

    The Conversation query is restricted to:

        participants=request.user

    Therefore an authenticated user cannot manually change:

        /community/inbox/conversation/5/

    to:

        /community/inbox/conversation/6/

    and read Conversation 6 unless they are actually one of
    its participants.
    """

    # ========================================================
    # 7.1 AUTHORISED CONVERSATION QUERYSET
    # ========================================================

    conversation_queryset = (  # Store a security-restricted Conversation QuerySet.
        Conversation.objects  # Access the Conversation model manager.
        .filter(  # Restrict available conversations.
            participants=request.user,  # Current user must participate in the conversation.
        )
        .prefetch_related(  # Efficiently preload many-to-many participant objects.
            "participants",  # Related users to preload.
        )
        .distinct()  # Remove possible duplicate rows.
    )

    # ========================================================
    # 7.2 LOAD CONVERSATION
    # ========================================================

    conversation = get_object_or_404(  # Fetch an object or automatically return HTTP 404.
        conversation_queryset,  # Search only inside the authorised QuerySet.
        pk=pk,  # Require the requested primary key.
    )

    # ========================================================
    # 7.3 DETERMINE OTHER PARTICIPANT
    # ========================================================

    other_user = (  # Store the other participant.
        _get_other_participant(  # Call the reusable helper function.
            conversation,  # Supply the loaded conversation.
            request.user,  # Supply the authenticated user.
        )
    )

    # ========================================================
    # 7.4 CONVERSATION INTEGRITY
    # ========================================================

    if other_user is None:  # Check whether the conversation has no valid second participant.
        messages.error(  # Add a temporary error notification.
            request,  # Associate the error with the current request.
            (  # Combine adjacent strings.
                "This conversation does not have "  # First part of message.
                "another participant."  # Second part of message.
            ),
        )

        return redirect(  # Return the user to another URL.
            "community:inbox",  # Redirect back to the Inbox.
        )

    # ========================================================
    # 7.5 MARK INCOMING MESSAGES AS READ
    # ========================================================
    #
    # Only messages addressed to request.user are updated.
    #
    # The other participant's outgoing messages remain
    # unchanged.
    # ========================================================

    (  # Group the chained ORM expression.
        PrivateMessage.objects  # Access PrivateMessage records.
        .filter(  # Restrict which messages should be updated.
            conversation=conversation,  # Require this conversation.
            recipient=request.user,  # Require current user as recipient.
            is_read=False,  # Require currently unread messages.
        )
        .update(  # Perform a bulk database update.
            is_read=True,  # Mark every matching message as read.
        )
    )

    # ========================================================
    # 7.6 PROCESS REPLY
    # ========================================================

    if request.method == "POST":  # Check whether the conversation reply form was submitted.
        reply_form = MessageReplyForm(  # Build a form containing the submitted values.
            request.POST,  # Pass the submitted POST dictionary.
        )

        if reply_form.is_valid():  # Validate the submitted reply.
            body = (  # Store cleaned reply text.
                reply_form.cleaned_data[  # Access validated form data.
                    "body"  # Retrieve the body field.
                ]
                .strip()  # Remove surrounding whitespace.
            )

            # ------------------------------------------------
            # Defence-in-depth empty-message check
            # ------------------------------------------------

            if not body:  # Check whether the cleaned message is empty.
                reply_form.add_error(  # Add an error to the existing form.
                    "body",  # Associate the error with the body field.
                    "Please enter a message.",  # Validation message shown to the user.
                )

            else:  # Run when the reply contains valid text.
                with transaction.atomic():  # Start an all-or-nothing database transaction.

                    # -----------------------------------------
                    # Compatibility subject
                    # -----------------------------------------

                    subject = (  # Store the compatibility subject.
                        _conversation_subject(  # Call the subject helper.
                            conversation,  # Pass the active Conversation.
                            other_user,  # Pass its other participant.
                        )
                    )

                    # -----------------------------------------
                    # Save reply into SAME Conversation
                    # -----------------------------------------

                    PrivateMessage.objects.create(  # Insert the reply into the database.
                        conversation=  # Set conversation foreign key.
                            conversation,  # Keep reply in the current thread.
                        sender=  # Set sender foreign key.
                            request.user,  # Current authenticated user is sending it.
                        recipient=  # Set recipient foreign key.
                            other_user,  # Other participant receives it.
                        subject=  # Set transitional subject field.
                            subject,  # Use generated/reused compatibility subject.
                        body=  # Set body field.
                            body,  # Store cleaned message text.
                    )

                    # -----------------------------------------
                    # Move active thread to top of Inbox
                    # -----------------------------------------

                    _touch_conversation(  # Update the Conversation activity timestamp.
                        conversation,  # Conversation whose timestamp should change.
                    )

                # ------------------------------------------------
                # POST / REDIRECT / GET
                #
                # Prevent duplicate message submission after a
                # browser refresh.
                # ------------------------------------------------

                return redirect(  # Redirect after successfully processing POST.
                    "community:conversation_detail",  # Return to this conversation page.
                    pk=conversation.pk,  # Pass this Conversation's primary key.
                )

    # ========================================================
    # 7.7 GET - EMPTY REPLY FORM
    # ========================================================

    else:  # Run when the request is a normal GET.
        reply_form = (  # Store an empty reply form.
            MessageReplyForm()  # Instantiate the form without submitted data.
        )

    # ========================================================
    # 7.8 FETCH COMPLETE CONVERSATION HISTORY
    # ========================================================
    #
    # Chat messages display chronologically:
    #
    # oldest
    #   ↓
    # newest
    # ========================================================

    conversation_messages = (  # Store a QuerySet containing the complete message history.
        PrivateMessage.objects  # Access PrivateMessage database records.
        .filter(  # Restrict messages to one conversation.
            conversation=conversation,  # Require the currently opened conversation.
        )
        .select_related(  # Efficiently load related foreign-key User objects.
            "sender",  # Join sender data.
            "recipient",  # Join recipient data.
        )
        .order_by(  # Sort messages chronologically.
            "created_at",  # Oldest created date first.
        )
    )

    # ========================================================
    # 7.9 RENDER CHAT THREAD
    # ========================================================
    #
    # message_thread.html receives:
    #
    # conversation
    # other_user
    # conversation_messages
    # reply_form
    #
    # ========================================================

    return render(  # Render the final conversation page.
        request,  # Current HTTP request.
        "community/message_thread.html",  # Template responsible for the message thread.
        {  # Context dictionary sent into the template.
            "conversation":  # Template variable name.
                conversation,  # Current Conversation object.
            "other_user":  # Template variable name.
                other_user,  # Other participant's User object.
            "conversation_messages":  # Template variable name.
                conversation_messages,  # Chronological PrivateMessage QuerySet.
            "reply_form":  # Template variable name.
                reply_form,  # Reply form object.
        },
    )

# ============================================================
# 8. LEGACY COMPOSE MESSAGE COMPATIBILITY
# ============================================================
#
# PROGRAMMING CONCEPT:
#
# Function reuse.
#
# Instead of copying the new-conversation code, this function
# simply calls new_conversation() and returns its result.
#
# ============================================================

@login_required  # Keep the old route protected by authentication.
def compose_message(request):  # Define the legacy compatibility view.
    """
    Preserve the original:

        community:compose_message

    route during the transition to the new Conversation
    architecture.

    Older templates may still link to:

        /community/inbox/compose/

    Instead of maintaining two separate messaging systems,
    that route now uses the same new-conversation workflow.

    Once all templates use:

        community:new_conversation

    this compatibility view can eventually be removed.
    """

    return new_conversation(  # Call and return the newer view function.
        request,  # Forward the same HTTP request.
    )

# ============================================================
# 9. LEGACY MESSAGE DETAIL COMPATIBILITY
# ============================================================
#
# FRAMEWORK PURPOSE:
#
# Old URL
#     ↓
# message_detail()
#     ↓
# old PrivateMessage
#     ↓
# related Conversation
#     ↓
# redirect()
#     ↓
# new conversation_detail() URL
#
# ============================================================

@login_required  # Require an authenticated user before resolving an old message URL.
def message_detail(  # Define the legacy individual-message compatibility view.
    request,  # Current HTTP request.
    pk,  # PrivateMessage primary key captured from the URL.
):
    """
    Preserve older links pointing to one individual
    PrivateMessage.

    Previous architecture:

        /community/inbox/<message_id>/

    New architecture:

        /community/inbox/conversation/<conversation_id>/

    If the old message has already been assigned to a
    Conversation, redirect the authorised user to the complete
    conversation thread.

    If conversation is still NULL, return the user to the Inbox
    until legacy messages have been migrated.
    """

    # ========================================================
    # 9.1 AUTHORISED MESSAGE QUERYSET
    # ========================================================

    authorised_messages = (  # Build a QuerySet containing messages this user may inspect.
        PrivateMessage.objects  # Access the PrivateMessage model manager.
        .select_related(  # Load related foreign-key objects efficiently.
            "conversation",  # Load related Conversation.
            "sender",  # Load related sender User.
            "recipient",  # Load related recipient User.
        )
        .filter(  # Apply authorisation conditions.
            Q(  # First possible permission condition.
                sender=request.user,  # Current user sent the message.
            )
            |  # OR.
            Q(  # Second possible permission condition.
                recipient=request.user,  # Current user received the message.
            )
            |  # OR.
            Q(  # Third possible permission condition.
                conversation__participants=request.user,  # Current user belongs to its Conversation.
            )
        )
        .distinct()  # Remove duplicate rows caused by relationship joins.
    )

    # ========================================================
    # 9.2 FETCH MESSAGE
    # ========================================================

    message_object = get_object_or_404(  # Get an authorised message or return HTTP 404.
        authorised_messages,  # Restrict lookup to the authorised QuerySet.
        pk=pk,  # Require the requested message primary key.
    )

    # ========================================================
    # 9.3 LEGACY MESSAGE WITHOUT CONVERSATION
    # ========================================================

    if (  # Check whether the old message has no Conversation relationship.
        message_object.conversation_id  # Access the raw Conversation foreign-key ID.
        is None  # Test whether the value is Python None / database NULL.
    ):
        messages.info(  # Add an informational Django message.
            request,  # Associate it with the current request.
            (  # Combine adjacent strings.
                "This older message has not yet "  # First part.
                "been assigned to a conversation "  # Second part.
                "thread."  # Final part.
            ),
        )

        return redirect(  # Return an HTTP redirect.
            "community:inbox",  # Send the user back to their Inbox.
        )

    # ========================================================
    # 9.4 DEFENCE-IN-DEPTH PARTICIPANT CHECK
    # ========================================================

    user_is_participant = (  # Store a Boolean True/False result.
        message_object  # Start from the PrivateMessage instance.
        .conversation  # Access its related Conversation.
        .participants  # Access the Conversation's many-to-many participant manager.
        .filter(  # Restrict participants by primary key.
            pk=request.user.pk,  # Look for the authenticated user's ID.
        )
        .exists()  # Ask the database whether at least one matching record exists.
    )

    if not user_is_participant:  # Check whether the Boolean value is False.
        messages.error(  # Add an error notification.
            request,  # Associate it with this request.
            (  # Combine adjacent message strings.
                "You do not have permission to "  # First part.
                "open that conversation."  # Second part.
            ),
        )

        return redirect(  # Redirect instead of displaying unauthorised content.
            "community:inbox",  # Return user to their Inbox.
        )

    # ========================================================
    # 9.5 REDIRECT TO COMPLETE CONVERSATION
    # ========================================================

    return redirect(  # Return an HTTP redirect response.
        "community:conversation_detail",  # Use the new Conversation-based URL.
        pk=message_object.conversation_id,  # Pass the related Conversation primary key.
    )